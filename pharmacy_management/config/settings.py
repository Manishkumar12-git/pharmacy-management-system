"""
================================================================================
Pharmacy Management System - Application Configuration & Settings
================================================================================
Module: pharmacy_management.config.settings
Quality Objective: Q10 - Improve Documentation & Total Quality Management (TQM)

Description:
    Centralized configuration management for the Pharmacy Management System.
    Provides immutable application metadata, file paths, database connection
    parameters, theme styles, business validation rules, and Poka-Yoke thresholds.

Design Pattern:
    Singleton configuration object with class-level attributes and helper methods.
================================================================================
"""

import os
from pathlib import Path

# Base Paths
# Resolve root directory of the pharmacy_management package
CONFIG_DIR = Path(__file__).resolve().parent
BASE_DIR = CONFIG_DIR.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Application Metadata (TQM Q10 Compliant)
APP_NAME = "PharmaCare Quality PMS"
APP_SUBTITLE = "Total Quality Management (TQM) Pharmacy Desktop Suite"
APP_VERSION = "2.5.0-TQM"
APP_AUTHOR = "Quality Engineering & Health Informatics Team"
APP_LICENSE = "MIT Enterprise Quality License"
TQM_OBJECTIVE = "Q10: Improve Documentation & Defect Prevention"

# Database Configuration
DATABASE_NAME = "pharmacy.db"
DATABASE_PATH = str(DATA_DIR / DATABASE_NAME)
DB_TIMEOUT_SECONDS = 15.0

# Logging Configuration
LOG_FILE = str(LOGS_DIR / "pharmacy_system.log")
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | [%(levelname)-8s] | %(name)s.%(funcName)s:%(lineno)d | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Poka-Yoke & Business Quality Thresholds
LOW_STOCK_THRESHOLD_DEFAULT = 10         # Alert when quantity <= 10 units
EXPIRY_WARNING_DAYS = 60                 # Alert when expiry is within 60 days
CRITICAL_EXPIRY_DAYS = 15                # Quarantine warning when within 15 days
MAX_DISCOUNT_PERCENT = 30.0              # Poka-Yoke: Block discount higher than 30% without override
DEFAULT_TAX_PERCENT = 5.0                # Default sales tax (GST/VAT)
CURRENCY_SYMBOL = "Rs."                 # Configurable ASCII-safe currency symbol
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Documentation & Help System Paths
FAQ_DATABASE_PATH = str(DOCS_DIR / "FAQ_DATABASE.json")
USER_MANUAL_PATH = str(DOCS_DIR / "USER_MANUAL.md")

# UI Theme & Styling Palette (Clean, Modern Medical Healthcare Aesthetics)
THEME = {
    "PRIMARY": "#0f766e",        # Medical Teal Primary
    "PRIMARY_HOVER": "#115e59",  # Darker Teal for button hover
    "PRIMARY_LIGHT": "#ccfbf1",  # Soft Teal background tint
    "SECONDARY": "#0369a1",      # Deep Sky Blue
    "SECONDARY_HOVER": "#075985",
    "ACCENT": "#0284c7",         # Vibrant Sky Blue
    "BACKGROUND": "#f8fafc",     # Light Slate Canvas
    "SURFACE": "#ffffff",        # Pure White Card Surface
    "SURFACE_ALT": "#f1f5f9",    # Alternating row background
    "TEXT_MAIN": "#0f172a",      # Slate 900 text
    "TEXT_MUTED": "#64748b",     # Slate 500 secondary text
    "TEXT_LIGHT": "#ffffff",     # White on primary
    "BORDER": "#cbd5e1",         # Border color
    "BORDER_LIGHT": "#e2e8f0",   # Soft card border
    "SUCCESS": "#16a34a",        # Green 600
    "SUCCESS_BG": "#dcfce7",     # Green 100
    "WARNING": "#d97706",        # Amber 600
    "WARNING_BG": "#fef3c7",     # Amber 100
    "DANGER": "#dc2626",         # Red 600
    "DANGER_BG": "#fee2e2",      # Red 100
    "INFO": "#2563eb",           # Blue 600
    "INFO_BG": "#dbeafe",        # Blue 100
    "FONT_FAMILY": "Segoe UI",
    "FONT_FAMILY_MONO": "Consolas",
}

# User Roles & Access Control
ROLE_ADMIN = "Admin"
ROLE_PHARMACIST = "Pharmacist"
ROLE_CASHIER = "Cashier"
ALL_ROLES = [ROLE_ADMIN, ROLE_PHARMACIST, ROLE_CASHIER]

# Role Permissions Matrix
ROLE_PERMISSIONS = {
    ROLE_ADMIN: {
        "can_manage_users": True,
        "can_manage_inventory": True,
        "can_process_sales": True,
        "can_process_purchases": True,
        "can_view_reports": True,
        "can_export_data": True,
        "can_override_discounts": True,
        "can_manage_suppliers": True,
        "can_manage_customers": True,
    },
    ROLE_PHARMACIST: {
        "can_manage_users": False,
        "can_manage_inventory": True,
        "can_process_sales": True,
        "can_process_purchases": True,
        "can_view_reports": True,
        "can_export_data": False,
        "can_override_discounts": False,
        "can_manage_suppliers": True,
        "can_manage_customers": True,
    },
    ROLE_CASHIER: {
        "can_manage_users": False,
        "can_manage_inventory": False,
        "can_process_sales": True,
        "can_process_purchases": False,
        "can_view_reports": False,
        "can_export_data": False,
        "can_override_discounts": False,
        "can_manage_suppliers": False,
        "can_manage_customers": True,
    },
}
