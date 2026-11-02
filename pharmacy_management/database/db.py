"""
================================================================================
Pharmacy Management System - Database Connection Manager & Access Layer
================================================================================
Module: pharmacy_management.database.db
Quality Objective: Q10 - Improve Documentation & Architectural Modularity

Description:
    Provides context-managed, thread-safe access to SQLite database.
    Ensures parameterized queries are always used (SQL-injection prevention),
    manages atomic transactions with automatic rollback on error, and
    sets sqlite3.Row for structured dictionary-like tuple access.
================================================================================
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, List, Dict, Any, Optional, Tuple
from pharmacy_management.config import settings
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)

# Thread-local storage for DB connections
_local = threading.local()


class DatabaseManager:
    """Singleton database manager managing connection lifecycles and transactions."""

    def __init__(self, db_path: Optional[str] = None):
        """Initializes the database manager.

        Args:
            db_path (Optional[str]): Path to the SQLite database file.
        """
        self.db_path = db_path or settings.DATABASE_PATH

    def get_connection(self) -> sqlite3.Connection:
        """Returns or creates a thread-local SQLite connection.

        Returns:
            sqlite3.Connection: Active database connection.
        """
        if not hasattr(_local, "connection") or _local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=settings.DB_TIMEOUT_SECONDS,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # Enable Foreign Key Enforcement on every fresh connection
            conn.execute("PRAGMA foreign_keys = ON;")
            _local.connection = conn
            logger.debug("Initialized new database connection for thread: %s", threading.current_thread().name)
        return _local.connection

    def close_connection(self) -> None:
        """Closes the thread-local database connection if one exists."""
        if hasattr(_local, "connection") and _local.connection is not None:
            try:
                _local.connection.close()
            except Exception as exc:
                logger.warning("Error closing connection: %s", exc)
            finally:
                _local.connection = None

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager yielding a database cursor with automatic commit/rollback.

        Yields:
            sqlite3.Cursor: Database cursor.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error("Transaction rolled back due to error: %s", exc)
            raise
        finally:
            cursor.close()

    def execute_query(self, sql: str, params: Tuple[Any, ...] = ()) -> int:
        """Executes an INSERT, UPDATE, or DELETE query and returns the lastrowid or rowcount.

        Args:
            sql (str): Parameterized SQL query.
            params (Tuple[Any, ...]): Query parameters.

        Returns:
            int: Last inserted row ID for INSERTs, or rows affected for UPDATE/DELETEs.
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            if cursor.lastrowid:
                return cursor.lastrowid
            return cursor.rowcount

    def fetch_one(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """Executes a SELECT query and returns a single row as a dictionary.

        Args:
            sql (str): Parameterized SQL query.
            params (Tuple[Any, ...]): Query parameters.

        Returns:
            Optional[Dict[str, Any]]: Row mapped to dictionary, or None if not found.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row is not None:
                return dict(row)
            return None
        finally:
            cursor.close()

    def fetch_all(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns all matching rows as dictionaries.

        Args:
            sql (str): Parameterized SQL query.
            params (Tuple[Any, ...]): Query parameters.

        Returns:
            List[Dict[str, Any]]: List of dictionary rows.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            cursor.close()

    def execute_script(self, script: str) -> None:
        """Executes a multi-statement SQL script.

        Args:
            script (str): Semicolon-delimited SQL script text.
        """
        conn = self.get_connection()
        try:
            conn.executescript(script)
            conn.commit()
            logger.info("Successfully executed SQL script.")
        except Exception as exc:
            conn.rollback()
            logger.error("Error executing SQL script: %s", exc)
            raise


# Global singleton instance
db_manager = DatabaseManager()

