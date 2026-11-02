"""
================================================================================
Pharmacy Management System - Supplier Purchase & Restocking Service
================================================================================
Module: pharmacy_management.services.purchase_service
Quality Objective: Q10 - Improve Documentation & Inbound Quality Control

Description:
    Processes wholesale supplier shipments, purchase invoices, and inventory
    restocking. Automatically increments physical stock counts upon receipt.
================================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.supplier import Supplier
from pharmacy_management.utils.helpers import generate_purchase_invoice_number
from pharmacy_management.utils.validators import (
    validate_text, validate_phone, validate_email, validate_positive_number,
    validate_integer, validate_date_string, validate_not_expired
)
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class PurchaseService:
    """Business service governing wholesale supplier purchases and stock replenishment."""

    def get_all_suppliers(self, active_only: bool = True) -> List[Supplier]:
        """Retrieves registered supplier partners."""
        sql = "SELECT * FROM suppliers"
        if active_only:
            sql += " WHERE status = 'Active'"
        sql += " ORDER BY name ASC"
        rows = db_manager.fetch_all(sql)
        return [Supplier.from_row(r) for r in rows]

    def add_supplier(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Registers a new pharmaceutical supplier partner with validation."""
        val_name = validate_text(data.get("name"), "Supplier Name", min_length=2, max_length=150)
        if not val_name:
            return False, val_name.message

        val_phone = validate_phone(data.get("phone"))
        if not val_phone:
            return False, val_phone.message

        if data.get("email"):
            val_mail = validate_email(data.get("email"))
            if not val_mail:
                return False, val_mail.message

        try:
            db_manager.execute_query(
                """
                INSERT INTO suppliers (name, contact_person, phone, email, address, gst_tax_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Active')
                """,
                (
                    data.get("name").strip(),
                    data.get("contact_person", "").strip() if data.get("contact_person") else None,
                    data.get("phone").strip(),
                    data.get("email", "").strip() if data.get("email") else None,
                    data.get("address", "").strip() if data.get("address") else None,
                    data.get("gst_tax_id", "").strip() if data.get("gst_tax_id") else None,
                )
            )
            return True, f"Supplier '{data.get('name')}' registered successfully."
        except Exception as exc:
            logger.error("Failed to add supplier: %s", exc)
            return False, f"Database error: {str(exc)}"

    def process_purchase(
        self,
        supplier_id: int,
        user_id: int,
        invoice_number: str,
        items: List[Dict[str, Any]],
        payment_status: str = "Paid",
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """Processes an inbound restocking shipment, updating stock levels atomically.

        Args:
            supplier_id (int): Foreign key to suppliers.
            user_id (int): Operator receiving stock.
            invoice_number (str): Supplier commercial invoice ID.
            items (List[Dict[str, Any]]): Line items with medicine_id, batch, expiry, quantity, cost_price.
            payment_status (str): 'Paid', 'Pending', or 'Partial'.
            notes (Optional[str]): Inbound inspection remarks.

        Returns:
            Tuple[bool, str, Optional[int]]: (Success, Message, Purchase ID)
        """
        if not items:
            return False, "No items in restocking order.", None

        inv_num = invoice_number.strip() if invoice_number else generate_purchase_invoice_number()

        # Validate all items
        total_amount = 0.0
        for item in items:
            mid = item.get("medicine_id")
            qty = item.get("quantity")
            cost = item.get("cost_price")
            exp = item.get("expiry_date")

            val_qty = validate_integer(qty, "Restock Quantity", min_value=1)
            if not val_qty:
                return False, val_qty.message, None

            val_cost = validate_positive_number(cost, "Cost Price")
            if not val_cost:
                return False, val_cost.message, None

            val_exp = validate_date_string(exp, "Expiry Date")
            if not val_exp:
                return False, val_exp.message, None

            line_tot = round(float(cost) * int(qty), 2)
            total_amount += line_tot

        total_amount = round(total_amount, 2)

        # Atomic Transaction
        conn = db_manager.get_connection()
        try:
            cursor = conn.cursor()

            # 1. Insert Purchase Header
            cursor.execute(
                """
                INSERT INTO purchases (invoice_number, supplier_id, user_id, total_amount, payment_status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (inv_num, supplier_id, user_id, total_amount, payment_status, notes)
            )
            purchase_id = cursor.lastrowid

            # 2. Insert Items and Increment Stock
            for item in items:
                mid = int(item["medicine_id"])
                qty = int(item["quantity"])
                cost = float(item["cost_price"])
                batch = str(item.get("batch_number", "")).strip()
                exp = str(item.get("expiry_date", "")).strip()
                tot = round(qty * cost, 2)

                cursor.execute(
                    """
                    INSERT INTO purchase_items (purchase_id, medicine_id, batch_number, expiry_date, quantity, cost_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (purchase_id, mid, batch, exp, qty, cost, tot)
                )

                # Increment inventory and update cost price / batch if provided
                cursor.execute(
                    """
                    UPDATE medicines
                    SET stock_quantity = stock_quantity + ?,
                        cost_price = ?,
                        batch_number = CASE WHEN ? != '' THEN ? ELSE batch_number END,
                        expiry_date = CASE WHEN ? != '' THEN ? ELSE expiry_date END
                    WHERE id = ?
                    """,
                    (qty, cost, batch, batch, exp, exp, mid)
                )

            conn.commit()
            cursor.close()
            logger.info("Purchase completed: %s (Amount: %s)", inv_num, total_amount)
            return True, f"Stock replenished successfully. PO #{inv_num}", purchase_id

        except Exception as exc:
            conn.rollback()
            logger.error("Failed to execute purchase transaction: %s", exc)
            return False, f"Database error during purchase: {str(exc)}", None

    def get_recent_purchases(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent purchase records."""
        sql = """
            SELECT p.*, s.name AS supplier_name, u.full_name AS receiver_name
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            JOIN users u ON p.user_id = u.id
            ORDER BY p.purchase_date DESC LIMIT ?
        """
        return db_manager.fetch_all(sql, (limit,))


# Global singleton instance
purchase_service = PurchaseService()

