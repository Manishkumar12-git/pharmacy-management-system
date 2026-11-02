"""
================================================================================
Pharmacy Management System - User Domain Model
================================================================================
Module: pharmacy_management.models.user
Quality Objective: Q10 - Improve Documentation & Data Typing

Description:
    Defines the User entity representing system operators with role-based
    access control (Admin, Pharmacist, Cashier).
================================================================================
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class User:
    """Represents a system user account.

    Attributes:
        id (Optional[int]): Primary key ID.
        username (str): Unique login identifier.
        full_name (str): Full display name of the operator.
        role (str): Operational role ('Admin', 'Pharmacist', 'Cashier').
        email (Optional[str]): Contact email.
        phone (Optional[str]): Contact telephone number.
        status (str): Account state ('Active' or 'Inactive').
        created_at (Optional[str]): Account creation ISO timestamp.
        last_login (Optional[str]): Most recent login timestamp.
        password_hash (Optional[str]): PBKDF2 hash (omitted from serialized views).
        salt (Optional[str]): Cryptographic salt.
    """
    id: Optional[int]
    username: str
    full_name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "Active"
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    password_hash: Optional[str] = None
    salt: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "User":
        """Instantiates a User domain object from an SQLite dictionary row.

        Args:
            row (Dict[str, Any]): Dictionary row from database.

        Returns:
            User: Populated instance.
        """
        return cls(
            id=row.get("id"),
            username=row.get("username", ""),
            full_name=row.get("full_name", ""),
            role=row.get("role", "Cashier"),
            email=row.get("email"),
            phone=row.get("phone"),
            status=row.get("status", "Active"),
            created_at=row.get("created_at"),
            last_login=row.get("last_login"),
            password_hash=row.get("password_hash"),
            salt=row.get("salt"),
        )

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Serializes user attributes to a standard dictionary.

        Args:
            include_sensitive (bool): If True, retains password_hash and salt.

        Returns:
            Dict[str, Any]: Serialized dictionary.
        """
        data = {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["salt"] = self.salt
        return data

    @property
    def is_active(self) -> bool:
        """Indicates whether user account is currently active."""
        return self.status == "Active"

    @property
    def is_admin(self) -> bool:
        """Indicates whether user has administrative privileges."""
        return self.role == "Admin"

