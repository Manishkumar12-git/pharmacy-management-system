"""
================================================================================
Pharmacy Management System - Automated Quality Assurance & Integration Test Suite
================================================================================
Quality Objective: Q10 - Improve Documentation & Defect Prevention

Description:
    End-to-end automated integration and quality validation suite.
    Verifies:
      1. Database initialization and migrations.
      2. Role-Based Access Control and authentication.
      3. Poka-Yoke Safeguard 1: Blocking blank medicine names.
      4. Poka-Yoke Safeguard 2: Blocking negative and non-positive prices.
      5. Poka-Yoke Safeguard 3: Blocking dispensing of expired medicines.
      6. Poka-Yoke Safeguard 4: Blocking dispensing of quantities exceeding inventory.
      7. Atomic checkout transaction and physical inventory decrement.
      8. Wholesale supplier purchase intake and physical inventory increment.
      9. In-app Searchable FAQ retrieval and User Manual loading (Q10).
     10. Live AST Documentation Health and Docstring Coverage analysis (Q10).
     11. TQM Quality Audit report generation (ASCII and CSV).
================================================================================
"""

import sys
from pathlib import Path

# Set up path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pharmacy_management.config import settings
from pharmacy_management.database.migrations import initialize_database
from pharmacy_management.database.db import db_manager
from pharmacy_management.services.auth_service import auth_service
from pharmacy_management.services.medicine_service import medicine_service
from pharmacy_management.services.sales_service import sales_service
from pharmacy_management.services.purchase_service import purchase_service
from pharmacy_management.services.inventory_service import inventory_service
from pharmacy_management.services.search_service import search_service
from pharmacy_management.services.help_service import help_service
from pharmacy_management.services.report_service import report_service
from pharmacy_management.reports.sales_report import SalesReportGenerator
from pharmacy_management.reports.inventory_report import InventoryReportGenerator
from pharmacy_management.reports.expiry_report import ExpiryReportGenerator
from pharmacy_management.reports.tqm_report import TQMReportGenerator
from pharmacy_management.services.fmea_service import fmea_service
from pharmacy_management.reports.pareto_report import ParetoReportGenerator
from pharmacy_management.services.traceability_service import TraceabilityService


def run_all_tests():
    print("=" * 70)
    print("PHARMACARE QUALITY PMS - AUTOMATED TQM QUALITY TEST SUITE")
    print(f"Goal: {settings.TQM_OBJECTIVE} | Version: {settings.APP_VERSION}")
    print("=" * 70)

    # 1. Database Initialization
    print("[TEST 1/11] Initializing database and running seed migrations...")
    initialize_database()
    print("  -> Database initialized successfully.")

    # 2. Authentication & RBAC
    print("\n[TEST 2/11] Testing Authentication Service & RBAC...")
    ok, admin_user, msg = auth_service.login("admin", "admin123")
    assert ok and admin_user.is_admin, f"Admin login failed: {msg}"
    print(f"  -> Admin login successful: {admin_user.full_name} ({admin_user.role})")

    ok_cashier, cashier_user, _ = auth_service.login("cashier", "cash123")
    assert ok_cashier and cashier_user.role == "Cashier", "Cashier login failed"
    print(f"  -> Cashier login successful: {cashier_user.full_name} ({cashier_user.role})")

    bad_ok, _, bad_msg = auth_service.login("admin", "wrongpassword")
    assert not bad_ok, "Security flaw: Wrong password allowed!"
    print(f"  -> Incorrect password rejected properly: {bad_msg}")

    # 3. Poka-Yoke 1: Blank Medicine Name Rejection
    print("\n[TEST 3/11] Testing Poka-Yoke 1: Blank medicine name rejection...")
    ok, msg, _ = medicine_service.add_medicine({
        "name": "   ",
        "batch_number": "BAT-TEST-01",
        "unit_price": 50.0,
        "cost_price": 30.0,
        "stock_quantity": 100,
        "expiry_date": "2027-12-31"
    })
    assert not ok, "Defect escaped: Blank medicine name was accepted!"
    print(f"  -> Poka-Yoke intercepted defect: {msg}")

    # 4. Poka-Yoke 2: Non-Positive / Negative Pricing Rejection
    print("\n[TEST 4/11] Testing Poka-Yoke 2: Negative pricing rejection...")
    ok, msg, _ = medicine_service.add_medicine({
        "name": "Defective Drug Pricing",
        "batch_number": "BAT-TEST-02",
        "unit_price": -25.0,
        "cost_price": 10.0,
        "stock_quantity": 50,
        "expiry_date": "2027-12-31"
    })
    assert not ok, "Defect escaped: Negative unit price was accepted!"
    print(f"  -> Poka-Yoke intercepted defect: {msg}")

    # 5. Poka-Yoke 3: Dispensing Expired Medication Strictly Blocked
    print("\n[TEST 5/11] Testing Poka-Yoke 3: Dispensing expired medication blocked...")
    meds = medicine_service.get_all_medicines()
    expired_items = [m for m in meds if m.is_expired]
    assert len(expired_items) > 0, "No expired item in test catalog"
    exp_med = expired_items[0]
    print(f"  -> Target item for test: '{exp_med.name}' (Expired on: {exp_med.expiry_date})")

    is_valid, err_msg, _ = sales_service.validate_cart_item(exp_med.id, 1)
    assert not is_valid, "CRITICAL SAFETY DEFECT: Expired drug was permitted into cart!"
    print(f"  -> Poka-Yoke intercepted defect: {err_msg}")

    # 6. Poka-Yoke 4: Overselling / Depleted Stock Blocked
    print("\n[TEST 6/11] Testing Poka-Yoke 4: Overselling stock blocked...")
    safe_meds = [m for m in meds if not m.is_expired and m.stock_quantity > 0]
    assert len(safe_meds) > 0, "No safe in-stock medicine found"
    active_med = safe_meds[0]
    excess_qty = active_med.stock_quantity + 500
    print(f"  -> Target item: '{active_med.name}' (Available stock: {active_med.stock_quantity}, Requesting: {excess_qty})")

    is_valid, err_msg, _ = sales_service.validate_cart_item(active_med.id, excess_qty)
    assert not is_valid, "Defect escaped: Overselling permitted!"
    print(f"  -> Poka-Yoke intercepted defect: {err_msg}")

    # 7. Atomic Sales Transaction & Physical Stock Decrement
    print("\n[TEST 7/11] Testing Atomic Sales Transaction & Inventory Decrement...")
    initial_stock = active_med.stock_quantity
    dispense_qty = 3
    ok, sale_msg, summary = sales_service.process_sale(
        cart_items=[{"medicine_id": active_med.id, "quantity": dispense_qty}],
        user_id=cashier_user.id,
        discount_percent=5.0,
        payment_method="Cash"
    )
    assert ok and summary is not None, f"Sale transaction failed: {sale_msg}"
    reloaded_med = medicine_service.get_medicine_by_id(active_med.id)
    expected_stock = initial_stock - dispense_qty
    assert reloaded_med.stock_quantity == expected_stock, f"Stock discrepancy! Expected {expected_stock}, got {reloaded_med.stock_quantity}"
    print(f"  -> Sale processed: Invoice #{summary['invoice_number']}")
    print(f"  -> Grand Total: Rs.{summary['grand_total']:.2f}")
    print(f"  -> Stock successfully decremented from {initial_stock} to {reloaded_med.stock_quantity} units.")

    # 8. Inbound Wholesale Purchase & Physical Stock Replenishment
    print("\n[TEST 8/11] Testing Inbound Wholesale Restocking & Stock Increment...")
    suppliers = purchase_service.get_all_suppliers()
    assert len(suppliers) > 0, "No suppliers in database"
    sup = suppliers[0]
    restock_qty = 25
    before_restock = reloaded_med.stock_quantity

    ok, po_msg, po_id = purchase_service.process_purchase(
        supplier_id=sup.id,
        user_id=admin_user.id,
        invoice_number="",
        items=[{
            "medicine_id": reloaded_med.id,
            "quantity": restock_qty,
            "cost_price": reloaded_med.cost_price,
            "batch_number": reloaded_med.batch_number,
            "expiry_date": reloaded_med.expiry_date
        }]
    )
    assert ok and po_id is not None, f"Purchase failed: {po_msg}"
    after_restock_med = medicine_service.get_medicine_by_id(reloaded_med.id)
    assert after_restock_med.stock_quantity == before_restock + restock_qty, "Stock increment failed"
    print(f"  -> Purchase order {po_msg} logged.")
    print(f"  -> Stock successfully incremented from {before_restock} to {after_restock_med.stock_quantity} units.")

    # 9. In-App Knowledge Base & User Manual [Q10]
    print("\n[TEST 9/11] Testing In-App Help & FAQ Knowledge Base (Q10)...")
    faqs = help_service.search_faqs(query="expired")
    assert len(faqs) > 0, "FAQ search for 'expired' returned no results"
    print(f"  -> FAQ Search found {len(faqs)} relevant articles on drug expiration safety.")
    manual_content = help_service.get_user_manual_content()
    assert len(manual_content) > 500, "User manual content is missing or too short"
    print(f"  -> User manual loaded successfully ({len(manual_content):,} characters).")

    # 10. AST Code Documentation Coverage Audit [Q10]
    print("\n[TEST 10/11] Testing AST Code Documentation Coverage Audit (Q10)...")
    doc_audit = help_service.audit_codebase_documentation()
    print(f"  -> Total Python Modules  : {doc_audit['total_modules']} (Documented: {doc_audit['documented_modules']})")
    print(f"  -> Total Classes Defined : {doc_audit['total_classes']} (Documented: {doc_audit['documented_classes']})")
    print(f"  -> Total Functions       : {doc_audit['total_functions']} (Documented: {doc_audit['documented_functions']})")
    print(f"  -> Total Code Symbols    : {doc_audit['total_symbols']} (Documented: {doc_audit['documented_symbols']})")
    print(f"  -> Coverage Percentage   : {doc_audit['documentation_coverage_percent']}%")
    print(f"  -> TQM Compliance Rating : {doc_audit['compliance_grade']}")
    assert doc_audit["documentation_coverage_percent"] >= 90.0, "Documentation coverage below 90% threshold!"

    # 11. Reports & TQM Quality Audit Verification
    print("\n[TEST 11/14] Testing Report Generation & TQM Audit Trail...")
    sales_rep = SalesReportGenerator.generate_text_report()
    assert "EXECUTIVE SALES & REVENUE REPORT" in sales_rep
    print("  -> Sales Report generated.")

    inv_rep = InventoryReportGenerator.generate_text_report()
    assert "INVENTORY ASSET VALUATION" in inv_rep
    print("  -> Inventory Report generated.")

    exp_rep = ExpiryReportGenerator.generate_text_report()
    assert "CRITICAL EXPIRY RISK" in exp_rep
    print("  -> Expiry Risk Report generated.")

    tqm_rep = TQMReportGenerator.generate_text_report()
    assert "TOTAL QUALITY MANAGEMENT" in tqm_rep
    print("  -> TQM Quality Audit Report generated.")

    # 12. TQM Feature 1: Automated FMEA Risk Analysis & Dynamic RPN
    print("\n[TEST 12/14] Testing Automated FMEA Risk Analysis & Dynamic RPN Calculation...")
    fmea_matrix = fmea_service.get_fmea_matrix()
    assert len(fmea_matrix) >= 8, f"Expected at least 8 failure modes, found {len(fmea_matrix)}"
    print(f"  -> Successfully generated FMEA matrix with {len(fmea_matrix)} failure modes.")

    for fm in fmea_matrix:
        s = fm["severity"]
        o = fm["occurrence"]
        d = fm["detection"]
        rpn = fm["rpn"]
        expected_rpn = s * o * d
        assert rpn == expected_rpn, f"RPN calculation error: {rpn} != {expected_rpn}"
        if rpn >= 200 or s >= 9:
            assert fm["risk_level"] == "HIGH"
        elif rpn >= 100:
            assert fm["risk_level"] == "MEDIUM"
        else:
            assert fm["risk_level"] == "LOW"

    # Test dynamic weight adjustment
    target_fm_id = fmea_matrix[0]["mode_id"]
    fmea_service.update_mode_parameters(target_fm_id, severity=10, detection=5)
    updated_matrix = {m["mode_id"]: m for m in fmea_service.get_fmea_matrix()}
    updated = updated_matrix[target_fm_id]
    assert updated["severity"] == 10 and updated["detection"] == 5
    assert updated["rpn"] == 10 * updated["occurrence"] * 5
    print(f"  -> Dynamic weight adjustment verified: Mode {target_fm_id} RPN updated to {updated['rpn']} ({updated['risk_level']}).")

    summary_stats = fmea_service.get_fmea_kpis()
    assert summary_stats["total_modes"] == len(fmea_matrix)
    print(f"  -> FMEA Summary: High={summary_stats['high_risk_count']}, Medium={summary_stats['medium_risk_count']}, Low={summary_stats['low_risk_count']}.")
    
    csv_fmea = fmea_service.export_fmea_csv()
    assert "RPN" in csv_fmea
    print("  -> FMEA CSV report export verified.")

    # 13. TQM Feature 2: Interactive Pareto Error Report & 80/20 Rule
    print("\n[TEST 13/14] Testing Pareto Error Report Engine & 80/20 Principle...")
    pareto_gen = ParetoReportGenerator()
    pareto_data = pareto_gen.get_pareto_data()
    assert "items" in pareto_data and "total_defects" in pareto_data
    print(f"  -> Pareto dataset generated: {pareto_data['total_defects']} logged error events across {len(pareto_data['items'])} categories.")

    # Verify descending ordering and cumulative calculations
    items = pareto_data["items"]
    if items:
        for i in range(len(items) - 1):
            assert items[i]["frequency"] >= items[i + 1]["frequency"], "Pareto items not sorted in descending frequency order!"
            assert items[i]["cumulative_pct"] <= items[i + 1]["cumulative_pct"], "Cumulative percent must be non-decreasing!"
        assert abs(items[-1]["cumulative_pct"] - 100.0) < 0.1, "Final cumulative percentage must equal 100%!"

    assert pareto_data["insight_text"], "Pareto analytical insight text must not be empty"
    print(f"  -> Pareto Insight: {pareto_data['insight_text'].splitlines()[0]}")

    pareto_text = pareto_gen.generate_text_report()
    assert "SIX SIGMA DEFECT & POKA-YOKE PARETO ANALYSIS" in pareto_text
    print("  -> Pareto text report verified.")

    pareto_csv = pareto_gen.generate_csv_report()
    assert "Cumulative %" in pareto_csv
    print("  -> Pareto CSV report verified.")

    # 14. TQM Feature 3: Digital Batch Traceability Tree & Recall Engine
    print("\n[TEST 14/14] Testing Digital Batch Traceability & Emergency Recall Tree...")
    trace_service = TraceabilityService()
    all_batches = trace_service.get_all_batches()
    assert len(all_batches) > 0, "No batches found in inventory for traceability testing!"
    sample_batch = all_batches[0]["batch_number"]
    print(f"  -> Tracing sample batch: '{sample_batch}' ({all_batches[0]['medicine_name']})")

    trace_result = trace_service.trace_batch(sample_batch)
    assert trace_result is not None, f"Trace failed for batch: {sample_batch}"
    assert "medicine" in trace_result
    assert "backward_trace" in trace_result
    assert "forward_trace" in trace_result
    assert "metrics" in trace_result

    metrics = trace_result["metrics"]
    assert metrics["batch_number"] == sample_batch
    assert metrics["total_received"] >= 0
    assert metrics["current_stock"] >= 0
    assert metrics["total_sold"] >= 0

    print(f"  -> Backward Trace: {len(trace_result['backward_trace'])} supplier restock records.")
    print(f"  -> Forward Trace: {len(trace_result['forward_trace'])} customer dispensing records.")
    print(f"  -> Mass Balance: Received {metrics['total_received']}, Sold {metrics['total_sold']}, Stock {metrics['current_stock']} (Balanced: {metrics['is_balanced']}).")

    recall_csv = trace_service.generate_recall_csv(trace_result)
    assert "Sale Invoice" in recall_csv
    print("  -> Emergency recall customer contact list CSV generated successfully.")
    assert metrics["batch_number"] == sample_batch
    assert metrics["total_received"] >= 0
    assert metrics["current_stock"] >= 0
    assert metrics["total_sold"] >= 0

    print(f"  -> Backward Trace: {len(trace_result['backward_trace'])} supplier restock records.")
    print(f"  -> Forward Trace: {len(trace_result['forward_trace'])} customer dispensing records.")
    print(f"  -> Mass Balance: Received {metrics['total_received']}, Sold {metrics['total_sold']}, Stock {metrics['current_stock']} (Balanced: {metrics['is_balanced']}).")

    recall_csv = trace_service.generate_recall_csv(trace_result)
    assert "Patient / Customer Name" in recall_csv
    print("  -> Emergency recall customer contact list CSV generated successfully.")

    print("\n" + "=" * 70)
    print("ALL 14 INTEGRATION & QUALITY VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("TQM Goals Q10, FMEA, Pareto 80/20, and Batch Traceability are Verified.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
