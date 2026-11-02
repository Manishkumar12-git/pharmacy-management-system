"""
================================================================================
Pharmacy Management System - Database Initialization & Seed Migrations
================================================================================
Module: pharmacy_management.database.migrations
Quality Objective: Q10 - Improve Documentation & Initial Quality Baseline

Description:
    Initializes database tables and populates baseline reference data
    for users (Admin, Pharmacist, Cashier), medicine categories,
    sample suppliers, sample customers, and initial pharmaceutical inventory.
================================================================================
"""

from datetime import date, timedelta
from pharmacy_management.database.db import db_manager
from pharmacy_management.database.schema import CREATE_TABLES_SQL
from pharmacy_management.utils.security import hash_password
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


def initialize_database() -> None:
    """Executes schema creation scripts and seeds default records if empty."""
    logger.info("Initializing database schema...")
    db_manager.execute_script(CREATE_TABLES_SQL)
    seed_default_data()
    logger.info("Database schema and baseline seed verification complete.")


def seed_default_data() -> None:
    """Seeds baseline administrative users, categories, suppliers, customers, and inventory."""
    _seed_users()
    _seed_categories()
    _seed_suppliers()
    _seed_customers()
    _seed_medicines()


def _seed_users() -> None:
    """Seeds standard role accounts if user table is empty."""
    user_count = db_manager.fetch_one("SELECT COUNT(*) AS count FROM users")["count"]
    if user_count > 0:
        return

    logger.info("Seeding default user accounts (Admin, Pharmacist, Cashier)...")
    default_users = [
        ("admin", "admin123", "System Administrator", "Admin", "admin@pharmacare.local", "9876543210"),
        ("pharmacist", "pharm123", "dr.bargli", "Pharmacist", "dr.bargli@pharmacare.local", "9876543211"),
        ("cashier", "cash123", "Vineet", "Cashier", "vineet@pharmacare.local", "9876543212"),
    ]

    for uname, pwd, name, role, email, phone in default_users:
        pwd_hash, salt = hash_password(pwd)
        db_manager.execute_query(
            """
            INSERT INTO users (username, password_hash, salt, full_name, role, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (uname, pwd_hash, salt, name, role, email, phone)
        )


def _seed_categories() -> None:
    """Seeds standard pharmaceutical therapeutic categories."""
    cat_count = db_manager.fetch_one("SELECT COUNT(*) AS count FROM categories")["count"]
    if cat_count > 0:
        return

    logger.info("Seeding pharmaceutical drug categories...")
    categories = [
        ("Antibiotics", "Antimicrobial substances active against bacteria"),
        ("Analgesics & Antipyretics", "Pain relief and fever reduction medications"),
        ("Cardiovascular", "Antihypertensive and cardiac regulation drugs"),
        ("Antidiabetic", "Blood glucose regulation and insulin management"),
        ("Vitamins & Supplements", "Dietary supplements, micronutrients, and minerals"),
        ("Dermatology", "Topical treatments, ointments, and skin care agents"),
        ("Gastrointestinal", "Antacids, proton pump inhibitors, and antiemetics"),
        ("Respiratory", "Bronchodilators, antihistamines, and cough syrups"),
    ]

    for name, desc in categories:
        db_manager.execute_query(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, desc)
        )


def _seed_suppliers() -> None:
    """Seeds baseline certified pharmaceutical wholesale suppliers."""
    sup_count = db_manager.fetch_one("SELECT COUNT(*) AS count FROM suppliers")["count"]
    if sup_count > 0:
        return

    logger.info("Seeding certified pharmaceutical suppliers...")
    suppliers = [
        ("Apollo Wholesale Pharma Ltd", "Vikram Malhotra", "9810011223", "vikram@apollopharm.com", "Sector 14, Industrial Area, New Delhi", "GSTIN07AAACA1234A1Z"),
        ("Sun Health Logistics", "Pooja Reddy", "9820033445", "pooja@sunlogistics.com", "Andheri East, Logistics Hub, Mumbai", "GSTIN27AAACB5678B1Z"),
        ("MedLife National Distributors", "Rajesh Sharma", "9830055667", "orders@medlifenat.com", "Electronics City, Phase 1, Bengaluru", "GSTIN29AAACC9012C1Z"),
    ]

    for name, contact, phone, email, addr, gst in suppliers:
        db_manager.execute_query(
            """
            INSERT INTO suppliers (name, contact_person, phone, email, address, gst_tax_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, contact, phone, email, addr, gst)
        )


def _seed_customers() -> None:
    """Seeds baseline customer records."""
    cust_count = db_manager.fetch_one("SELECT COUNT(*) AS count FROM customers")["count"]
    if cust_count > 0:
        return

    logger.info("Seeding baseline customer profiles...")
    customers = [
        ("Walk-in Customer", "9999999999", "walkin@pharmacare.local", "Counter Sales", 0),
        ("John Arthur", "9845012345", "john.arthur@email.com", "42 Green Valley Ave, New Delhi", 120),
        ("Mary Catherine", "9845067890", "mary.catherine@email.com", "15 Lakeview Heights, Mumbai", 85),
    ]

    for name, phone, email, addr, pts in customers:
        db_manager.execute_query(
            """
            INSERT INTO customers (name, phone, email, address, loyalty_points)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, phone, email, addr, pts)
        )


def _seed_medicines() -> None:
    """Seeds baseline pharmaceutical inventory with varying stock and expiry profiles."""
    med_count = db_manager.fetch_one("SELECT COUNT(*) AS count FROM medicines")["count"]
    if med_count > 0:
        return

    logger.info("Seeding initial pharmaceutical catalog and inventory batches...")
    today = date.today()

    # Pre-calculated dynamic dates for realistic demonstration
    safe_expiry_1 = (today + timedelta(days=420)).isoformat()
    safe_expiry_2 = (today + timedelta(days=310)).isoformat()
    near_expiry = (today + timedelta(days=28)).isoformat()    # Warning: 28 days left
    critical_expiry = (today + timedelta(days=7)).isoformat()  # Critical: 7 days left
    expired_batch = (today - timedelta(days=15)).isoformat()   # Expired: For Poka-Yoke demo

    # Structure: (name, generic, cat_id, batch, barcode, mfg, unit, unit_price, cost_price, stock, reorder, expiry, storage, rx)
    medicines = [
        ("Amoxicillin 500mg", "Amoxicillin Trihydrate", 1, "AMX-2026-01", "8901234567890", "Pfizer Labs", "Strip of 10", 125.00, 85.00, 150, 20, safe_expiry_1, "Cool & Dry (<25°C)", 1),
        ("Paracetamol 650mg (Dolo)", "Paracetamol", 2, "PCM-2026-09", "8901234567891", "Micro Labs", "Strip of 15", 35.00, 20.00, 250, 30, safe_expiry_2, "Room Temperature", 0),
        ("Metformin 500mg", "Metformin Hydrochloride", 4, "MET-2026-44", "8901234567892", "USV Pharma", "Strip of 10", 45.00, 28.00, 18, 25, near_expiry, "Room Temperature", 1),
        ("Atorvastatin 20mg", "Atorvastatin Calcium", 3, "ATV-2026-88", "8901234567893", "Sun Pharma", "Strip of 10", 160.00, 110.00, 8, 15, safe_expiry_1, "Cool & Dry (<25°C)", 1),  # Low stock
        ("Cetirizine 10mg", "Cetirizine Dihydrochloride", 8, "CTZ-2026-12", "8901234567894", "Dr. Reddy's", "Strip of 10", 25.00, 14.00, 300, 20, safe_expiry_2, "Room Temperature", 0),
        ("Azithromycin 500mg (Azithral)", "Azithromycin", 1, "AZI-2026-03", "8901234567895", "Alembic Pharma", "Strip of 3", 115.00, 78.00, 4, 15, critical_expiry, "Cool & Dry (<25°C)", 1), # Critical expiry + low stock
        ("Omeprazole 20mg (Omez)", "Omeprazole", 7, "OMZ-2026-77", "8901234567896", "Dr. Reddy's", "Strip of 15", 85.00, 52.00, 120, 20, safe_expiry_1, "Room Temperature", 0),
        ("Vitamin C 500mg (Limcee)", "Ascorbic Acid", 5, "VTC-2025-99", "8901234567897", "Abbott Healthcare", "Strip of 15", 30.00, 18.00, 180, 25, expired_batch, "Cool & Dry (<25°C)", 0), # Expired (Poka-Yoke demonstration item)
        ("Pantoprazole 40mg (Pan 40)", "Pantoprazole Sodium", 7, "PAN-2026-31", "8901234567898", "Alkem Labs", "Strip of 15", 145.00, 95.00, 90, 15, safe_expiry_2, "Room Temperature", 0),
        ("Insulin Glargine 100IU", "Insulin Glargine", 4, "INS-2026-05", "8901234567899", "Sanofi Aventis", "Vial (10ml)", 680.00, 510.00, 12, 10, safe_expiry_1, "Refrigerated (2°C - 8°C)", 1),
    ]

    for item in medicines:
        db_manager.execute_query(
            """
            INSERT INTO medicines (
                name, generic_name, category_id, batch_number, barcode,
                manufacturer, unit, unit_price, cost_price, stock_quantity,
                reorder_level, expiry_date, storage_condition, prescription_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item
        )

