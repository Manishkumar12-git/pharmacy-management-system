# PharmaCare Quality PMS — End-User Operations Manual
**Total Quality Management (TQM) Edition**
**Assigned Quality Goal:** `Q10: Improve Documentation & Defect Prevention`
**Application Version:** `2.5.0-TQM`
**Target Audience:** Pharmacy Administrators, Chief Pharmacists, Pharmacy Technicians, and Cashiers

---

## Table of Contents
1. [Executive Summary & Quality Philosophy (TQM Q10)](#1-executive-summary--quality-philosophy)
2. [Architectural Principles & Layered Flow](#2-architectural-principles--layered-flow)
3. [System Setup & Default Credentials](#3-system-setup--default-credentials)
4. [User Roles and Permissions (RBAC)](#4-user-roles-and-permissions)
5. [Operational Module Walkthroughs](#5-operational-module-walkthroughs)
   - [5.1 Dashboard & Live KPI Monitoring](#51-dashboard--live-kpi-monitoring)
   - [5.2 Billing & Point of Sale (POS)](#52-billing--point-of-sale-pos)
   - [5.3 Medicine Catalog Management](#53-medicine-catalog-management)
   - [5.4 Inventory Control & Expiry Tracking](#54-inventory-control--expiry-tracking)
   - [5.5 Supplier Purchases & Restocking](#55-supplier-purchases--restocking)
   - [5.6 Customer Loyalty & Profiles](#56-customer-loyalty--profiles)
   - [5.7 Universal Search](#57-universal-search)
   - [5.8 Management & Quality Reports](#58-management--quality-reports)
   - [5.9 User Account Management](#59-user-account-management)
   - [5.10 In-App Help & Searchable FAQ (Q10)](#510-in-app-help--searchable-faq)
   - [5.11 About & TQM Quality Audit Scorecard](#511-about--tqm-quality-audit-scorecard)
   - [5.12 Automated FMEA Risk Analysis Dashboard](#512-automated-fmea-risk-analysis-dashboard)
   - [5.13 Interactive Pareto Error Chart (80/20 Rule)](#513-interactive-pareto-error-chart-8020-rule)
   - [5.14 Digital Batch Traceability & Recall Tree](#514-digital-batch-traceability--recall-tree)
6. [Poka-Yoke (Mistake-Proofing) Rules & Error Code Matrix](#6-poka-yoke-rules--error-code-matrix)
7. [Keyboard Shortcuts Reference](#7-keyboard-shortcuts-reference)
8. [Data Backup, Security & Maintenance](#8-data-backup-security--maintenance)

---

## 1. Executive Summary & Quality Philosophy

The **PharmaCare Quality Pharmacy Management System (PMS)** is built from the ground up according to the tenets of **Total Quality Management (TQM)**. Unlike legacy retail systems that allow accidental sales of expired medicines or negative inventory tallies, PharmaCare integrates automated **Poka-Yoke (fail-safe error prevention)** into every transaction boundary.

Under our designated quality objective **Q10: Improve Documentation**, this application provides:
- **Zero Ambiguity:** Complete, human-readable documentation embedded inside the desktop application.
- **Searchable Knowledge Base:** Instant answers to workflow queries and error code resolutions via `Help & FAQ`.
- **Auditable Quality Baselines:** Real-time metrics verifying code documentation coverage, input validation compliance, and defect prevention frequency.

---

## 2. Architectural Principles & Layered Flow

PharmaCare strictly adheres to a three-tier layered architecture:

$$\text{Presentation (UI Layer)} \longrightarrow \text{Business / Service Layer} \longrightarrow \text{Domain Models / SQLite Database}$$

* **Rule 1 (Zero Direct SQL in UI):** UI screens never formulate or execute SQL queries. All interactions invoke dedicated Service classes (`SalesService`, `MedicineService`, `HelpService`, etc.).
* **Rule 2 (Fail-Safe Gateways):** Services validate incoming arguments using `utils.validators` before database execution.
* **Rule 3 (Atomicity):** Multi-table operations (such as reducing inventory, incrementing loyalty points, and saving invoice headers) execute in ACID-compliant database transactions with automatic rollback.

---

## 3. System Setup & Default Credentials

### System Requirements
* Python 3.10+ (Standard Library `tkinter` and `sqlite3` included by default).
* Zero external pip dependencies required.

### Launching the Application
Execute the following command in PowerShell or terminal from the repository root:
```powershell
py pharmacy_management\main.py
```

### Pre-Configured Accounts
The application initializes an SQLite database (`data/pharmacy.db`) seeded with three default test accounts:

| Role | Username | Default Password | Recommended Usage |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | System setup, auditing, user management, financial reports |
| **Pharmacist** | `pharmacist` | `pharm123` | Catalog editing, stock intake, expiry review, dispensing |
| **Cashier** | `cashier` | `cash123` | Counter POS billing, customer registration |

> **Security Note:** Default passwords must be changed immediately upon installation in production environments.

---

## 4. User Roles and Permissions

PharmaCare implements a **Role-Based Access Control (RBAC)** matrix to safeguard system integrity:

| Capability / Screen | Admin | Pharmacist | Cashier |
| :--- | :---: | :---: | :---: |
| Point-of-Sale (POS) Billing | Allowed | Allowed | Allowed |
| Customer Management & Loyalty | Allowed | Allowed | Allowed |
| Medicine Catalog (Add / Edit) | Allowed | Allowed | View Only |
| Inventory Adjustment & Restocking | Allowed | Allowed | View Only |
| Supplier Purchases & Inbound POs | Allowed | Allowed | Restricted |
| Sales & Inventory Reports | Allowed | Allowed | Restricted |
| TQM Quality & Audit Reports | Allowed | Allowed | Restricted |
| User Account Management | Allowed | Restricted | Restricted |
| In-App Help & FAQ (Q10) | Allowed | Allowed | Allowed |

---

## 5. Operational Module Walkthroughs

### 5.1 Dashboard & Live KPI Monitoring
Upon logging in, the **Dashboard** displays real-time operational indicators:
- **Today's Revenue:** Total sales volume processed since midnight.
- **Total Medicines:** Active SKUs in the catalog.
- **Low Stock Alerts:** Items at or below their reorder threshold.
- **Expiring Soon Alerts:** Batches expiring within 60 days.
- **Quick Action Buttons:** Direct shortcuts to start a sale, add medicine, or view quality audits.

### 5.2 Billing & Point of Sale (POS)
The POS interface is optimized for rapid checkout while strictly enforcing patient safety:
1. **Customer Selection:** Choose an existing customer or leave as "Walk-in Customer". To register a new patient, click `+ New Customer`.
2. **Item Search:** Enter medicine name or scan the barcode. The screen displays active stock and expiry date.
3. **Quantity Entry:** Specify requested units.
4. **Poka-Yoke Verification:**
   - If stock is insufficient $\rightarrow$ **Blocked** (`ERR_INSUFFICIENT_STOCK`).
   - If the medicine has expired $\rightarrow$ **Strictly Blocked** (`ERR_EXPIRED_MEDICINE`).
5. **Discounts & Taxes:** Cashiers can enter approved discounts up to 30%.
6. **Checkout & Thermal Receipt:** Select payment method (Cash, Card, UPI, Insurance) and click `Complete Sale`. A professional thermal receipt dialog appears with options to export or print.

### 5.3 Medicine Catalog Management
Allows managing pharmaceutical records:
- **Mandatory Fields:** Name, Batch Number, Unit Price, Cost Price, Expiration Date.
- **Classification:** Therapeutic Category, Manufacturer, Unit Form (Strip, Vial, etc.), Rx Requirement.
- **Storage Condition:** Flag cold-chain medications (e.g., Insulin 2°C–8°C).

### 5.4 Inventory Control & Expiry Tracking
Provides a multi-tab view of stock health:
- **All Stock:** Complete inventory ledger with stock values.
- **Low Stock Filter:** Instantly filters medicines below reorder level.
- **Expiring Soon Filter:** Highlights drugs nearing expiration for return or discount promotion.
- **Expired Quarantine:** Lists expired stock strictly quarantined from sales.

### 5.5 Supplier Purchases & Restocking
Enables logging inbound shipments from wholesale distributors:
- Select the supplier and input their commercial invoice number.
- Add items with batch numbers, verified expiry dates, and unit cost prices.
- Upon saving, on-hand stock quantities are incremented automatically.

### 5.6 Customer Loyalty & Profiles
Tracks patient purchase history, telephone numbers, and loyalty points accumulated at 1 point per ₹100 spent.

### 5.7 Universal Search
A unified lookup center allowing cross-table search across:
- Medicines (by brand, generic ingredient, or barcode)
- Past Sales Invoices (by invoice number or date)
- Suppliers (by name or contact)
- Customers (by phone or name)

### 5.8 Management & Quality Reports
- **Sales Report:** Revenue summaries, gross profit calculations, top-moving items, and payment method breakdowns.
- **Inventory Report:** Stock valuation (total cost vs retail market value).
- **Expiry Risk Report:** Financial risk quantification of expiring batches.
- **TQM Quality Report:** Measures documentation completeness, audit log trail, and Poka-Yoke prevention frequency.

### 5.9 User Account Management
Exclusive to Administrators:
- Create new user accounts with specified roles.
- Reset passwords.
- Deactivate operators without deleting historical audit logs.

### 5.10 In-App Help & Searchable FAQ
Designed specifically for **Quality Objective Q10**:
- **Search Bar:** Real-time keyword filter across questions, answers, and tags.
- **Category Filters:** Filter by POS, Inventory, Poka-Yoke, Security, or Error Codes.
- **Integrated User Manual Viewer:** Browse this operations manual without leaving the app.
- **Shortcuts Sheet:** Instant access to keyboard shortcuts.

### 5.11 About & TQM Quality Audit Scorecard
Presents system metadata, licensing, and an interactive **TQM Audit Engine** that inspects database integrity, docstring coverage, and defect prevention health in real time.

### 5.12 Automated FMEA Risk Analysis Dashboard
Enables dynamic Failure Mode & Effects Analysis:
- Visualizes Risk Priority Numbers ($\text{RPN} = S \times O \times D$) for critical pharmacy failure modes.
- Occurrence ($O$) is derived live from `error_logs` and `poka_yoke_events` counts.
- Adjust Severity and Detection weights dynamically with live color-coded risk bands (High, Medium, Low).
- Review Poka-Yoke mistake-proofing controls and export FMEA matrices to CSV.

### 5.13 Interactive Pareto Error Chart (80/20 Rule)
Isolates the "Vital Few" defects causing 80% of operational errors:
- Pure Tkinter dual-axis chart: Bars represent error frequency (descending order), and the curved line plots cumulative percentage.
- The 80% reference marker separates the high-priority failure modes from the "Useful Many".
- Real-time analytical summary explains the operational insight and recommended focus areas.

### 5.14 Digital Batch Traceability & Recall Tree
Provides complete forward and backward supply chain traceability:
- **Backward Traceability:** Look up any batch or medicine to inspect inbound supplier restock orders, wholesale distributor contact info, purchase invoice numbers, and unit costs.
- **Current Inventory Status:** Remaining stock, shelf/cold-chain storage conditions, days to expiry, and automatic status badges.
- **Forward Traceability:** Comprehensive distribution log detailing every customer/patient invoice, dispensed quantity, timestamp, and cashier.
- **Mass Balance Audit:** Verifies physical consistency: $\text{Received} = \text{Sold} + \text{On Hand}$.
- **Emergency Recall Export:** Export patient contact manifests to CSV in one click for regulatory compliance.

---

## 6. Poka-Yoke Rules & Error Code Matrix

| Error Code | Trigger Condition | System Action | Resolution |
| :--- | :--- | :--- | :--- |
| `ERR_BLANK_FIELD` | Mandatory field left blank | Form submission blocked | Input required information |
| `ERR_NEGATIVE_VALUE` | Price or quantity $\le 0$ | Input rejected | Enter positive value |
| `ERR_INSUFFICIENT_STOCK` | Requested qty > Available stock | POS item add blocked | Reduce qty or restock |
| `ERR_EXPIRED_MEDICINE` | Item expiry date $\le$ Today | POS item add strictly blocked | Quarantine item; do not sell |
| `ERR_INVALID_DATE_FORMAT` | Date does not follow `YYYY-MM-DD` | Date input rejected | Use format `2026-12-31` |
| `ERR_DISCOUNT_EXCEEDED` | Discount $> 30\%$ without override | Sale processing blocked | Cap discount at $\le 30\%$ |
| `ERR_DUPLICATE_USERNAME` | Username already registered | Account creation blocked | Choose unique username |

---

## 7. Keyboard Shortcuts Reference

| Shortcut | Action | Scope |
| :--- | :--- | :--- |
| `Ctrl + B` | Switch to Billing / POS Screen | Global |
| `Ctrl + M` | Switch to Medicines Screen | Global |
| `Ctrl + I` | Switch to Inventory Screen | Global |
| `Ctrl + F` | Switch to Universal Search | Global |
| `F1` | Open In-App Help & FAQ (Q10) | Global |
| `Ctrl + R` | Refresh Current Table Data | Active Screen |
| `Escape` | Close Dialog or Modal Window | Modal |

---

## 8. Data Backup, Security & Maintenance

1. **Database Location:** All data is persisted in `pharmacy_management/data/pharmacy.db`.
2. **Backing Up:** Simply copy `pharmacy.db` to secure secondary storage or cloud backup while the application is idle.
3. **Audit Logs:** Every administrative action, price change, and Poka-Yoke prevention event is recorded in the `audit_logs` and `poka_yoke_events` tables for compliance inspections.
4. **Log Rotation:** File logs in `pharmacy_management/logs/pharmacy_system.log` automatically rotate when reaching 5MB, retaining 5 historical archives.

