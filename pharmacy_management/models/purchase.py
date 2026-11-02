"""
================================================================================
Pharmacy Management System - Purchase & PurchaseItem Domain Models
================================================================================
Module: pharmacy_management.models.purchase
Quality Objective: Q10 - Improve Documentation & Inbound Quality Control

Description:
    Represents wholesale supplier stock receipts, batch acquisition details,
    inbound expiration dating, and purchase order tracking.
================================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class PurchaseItem:
    """Represents an inbound product line item received from a supplier.

    Attributes:
        id (Optional[int]): Primary key identifier.
        purchase_id (Optional[int]): Foreign key to purchases header.
        medicine_id (int): Foreign key to medicines catalog.
        batch_number (str): Manufacturing lot/batch identifier.
        expiry_date (str): Manufacturer batch expiration date.
        quantity (int): Number of units received.
        cost_price (float): Inbound acquisition cost per unit.
        total_price (float): Extended purchase cost (quantity * cost_price).
        medicine_name (Optional[str]): Joined medicine display name.
    """
    medicine_id: int
    batch_number: str
    expiry_date: str
    quantity: int
    cost_price: float
    total_price: float
    id: Optional[int] = None
    purchase_id: Optional[int] = None
    medicine_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "PurchaseItem":
        """Instantiates PurchaseItem from database row."""
        return cls(
            id=row.get("id"),
            purchase_id=row.get("purchase_id"),
            medicine_id=row.get("medicine_id"),
            batch_number=row.get("batch_number", ""),
            expiry_date=row.get("expiry_date", ""),
            quantity=int(row.get("quantity", 0)),
            cost_price=float(row.get("cost_price", 0.0)),
            total_price=float(row.get("total_price", 0.0)),
            medicine_name=row.get("medicine_name"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes purchase item to dictionary."""
        return {
            "id": self.id,
            "purchase_id": self.purchase_id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine_name,
            "batch_number": self.batch_number,
            "expiry_date": self.expiry_date,
            "quantity": self.quantity,
            "cost_price": self.cost_price,
            "total_price": self.total_price,
        }


@dataclass
class Purchase:
    """Represents an inbound supplier restocking order header.

    Attributes:
        id (Optional[int]): Primary key identifier.
        invoice_number (str): Supplier invoice or PO number.
        supplier_id (int): Foreign key to suppliers table.
        user_id (int): Staff member receiving the shipment.
        total_amount (float): Total invoice sum payable to supplier.
        purchase_date (Optional[str]): Receipt timestamp.
        payment_status (str): 'Paid', 'Pending', or 'Partial'.
        notes (Optional[str]): Receiving inspection notes.
        supplier_name (Optional[str]): Joined supplier company name.
        receiver_name (Optional[str]): Joined receiving staff name.
        items (List[PurchaseItem]): Shipment line items.
    """
    invoice_number: str
    supplier_id: int
    user_id: int
    total_amount: float
    id: Optional[int] = None
    purchase_date: Optional[str] = None
    payment_status: str = "Paid"
    notes: Optional[str] = None
    supplier_name: Optional[str] = None
    receiver_name: Optional[str] = None
    items: List[PurchaseItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Purchase":
        """Instantiates Purchase entity from database row."""
        return cls(
            id=row.get("id"),
            invoice_number=row.get("invoice_number", ""),
            supplier_id=row.get("supplier_id"),
            user_id=row.get("user_id"),
            total_amount=float(row.get("total_amount", 0.0)),
            purchase_date=row.get("purchase_date"),
            payment_status=row.get("payment_status", "Paid"),
            notes=row.get("notes"),
            supplier_name=row.get("supplier_name"),
            receiver_name=row.get("receiver_name"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes purchase and items to dictionary."""
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "receiver_name": self.receiver_name,
            "user_id": self.user_id,
            "purchase_date": self.purchase_date,
            "total_amount": self.total_amount,
            "payment_status": self.payment_status,
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
        }

