"""
================================================================================
Pharmacy Management System - Sales & Revenue Report Generator
================================================================================
Module: pharmacy_management.reports.sales_report
Quality Objective: Q10 - Improve Documentation & Financial Traceability

Description:
    Generates structured revenue summaries, gross margins, best-selling
    drug rankings, and exportable CSV matrices for executive auditing.
================================================================================
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pharmacy_management.services.report_service import report_service
from pharmacy_management.utils.helpers import format_currency, generate_csv_string
from pharmacy_management.config import settings


class SalesReportGenerator:
    """Generates structured sales and revenue reports."""

    @staticmethod
    def generate_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Produces sales analytics summary dictionary."""
        return report_service.get_sales_analytics(start_date, end_date)

    @staticmethod
    def generate_text_report(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Generates a formatted ASCII sales report."""
        data = report_service.get_sales_analytics(start_date, end_date)
        divider = "=" * 60
        thin_divider = "-" * 60

        period = f"{start_date or 'Beginning'} to {end_date or 'Today'}"
        lines = [
            divider,
            f"{settings.APP_NAME:^60}",
            f"{'EXECUTIVE SALES & REVENUE REPORT':^60}",
            f"{'Reporting Period: ' + period:^60}",
            divider,
            f"Generated On       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Invoices     : {data['total_invoices']}",
            f"Gross Revenue      : {format_currency(data['total_revenue'])}",
            f"Discounts Granted  : {format_currency(data['total_discount'])}",
            f"Taxes Collected    : {format_currency(data['total_tax'])}",
            thin_divider,
            "TOP SELLING PHARMACEUTICALS",
            thin_divider,
            f"{'Medicine Name':<32}{'Units Sold':>12}{'Revenue':>16}",
        ]

        for item in data["top_selling_medicines"]:
            lines.append(f"{item['name'][:30]:<32}{item['total_qty']:>12}{format_currency(item['total_revenue']):>16}")

        lines.extend([
            thin_divider,
            "PAYMENT METHOD DISTRIBUTION",
            thin_divider,
            f"{'Method':<24}{'Transactions':>16}{'Volume':>20}",
        ])

        for pm in data["payment_breakdown"]:
            lines.append(f"{pm['payment_method']:<24}{pm['count']:>16}{format_currency(pm['total']):>20}")

        lines.append(divider)
        return "\n".join(lines)

    @staticmethod
    def generate_csv(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Generates CSV export of top-selling products and revenue summary."""
        data = report_service.get_sales_analytics(start_date, end_date)
        headers = ["Medicine Name", "Units Sold", "Total Revenue"]
        rows = [[item["name"], item["total_qty"], item["total_revenue"]] for item in data["top_selling_medicines"]]
        return generate_csv_string(headers, rows)

