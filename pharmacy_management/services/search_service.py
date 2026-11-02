"""
================================================================================
Pharmacy Management System - Universal Search Service
================================================================================
Module: pharmacy_management.services.search_service
Quality Objective: Q10 - Improve Documentation & Rapid Data Retrieval

Description:
    Provides indexed and multi-attribute search across the pharmaceutical
    catalog, customer registry, supplier listings, and sales invoices.
================================================================================
"""

from typing import List, Dict, Any
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.medicine import Medicine


class SearchService:
    """Consolidated search facility across entities."""

    def search_medicines(self, query: str, active_only: bool = True) -> List[Medicine]:
        """Searches medicines by name, generic name, barcode, batch number, or manufacturer.

        Args:
            query (str): Search keyword.
            active_only (bool): If True, limits results to Active items.

        Returns:
            List[Medicine]: Matching medicine entities.
        """
        if not query or not query.strip():
            sql = """
                SELECT m.*, c.name AS category_name
                FROM medicines m
                LEFT JOIN categories c ON m.category_id = c.id
                WHERE 1=1
            """
            if active_only:
                sql += " AND m.status = 'Active'"
            sql += " ORDER BY m.name ASC LIMIT 100"
            rows = db_manager.fetch_all(sql)
            return [Medicine.from_row(r) for r in rows]

        pattern = f"%{query.strip()}%"
        sql = """
            SELECT m.*, c.name AS category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE (
                m.name LIKE ?
                OR m.generic_name LIKE ?
                OR m.barcode LIKE ?
                OR m.batch_number LIKE ?
                OR m.manufacturer LIKE ?
            )
        """
        if active_only:
            sql += " AND m.status = 'Active'"

        sql += " ORDER BY m.name ASC LIMIT 100"
        rows = db_manager.fetch_all(sql, (pattern, pattern, pattern, pattern, pattern))
        return [Medicine.from_row(r) for r in rows]

    def search_sales(self, query: str) -> List[Dict[str, Any]]:
        """Searches sales records by invoice number, customer phone, customer name, or payment method."""
        if not query or not query.strip():
            sql = """
                SELECT s.*, c.name AS customer_name, u.full_name AS cashier_name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN users u ON s.user_id = u.id
                ORDER BY s.sale_date DESC LIMIT 50
            """
            return db_manager.fetch_all(sql)

        pattern = f"%{query.strip()}%"
        sql = """
            SELECT s.*, c.name AS customer_name, u.full_name AS cashier_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.invoice_number LIKE ?
               OR c.name LIKE ?
               OR c.phone LIKE ?
               OR s.payment_method LIKE ?
            ORDER BY s.sale_date DESC LIMIT 50
        """
        return db_manager.fetch_all(sql, (pattern, pattern, pattern, pattern))

    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """Searches customers by name or phone."""
        if not query or not query.strip():
            return db_manager.fetch_all("SELECT * FROM customers ORDER BY name ASC LIMIT 50")

        pattern = f"%{query.strip()}%"
        sql = """
            SELECT * FROM customers
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY name ASC LIMIT 50
        """
        return db_manager.fetch_all(sql, (pattern, pattern))

    def search_suppliers(self, query: str) -> List[Dict[str, Any]]:
        """Searches suppliers by company name, contact person, or telephone."""
        if not query or not query.strip():
            return db_manager.fetch_all("SELECT * FROM suppliers ORDER BY name ASC LIMIT 50")

        pattern = f"%{query.strip()}%"
        sql = """
            SELECT * FROM suppliers
            WHERE name LIKE ? OR contact_person LIKE ? OR phone LIKE ?
            ORDER BY name ASC LIMIT 50
        """
        return db_manager.fetch_all(sql, (pattern, pattern, pattern))


# Global singleton instance
search_service = SearchService()

