"""
================================================================================
Pharmacy Management System - Supplier Domain Model
================================================================================
Module: pharmacy_management.models.supplier
Quality Objective: Q10 - Improve Documentation & Traceability

Description:
    Represents certified pharmaceutical distributors, wholesale suppliers,
    and logistical contacts.
================================================================================
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Supplier:
    """Represents a pharmaceutical wholesale distributor.

    Attributes:
        id (Optional[int]): Supplier ID.
        name (str): Company name.
        contact_person (Optional[str]): Contact representative.
        phone (str): Direct phone number.
        email (Optional[str]): Email address.
        address (Optional[str]): Physical logistics warehouse address.
        gst_tax_id (Optional[str]): GST / VAT / Tax ID.
        status (str): 'Active' or 'Inactive'.
        created_at (Optional[str]): Registration timestamp.
    """
    id: Optional[int]
    name: str
    phone: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gst_tax_id: Optional[str] = None
    status: str = "Active"
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Supplier":
        """Builds a Supplier instance from a database dictionary row.

        Args:
            row (Dict[str, Any]): Database row.

        Returns:
            Supplier: Populated entity.
        """
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            phone=row.get("phone", ""),
            contact_person=row.get("contact_person"),
            email=row.get("email"),
            address=row.get("address"),
            gst_tax_id=row.get("gst_tax_id"),
            status=row.get("status", "Active"),
            created_at=row.get("created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes supplier attributes to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "gst_tax_id": self.gst_tax_id,
            "status": self.status,
            "created_at": self.created_at,
        }

