"""
================================================================================
Pharmacy Management System - Medicine & Catalog Service
================================================================================
Module: pharmacy_management.services.medicine_service
Quality Objective: Q10 - Improve Documentation & Poka-Yoke Defect Prevention

Description:
    Manages pharmaceutical catalog, categories, pricing validations,
    and inventory stock adjustments. Enforces strict input validation
    at the source to prevent invalid pricing, missing batch codes,
    or past expiration dates during stock entry.
================================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.medicine import Medicine
from pharmacy_management.utils.validators import (
    validate_text, validate_positive_number, validate_integer,
    validate_date_string, validate_not_expired
)
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class MedicineService:
    """Business service governing medicine records, categories, and catalog rules."""

    def get_all_medicines(self, category_id: Optional[int] = None, active_only: bool = True) -> List[Medicine]:
        """Retrieves pharmaceutical items joined with category names.

        Args:
            category_id (Optional[int]): Optional filter by category.
            active_only (bool): If True, filters for status='Active'.

        Returns:
            List[Medicine]: Catalog items.
        """
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE 1=1
        """
        params = []
        if active_only:
            sql += " AND m.status = 'Active'"
        if category_id:
            sql += " AND m.category_id = ?"
            params.append(category_id)

        sql += " ORDER BY m.name ASC"
        rows = db_manager.fetch_all(sql, tuple(params))
        return [Medicine.from_row(r) for r in rows]

    def get_medicine_by_id(self, med_id: int) -> Optional[Medicine]:
        """Looks up a medicine record by its primary key ID."""
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.id = ?
        """
        row = db_manager.fetch_one(sql, (med_id,))
        return Medicine.from_row(row) if row else None

    def get_medicine_by_barcode(self, barcode: str) -> Optional[Medicine]:
        """Looks up a medicine record by exact barcode string."""
        if not barcode:
            return None
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.barcode = ? AND m.status = 'Active'
        """
        row = db_manager.fetch_one(sql, (barcode.strip(),))
        return Medicine.from_row(row) if row else None

    def get_categories(self) -> List[Dict[str, Any]]:
        """Returns all registered therapeutic medicine categories."""
        return db_manager.fetch_all("SELECT * FROM categories ORDER BY name ASC")

    def add_category(self, name: str, description: Optional[str] = None) -> Tuple[bool, str]:
        """Adds a new therapeutic category."""
        val = validate_text(name, "Category Name", min_length=2, max_length=50)
        if not val:
            return False, val.message
        try:
            db_manager.execute_query(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                (name.strip(), description)
            )
            return True, f"Category '{name}' created."
        except Exception as exc:
            return False, f"Failed to add category: {str(exc)}"

    def add_medicine(self, data: Dict[str, Any], user_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """Creates a new medicine batch with comprehensive Poka-Yoke verification.

        Args:
            data (Dict[str, Any]): Dictionary of medicine attributes.
            user_id (Optional[int]): ID of the operator adding the medicine.

        Returns:
            Tuple[bool, str, Optional[int]]: (Success, Message, Inserted ID)
        """
        # 1. Poka-Yoke: Mandatory Name
        val_name = validate_text(data.get("name"), "Medicine Name", min_length=2, max_length=150)
        if not val_name:
            self._log_poka_yoke("BLANK_MEDICINE_NAME_BLOCKED", str(data.get("name")), val_name.message, user_id)
            return False, val_name.message, None

        # 2. Poka-Yoke: Mandatory Batch Number
        val_batch = validate_text(data.get("batch_number"), "Batch Number", min_length=2, max_length=50)
        if not val_batch:
            self._log_poka_yoke("BLANK_BATCH_BLOCKED", str(data.get("batch_number")), val_batch.message, user_id)
            return False, val_batch.message, None

        # 3. Poka-Yoke: Non-Negative Unit Price
        val_price = validate_positive_number(data.get("unit_price"), "Unit Price (Selling)")
        if not val_price:
            self._log_poka_yoke("NEGATIVE_PRICE_BLOCKED", str(data.get("unit_price")), val_price.message, user_id)
            return False, val_price.message, None

        # 4. Poka-Yoke: Non-Negative Cost Price
        val_cost = validate_positive_number(data.get("cost_price"), "Cost Price (Acquisition)", allow_zero=True)
        if not val_cost:
            self._log_poka_yoke("NEGATIVE_COST_BLOCKED", str(data.get("cost_price")), val_cost.message, user_id)
            return False, val_cost.message, None

        # 5. Cost <= Unit Price logic check
        unit_price = float(data.get("unit_price"))
        cost_price = float(data.get("cost_price"))
        if cost_price > unit_price:
            logger.warning("Cost price (%s) is higher than selling price (%s) for %s", cost_price, unit_price, data.get("name"))

        # 6. Poka-Yoke: Stock Quantity integer bounds
        val_stock = validate_integer(data.get("stock_quantity", 0), "Stock Quantity", min_value=0)
        if not val_stock:
            return False, val_stock.message, None

        # 7. Poka-Yoke: Valid Expiration Date format and not already expired
        val_date = validate_date_string(data.get("expiry_date", ""), "Expiry Date")
        if not val_date:
            return False, val_date.message, None

        val_exp = validate_not_expired(data.get("expiry_date", ""), data.get("name", "Medicine"))
        if not val_exp:
            self._log_poka_yoke("EXPIRED_INITIAL_STOCK_BLOCKED", str(data.get("expiry_date")), val_exp.message, user_id)
            return False, f"Poka-Yoke Safeguard: Inbound medicine is already expired ({data.get('expiry_date')}). Cannot register expired stock.", None

        # Execute insertion
        try:
            med_id = db_manager.execute_query(
                """
                INSERT INTO medicines (
                    name, generic_name, category_id, batch_number, barcode,
                    manufacturer, unit, unit_price, cost_price, stock_quantity,
                    reorder_level, expiry_date, storage_condition, prescription_required, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active')
                """,
                (
                    data.get("name").strip(),
                    data.get("generic_name", "").strip() if data.get("generic_name") else None,
                    data.get("category_id") or None,
                    data.get("batch_number").strip(),
                    data.get("barcode", "").strip() if data.get("barcode") else None,
                    data.get("manufacturer", "").strip() if data.get("manufacturer") else None,
                    data.get("unit", "Strips"),
                    unit_price,
                    cost_price,
                    int(data.get("stock_quantity", 0)),
                    int(data.get("reorder_level", 10)),
                    data.get("expiry_date").strip(),
                    data.get("storage_condition", "Room Temperature"),
                    1 if data.get("prescription_required") else 0,
                )
            )
            logger.info("Created new medicine ID %s (%s)", med_id, data.get("name"))
            return True, f"Medicine '{data.get('name')}' created successfully.", med_id
        except Exception as exc:
            logger.error("Failed to insert medicine: %s", exc)
            return False, f"Database error creating medicine: {str(exc)}", None

    def update_medicine(self, med_id: int, data: Dict[str, Any], user_id: Optional[int] = None) -> Tuple[bool, str]:
        """Updates an existing medicine catalog record with validation."""
        val_name = validate_text(data.get("name"), "Medicine Name", min_length=2, max_length=150)
        if not val_name:
            return False, val_name.message

        val_price = validate_positive_number(data.get("unit_price"), "Unit Price")
        if not val_price:
            return False, val_price.message

        val_cost = validate_positive_number(data.get("cost_price"), "Cost Price", allow_zero=True)
        if not val_cost:
            return False, val_cost.message

        val_stock = validate_integer(data.get("stock_quantity", 0), "Stock Quantity", min_value=0)
        if not val_stock:
            return False, val_stock.message

        val_date = validate_date_string(data.get("expiry_date", ""), "Expiry Date")
        if not val_date:
            return False, val_date.message

        try:
            db_manager.execute_query(
                """
                UPDATE medicines
                SET name = ?, generic_name = ?, category_id = ?, batch_number = ?, barcode = ?,
                    manufacturer = ?, unit = ?, unit_price = ?, cost_price = ?, stock_quantity = ?,
                    reorder_level = ?, expiry_date = ?, storage_condition = ?, prescription_required = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    data.get("name").strip(),
                    data.get("generic_name", "").strip() if data.get("generic_name") else None,
                    data.get("category_id") or None,
                    data.get("batch_number", "").strip(),
                    data.get("barcode", "").strip() if data.get("barcode") else None,
                    data.get("manufacturer", "").strip() if data.get("manufacturer") else None,
                    data.get("unit", "Strips"),
                    float(data.get("unit_price")),
                    float(data.get("cost_price")),
                    int(data.get("stock_quantity")),
                    int(data.get("reorder_level", 10)),
                    data.get("expiry_date").strip(),
                    data.get("storage_condition", "Room Temperature"),
                    1 if data.get("prescription_required") else 0,
                    data.get("status", "Active"),
                    med_id,
                )
            )
            return True, "Medicine updated successfully."
        except Exception as exc:
            logger.error("Failed to update medicine ID %s: %s", med_id, exc)
            return False, f"Database error: {str(exc)}"

    def delete_medicine(self, med_id: int) -> Tuple[bool, str]:
        """Soft-deletes a medicine batch by changing status to 'Discontinued'."""
        try:
            db_manager.execute_query(
                "UPDATE medicines SET status = 'Discontinued' WHERE id = ?",
                (med_id,)
            )
            return True, "Medicine discontinued successfully."
        except Exception as exc:
            return False, f"Failed to discontinue medicine: {str(exc)}"

    def update_stock(self, med_id: int, quantity_delta: int) -> Tuple[bool, str]:
        """Adjusts stock balance by quantity_delta (positive or negative)."""
        med = self.get_medicine_by_id(med_id)
        if not med:
            return False, "Medicine not found."

        new_stock = med.stock_quantity + quantity_delta
        if new_stock < 0:
            return False, f"Cannot reduce stock below zero. Current: {med.stock_quantity}, Delta: {quantity_delta}"

        db_manager.execute_query(
            "UPDATE medicines SET stock_quantity = ? WHERE id = ?",
            (new_stock, med_id)
        )
        return True, f"Stock updated to {new_stock} units."

    def _log_poka_yoke(self, rule_name: str, attempted_value: str, message: str, user_id: Optional[int]) -> None:
        """Records a defect prevention event in the TQM audit table."""
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
medicine_service = MedicineService()

