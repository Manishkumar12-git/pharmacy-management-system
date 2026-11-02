"""
================================================================================
Pharmacy Management System - Medicine Domain Model
================================================================================
Module: pharmacy_management.models.medicine
Quality Objective: Q10 - Improve Documentation & Quality Bounds

Description:
    Defines the Medicine entity with clinical metadata, batch tracking,
    pricing, inventory bounds, and dynamic expiry / stock status properties.
================================================================================
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pharmacy_management.utils.helpers import calculate_days_until_expiry


@dataclass
class Medicine:
    """Represents a pharmaceutical product batch.

    Attributes:
        id (Optional[int]): Primary key identifier.
        name (str): Commercial brand or drug name.
        generic_name (Optional[str]): Active pharmaceutical ingredient (API).
        category_id (Optional[int]): Foreign key to categories table.
        batch_number (str): Manufacturing batch/lot number.
        barcode (Optional[str]): EAN/UPC barcode string.
        manufacturer (Optional[str]): Pharmaceutical manufacturing company.
        unit (str): Dispense unit (e.g., 'Strip of 10', 'Vial', 'Bottle').
        unit_price (float): Selling retail price per unit.
        cost_price (float): Purchase acquisition cost per unit.
        stock_quantity (int): Units currently on hand in inventory.
        reorder_level (int): Safety stock threshold.
        expiry_date (str): Calendar expiration date (YYYY-MM-DD).
        storage_condition (str): Temperature and humidity requirements.
        prescription_required (int): 1 if Rx required, 0 if OTC.
        status (str): 'Active' or 'Discontinued'.
        category_name (Optional[str]): Joined category label.
        created_at (Optional[str]): Record creation timestamp.
    """
    id: Optional[int]
    name: str
    batch_number: str
    unit_price: float
    cost_price: float
    stock_quantity: int
    expiry_date: str
    generic_name: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    manufacturer: Optional[str] = None
    unit: str = "Strips"
    reorder_level: int = 10
    storage_condition: str = "Room Temperature"
    prescription_required: int = 0
    status: str = "Active"
    category_name: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Medicine":
        """Instantiates a Medicine domain entity from a database dictionary row.

        Args:
            row (Dict[str, Any]): Row mapping.

        Returns:
            Medicine: Entity instance.
        """
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            generic_name=row.get("generic_name"),
            category_id=row.get("category_id"),
            batch_number=row.get("batch_number", ""),
            barcode=row.get("barcode"),
            manufacturer=row.get("manufacturer"),
            unit=row.get("unit", "Strips"),
            unit_price=float(row.get("unit_price", 0.0)),
            cost_price=float(row.get("cost_price", 0.0)),
            stock_quantity=int(row.get("stock_quantity", 0)),
            reorder_level=int(row.get("reorder_level", 10)),
            expiry_date=str(row.get("expiry_date", "")),
            storage_condition=row.get("storage_condition", "Room Temperature"),
            prescription_required=int(row.get("prescription_required", 0)),
            status=row.get("status", "Active"),
            category_name=row.get("category_name"),
            created_at=row.get("created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes medicine attributes to a dictionary with computed properties.

        Returns:
            Dict[str, Any]: Serialized dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "generic_name": self.generic_name,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "batch_number": self.batch_number,
            "barcode": self.barcode,
            "manufacturer": self.manufacturer,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "cost_price": self.cost_price,
            "stock_quantity": self.stock_quantity,
            "reorder_level": self.reorder_level,
            "expiry_date": self.expiry_date,
            "storage_condition": self.storage_condition,
            "prescription_required": self.prescription_required,
            "status": self.status,
            "is_expired": self.is_expired,
            "days_until_expiry": self.days_until_expiry,
            "is_low_stock": self.is_low_stock,
            "profit_margin": self.profit_margin,
            "created_at": self.created_at,
        }

    @property
    def days_until_expiry(self) -> int:
        """Returns signed days until product expiration."""
        return calculate_days_until_expiry(self.expiry_date)

    @property
    def is_expired(self) -> bool:
        """Checks if the product has surpassed its expiry date."""
        return self.days_until_expiry <= 0

    @property
    def is_low_stock(self) -> bool:
        """Checks if inventory count is at or below the reorder threshold."""
        return self.stock_quantity <= self.reorder_level

    @property
    def profit_margin(self) -> float:
        """Computes absolute monetary profit margin per unit."""
        return round(self.unit_price - self.cost_price, 2)

    @property
    def total_stock_value(self) -> float:
        """Computes inventory valuation based on unit retail price."""
        return round(self.unit_price * self.stock_quantity, 2)

