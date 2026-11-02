"""
================================================================================
Pharmacy Management System - Inventory Control Service
================================================================================
Module: pharmacy_management.services.inventory_service
Quality Objective: Q10 - Improve Documentation & Quality Bounds

Description:
    Manages physical stock valuation, low-stock alerts, quarantine of expired
    lots, and auditable manual inventory adjustments.
================================================================================
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import date, timedelta
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.medicine import Medicine
from pharmacy_management.config import settings
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class InventoryService:
    """Business service governing warehouse stock levels, expiry alerts, and inventory health."""

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Calculates aggregated metrics for stock health and inventory valuation.

        Returns:
            Dict[str, Any]: Inventory KPI indicators.
        """
        today_str = date.today().isoformat()
        soon_str = (date.today() + timedelta(days=settings.EXPIRY_WARNING_DAYS)).isoformat()

        # Total active medicines
        total_meds = db_manager.fetch_one(
            "SELECT COUNT(*) AS c FROM medicines WHERE status = 'Active'"
        )["c"]

        # Stock valuation
        val_row = db_manager.fetch_one(
            """
            SELECT
                SUM(stock_quantity * cost_price) AS total_cost_value,
                SUM(stock_quantity * unit_price) AS total_retail_value,
                SUM(stock_quantity) AS total_units
            FROM medicines
            WHERE status = 'Active'
            """
        )

        # Low stock count
        low_stock_count = db_manager.fetch_one(
            "SELECT COUNT(*) AS c FROM medicines WHERE status = 'Active' AND stock_quantity <= reorder_level"
        )["c"]

        # Expired items count
        expired_count = db_manager.fetch_one(
            "SELECT COUNT(*) AS c FROM medicines WHERE status = 'Active' AND expiry_date <= ?",
            (today_str,)
        )["c"]

        # Expiring soon count
        expiring_soon_count = db_manager.fetch_one(
            """
            SELECT COUNT(*) AS c FROM medicines
            WHERE status = 'Active'
              AND expiry_date > ?
              AND expiry_date <= ?
            """,
            (today_str, soon_str)
        )["c"]

        cost_val = float(val_row["total_cost_value"] or 0.0)
        retail_val = float(val_row["total_retail_value"] or 0.0)

        return {
            "total_medicines": total_meds,
            "total_units": int(val_row["total_units"] or 0),
            "total_cost_value": cost_val,
            "total_retail_value": retail_val,
            "potential_profit": round(retail_val - cost_val, 2),
            "low_stock_count": low_stock_count,
            "expired_count": expired_count,
            "expiring_soon_count": expiring_soon_count,
        }

    def get_low_stock_items(self) -> List[Medicine]:
        """Retrieves items whose inventory balance is at or below the reorder point."""
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status = 'Active' AND m.stock_quantity <= m.reorder_level
            ORDER BY m.stock_quantity ASC
        """
        rows = db_manager.fetch_all(sql)
        return [Medicine.from_row(r) for r in rows]

    def get_expiring_soon_items(self, days: int = settings.EXPIRY_WARNING_DAYS) -> List[Medicine]:
        """Retrieves batches expiring within the specified number of calendar days."""
        today_str = date.today().isoformat()
        cutoff_str = (date.today() + timedelta(days=days)).isoformat()
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status = 'Active'
              AND m.expiry_date > ?
              AND m.expiry_date <= ?
            ORDER BY m.expiry_date ASC
        """
        rows = db_manager.fetch_all(sql, (today_str, cutoff_str))
        return [Medicine.from_row(r) for r in rows]

    def get_expired_items(self) -> List[Medicine]:
        """Retrieves pharmaceutical batches whose expiration date has passed."""
        today_str = date.today().isoformat()
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status = 'Active' AND m.expiry_date <= ?
            ORDER BY m.expiry_date ASC
        """
        rows = db_manager.fetch_all(sql, (today_str,))
        return [Medicine.from_row(r) for r in rows]

    def adjust_stock(
        self,
        medicine_id: int,
        new_quantity: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Performs an auditable physical inventory stock adjustment.

        Args:
            medicine_id (int): Foreign key to medicines.
            new_quantity (int): Verified physical count.
            reason (str): Reason for discrepancy (e.g., 'Stock Audit', 'Damage').
            user_id (Optional[int]): Operator ID.

        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if new_quantity < 0:
            return False, "Stock quantity cannot be negative."

        row = db_manager.fetch_one("SELECT * FROM medicines WHERE id = ?", (medicine_id,))
        if not row:
            return False, "Medicine not found."

        old_quantity = row["stock_quantity"]
        diff = new_quantity - old_quantity

        db_manager.execute_query(
            "UPDATE medicines SET stock_quantity = ? WHERE id = ?",
            (new_quantity, medicine_id)
        )

        # Audit discrepancy
        details = f"Adjusted stock from {old_quantity} to {new_quantity} (Delta: {diff}). Reason: {reason}"
        db_manager.execute_query(
            """
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
            VALUES (?, 'STOCK_ADJUSTMENT', 'medicines', ?, ?)
            """,
            (user_id, medicine_id, details)
        )
        logger.info(details)
        return True, "Stock count updated successfully."


# Global singleton instance
inventory_service = InventoryService()

