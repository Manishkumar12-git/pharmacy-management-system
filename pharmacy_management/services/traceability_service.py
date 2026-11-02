"""
================================================================================
Pharmacy Management System - Digital Batch Traceability Service
================================================================================
Module: pharmacy_management.services.traceability_service
Quality Objective: Q10 - Six Sigma Traceability & Inbound/Outbound Auditing

Description:
    Provides end-to-end forward and backward traceability for any pharmaceutical
    batch. Links supplier purchase orders to current inventory storage, and
    tracks every dispensed unit through customer sales invoices for audits,
    Poka-Yoke verification, and regulatory recall notifications.
================================================================================
"""

import io
import csv
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from pharmacy_management.database.db import db_manager
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class TraceabilityService:
    """Service governing end-to-end supply chain batch traceability and recall analysis."""

    def get_all_batches(self) -> List[Dict[str, Any]]:
        """Retrieves a list of all distinct batches currently recorded in inventory.

        Returns:
            List[Dict[str, Any]]: List of dictionary records containing batch_number,
                medicine_id, medicine_name, stock_quantity, and expiry_date.
        """
        sql = """
            SELECT DISTINCT
                m.id AS medicine_id,
                m.batch_number,
                m.name AS medicine_name,
                m.generic_name,
                m.stock_quantity,
                m.expiry_date,
                m.manufacturer
            FROM medicines m
            WHERE m.batch_number IS NOT NULL AND TRIM(m.batch_number) != ''
            ORDER BY m.name ASC, m.expiry_date ASC
        """
        rows = db_manager.fetch_all(sql)
        return [dict(r) for r in rows]

    def search_batches(self, query: str) -> List[Dict[str, Any]]:
        """Searches batches matching a batch number or medicine name keyword.

        Args:
            query (str): Search string (partial batch number or medicine name).

        Returns:
            List[Dict[str, Any]]: Matching batch summary records.
        """
        clean_q = f"%{query.strip()}%"
        sql = """
            SELECT DISTINCT
                m.id AS medicine_id,
                m.batch_number,
                m.name AS medicine_name,
                m.generic_name,
                m.stock_quantity,
                m.expiry_date,
                m.manufacturer
            FROM medicines m
            WHERE m.batch_number LIKE ? OR m.name LIKE ? OR m.generic_name LIKE ?
            ORDER BY m.name ASC
        """
        rows = db_manager.fetch_all(sql, (clean_q, clean_q, clean_q))
        return [dict(r) for r in rows]

    def trace_batch(self, query: str) -> Optional[Dict[str, Any]]:
        """Executes a full 360-degree forward and backward traceability analysis on a batch.

        Workflow:
            1. Locates medicine record via exact batch number, partial batch number, or name.
            2. Backward Traceability: Queries supplier purchase history and inbound POs.
            3. Current Status: Evaluates real-time inventory level, storage condition, and expiry.
            4. Forward Traceability: Queries customer sales distribution invoices.
            5. Mass Balance Reconciliation: Received vs Dispensed vs Stock on Hand.

        Args:
            query (str): Batch number or medicine name to trace.

        Returns:
            Optional[Dict[str, Any]]: Complete traceability data package, or None if not found.
        """
        clean_query = query.strip()
        if not clean_query:
            return None

        # 1. Resolve Medicine Record
        med_sql = """
            SELECT 
                m.id AS medicine_id,
                m.name AS medicine_name,
                m.generic_name,
                c.name AS category_name,
                m.batch_number,
                m.barcode,
                m.manufacturer,
                m.unit,
                m.unit_price,
                m.cost_price,
                m.stock_quantity,
                m.reorder_level,
                m.expiry_date,
                m.storage_condition,
                m.prescription_required,
                m.status
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE UPPER(m.batch_number) = UPPER(?)
               OR UPPER(m.name) = UPPER(?)
               OR m.batch_number LIKE ?
               OR m.name LIKE ?
            ORDER BY 
                CASE WHEN UPPER(m.batch_number) = UPPER(?) THEN 1 ELSE 2 END,
                m.id DESC
            LIMIT 1
        """
        param_like = f"%{clean_query}%"
        med_row = db_manager.fetch_one(
            med_sql, 
            (clean_query, clean_query, param_like, param_like, clean_query)
        )

        if not med_row:
            logger.warning("Traceability query yielded no results for: %s", clean_query)
            return None

        med_dict = dict(med_row)
        medicine_id = med_dict["medicine_id"]
        batch_number = med_dict["batch_number"]

        # 2. Evaluate Expiry Status
        exp_date_str = med_dict.get("expiry_date", "")
        days_to_expiry = None
        expiry_status = "SAFE"
        expiry_color = "#2e7d32"  # Green

        if exp_date_str:
            try:
                exp_dt = datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                today = date.today()
                days_to_expiry = (exp_dt - today).days

                if days_to_expiry < 0:
                    expiry_status = f"EXPIRED ({abs(days_to_expiry)} days ago)"
                    expiry_color = "#d32f2f"  # Red
                elif days_to_expiry <= 60:
                    expiry_status = f"EXPIRING SOON ({days_to_expiry} days left)"
                    expiry_color = "#ed6c02"  # Amber
                else:
                    expiry_status = f"SAFE ({days_to_expiry} days shelf-life)"
                    expiry_color = "#2e7d32"  # Green
            except ValueError:
                expiry_status = "UNKNOWN"
                expiry_color = "#757575"

        med_dict["days_to_expiry"] = days_to_expiry
        med_dict["expiry_status"] = expiry_status
        med_dict["expiry_color"] = expiry_color

        # 3. Backward Traceability (Supplier Restocking & POs)
        # Search purchase_items by batch_number OR medicine_id
        purchases_sql = """
            SELECT 
                pi.id AS purchase_item_id,
                pi.purchase_id,
                pi.batch_number,
                pi.expiry_date,
                pi.quantity AS received_quantity,
                pi.cost_price,
                pi.total_price,
                p.invoice_number AS purchase_invoice_number,
                p.purchase_date,
                p.payment_status,
                p.notes AS purchase_notes,
                s.id AS supplier_id,
                s.name AS supplier_name,
                s.contact_person AS supplier_contact,
                s.phone AS supplier_phone,
                s.email AS supplier_email,
                s.address AS supplier_address,
                s.gst_tax_id AS supplier_gst,
                COALESCE(u.full_name, u.username, 'Admin') AS received_by_user
            FROM purchase_items pi
            JOIN purchases p ON pi.purchase_id = p.id
            JOIN suppliers s ON p.supplier_id = s.id
            LEFT JOIN users u ON p.user_id = u.id
            WHERE pi.medicine_id = ? OR (pi.batch_number = ? AND pi.batch_number != '')
            ORDER BY p.purchase_date DESC
        """
        p_rows = db_manager.fetch_all(purchases_sql, (medicine_id, batch_number))
        backward_trace = [dict(r) for r in p_rows]

        total_received = sum(item["received_quantity"] for item in backward_trace)
        
        # If no purchase items recorded (e.g. initial inventory seed), provide synthetic origin record
        if not backward_trace:
            backward_trace.append({
                "purchase_item_id": 0,
                "purchase_id": 0,
                "batch_number": batch_number,
                "expiry_date": exp_date_str,
                "received_quantity": med_dict["stock_quantity"],
                "cost_price": med_dict["cost_price"],
                "total_price": round(med_dict["stock_quantity"] * med_dict["cost_price"], 2),
                "purchase_invoice_number": "INIT-SEED-RESTOCK",
                "purchase_date": "Initial Inventory Setup",
                "payment_status": "System Seeded",
                "purchase_notes": "Initial inventory baseline",
                "supplier_id": 0,
                "supplier_name": med_dict.get("manufacturer") or "Direct Manufacturer",
                "supplier_contact": "Quality Control Department",
                "supplier_phone": "N/A",
                "supplier_email": "compliance@pharmacy.local",
                "supplier_address": "Factory Depot",
                "supplier_gst": "N/A",
                "received_by_user": "System Administrator",
            })
            total_received = med_dict["stock_quantity"]

        # 4. Forward Traceability (Customer Sales Distribution)
        sales_sql = """
            SELECT 
                si.id AS sale_item_id,
                si.quantity AS quantity_sold,
                si.unit_price,
                si.total_price,
                s.id AS sale_id,
                s.invoice_number AS sale_invoice_number,
                s.sale_date,
                s.payment_method,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(c.phone, 'N/A') AS customer_phone,
                COALESCE(c.email, 'N/A') AS customer_email,
                COALESCE(c.address, 'N/A') AS customer_address,
                COALESCE(u.full_name, u.username, 'Cashier') AS dispensed_by
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN users u ON s.user_id = u.id
            WHERE si.medicine_id = ?
            ORDER BY s.sale_date DESC
        """
        s_rows = db_manager.fetch_all(sales_sql, (medicine_id,))
        forward_trace = [dict(r) for r in s_rows]

        total_sold = sum(item["quantity_sold"] for item in forward_trace)
        
        # Calculate distinct customers affected
        unique_customers = set()
        for s in forward_trace:
            c_name = s.get("customer_name")
            c_phone = s.get("customer_phone")
            if c_name and c_name != "Walk-in Customer":
                unique_customers.add(f"{c_name} ({c_phone})")
            elif c_phone and c_phone != "N/A":
                unique_customers.add(c_phone)
            else:
                unique_customers.add(f"Invoice {s.get('sale_invoice_number')}")

        # 5. Mass Balance Reconciliation & Six Sigma Integrity
        current_stock = med_dict["stock_quantity"]
        expected_balance = total_received - total_sold
        mass_balance_delta = current_stock - expected_balance

        return {
            "medicine": med_dict,
            "backward_trace": backward_trace,
            "forward_trace": forward_trace,
            "metrics": {
                "batch_number": batch_number,
                "medicine_name": med_dict["name"],
                "total_received": total_received,
                "total_sold": total_sold,
                "current_stock": current_stock,
                "expected_stock": expected_balance,
                "mass_balance_delta": mass_balance_delta,
                "sales_count": len(forward_trace),
                "patients_affected_count": len(unique_customers),
                "is_balanced": abs(mass_balance_delta) == 0,
            }
        }

    def generate_recall_csv(self, trace_result: Dict[str, Any]) -> str:
        """Generates an emergency batch recall patient contact distribution list in CSV format.

        Args:
            trace_result (Dict[str, Any]): Full traceability dictionary from trace_batch().

        Returns:
            str: Formatted CSV string ready for download or distribution to health authorities.
        """
        if not trace_result or not trace_result.get("forward_trace"):
            return "Sale Invoice,Sale Date,Patient Name,Phone,Email,Address,Quantity Dispensed,Batch Number,Medicine Name\n"

        med = trace_result["medicine"]
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Sale Invoice",
            "Sale Date",
            "Patient / Customer Name",
            "Phone",
            "Email",
            "Address",
            "Quantity Dispensed",
            "Unit Price (Rs.)",
            "Line Total (Rs.)",
            "Dispensed By",
            "Batch Number",
            "Medicine Name",
            "Expiry Date"
        ])

        for item in trace_result["forward_trace"]:
            writer.writerow([
                item.get("sale_invoice_number"),
                item.get("sale_date"),
                item.get("customer_name"),
                item.get("customer_phone"),
                item.get("customer_email"),
                item.get("customer_address"),
                item.get("quantity_sold"),
                f"{item.get('unit_price', 0):.2f}",
                f"{item.get('total_price', 0):.2f}",
                item.get("dispensed_by"),
                med.get("batch_number"),
                med.get("name"),
                med.get("expiry_date")
            ])

        return output.getvalue()

