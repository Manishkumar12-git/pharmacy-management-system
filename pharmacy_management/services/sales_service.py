"""
================================================================================
Pharmacy Management System - Retail Sales & POS Service
================================================================================
Module: pharmacy_management.services.sales_service
Quality Objective: Q10 - Improve Documentation & Poka-Yoke Error Prevention

Description:
    Processes retail sales transactions atomically under ACID guarantees.
    Enforces strict Poka-Yoke mistake-proofing:
      - Intercepts and blocks expired pharmaceuticals from being sold.
      - Blocks sales exceeding on-hand inventory levels.
      - Enforces authorized discount boundaries.
      - Decrements inventory counts atomically.
      - Calculates taxes, discounts, and awards customer loyalty points.
================================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.sale import Sale, SaleItem
from pharmacy_management.utils.helpers import generate_sale_invoice_number
from pharmacy_management.utils.validators import (
    validate_stock_availability, validate_not_expired, validate_positive_number
)
from pharmacy_management.config import settings
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class SalesService:
    """Business service governing retail POS transactions, dispensing, and customer checkout."""

    def validate_cart_item(self, medicine_id: int, quantity: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Performs pre-billing Poka-Yoke verification on an individual medicine.

        Args:
            medicine_id (int): Foreign key to medicines table.
            quantity (int): Units requested.

        Returns:
            Tuple[bool, str, Optional[Dict]]: (Valid, Message, Medicine dictionary)
        """
        row = db_manager.fetch_one("SELECT * FROM medicines WHERE id = ?", (medicine_id,))
        if not row:
            return False, "Medicine not found in catalog.", None

        medicine = dict(row)
        med_name = medicine.get("name", "Unknown Item")

        # 1. Poka-Yoke: Positive quantity
        if quantity <= 0:
            return False, f"Quantity for '{med_name}' must be at least 1 unit.", medicine

        # 2. Poka-Yoke: Check Expiry Date
        exp_check = validate_not_expired(medicine.get("expiry_date", ""), med_name)
        if not exp_check:
            self._log_poka_yoke(
                "EXPIRED_MEDICINE_BILLING_BLOCKED",
                f"MedID: {medicine_id}, Expiry: {medicine.get('expiry_date')}",
                exp_check.message
            )
            return False, exp_check.message, medicine

        # 3. Poka-Yoke: Check Stock Availability
        stock_check = validate_stock_availability(quantity, medicine.get("stock_quantity", 0), med_name)
        if not stock_check:
            self._log_poka_yoke(
                "OVERSTOCK_SALE_BLOCKED",
                f"Requested: {quantity}, Available: {medicine.get('stock_quantity')}",
                stock_check.message
            )
            return False, stock_check.message, medicine

        return True, "Item verified for dispensing.", medicine

    def process_sale(
        self,
        cart_items: List[Dict[str, Any]],
        user_id: int,
        customer_id: Optional[int] = None,
        discount_percent: float = 0.0,
        tax_percent: float = settings.DEFAULT_TAX_PERCENT,
        payment_method: str = "Cash",
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Executes a complete sales checkout transaction atomically.

        Args:
            cart_items (List[Dict[str, Any]]): List of dicts containing 'medicine_id' and 'quantity'.
            user_id (int): Operator ID performing checkout.
            customer_id (Optional[int]): Customer ID or None for walk-in.
            discount_percent (float): Discount rate applied.
            tax_percent (float): Tax percentage applied.
            payment_method (str): Payment mode.
            notes (Optional[str]): Operational notes.

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (Success, Message, Sale summary dict)
        """
        if not cart_items:
            return False, "Cart is empty. Please add items before checkout.", None

        # Poka-Yoke: Discount sanity check
        if discount_percent < 0 or discount_percent > settings.MAX_DISCOUNT_PERCENT:
            msg = f"Discount cannot exceed {settings.MAX_DISCOUNT_PERCENT}% (provided: {discount_percent}%)."
            self._log_poka_yoke("DISCOUNT_CAP_EXCEEDED", f"{discount_percent}%", msg, user_id)
            return False, msg, None

        # Deep verification of every cart item before starting transaction
        verified_items = []
        subtotal = 0.0

        for item in cart_items:
            mid = item.get("medicine_id")
            qty = int(item.get("quantity", 1))
            is_valid, msg, med_dict = self.validate_cart_item(mid, qty)
            if not is_valid:
                return False, f"Checkout aborted due to Poka-Yoke safeguard: {msg}", None

            unit_price = float(med_dict["unit_price"])
            line_total = round(unit_price * qty, 2)
            subtotal += line_total

            verified_items.append({
                "medicine_id": mid,
                "medicine_name": med_dict["name"],
                "batch_number": med_dict["batch_number"],
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": line_total,
                "current_stock": med_dict["stock_quantity"]
            })

        # Calculations
        subtotal = round(subtotal, 2)
        discount_amount = round(subtotal * (discount_percent / 100.0), 2)
        after_discount = subtotal - discount_amount
        tax_amount = round(after_discount * (tax_percent / 100.0), 2)
        grand_total = round(after_discount + tax_amount, 2)

        invoice_number = generate_sale_invoice_number()

        # Atomic Transaction Execution
        conn = db_manager.get_connection()
        try:
            cursor = conn.cursor()

            # 1. Insert Sales Header
            cursor.execute(
                """
                INSERT INTO sales (
                    invoice_number, customer_id, user_id, subtotal, discount_percent,
                    discount_amount, tax_percent, tax_amount, grand_total, payment_method, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_number, customer_id, user_id, subtotal, discount_percent,
                    discount_amount, tax_percent, tax_amount, grand_total, payment_method, notes
                )
            )
            sale_id = cursor.lastrowid

            # 2. Insert Sale Items and Deduct Inventory
            for v_item in verified_items:
                cursor.execute(
                    """
                    INSERT INTO sale_items (sale_id, medicine_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (sale_id, v_item["medicine_id"], v_item["quantity"], v_item["unit_price"], v_item["total_price"])
                )

                # Deduct inventory count
                cursor.execute(
                    """
                    UPDATE medicines
                    SET stock_quantity = stock_quantity - ?
                    WHERE id = ?
                    """,
                    (v_item["quantity"], v_item["medicine_id"])
                )

            # 3. Award Loyalty Points if customer is linked (1 point per 100 spent)
            if customer_id:
                pts_earned = int(grand_total // 100)
                if pts_earned > 0:
                    cursor.execute(
                        "UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?",
                        (pts_earned, customer_id)
                    )

            # Commit Transaction
            conn.commit()
            cursor.close()

            logger.info("Sale completed successfully: %s (Grand Total: %s)", invoice_number, grand_total)

            summary = {
                "id": sale_id,
                "invoice_number": invoice_number,
                "subtotal": subtotal,
                "discount_percent": discount_percent,
                "discount_amount": discount_amount,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount,
                "grand_total": grand_total,
                "payment_method": payment_method,
                "items": verified_items,
            }
            return True, f"Sale finalized successfully. Invoice #{invoice_number}", summary

        except Exception as exc:
            conn.rollback()
            logger.error("Transaction failed during sale processing: %s", exc)
            return False, f"Database transaction failed: {str(exc)}", None

    def get_sale_by_invoice(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """Retrieves a complete sale record including customer, cashier, and items."""
        sql = """
            SELECT s.*, c.name AS customer_name, c.phone AS customer_phone, u.full_name AS cashier_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.invoice_number = ?
        """
        row = db_manager.fetch_one(sql, (invoice_number.strip(),))
        if not row:
            return None

        sale_data = dict(row)
        items_sql = """
            SELECT si.*, m.name AS medicine_name, m.batch_number
            FROM sale_items si
            JOIN medicines m ON si.medicine_id = m.id
            WHERE si.sale_id = ?
        """
        sale_data["items"] = db_manager.fetch_all(items_sql, (sale_data["id"],))
        return sale_data

    def get_recent_sales(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent completed sales headers."""
        sql = """
            SELECT s.*, c.name AS customer_name, u.full_name AS cashier_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN users u ON s.user_id = u.id
            ORDER BY s.sale_date DESC LIMIT ?
        """
        return db_manager.fetch_all(sql, (limit,))

    def _log_poka_yoke(self, rule_name: str, attempted_value: str, message: str, user_id: Optional[int] = None) -> None:
        """Records a defect prevention event in the audit register."""
        try:
            db_manager.execute_query(
                """
                INSERT INTO poka_yoke_events (user_id, rule_name, attempted_value, message, status)
                VALUES (?, ?, ?, ?, 'PREVENTED')
                """,
                (user_id, rule_name, attempted_value, message)
            )
        except Exception as exc:
            logger.error("Failed to log Poka-Yoke event: %s", exc)


# Global singleton instance
sales_service = SalesService()

