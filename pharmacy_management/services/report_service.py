"""
================================================================================
Pharmacy Management System - Reporting & Business Intelligence Service
================================================================================
Module: pharmacy_management.services.report_service
Quality Objective: Q10 - Improve Documentation & Quality Analytics

Description:
    Aggregates financial, inventory, expiry risk, and Total Quality Management
    (TQM) metrics for executive decision-making and quality auditing.
================================================================================
"""

from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from pharmacy_management.database.db import db_manager


class ReportService:
    """Consolidated business intelligence and analytics reporting engine."""

    def get_sales_analytics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculates revenue, gross margin, invoice volume, and payment distributions.

        Args:
            start_date (Optional[str]): Start filter (YYYY-MM-DD).
            end_date (Optional[str]): End filter (YYYY-MM-DD).

        Returns:
            Dict[str, Any]: Sales analytics structure.
        """
        sql = """
            SELECT
                COUNT(s.id) AS total_invoices,
                COALESCE(SUM(s.grand_total), 0.0) AS total_revenue,
                COALESCE(SUM(s.discount_amount), 0.0) AS total_discount,
                COALESCE(SUM(s.tax_amount), 0.0) AS total_tax
            FROM sales s
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND date(s.sale_date) >= date(?)"
            params.append(start_date)
        if end_date:
            sql += " AND date(s.sale_date) <= date(?)"
            params.append(end_date)

        summary = db_manager.fetch_one(sql, tuple(params))

        # Top 5 best selling medicines
        top_sql = """
            SELECT m.name, SUM(si.quantity) AS total_qty, SUM(si.total_price) AS total_revenue
            FROM sale_items si
            JOIN medicines m ON si.medicine_id = m.id
            JOIN sales s ON si.sale_id = s.id
            WHERE 1=1
        """
        top_params = []
        if start_date:
            top_sql += " AND date(s.sale_date) >= date(?)"
            top_params.append(start_date)
        if end_date:
            top_sql += " AND date(s.sale_date) <= date(?)"
            top_params.append(end_date)

        top_sql += " GROUP BY m.id, m.name ORDER BY total_qty DESC LIMIT 5"
        top_items = db_manager.fetch_all(top_sql, tuple(top_params))

        # Payment methods breakdown
        pm_sql = """
            SELECT payment_method, COUNT(*) AS count, SUM(grand_total) AS total
            FROM sales
            WHERE 1=1
        """
        pm_params = []
        if start_date:
            pm_sql += " AND date(sale_date) >= date(?)"
            pm_params.append(start_date)
        if end_date:
            pm_sql += " AND date(sale_date) <= date(?)"
            pm_params.append(end_date)

        pm_sql += " GROUP BY payment_method"
        pm_breakdown = db_manager.fetch_all(pm_sql, tuple(pm_params))

        return {
            "total_invoices": summary["total_invoices"],
            "total_revenue": float(summary["total_revenue"]),
            "total_discount": float(summary["total_discount"]),
            "total_tax": float(summary["total_tax"]),
            "top_selling_medicines": top_items,
            "payment_breakdown": pm_breakdown,
        }

    def get_inventory_valuation_by_category(self) -> List[Dict[str, Any]]:
        """Returns inventory value and SKU count grouped by drug category."""
        sql = """
            SELECT
                COALESCE(c.name, 'Uncategorized') AS category_name,
                COUNT(m.id) AS sku_count,
                SUM(m.stock_quantity) AS total_units,
                SUM(m.stock_quantity * m.cost_price) AS cost_value,
                SUM(m.stock_quantity * m.unit_price) AS retail_value
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status = 'Active'
            GROUP BY c.id, c.name
            ORDER BY retail_value DESC
        """
        return db_manager.fetch_all(sql)

    def get_expiry_risk_analytics(self) -> Dict[str, Any]:
        """Quantifies financial exposure of expiring inventory batches."""
        today = date.today().isoformat()
        in_30 = (date.today() + timedelta(days=30)).isoformat()
        in_60 = (date.today() + timedelta(days=60)).isoformat()
        in_90 = (date.today() + timedelta(days=90)).isoformat()

        # Expired items
        expired = db_manager.fetch_one(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(stock_quantity * cost_price), 0.0) AS value_at_risk
            FROM medicines WHERE status = 'Active' AND expiry_date <= ?
            """,
            (today,)
        )

        # 1-30 days
        exp_30 = db_manager.fetch_one(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(stock_quantity * cost_price), 0.0) AS value_at_risk
            FROM medicines WHERE status = 'Active' AND expiry_date > ? AND expiry_date <= ?
            """,
            (today, in_30)
        )

        # 31-60 days
        exp_60 = db_manager.fetch_one(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(stock_quantity * cost_price), 0.0) AS value_at_risk
            FROM medicines WHERE status = 'Active' AND expiry_date > ? AND expiry_date <= ?
            """,
            (in_30, in_60)
        )

        # 61-90 days
        exp_90 = db_manager.fetch_one(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(stock_quantity * cost_price), 0.0) AS value_at_risk
            FROM medicines WHERE status = 'Active' AND expiry_date > ? AND expiry_date <= ?
            """,
            (in_60, in_90)
        )

        return {
            "expired": {"count": expired["count"], "value": float(expired["value_at_risk"])},
            "within_30_days": {"count": exp_30["count"], "value": float(exp_30["value_at_risk"])},
            "within_60_days": {"count": exp_60["count"], "value": float(exp_60["value_at_risk"])},
            "within_90_days": {"count": exp_90["count"], "value": float(exp_90["value_at_risk"])},
        }

    def get_tqm_metrics(self) -> Dict[str, Any]:
        """Retrieves TQM audit counts, Poka-Yoke prevention events, and quality indicators."""
        audit_count = db_manager.fetch_one("SELECT COUNT(*) AS c FROM audit_logs")["c"]
        poka_count = db_manager.fetch_one("SELECT COUNT(*) AS c FROM poka_yoke_events")["c"]

        rules_breakdown = db_manager.fetch_all(
            """
            SELECT rule_name, COUNT(*) AS count
            FROM poka_yoke_events
            GROUP BY rule_name
            ORDER BY count DESC
            """
        )

        recent_poka_events = db_manager.fetch_all(
            """
            SELECT timestamp, rule_name, message, attempted_value, status
            FROM poka_yoke_events
            ORDER BY timestamp DESC LIMIT 10
            """
        )

        return {
            "total_audit_events": audit_count,
            "total_poka_yoke_interceptions": poka_count,
            "rule_breakdown": rules_breakdown,
            "recent_events": recent_poka_events,
            "quality_goal": "Q10: Improve Documentation",
            "compliance_status": "CERTIFIED_COMPLIANT",
        }


# Global singleton instance
report_service = ReportService()

