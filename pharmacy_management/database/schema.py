"""
================================================================================
Pharmacy Management System - Database DDL Schema Definitions
================================================================================
Module: pharmacy_management.database.schema
Quality Objective: Q10 - Improve Documentation & Data Integrity

Description:
    Contains complete ANSI SQLite DDL statements for initializing
    relational tables, foreign key constraints, indexes, and audit logs.
================================================================================
"""

CREATE_TABLES_SQL = """
-- Enable Foreign Key Enforcement
PRAGMA foreign_keys = ON;

-- 1. Users Table (RBAC Authentication)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Admin', 'Pharmacist', 'Cashier')),
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- 3. Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT NOT NULL,
    email TEXT,
    address TEXT,
    gst_tax_id TEXT,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    email TEXT,
    address TEXT,
    loyalty_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Medicines Table
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    generic_name TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    batch_number TEXT NOT NULL,
    barcode TEXT,
    manufacturer TEXT,
    unit TEXT DEFAULT 'Strips',
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    cost_price REAL NOT NULL CHECK(cost_price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 10,
    expiry_date DATE NOT NULL,
    storage_condition TEXT DEFAULT 'Room Temperature',
    prescription_required INTEGER DEFAULT 0 CHECK(prescription_required IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Discontinued')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Purchases Table (Stock Restocking Header)
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    payment_status TEXT DEFAULT 'Paid' CHECK(payment_status IN ('Paid', 'Pending', 'Partial')),
    notes TEXT
);

-- 7. Purchase Items Table
CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    medicine_id INTEGER NOT NULL REFERENCES medicines(id),
    batch_number TEXT NOT NULL,
    expiry_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    cost_price REAL NOT NULL CHECK(cost_price >= 0),
    total_price REAL NOT NULL CHECK(total_price >= 0)
);

-- 8. Sales Table (POS Transaction Header)
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal REAL NOT NULL CHECK(subtotal >= 0),
    discount_percent REAL DEFAULT 0.0 CHECK(discount_percent >= 0),
    discount_amount REAL DEFAULT 0.0 CHECK(discount_amount >= 0),
    tax_percent REAL DEFAULT 0.0 CHECK(tax_percent >= 0),
    tax_amount REAL DEFAULT 0.0 CHECK(tax_amount >= 0),
    grand_total REAL NOT NULL CHECK(grand_total >= 0),
    payment_method TEXT DEFAULT 'Cash' CHECK(payment_method IN ('Cash', 'Card', 'UPI', 'Insurance')),
    notes TEXT
);

-- 9. Sale Items Table
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    medicine_id INTEGER NOT NULL REFERENCES medicines(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    total_price REAL NOT NULL CHECK(total_price >= 0)
);

-- 10. Audit Logs Table (TQM Traceability)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    username TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT
);

-- 11. Poka-Yoke Defect Prevention Events Table (TQM Q10 Focus)
CREATE TABLE IF NOT EXISTS poka_yoke_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    username TEXT,
    rule_name TEXT NOT NULL,
    attempted_value TEXT,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'PREVENTED'
);

-- 12. Error Logs View (TQM Six Sigma Analytics compatibility)
CREATE VIEW IF NOT EXISTS error_logs AS
SELECT
    id,
    timestamp,
    user_id,
    username,
    rule_name AS error_code,
    rule_name AS error_type,
    message,
    attempted_value,
    status
FROM poka_yoke_events;

-- Performance & Integrity Indexes
CREATE INDEX IF NOT EXISTS idx_medicines_name ON medicines(name);
CREATE INDEX IF NOT EXISTS idx_medicines_barcode ON medicines(barcode);
CREATE INDEX IF NOT EXISTS idx_medicines_expiry ON medicines(expiry_date);
CREATE INDEX IF NOT EXISTS idx_medicines_stock ON medicines(stock_quantity);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number);
CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_poka_yoke_timestamp ON poka_yoke_events(timestamp);
"""

