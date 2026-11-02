"""
================================================================================
Pharmacy Management System - Security & Cryptographic Utilities
================================================================================
Module: pharmacy_management.utils.security
Quality Objective: Q10 - Improve Documentation & Security Compliance

Description:
    Implements cryptographic hashing for credentials, salt generation,
    session tokens, and role-based authorization verification using
    Python standard library hashlib and secrets modules.
================================================================================
"""

import hashlib
import secrets
from typing import Tuple, Optional
from pharmacy_management.config import settings
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Computes a secure PBKDF2-HMAC-SHA256 password hash.

    Args:
        password (str): Plain-text user password.
        salt (Optional[str]): 32-character hexadecimal salt. Generated if None.

    Returns:
        Tuple[str, str]: (password_hash, salt) as hexadecimal strings.
    """
    if not salt:
        salt = secrets.token_hex(16)  # 16 bytes = 32 hex chars

    # 100,000 PBKDF2 iterations for industry-standard key stretching
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, iterations=100000)
    hash_hex = key.hex()
    return hash_hex, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a plain-text password against a stored PBKDF2 hash using constant-time comparison.

    Args:
        password (str): Plain-text password to verify.
        stored_hash (str): The existing hex-encoded PBKDF2 hash.
        salt (str): The hex-encoded salt string.

    Returns:
        bool: True if password matches stored hash, False otherwise.
    """
    try:
        calculated_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, stored_hash)
    except Exception as exc:
        logger.error("Error during password verification: %s", exc)
        return False


def check_permission(user_role: str, permission_key: str) -> bool:
    """Evaluates whether a given user role possesses the requested permission.

    Args:
        user_role (str): Role of the user (e.g., 'Admin', 'Pharmacist', 'Cashier').
        permission_key (str): Permission attribute name defined in settings.ROLE_PERMISSIONS.

    Returns:
        bool: True if authorized, False otherwise.
    """
    role_perms = settings.ROLE_PERMISSIONS.get(user_role, {})
    return role_perms.get(permission_key, False)

