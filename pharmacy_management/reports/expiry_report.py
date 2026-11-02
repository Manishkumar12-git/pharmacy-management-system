"""
================================================================================
Pharmacy Management System - Expiry Risk & Quarantine Report
================================================================================
Module: pharmacy_management.reports.expiry_report
Quality Objective: Q10 - Improve Documentation & Patient Safety Control

Description:
    Generates regulatory quarantine listings of expired drugs and financial
    exposure summaries for batches approaching expiration.
================================================================================
"""

from typing import Dict, Any, List
from datetime import datetime
from pharmacy_management.services.report_service import report_service
from pharmacy_management.services.inventory_service import inventory_service
from pharmacy_management.utils.helpers import format_currency, generate_csv_string
from pharmacy_management.config import settings


class ExpiryReportGenerator:
    """Generates pharmaceutical expiration and quarantine risk reports."""

    @staticmethod
    def generate_risk_summary() -> Dict[str, Any]:
        """Returns exposure metrics grouped by expiration horizon."""
        return report_service.get_expiry_risk_analytics()

    @staticmethod
    def generate_text_report() -> str:
        """Produces a formatted ASCII quarantine and expiry risk audit."""
        risk = report_service.get_expiry_risk_analytics()
        expired_items = inventory_service.get_expired_items()
        soon_items = inventory_service.get_expiring_soon_items(days=settings.EXPIRY_WARNING_DAYS)
        divider = "=" * 70
        thin_divider = "-" * 70

        lines = [
            divider,
            f"{settings.APP_NAME:^70}",
            f"{'CRITICAL EXPIRY RISK & QUARANTINE AUDIT REPORT':^70}",
            divider,
            f"Generated On          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Expired Batches       : {risk['expired']['count']} (Cost at Risk: {format_currency(risk['expired']['value'])})",
            f"Expiring in 30 Days   : {risk['within_30_days']['count']} (Cost at Risk: {format_currency(risk['within_30_days']['value'])})",
            f"Expiring in 60 Days   : {risk['within_60_days']['count']} (Cost at Risk: {format_currency(risk['within_60_days']['value'])})",
            f"Expiring in 90 Days   : {risk['within_90_days']['count']} (Cost at Risk: {format_currency(risk['within_90_days']['value'])})",
            thin_divider,
            "MANDATORY QUARANTINE LIST (EXPIRED MEDICINES - FORBIDDEN FROM SALE)",
            thin_divider,
            f"{'Medicine Name':<28}{'Batch':<14}{'Units':>6}{'Expiry':>12}{'Loss Value':>10}",
            thin_divider,
        ]

        if not expired_items:
            lines.append("  [No expired items detected in active inventory. Zero quarantine required.]")
        else:
            for item in expired_items:
                name = item.name[:26]
                batch = item.batch_number[:12]
                qty = item.stock_quantity
                exp = item.expiry_date
                val = format_currency(item.cost_price * qty)
                lines.append(f"{name:<28}{batch:<14}{qty:>6}{exp:>12}{val:>10}")

        lines.extend([
            thin_divider,
            f"BATCHES EXPIRING WITHIN {settings.EXPIRY_WARNING_DAYS} DAYS (ACTION REQUIRED)",
            thin_divider,
            f"{'Medicine Name':<28}{'Batch':<14}{'Units':>6}{'Expiry':>12}{'Days Left':>10}",
            thin_divider,
        ])

        if not soon_items:
            lines.append("  [No batches expiring within warning window.]")
        else:
            for item in soon_items:
                name = item.name[:26]
                batch = item.batch_number[:12]
                qty = item.stock_quantity
                exp = item.expiry_date
                days = f"{item.days_until_expiry}d"
                lines.append(f"{name:<28}{batch:<14}{qty:>6}{exp:>12}{days:>10}")

        lines.append(divider)
        return "\n".join(lines)

    @staticmethod
    def generate_csv() -> str:
        """Exports expired and near-expiry medicines to CSV."""
        expired_items = inventory_service.get_expired_items()
        soon_items = inventory_service.get_expiring_soon_items(days=settings.EXPIRY_WARNING_DAYS)
        headers = ["Status", "Medicine Name", "Batch Number", "Stock Units", "Expiry Date", "Unit Cost", "Total Loss"]
        rows = []
        for item in expired_items:
            rows.append(["EXPIRED_QUARANTINE", item.name, item.batch_number, item.stock_quantity, item.expiry_date, item.cost_price, round(item.stock_quantity * item.cost_price, 2)])
        for item in soon_items:
            rows.append(["EXPIRING_SOON", item.name, item.batch_number, item.stock_quantity, item.expiry_date, item.cost_price, round(item.stock_quantity * item.cost_price, 2)])
        return generate_csv_string(headers, rows)

