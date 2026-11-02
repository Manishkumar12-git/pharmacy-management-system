"""
================================================================================
Pharmacy Management System - Poka-Yoke Input Validators
================================================================================
Module: pharmacy_management.utils.validators
Quality Objective: Q10 - Improve Documentation & Poka-Yoke Error Prevention

Description:
    Implements source-level data verification and Poka-Yoke (fail-safe) rules.
    Prevents invalid data from propagating into the domain and persistence layers:
      - Rejects blank, whitespace-only, or abnormally long names.
      - Blocks non-positive or negative prices and costs.
      - Enforces positive integer quantities and stock constraints.
      - Rejects expired items during dispense/billing operations.
      - Enforces strict date format (YYYY-MM-DD) and logical date bounds.
================================================================================
"""

import re
from datetime import datetime, date
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class ValidationResult:
    """Encapsulates the outcome of a validation check.

    Attributes:
        is_valid (bool): True if verification succeeded, False if a defect was detected.
        message (str): Human-readable error description or empty string.
        field (str): Name of the validated input field.
        error_code (str): Structured error identifier for Poka-Yoke audit reporting.
    """
    is_valid: bool
    message: str = ""
    field: str = ""
    error_code: str = ""

    def __bool__(self) -> bool:
        return self.is_valid


def validate_text(
    value: Optional[str],
    field_name: str,
    min_length: int = 1,
    max_length: int = 100,
    required: bool = True
) -> ValidationResult:
    """Validates generic string inputs for presence, length, and sanity.

    Args:
        value (Optional[str]): String to validate.
        field_name (str): Label of the field for reporting.
        min_length (int): Minimum required length. Defaults to 1.
        max_length (int): Maximum allowed length. Defaults to 100.
        required (bool): Whether empty values are rejected.

    Returns:
        ValidationResult: Result containing validation status and error message.
    """
    if value is None or not str(value).strip():
        if required:
            return ValidationResult(
                is_valid=False,
                message=f"{field_name} is required and cannot be blank.",
                field=field_name,
                error_code="ERR_BLANK_FIELD"
            )
        return ValidationResult(is_valid=True, field=field_name)

    cleaned = str(value).strip()
    if len(cleaned) < min_length:
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} must have at least {min_length} characters.",
            field=field_name,
            error_code="ERR_TOO_SHORT"
        )
    if len(cleaned) > max_length:
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} cannot exceed {max_length} characters.",
            field=field_name,
            error_code="ERR_TOO_LONG"
        )

    return ValidationResult(is_valid=True, field=field_name)


def validate_positive_number(
    value: Union[str, float, int],
    field_name: str,
    allow_zero: bool = False
) -> ValidationResult:
    """Validates that a numeric input is positive and correctly formatted.

    Args:
        value (Union[str, float, int]): Numeric value or representation.
        field_name (str): Field identifier.
        allow_zero (bool): Whether zero is deemed valid. Defaults to False.

    Returns:
        ValidationResult: Result object.
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} must be a valid numeric value.",
            field=field_name,
            error_code="ERR_INVALID_NUMBER"
        )

    if allow_zero:
        if num < 0:
            return ValidationResult(
                is_valid=False,
                message=f"{field_name} cannot be negative (provided: {num}).",
                field=field_name,
                error_code="ERR_NEGATIVE_VALUE"
            )
    else:
        if num <= 0:
            return ValidationResult(
                is_valid=False,
                message=f"{field_name} must be strictly greater than zero (provided: {num}).",
                field=field_name,
                error_code="ERR_NON_POSITIVE_VALUE"
            )

    return ValidationResult(is_valid=True, field=field_name)


def validate_integer(
    value: Union[str, int],
    field_name: str,
    min_value: int = 0
) -> ValidationResult:
    """Validates that an input is an integer meeting the minimum value threshold.

    Args:
        value (Union[str, int]): Value to test.
        field_name (str): Field label.
        min_value (int): Minimum integer value accepted. Defaults to 0.

    Returns:
        ValidationResult: Result object.
    """
    try:
        val_str = str(value).strip()
        if not val_str.lstrip("-").isdigit():
            raise ValueError()
        num = int(val_str)
    except (ValueError, TypeError):
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} must be a valid integer.",
            field=field_name,
            error_code="ERR_INVALID_INTEGER"
        )

    if num < min_value:
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} cannot be less than {min_value} (provided: {num}).",
            field=field_name,
            error_code="ERR_INTEGER_OUT_OF_BOUNDS"
        )

    return ValidationResult(is_valid=True, field=field_name)


def validate_date_string(date_text: str, field_name: str = "Date") -> ValidationResult:
    """Validates that a string adheres to YYYY-MM-DD calendar date specifications.

    Args:
        date_text (str): Candidate date string.
        field_name (str): Field identifier. Defaults to 'Date'.

    Returns:
        ValidationResult: Result object.
    """
    if not date_text or not str(date_text).strip():
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} cannot be blank.",
            field=field_name,
            error_code="ERR_BLANK_DATE"
        )

    cleaned = str(date_text).strip()
    try:
        parsed_date = datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        return ValidationResult(
            is_valid=False,
            message=f"{field_name} must follow YYYY-MM-DD format (e.g., 2026-12-31).",
            field=field_name,
            error_code="ERR_INVALID_DATE_FORMAT"
        )

    return ValidationResult(is_valid=True, field=field_name)


def validate_not_expired(expiry_date_str: str, medicine_name: str = "Item") -> ValidationResult:
    """Poka-Yoke check: Ensures a medicine batch has not passed its expiration date.

    Args:
        expiry_date_str (str): Expiration date string in YYYY-MM-DD format.
        medicine_name (str): Name of medicine for clear warning context.

    Returns:
        ValidationResult: Result object. False if item is expired.
    """
    date_res = validate_date_string(expiry_date_str, "Expiry Date")
    if not date_res:
        return date_res

    exp_date = datetime.strptime(expiry_date_str.strip(), "%Y-%m-%d").date()
    today = date.today()

    if exp_date <= today:
        days_ago = (today - exp_date).days
        return ValidationResult(
            is_valid=False,
            message=(
                f"POKA-YOKE REJECTION: '{medicine_name}' expired on {expiry_date_str} "
                f"({days_ago} days ago). Dispensing expired pharmaceutical products is forbidden."
            ),
            field="expiry_date",
            error_code="ERR_EXPIRED_MEDICINE"
        )

    return ValidationResult(is_valid=True, field="expiry_date")


def validate_stock_availability(
    requested_qty: int,
    available_stock: int,
    medicine_name: str = "Medicine"
) -> ValidationResult:
    """Poka-Yoke check: Ensures requested dispensing quantity does not exceed inventory on hand.

    Args:
        requested_qty (int): Units requested.
        available_stock (int): Units currently in storage.
        medicine_name (str): Medicine name for diagnostics.

    Returns:
        ValidationResult: Result object.
    """
    if requested_qty <= 0:
        return ValidationResult(
            is_valid=False,
            message=f"Requested quantity for '{medicine_name}' must be at least 1 unit.",
            field="quantity",
            error_code="ERR_ZERO_QUANTITY"
        )

    if requested_qty > available_stock:
        return ValidationResult(
            is_valid=False,
            message=(
                f"POKA-YOKE REJECTION: Insufficient stock for '{medicine_name}'. "
                f"Requested {requested_qty} units, but only {available_stock} available in inventory."
            ),
            field="quantity",
            error_code="ERR_INSUFFICIENT_STOCK"
        )

    return ValidationResult(is_valid=True, field="quantity")


def validate_phone(phone: Optional[str]) -> ValidationResult:
    """Validates customer or supplier contact telephone strings.

    Args:
        phone (Optional[str]): Phone number string.

    Returns:
        ValidationResult: Result object.
    """
    if not phone or not str(phone).strip():
        return ValidationResult(
            is_valid=False,
            message="Phone number is required.",
            field="phone",
            error_code="ERR_BLANK_PHONE"
        )

    cleaned = re.sub(r"[\s\-\(\)\+]", "", str(phone).strip())
    if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
        return ValidationResult(
            is_valid=False,
            message="Phone number must contain between 7 and 15 digits.",
            field="phone",
            error_code="ERR_INVALID_PHONE"
        )

    return ValidationResult(is_valid=True, field="phone")


def validate_email(email: Optional[str], required: bool = False) -> ValidationResult:
    """Validates email format using standard regular expressions.

    Args:
        email (Optional[str]): Email string.
        required (bool): Whether empty string is allowed. Defaults to False.

    Returns:
        ValidationResult: Result object.
    """
    if not email or not str(email).strip():
        if required:
            return ValidationResult(
                is_valid=False,
                message="Email address is required.",
                field="email",
                error_code="ERR_BLANK_EMAIL"
            )
        return ValidationResult(is_valid=True, field="email")

    pattern = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"
    if not re.match(pattern, str(email).strip()):
        return ValidationResult(
            is_valid=False,
            message="Invalid email address format (e.g., name@domain.com).",
            field="email",
            error_code="ERR_INVALID_EMAIL"
        )

    return ValidationResult(is_valid=True, field="email")

