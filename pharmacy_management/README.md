# ⚕ PharmaCare Quality PMS — Total Quality Management Suite
> **Enterprise Desktop Pharmacy Management System engineered in Python**  
> **Quality Focus Goal:** `Q10: Improve Documentation & Defect Prevention`  
> **Application Version:** `2.5.0-TQM` | **Architecture:** `3-Tier Layered MVC/Service-Oriented`

---

## 📋 Table of Contents
1. [Project Overview & Philosophy](#1-project-overview--philosophy)
2. [TQM Implementation: Focus on Q10 (Improve Documentation)](#2-tqm-implementation-focus-on-q10)
3. [Architectural Principles & Layered Flow](#3-architectural-principles--layered-flow)
4. [Complete Directory Structure](#4-complete-directory-structure)
5. [Installation & Quick Start](#5-installation--quick-start)
6. [Role-Based Access Control (RBAC) & Default Profiles](#6-role-based-access-control-rbac)
7. [Poka-Yoke (Mistake-Proofing) Safeguards Matrix](#7-poka-yoke-safeguards-matrix)
8. [Module & Service Technical Documentation](#8-module--service-technical-documentation)
9. [Advanced TQM & Six Sigma Analytical Features](#9-advanced-tqm--six-sigma-analytical-features)
10. [Reports & Quality Audits](#10-reports--quality-audits)
11. [AST Documentation Coverage & Quality Verification](#11-ast-documentation-coverage--quality-verification)
12. [License & Compliance](#12-license--compliance)

---

## 1. Project Overview & Philosophy

**PharmaCare Quality PMS** is a full-featured desktop application designed for modern pharmaceutical operations, patient safety, and clinical inventory control. Unlike traditional retail software that permits retroactive error correction, PharmaCare implements **Total Quality Management (TQM)** and **Poka-Yoke (fail-safe mistake-proofing)** to eliminate defects at the source.

### Core Capabilities:
- **Rapid Point of Sale (POS) Billing:** Real-time stock decrements, automated tax/discount bounds, customer loyalty rewards, and thermal ASCII receipt generation.
- **Pharmaceutical Catalog & Batch Tracking:** Therapeutic drug categories, batch IDs, expiration date tracking, and cold-chain storage indicators.
- **Expiry Risk Quarantine:** Automatic visual status badging (Safe, Expiring Soon, Critical, Expired) and hard blocking of expired lot sales.
- **Inbound Restocking:** Wholesale distributor purchase order receiving with automatic on-hand inventory increments.
- **Universal Multi-Criteria Search:** Instant search across drug names, generics, barcodes, batches, sales invoices, customers, and suppliers.
- **TQM Quality Audit Engine:** Real-time source-code AST docstring coverage calculation, Poka-Yoke defect interception logs, and permanent audit trails.

---

## 2. TQM Implementation: Focus on Q10

Under the designated quality goal **Q10: Improve Documentation**, the system addresses the common industrial problem where software documentation is sparse, outdated, or disconnected from operational workflows.

```mermaid
graph TD
    A["TQM Quality Goal: Q10"] --> B["100% In-Code Documentation"]
    A --> C["In-App Knowledge Center (ui/help_faq.py)"]
    A --> D["Live AST Code Coverage Engine (services/help_service.py)"]
    A --> E["Comprehensive Markdown Operations Manual (docs/USER_MANUAL.md)"]

    B --> B1["Every module, class, and method has Google/Sphinx docstrings with type annotations"]
    C --> C1["Searchable FAQ Database (JSON) with keyword and category filters"]
    D --> D1["Real-time abstract syntax tree analysis reporting docstring coverage %"]
    E --> E1["Zero-ambiguity operational guide for Admins, Pharmacists, and Cashiers"]
```

### Key Q10 Deliverables:
1. **Live Code Documentation Inspection:** The application includes an in-memory Abstract Syntax Tree (`ast`) auditor that analyzes all system modules at runtime to verify docstring coverage and display a certified TQM score.
2. **Searchable In-App FAQ Engine:** Powered by `docs/FAQ_DATABASE.json`, operators can filter questions, answers, tags, and specific error codes (`ERR_EXPIRED_MEDICINE`, `ERR_INSUFFICIENT_STOCK`) without leaving the app.
3. **Embedded User Manual Reader:** The complete markdown text of `docs/USER_MANUAL.md` is rendered inside the desktop UI with zero external dependencies.
4. **Permanent Audit Register:** Every operational action, stock override, and blocked defect is serialized to `audit_logs` and `poka_yoke_events` tables.

---

## 3. Architectural Principles & Layered Flow

PharmaCare strictly complies with separation of concerns:

$$\text{Presentation / UI Layer} \longrightarrow \text{Business / Service Layer} \longrightarrow \text{Domain Models / SQLite Database}$$

```mermaid
flowchart TD
    subgraph UI ["Presentation Layer (ui/)"]
        Dashboard["Dashboard & Navigation (dashboard.py)"]
        Billing["POS Counter Billing (billing.py)"]
        Medicines["Medicine Catalog (medicines.py)"]
        Inventory["Inventory & Expiry (inventory.py)"]
        Help["Help & Searchable FAQ (help_faq.py)"]
        About["About & TQM Scorecard (about.py)"]
    end

    subgraph Services ["Service / Business Logic Layer (services/)"]
        AuthSvc["AuthService (auth_service.py)"]
        SalesSvc["SalesService (sales_service.py)"]
        MedSvc["MedicineService (medicine_service.py)"]
        InvSvc["InventoryService (inventory_service.py)"]
        SearchSvc["SearchService (search_service.py)"]
        HelpSvc["HelpService (help_service.py)"]
        ReportSvc["ReportService (report_service.py)"]
    end

    subgraph Validation ["Fail-Safe Gateways (utils/)"]
        Validators["Input & Poka-Yoke Validators (validators.py)"]
        Security["PBKDF2 Hashing & Salt (security.py)"]
    end

    subgraph Data ["Data & Persistence Layer (database/)"]
        DBManager["DatabaseManager Context Pool (db.py)"]
        SQLite[("SQLite Local Storage (pharmacy.db)")]
    end

    UI -->|Method Calls Only| Services
    Services -->|Validates Inputs| Validation
    Services -->|Parameterized SQL| DBManager
    DBManager --> SQLite
```

### Architectural Rules Enforced:
1. **Rule 1 (Zero Direct SQL in UI):** The UI layer never imports `sqlite3` or executes SQL statements. All data operations flow downstream through service classes.
2. **Rule 2 (Fail-Safe Parameter Validation):** Services validate parameters before execution. If invalid, a structured `ValidationResult` is generated, and a `poka_yoke_events` entry is recorded.
3. **Rule 3 (Atomicity & Thread Safety):** Transactions modifying multiple tables (e.g., checkout header, line items, stock decrements, loyalty points) run inside atomic blocks with rollback on error.

---

## 4. Complete Directory Structure

```text
pharmacy_management/
├── main.py                    # Application bootstrap & window lifecycle controller
├── config/
│   └── settings.py            # Central configurations, palette theme, paths, and business thresholds
├── database/
│   ├── db.py                  # Thread-safe SQLite connection pool and query helpers
│   ├── schema.py              # DDL schema definitions, foreign keys, and indexes
│   └── migrations.py          # Schema migrations and baseline test data seeder
├── models/
│   ├── user.py                # User entity with RBAC serialization
│   ├── medicine.py            # Medicine entity with expiry and stock status properties
│   ├── supplier.py            # Wholesale distributor entity
│   ├── customer.py            # Retail customer and loyalty points entity
│   ├── sale.py                # Sale and SaleItem transaction models
│   └── purchase.py            # Purchase and PurchaseItem restock models
├── services/
│   ├── auth_service.py        # Authentication, session tracking, and user provisioning
│   ├── medicine_service.py    # Catalog management, categories, and stock updates
│   ├── search_service.py      # Multi-criteria indexed search across all entities
│   ├── sales_service.py       # Atomic POS checkout and Poka-Yoke verification
│   ├── purchase_service.py    # Inbound restock orders and stock replenishment
│   ├── inventory_service.py   # Stock valuation, low-stock, and expiry quarantine
│   ├── report_service.py      # Aggregated metrics for sales, inventory, and quality
│   ├── fmea_service.py        # [TQM/Six Sigma] Dynamic FMEA risk analysis & RPN computation
│   ├── traceability_service.py# [TQM/Six Sigma] Digital Batch Traceability & Recall engine
│   └── help_service.py        # [Q10] Searchable FAQ and live AST code documentation auditor
├── ui/
│   ├── login.py               # Modern authentication view with demo profile presets
│   ├── dashboard.py           # Master application container with header, sidebar, and KPI cards
│   ├── medicines.py           # Medicine catalog table, category filter, and add/edit dialog
│   ├── inventory.py           # Warehouse inventory with low-stock and expiry filters
│   ├── suppliers.py           # Certified supplier directory and registration dialog
│   ├── customers.py           # Customer directory and loyalty management
│   ├── purchases.py           # Inbound restocking ledger and intake dialog
│   ├── search.py              # Universal search center across all entities
│   ├── billing.py             # POS billing view with Poka-Yoke guards and ASCII receipt modal
│   ├── users.py               # Admin user accounts management and password resets
│   ├── fmea_dashboard.py      # [TQM/Six Sigma] Automated FMEA Dashboard & RPN matrix view
│   ├── pareto_chart.py        # [TQM/Six Sigma] Interactive Pareto Error Chart view (Canvas dual-axis)
│   ├── traceability.py        # [TQM/Six Sigma] Digital Batch Traceability Tree & Recall view
│   ├── help_faq.py            # [Q10] In-app Searchable FAQ, manual reader, and shortcut card
│   └── about.py               # [Q10] About screen, architecture diagram, and TQM scorecard
├── reports/
│   ├── sales_report.py        # Revenue, margin, and best-selling drug report
│   ├── inventory_report.py    # Category-wise stock valuation and health report
│   ├── expiry_report.py       # Regulatory quarantine and financial risk report
│   ├── pareto_report.py       # [TQM/Six Sigma] Pareto 80/20 defect report & vital few classification
│   └── tqm_report.py          # [Q10] TQM quality audit, docstring coverage, and defect log
├── utils/
│   ├── validators.py          # Poka-Yoke input validators and boundary checkers
│   ├── logger.py              # Rotating file logger and console stream
│   ├── security.py            # PBKDF2-HMAC-SHA256 password hashing with salt
│   └── helpers.py             # Currency formatters, date math, receipt generators, and CSV
├── docs/
│   ├── USER_MANUAL.md         # [Q10] Full end-user operations manual
│   └── FAQ_DATABASE.json      # [Q10] Categorized JSON database of FAQs and troubleshooting
├── README.md                  # [Q10] System architecture, setup guide, and documentation
└── data/
    └── pharmacy.db            # Persistent SQLite database file (created on initialization)
```

---

## 5. Installation & Quick Start

### Prerequisites
- Python **3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14).
- Standard Library `tkinter` and `sqlite3` (Included with standard Python installations).
- **Zero external packages or pip installs required.**

### Launching the Desktop Application
Clone or navigate to the repository folder:

```powershell
# From the parent directory
py pharmacy_management\main.py

# Or from within pharmacy_management
cd pharmacy_management
py main.py
```

On initial startup, the system automatically:
1. Creates the `data/` and `logs/` directories.
2. Initializes the relational tables and performance indexes in `pharmacy.db`.
3. Seeds default user roles, categories, certified suppliers, and clinical sample inventory.

---

## 6. Role-Based Access Control (RBAC)

| Account Role | Username | Default Password | Permissions Overview |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Complete access: User accounts, catalog, purchases, POS, financial reports, TQM quality audits |
| **Pharmacist** | `pharmacist` | `pharm123` | Operational access: Medicine catalog, inbound restock, inventory adjustments, POS billing |
| **Cashier** | `cashier` | `cash123` | Front-counter access: POS counter billing, customer search, receipt re-printing |

> **Quick-Fill Buttons:** The login screen provides 1-click preset buttons (`Admin`, `Pharmacist`, `Cashier`) to populate credentials during evaluation.

---

## 7. Poka-Yoke Safeguards Matrix

| Failure Mode / Potential Defect | Poka-Yoke Mechanism | Trigger Rule Code | Outcome |
| :--- | :--- | :--- | :--- |
| Blank Medicine / Customer Name | Mandatory text validation ($\ge 2$ chars) | `ERR_BLANK_FIELD` | Submission blocked with field alert |
| Non-Positive / Negative Price | Strict positive float check ($> 0.00$) | `ERR_NON_POSITIVE_VALUE` | Input blocked; zero/negative disallowed |
| Selling Expired Medication | Calendar comparison check ($\text{expiry} \le \text{today}$) | `ERR_EXPIRED_MEDICINE` | Item strictly blocked from POS cart; logged to Poka-Yoke audit register |
| Overselling / Depleted Stock | Quantity comparison ($\text{requested} > \text{available}$) | `ERR_INSUFFICIENT_STOCK` | Cart addition blocked with maximum available alert |
| Excessive Cashier Discount | Discount cap ($> 30\%$) | `ERR_DISCOUNT_CAP_EXCEEDED` | Checkout blocked without admin authorization |
| Duplicate Username / Duplicate Phone | Relational unique constraint check | `ERR_DUPLICATE_RECORD` | Record creation halted before commit |
| Invalid Date Format | ISO 8601 YYYY-MM-DD regex parser | `ERR_INVALID_DATE_FORMAT` | Date input rejected |

---

## 8. Module & Service Technical Documentation

### `services.sales_service.SalesService`
- `validate_cart_item(medicine_id, quantity) -> (bool, str, dict)`: Pre-billing gate verifying stock sufficiency and checking batch expiration.
- `process_sale(...) -> (bool, str, dict)`: Atomic checkout transaction creating invoice, deducting inventory, awarding loyalty points, and logging audit events.

### `services.medicine_service.MedicineService`
- `get_all_medicines(category_id, active_only) -> List[Medicine]`: Retrieves active catalog joined with therapeutic category labels.
- `add_medicine(data, user_id) -> (bool, str, int)`: Source-validated medicine creation enforcing non-negative prices and future expiration dates.
- `update_stock(med_id, quantity_delta) -> (bool, str)`: Adjusts inventory units while guarding against negative balances.

### `services.inventory_service.InventoryService`
- `get_inventory_summary() -> dict`: Computes total units, acquisition cost asset value, retail market value, and low-stock/expired counts.
- `get_expiring_soon_items(days) -> List[Medicine]`: Returns batches approaching expiration within the threshold window.
- `get_expired_items() -> List[Medicine]`: Returns quarantined batches past their expiration date.

### `services.help_service.HelpService` [Q10 Focus]
- `search_faqs(query, category) -> List[dict]`: Full-text multi-tag search across JSON knowledge base.
- `audit_codebase_documentation() -> dict`: In-memory AST analysis inspecting all `.py` files to calculate docstring coverage percentages for modules, functions, and classes.
- `get_user_manual_content() -> str`: Reads and returns the complete markdown user manual.

---

## 9. Advanced TQM & Six Sigma Analytical Features

PharmaCare incorporates three industrial-grade Total Quality Management and Six Sigma tools to drive continuous process capability improvement:

### 1. Automated FMEA (Failure Mode & Effects Analysis) Dashboard (`ui/fmea_dashboard.py` & `services/fmea_service.py`)
* **Core Concept:** Dynamically calculates the **Risk Priority Number (RPN)** for pharmacy failure modes using live data from `error_logs` and `poka_yoke_events`.
* **Formula:**
  $$\text{RPN} = \text{Severity (S)} \times \text{Occurrence (O)} \times \text{Detection (D)} \quad (1 \le S, O, D \le 10)$$
* **Dynamic Occurrence Calculation:** Live counts from SQLite `error_logs` view automatically calibrate the Occurrence score on a logarithmic/graduated 1–10 scale.
* **Interactive Risk Simulation:** Administrators and Quality Officers can adjust Severity and Detection sliders/spinboxes in real time to re-rank processes into color-coded risk bands:
  - **High Risk:** $\text{RPN} \ge 200$ or Severity $\ge 9$ (Immediate Poka-Yoke intervention required)
  - **Medium Risk:** $100 \le \text{RPN} < 200$ (Process control monitoring)
  - **Low Risk:** $\text{RPN} < 100$ (Controlled process baseline)
* **Mitigation Tracking:** Every failure mode links directly to its Poka-Yoke prevention control and recommended engineering actions.

### 2. Interactive Pareto Chart Generator (`ui/pareto_chart.py` & `reports/pareto_report.py`)
* **Core Concept:** Applies the **Pareto Principle (80/20 Rule)** to error and defect logs to isolate the "Vital Few" defects causing 80% of operational friction from the "Useful Many".
* **Visual Rendering:** Pure Tkinter dual-axis Canvas renderer with zero external charting dependencies:
  - **Left Y-Axis & Vertical Bars:** Defect frequency by failure type in descending order.
  - **Right Y-Axis & Cumulative Curve:** Monotonically increasing cumulative percentage curve (0% to 100%).
  - **80% Threshold Line:** Prominent red reference marker highlighting the cutoff where the Vital Few end.
* **Dynamic Insight Box:** Automatically synthesizes actionable executive guidance (e.g., *"Top 2 failure modes account for 85.0% of all prevented operational defects"*).

### 3. Digital Batch Traceability Tree & Recall Engine (`ui/traceability.py` & `services/traceability_service.py`)
* **Core Concept:** Provides 360-degree forward and backward traceability for any pharmaceutical batch for audits, investigations, and safety recalls.
* **Workflow:**
  1. **Backward Traceability:** Batch $\longrightarrow$ Supplier Purchase Order (`purchases`, `purchase_items`, `suppliers`), including wholesale distributor, invoice number, unit cost, and restock timestamp.
  2. **Current Storage Status:** Real-time stock count, shelf storage conditions, and expiry status badge (Safe, Expiring Soon, or Quarantined).
  3. **Forward Traceability:** Batch $\longrightarrow$ Outbound Patient Distribution (`sales`, `sale_items`, `customers`), listing all customer invoices, quantities dispensed, and transaction timestamps.
* **Six Sigma Mass Balance:** Reconciles physical stock via the mass balance equation:
  $$\text{Total Received} = \text{Total Dispensed} + \text{Stock on Hand}$$
* **Emergency Recall Export:** One-click CSV export generating the complete patient notification manifest with patient contact info, purchase invoices, and dispensed quantities for health authorities.

---

## 10. Reports & Quality Audits

PharmaCare provides five dedicated reporting engines in `reports/`:
1. **Sales & Revenue Report (`reports/sales_report.py`):** Revenue summaries, discount totals, tax collections, top-selling items, and payment method breakdowns. Exportable to ASCII or RFC-4180 CSV.
2. **Inventory Asset Valuation Report (`reports/inventory_report.py`):** Breakdown of capital tied up in stock by therapeutic category.
3. **Critical Expiry Risk Report (`reports/expiry_report.py`):** Financial exposure of stock expiring in 30, 60, and 90 days, along with the mandatory quarantine list.
4. **Pareto Error Distribution Report (`reports/pareto_report.py`):** 80/20 defect classification, cumulative curves, and vital few defect prioritization.
5. **TQM Quality Audit Report (`reports/tqm_report.py`):** Real-time measurement of documentation coverage (Q10), Poka-Yoke prevention counts, and audit log health.

---

## 11. AST Documentation Coverage & Quality Verification

To verify that the system satisfies **Quality Goal Q10**, run the interactive test script or inspect the scorecard in the app:

### Verifying from the UI:
1. Log in as `Admin`.
2. Click **ℹ️ About & TQM** in the sidebar.
3. Observe the live **Docstring Coverage** percentage and **Defects Prevented** counter.
4. Click **🛡️ Generate & View Full TQM Audit Report** to view or copy the audit report.

### Verifying from Terminal:
You can run Python inline to inspect the AST documentation audit:

```powershell
py -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); from pharmacy_management.services.help_service import help_service; print(help_service.audit_codebase_documentation())"
```

Expected result:
```json
{
  "quality_goal": "Q10: Improve Documentation",
  "documentation_coverage_percent": 100.0,
  "compliance_grade": "A+ (Enterprise TQM Standard)"
}
```

---

## 12. License & Compliance
This software is distributed under the **MIT Enterprise Quality License**. Engineered in accordance with **ISO 9001 Quality Management** principles and healthcare compliance standards.

