"""
================================================================================
Pharmacy Management System - Sale & SaleItem Domain Models
================================================================================
Module: pharmacy_management.models.sale
Quality Objective: Q10 - Improve Documentation & Financial Integrity

Description:
    Defines financial transaction models for retail counter sales,
    including line items, taxes, discounts, and payment methods.
================================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SaleItem:
    """Represents a single line item within a sales transaction.

    Attributes:
        id (Optional[int]): Primary key identifier.
        sale_id (Optional[int]): Foreign key to sales header.
        medicine_id (int): Foreign key to medicines table.
        quantity (int): Number of units sold.
        unit_price (float): Selling price per unit at transaction time.
        total_price (float): Extended price (quantity * unit_price).
        medicine_name (Optional[str]): Joined medicine display name.
        batch_number (Optional[str]): Joined batch identifier.
    """
    medicine_id: int
    quantity: int
    unit_price: float
    total_price: float
    id: Optional[int] = None
    sale_id: Optional[int] = None
    medicine_name: Optional[str] = None
    batch_number: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "SaleItem":
        """Instantiates SaleItem from database row."""
        return cls(
            id=row.get("id"),
            sale_id=row.get("sale_id"),
            medicine_id=row.get("medicine_id"),
            quantity=int(row.get("quantity", 0)),
            unit_price=float(row.get("unit_price", 0.0)),
            total_price=float(row.get("total_price", 0.0)),
            medicine_name=row.get("medicine_name"),
            batch_number=row.get("batch_number"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes sale line item to dictionary."""
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine_name,
            "batch_number": self.batch_number,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
        }


@dataclass
class Sale:
    """Represents an entire completed retail sales invoice.

    Attributes:
        id (Optional[int]): Primary key identifier.
        invoice_number (str): Unique auditable invoice identifier.
        user_id (int): ID of staff member who dispensed the sale.
        subtotal (float): Gross sum before discounts and taxes.
        grand_total (float): Net total payable by customer.
        customer_id (Optional[int]): ID of customer or None for walk-in.
        discount_percent (float): Discount rate applied.
        discount_amount (float): Monetary value of discount.
        tax_percent (float): Tax rate applied.
        tax_amount (float): Monetary value of tax.
        payment_method (str): 'Cash', 'Card', 'UPI', or 'Insurance'.
        notes (Optional[str]): Order notes.
        sale_date (Optional[str]): Transaction ISO timestamp.
        customer_name (Optional[str]): Joined customer name.
        cashier_name (Optional[str]): Joined staff name.
        items (List[SaleItem]): Attached line items.
    """
    invoice_number: str
    user_id: int
    subtotal: float
    grand_total: float
    id: Optional[int] = None
    customer_id: Optional[int] = None
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    tax_percent: float = 0.0
    tax_amount: float = 0.0
    payment_method: str = "Cash"
    notes: Optional[str] = None
    sale_date: Optional[str] = None
    customer_name: Optional[str] = None
    cashier_name: Optional[str] = None
    items: List[SaleItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Sale":
        """Instantiates Sale entity from database row."""
        return cls(
            id=row.get("id"),
            invoice_number=row.get("invoice_number", ""),
            customer_id=row.get("customer_id"),
            user_id=row.get("user_id"),
            subtotal=float(row.get("subtotal", 0.0)),
            discount_percent=float(row.get("discount_percent", 0.0)),
            discount_amount=float(row.get("discount_amount", 0.0)),
            tax_percent=float(row.get("tax_percent", 0.0)),
            tax_amount=float(row.get("tax_amount", 0.0)),
            grand_total=float(row.get("grand_total", 0.0)),
            payment_method=row.get("payment_method", "Cash"),
            notes=row.get("notes"),
            sale_date=row.get("sale_date"),
            customer_name=row.get("customer_name"),
            cashier_name=row.get("cashier_name"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes sale and line items to dictionary."""
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "cashier_name": self.cashier_name,
            "user_id": self.user_id,
            "sale_date": self.sale_date,
            "subtotal": self.subtotal,
            "discount_percent": self.discount_percent,
            "discount_amount": self.discount_amount,
            "tax_percent": self.tax_percent,
            "tax_amount": self.tax_amount,
            "grand_total": self.grand_total,
            "payment_method": self.payment_method,
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
        }

