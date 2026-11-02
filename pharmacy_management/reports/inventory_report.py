"""
================================================================================
Pharmacy Management System - Inventory Valuation & Health Report
================================================================================
Module: pharmacy_management.reports.inventory_report
Quality Objective: Q10 - Improve Documentation & Valuation Auditing

Description:
    Generates inventory summaries, category-wise stock asset values,
    and CSV export data for balance sheet reconciliations.
================================================================================
"""

from typing import Dict, Any, List
from datetime import datetime
from pharmacy_management.services.inventory_service import inventory_service
from pharmacy_management.services.report_service import report_service
from pharmacy_management.utils.helpers import format_currency, generate_csv_string
from pharmacy_management.config import settings


class InventoryReportGenerator:
    """Generates stock health and inventory asset valuation reports."""

    @staticmethod
    def generate_summary() -> Dict[str, Any]:
        """Returns inventory summary indicators."""
        return inventory_service.get_inventory_summary()

    @staticmethod
    def generate_text_report() -> str:
        """Produces a formatted ASCII inventory valuation report."""
        summary = inventory_service.get_inventory_summary()
        cat_breakdown = report_service.get_inventory_valuation_by_category()
        divider = "=" * 65
        thin_divider = "-" * 65

        lines = [
            divider,
            f"{settings.APP_NAME:^65}",
            f"{'INVENTORY ASSET VALUATION & STOCK HEALTH REPORT':^65}",
            divider,
            f"Generated On          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Active SKU Count      : {summary['total_medicines']}",
            f"Total Units in Stock  : {summary['total_units']}",
            f"Total Asset Cost      : {format_currency(summary['total_cost_value'])}",
            f"Total Retail Value    : {format_currency(summary['total_retail_value'])}",
            f"Projected Gross Margin: {format_currency(summary['potential_profit'])}",
            f"Low Stock SKUs        : {summary['low_stock_count']}",
            f"Expired SKUs          : {summary['expired_count']}",
            thin_divider,
            "CATEGORY VALUATION BREAKDOWN",
            thin_divider,
            f"{'Category':<26}{'SKUs':>6}{'Units':>8}{'Cost Val':>12}{'Retail Val':>13}",
            thin_divider,
        ]

        for cat in cat_breakdown:
            name = cat["category_name"][:24]
            skus = cat["sku_count"]
            units = cat["total_units"] or 0
            cost = format_currency(cat["cost_value"] or 0.0)
            retail = format_currency(cat["retail_value"] or 0.0)
            lines.append(f"{name:<26}{skus:>6}{units:>8}{cost:>12}{retail:>13}")

        lines.append(divider)
        return "\n".join(lines)

    @staticmethod
    def generate_csv() -> str:
        """Exports category valuation breakdown to CSV."""
        cat_breakdown = report_service.get_inventory_valuation_by_category()
        headers = ["Category", "SKU Count", "Total Units", "Cost Valuation", "Retail Valuation"]
        rows = [
            [c["category_name"], c["sku_count"], c["total_units"] or 0, c["cost_value"] or 0.0, c["retail_value"] or 0.0]
            for c in cat_breakdown
        ]
        return generate_csv_string(headers, rows)

