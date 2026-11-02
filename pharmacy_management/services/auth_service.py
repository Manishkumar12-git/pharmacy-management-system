"""
================================================================================
Pharmacy Management System - Authentication & User Service
================================================================================
Module: pharmacy_management.services.auth_service
Quality Objective: Q10 - Improve Documentation & Security Traceability

Description:
    Provides user authentication, session state tracking, role-based access
    verification, user account provisioning, and credential auditing.
================================================================================
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.user import User
from pharmacy_management.utils.security import hash_password, verify_password, check_permission
from pharmacy_management.utils.validators import validate_text, validate_email, validate_phone
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service handling operator authentication, user management, and session state."""

    def __init__(self):
        """Initializes the authentication service with an empty session state."""
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        """Returns the currently authenticated user entity, or None if unauthenticated."""
        return self._current_user

    def login(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """Authenticates user credentials and establishes the active session.

        Args:
            username (str): Provided login username.
            password (str): Plain-text password.

        Returns:
            Tuple[bool, Optional[User], str]: (Success, User instance, Status message)
        """
        if not username or not password:
            return False, None, "Username and password cannot be blank."

        row = db_manager.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (username.strip(),)
        )

        if not row:
            logger.warning("Authentication failed: User '%s' does not exist.", username)
            return False, None, "Invalid username or password."

        user = User.from_row(row)
        if not user.is_active:
            logger.warning("Authentication rejected: User '%s' is inactive.", username)
            return False, None, "Account is disabled. Please contact an Administrator."

        if not verify_password(password, user.password_hash or "", user.salt or ""):
            logger.warning("Authentication failed: Incorrect password for '%s'.", username)
            return False, None, "Invalid username or password."

        # Update last_login timestamp
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_manager.execute_query(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (now_str, user.id)
        )
        user.last_login = now_str
        self._current_user = user

        # Audit login
        self._log_audit("LOGIN", "users", user.id, f"User {user.username} logged in successfully.")
        logger.info("User '%s' authenticated successfully (Role: %s).", user.username, user.role)
        return True, user, f"Welcome, {user.full_name}!"

    def logout(self) -> None:
        """Terminates the active user session and records an audit log entry."""
        if self._current_user:
            self._log_audit("LOGOUT", "users", self._current_user.id, f"User {self._current_user.username} logged out.")
            logger.info("User '%s' logged out.", self._current_user.username)
        self._current_user = None

    def has_permission(self, permission_key: str) -> bool:
        """Verifies if the currently logged-in operator holds a specific capability."""
        if not self._current_user:
            return False
        return check_permission(self._current_user.role, permission_key)

    def get_all_users(self) -> List[User]:
        """Fetches all registered user accounts sorted by username.

        Returns:
            List[User]: List of User entities.
        """
        rows = db_manager.fetch_all("SELECT * FROM users ORDER BY role, username ASC")
        return [User.from_row(r) for r in rows]

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Finds user by primary key.

        Args:
            user_id (int): Primary key ID.

        Returns:
            Optional[User]: User entity or None.
        """
        row = db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        return User.from_row(row) if row else None

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Creates a new operator account with encrypted credentials.

        Args:
            username (str): Unique username.
            password (str): Initial password.
            full_name (str): Display name.
            role (str): Operational role.
            email (Optional[str]): Contact email.
            phone (Optional[str]): Contact phone.

        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        # Poka-Yoke Validations
        val_name = validate_text(username, "Username", min_length=3, max_length=30)
        if not val_name:
            return False, val_name.message

        val_pwd = validate_text(password, "Password", min_length=6, max_length=50)
        if not val_pwd:
            return False, val_pwd.message

        val_fname = validate_text(full_name, "Full Name", min_length=2, max_length=100)
        if not val_fname:
            return False, val_fname.message

        if email:
            val_mail = validate_email(email)
            if not val_mail:
                return False, val_mail.message

        if phone:
            val_ph = validate_phone(phone)
            if not val_ph:
                return False, val_ph.message

        # Check duplicate username
        existing = db_manager.fetch_one("SELECT id FROM users WHERE username = ?", (username.strip(),))
        if existing:
            return False, f"Username '{username}' is already in use."

        pwd_hash, salt = hash_password(password)
        try:
            uid = db_manager.execute_query(
                """
                INSERT INTO users (username, password_hash, salt, full_name, role, email, phone, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
                """,
                (username.strip(), pwd_hash, salt, full_name.strip(), role, email, phone)
            )
            self._log_audit("CREATE_USER", "users", uid, f"Created account for {username} ({role})")
            return True, f"User '{username}' created successfully."
        except Exception as exc:
            logger.error("Failed to create user: %s", exc)
            return False, f"Database error creating user: {str(exc)}"

    def update_user(
        self,
        user_id: int,
        full_name: str,
        role: str,
        email: Optional[str],
        phone: Optional[str],
        status: str,
        new_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Updates an existing operator account details.

        Args:
            user_id (int): Primary key ID.
            full_name (str): Full name.
            role (str): Role string.
            email (Optional[str]): Email.
            phone (Optional[str]): Phone.
            status (str): 'Active' or 'Inactive'.
            new_password (Optional[str]): Optional password reset string.

        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        val_name = validate_text(full_name, "Full Name", min_length=2, max_length=100)
        if not val_name:
            return False, val_name.message

        try:
            if new_password and new_password.strip():
                pwd_hash, salt = hash_password(new_password.strip())
                db_manager.execute_query(
                    """
                    UPDATE users
                    SET full_name = ?, role = ?, email = ?, phone = ?, status = ?,
                        password_hash = ?, salt = ?
                    WHERE id = ?
                    """,
                    (full_name.strip(), role, email, phone, status, pwd_hash, salt, user_id)
                )
            else:
                db_manager.execute_query(
                    """
                    UPDATE users
                    SET full_name = ?, role = ?, email = ?, phone = ?, status = ?
                    WHERE id = ?
                    """,
                    (full_name.strip(), role, email, phone, status, user_id)
                )

            self._log_audit("UPDATE_USER", "users", user_id, f"Updated user ID {user_id} ({full_name})")
            return True, "User updated successfully."
        except Exception as exc:
            logger.error("Failed to update user ID %s: %s", user_id, exc)
            return False, f"Database error: {str(exc)}"

    def _log_audit(self, action: str, entity_type: str, entity_id: Optional[int], details: str) -> None:
        """Internal helper to write audit entries."""
        try:
            uid = self._current_user.id if self._current_user else None
            uname = self._current_user.username if self._current_user else "SYSTEM"
            db_manager.execute_query(
                """
                INSERT INTO audit_logs (user_id, username, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (uid, uname, action, entity_type, entity_id, details)
            )
        except Exception as exc:
            logger.error("Audit logging failed: %s", exc)


# Global singleton instance
auth_service = AuthService()
