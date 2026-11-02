"""
================================================================================
Pharmacy Management System - General Helper Functions & Formatters
================================================================================
Module: pharmacy_management.utils.helpers
Quality Objective: Q10 - Improve Documentation & User Experience

Description:
    Provides domain formatting utilities, invoice and PO serial generator,
    date math calculations, and export helper routines.
================================================================================
"""

import random
import csv
import io
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from pharmacy_management.config import settings


def format_currency(amount: float) -> str:
    """Formats numeric values into localized currency strings.

    Args:
        amount (float): Monetary value.

    Returns:
        str: Formatted currency representation (e.g., '₹1,250.00').
    """
    try:
        val = float(amount)
        return f"{settings.CURRENCY_SYMBOL}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{settings.CURRENCY_SYMBOL}0.00"


def format_date(dt_value: Any) -> str:
    """Standardizes date presentations to YYYY-MM-DD.

    Args:
        dt_value (Any): Date or datetime object, or string.

    Returns:
        str: ISO date string.
    """
    if isinstance(dt_value, (datetime, date)):
        return dt_value.strftime(settings.DATE_FORMAT)
    if isinstance(dt_value, str) and len(dt_value) >= 10:
        return dt_value[:10]
    return str(dt_value or "")


def generate_sale_invoice_number() -> str:
    """Generates an auditable, collision-resistant sales invoice number.

    Format:
        INV-YYYYMMDD-HHMMSS-RRR (where RRR is 3 random digits)

    Returns:
        str: Unique invoice code.
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    rand_suffix = random.randint(100, 999)
    return f"INV-{timestamp}-{rand_suffix}"


def generate_purchase_invoice_number() -> str:
    """Generates a supplier purchase order reference number.

    Returns:
        str: Unique PO code.
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d")
    rand_suffix = random.randint(1000, 9999)
    return f"PO-{timestamp}-{rand_suffix}"


def calculate_days_until_expiry(expiry_date_str: str) -> int:
    """Calculates signed calendar days between today and the expiry date.

    Args:
        expiry_date_str (str): Date string in YYYY-MM-DD format.

    Returns:
        int: Number of days remaining (negative if already expired).
    """
    try:
        exp_date = datetime.strptime(expiry_date_str.strip()[:10], "%Y-%m-%d").date()
        today = date.today()
        return (exp_date - today).days
    except Exception:
        return 0


def get_expiry_status(expiry_date_str: str) -> Tuple[str, str, str]:
    """Evaluates the pharmaceutical expiry status and assigns a visual theme badge.

    Args:
        expiry_date_str (str): Expiry date (YYYY-MM-DD).

    Returns:
        Tuple[str, str, str]: (Status Label, Foreground Color, Background Color)
            Statuses: 'Expired', 'Critical', 'Expiring Soon', 'Safe'
    """
    days = calculate_days_until_expiry(expiry_date_str)
    if days < 0:
        return "Expired", settings.THEME["DANGER"], settings.THEME["DANGER_BG"]
    if days <= settings.CRITICAL_EXPIRY_DAYS:
        return f"Critical ({days}d)", settings.THEME["DANGER"], settings.THEME["DANGER_BG"]
    if days <= settings.EXPIRY_WARNING_DAYS:
        return f"Expiring Soon ({days}d)", settings.THEME["WARNING"], settings.THEME["WARNING_BG"]
    return f"Safe ({days}d)", settings.THEME["SUCCESS"], settings.THEME["SUCCESS_BG"]


def generate_csv_string(headers: List[str], rows: List[List[Any]]) -> str:
    """Converts tabular data rows into an RFC-4180 compliant CSV string.

    Args:
        headers (List[str]): Column headers.
        rows (List[List[Any]]): Row data matrix.

    Returns:
        str: Formatted CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def generate_receipt_text(sale_data: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    """Generates an ASCII receipt for POS thermal printing or text export.

    Args:
        sale_data (Dict[str, Any]): Sale record header.
        items (List[Dict[str, Any]]): Sale line items.

    Returns:
        str: Formatted ASCII thermal receipt string.
    """
    divider = "=" * 48
    thin_divider = "-" * 48

    lines = [
        divider,
        f"{settings.APP_NAME:^48}",
        f"{settings.APP_SUBTITLE:^48}",
        f"Quality Objective: {settings.TQM_OBJECTIVE:^48}",
        divider,
        f"Invoice No : {sale_data.get('invoice_number', 'N/A')}",
        f"Date/Time  : {sale_data.get('sale_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
        f"Customer   : {sale_data.get('customer_name', 'Walk-in Customer')}",
        f"Cashier    : {sale_data.get('cashier_name', 'Staff')}",
        f"Payment    : {sale_data.get('payment_method', 'Cash')}",
        thin_divider,
        f"{'Item':<22}{'Qty':>4}{'Price':>10}{'Total':>12}",
        thin_divider,
    ]

    for item in items:
        name = item.get("medicine_name", "Item")[:20]
        qty = item.get("quantity", 1)
        price = item.get("unit_price", 0.0)
        tot = item.get("total_price", 0.0)
        lines.append(f"{name:<22}{qty:>4}{price:>10.2f}{tot:>12.2f}")

    lines.extend([
        thin_divider,
        f"{'Subtotal:':<34}{format_currency(sale_data.get('subtotal', 0.0)):>14}",
        f"{'Discount (' + str(sale_data.get('discount_percent', 0)) + '%):':<34}"
        f"-{format_currency(sale_data.get('discount_amount', 0.0)):>13}",
        f"{'Tax (' + str(sale_data.get('tax_percent', 0)) + '%):':<34}"
        f"+{format_currency(sale_data.get('tax_amount', 0.0)):>13}",
        divider,
        f"{'GRAND TOTAL:':<34}{format_currency(sale_data.get('grand_total', 0.0)):>14}",
        divider,
        f"{'Thank you for trusting PharmaCare!':^48}",
        f"{'Poka-Yoke Verified - Quality Assured':^48}",
        divider,
    ])

    return "\n".join(lines)

