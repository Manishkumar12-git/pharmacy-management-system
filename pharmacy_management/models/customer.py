"""
================================================================================
Pharmacy Management System - Customer Domain Model
================================================================================
Module: pharmacy_management.models.customer
Quality Objective: Q10 - Improve Documentation & Customer Experience

Description:
    Represents patients and pharmacy retail customers, tracking loyalty points
    and contact details.
================================================================================
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Customer:
    """Represents a pharmacy retail customer or patient.

    Attributes:
        id (Optional[int]): Primary key identifier.
        name (str): Full customer name.
        phone (str): Primary telephone number.
        email (Optional[str]): Contact email.
        address (Optional[str]): Residential address.
        loyalty_points (int): Accumulated rewards points.
        created_at (Optional[str]): Registration timestamp.
    """
    id: Optional[int]
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    loyalty_points: int = 0
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Customer":
        """Instantiates Customer entity from a database dictionary row.

        Args:
            row (Dict[str, Any]): Database row.

        Returns:
            Customer: Populated entity.
        """
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            phone=row.get("phone", ""),
            email=row.get("email"),
            address=row.get("address"),
            loyalty_points=int(row.get("loyalty_points", 0)),
            created_at=row.get("created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes customer attributes to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "loyalty_points": self.loyalty_points,
            "created_at": self.created_at,
        }

