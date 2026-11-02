"""
================================================================================
Pharmacy Management System - Automated FMEA (Failure Mode & Effects Analysis) Service
================================================================================
Module: pharmacy_management.services.fmea_service
Quality Objective: Total Quality Management (TQM) & Six Sigma Risk Prioritization

Description:
    Computes Failure Mode and Effects Analysis (FMEA) metrics dynamically.
    Calculates the Risk Priority Number (RPN) using the standard formula:
        RPN = Severity (S) x Occurrence (O) x Detection (D)

    Occurrence (O) is dynamically derived from live database records in error_logs
    and poka_yoke_events, reflecting actual operational error frequencies.
================================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
from pharmacy_management.database.db import db_manager
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)

# Master Pharmacy Failure Modes Definition Catalog
FAILURE_MODES_CATALOG: List[Dict[str, Any]] = [
    {
        "mode_id": "FM-01",
        "name": "Dispensing Expired Medication",
        "process_step": "Counter Dispensing & POS Checkout",
        "category": "Patient Safety",
        "potential_effect": "Patient toxicity, lack of therapeutic efficacy, malpractice liability, regulatory sanction.",
        "potential_causes": "FIFO rotation oversight, expired stock left on retail shelf, human visual inspection error.",
        "error_codes": ["EXPIRED_MEDICINE_BILLING_BLOCKED", "EXPIRED_INITIAL_STOCK_BLOCKED", "ERR_EXPIRED_MEDICINE"],
        "base_severity": 10,
        "base_detection": 1,
        "poka_yoke_control": "Automated calendar date gate in SalesService blocks cart addition before checkout.",
        "recommended_action": "System automatic quarantine 15 days pre-expiry; daily visual bin audit."
    },
    {
        "mode_id": "FM-02",
        "name": "Overselling Stock / Phantom Inventory",
        "process_step": "POS Inventory Deductions",
        "category": "Inventory Integrity",
        "potential_effect": "Stockout of critical medications, delayed patient care, distorted inventory asset valuation.",
        "potential_causes": "Concurrent cashiers selling final units, untracked inventory shrinkage, damaged units.",
        "error_codes": ["OVERSTOCK_SALE_BLOCKED", "ERR_INSUFFICIENT_STOCK"],
        "base_severity": 6,
        "base_detection": 2,
        "poka_yoke_control": "Atomic database transaction with row-level stock boundary check.",
        "recommended_action": "Automated reorder notifications; cycle counts for top 20 moving medicines."
    },
    {
        "mode_id": "FM-03",
        "name": "Blank / Corrupted Medicine or Batch Name",
        "process_step": "Catalog & Inbound Stock Entry",
        "category": "Regulatory Compliance",
        "potential_effect": "Loss of batch traceability, FDA/CDSCO non-compliance, unlabeled medication error.",
        "potential_causes": "Keyboard entry haste, barcode scanner hardware glitch, supplier invoice omission.",
        "error_codes": ["BLANK_MEDICINE_NAME_BLOCKED", "BLANK_BATCH_BLOCKED", "ERR_BLANK_FIELD"],
        "base_severity": 8,
        "base_detection": 1,
        "poka_yoke_control": "Input validators strictly reject blank, whitespace-only, or abnormally short names.",
        "recommended_action": "Enforce barcode scanner entry; eliminate manual typing of batch codes."
    },
    {
        "mode_id": "FM-04",
        "name": "Negative or Inaccurate Unit Pricing",
        "process_step": "Drug Pricing Setup & Restock Intake",
        "category": "Financial Integrity",
        "potential_effect": "Direct financial revenue loss, erroneous tax calculations, audit failure.",
        "potential_causes": "Typographical decimal shift, negative quantity typo, currency unit confusion.",
        "error_codes": ["NEGATIVE_PRICE_BLOCKED", "NEGATIVE_COST_BLOCKED", "ERR_NON_POSITIVE_VALUE"],
        "base_severity": 7,
        "base_detection": 2,
        "poka_yoke_control": "Non-negative float validation gate and SQLite relational CHECK constraints.",
        "recommended_action": "Cost-vs-Selling margin sanity alert; automated price floor checks."
    },
    {
        "mode_id": "FM-05",
        "name": "Excessive / Unauthorized Cashier Discount",
        "process_step": "POS Final Checkout",
        "category": "Internal Governance",
        "potential_effect": "Erosion of gross profit margins, cashier embezzlement, accounting discrepancy.",
        "potential_causes": "Cashier policy breach, unauthorized customer negotiation, input typo.",
        "error_codes": ["DISCOUNT_CAP_EXCEEDED", "ERR_DISCOUNT_EXCEEDED"],
        "base_severity": 5,
        "base_detection": 2,
        "poka_yoke_control": "Hard 30% discount ceiling enforced in SalesService; requires Admin override.",
        "recommended_action": "Manager approval modal for discounts exceeding 15%; weekly discount audit."
    },
    {
        "mode_id": "FM-06",
        "name": "Inbound Supplier Stock Discrepancy",
        "process_step": "Supplier Purchase Order Receiving",
        "category": "Supply Chain Quality",
        "potential_effect": "Payment for unreceived stock, receiving unverified lots, inventory count drift.",
        "potential_causes": "Wholesale distributor picking error, missing packing slip, transit damage.",
        "error_codes": ["STOCK_ADJUSTMENT", "SUPPLIER_DISCREPANCY"],
        "base_severity": 6,
        "base_detection": 3,
        "poka_yoke_control": "Mandatory invoice matching and item verification in PurchaseService.",
        "recommended_action": "Dual-person intake signoff for scheduled narcotics and high-value orders."
    },
    {
        "mode_id": "FM-07",
        "name": "Cold-Chain Temperature Storage Breach",
        "process_step": "Warehouse & Refrigerator Storage",
        "category": "Clinical Stability",
        "potential_effect": "Loss of insulin/biologics potency, drug denaturing, patient treatment failure.",
        "potential_causes": "Power failure, refrigerator door left ajar, failure to check 2-8 C requirement.",
        "error_codes": ["STORAGE_CONDITION_BREACH", "REFRIGERATED_EXPOSURE"],
        "base_severity": 9,
        "base_detection": 5,
        "poka_yoke_control": "Storage condition attribute highlighted on medicine catalog and dashboard.",
        "recommended_action": "Install automated IoT temperature dataloggers with SMS alert thresholds."
    },
    {
        "mode_id": "FM-08",
        "name": "Unauthorized Access / Account Tampering",
        "process_step": "User Authentication & RBAC",
        "category": "Security & Auditability",
        "potential_effect": "Unauthorized inventory adjustment, falsified prescription dispense, data theft.",
        "potential_causes": "Shared cashier terminals, credential compromise, failure to sign out.",
        "error_codes": ["UNAUTHORIZED_USER_ACTION", "AUTH_FAILURE"],
        "base_severity": 8,
        "base_detection": 3,
        "poka_yoke_control": "PBKDF2-HMAC-SHA256 salted hashing and role permission matrix enforcement.",
        "recommended_action": "Auto-logout after 15 minutes idle time; mandatory credential rotation."
    }
]


class FMEAService:
    """Business service computing Failure Mode & Effects Analysis and dynamic RPN values."""

    def __init__(self):
        """Initializes FMEA service with custom weights cache."""
        self._custom_weights: Dict[str, Dict[str, int]] = {}

    def map_count_to_occurrence_score(self, event_count: int) -> int:
        """Dynamically maps live database error/incident counts to standard 1-10 Occurrence scale.

        Scale Calibration:
            0 events   -> O = 1 (Extremely remote / Zero defects)
            1-2 events  -> O = 2 (Very low frequency)
            3-5 events  -> O = 3 (Low frequency)
            6-10 events -> O = 4 (Moderately low)
            11-20 events-> O = 5 (Moderate frequency)
            21-35 events-> O = 6 (Moderately high)
            36-50 events-> O = 7 (High frequency)
            51-75 events-> O = 8 (Very high frequency)
            76-100 events->O = 9 (Repeated daily failures)
            >100 events -> O = 10 (Persistent, unmitigated failure)

        Args:
            event_count (int): Total incidents detected in logs.

        Returns:
            int: Occurrence rating (1 to 10).
        """
        if event_count <= 0:
            return 1
        elif event_count <= 2:
            return 2
        elif event_count <= 5:
            return 3
        elif event_count <= 10:
            return 4
        elif event_count <= 20:
            return 5
        elif event_count <= 35:
            return 6
        elif event_count <= 50:
            return 7
        elif event_count <= 75:
            return 8
        elif event_count <= 100:
            return 9
        else:
            return 10

    def get_live_error_counts(self) -> Dict[str, int]:
        """Queries error_logs and poka_yoke_events to get real-time frequency per rule/error code.

        Returns:
            Dict[str, int]: Mapping of error_code -> occurrence count.
        """
        counts: Dict[str, int] = {}
        try:
            # Query from error_logs view (with fallback to poka_yoke_events)
            sql = "SELECT error_code, COUNT(*) AS cnt FROM error_logs GROUP BY error_code"
            rows = db_manager.fetch_all(sql)
            for r in rows:
                code = r.get("error_code") or ""
                counts[code] = int(r.get("cnt", 0))
        except Exception as exc:
            logger.warning("Error querying error_logs, falling back to poka_yoke_events: %s", exc)
            try:
                sql2 = "SELECT rule_name, COUNT(*) AS cnt FROM poka_yoke_events GROUP BY rule_name"
                rows2 = db_manager.fetch_all(sql2)
                for r in rows2:
                    code = r.get("rule_name") or ""
                    counts[code] = int(r.get("cnt", 0))
            except Exception as exc2:
                logger.error("Failed to query live incident counts: %s", exc2)

        # Also incorporate stock adjustment entries from audit_logs
        try:
            adj_row = db_manager.fetch_one("SELECT COUNT(*) AS cnt FROM audit_logs WHERE action = 'STOCK_ADJUSTMENT'")
            if adj_row and adj_row.get("cnt"):
                counts["STOCK_ADJUSTMENT"] = int(adj_row["cnt"])
        except Exception as exc:
            logger.debug("Could not query audit_logs for adjustments: %s", exc)

        return counts

    def get_fmea_matrix(self) -> List[Dict[str, Any]]:
        """Calculates full FMEA matrix with live Occurrence counts and calculated RPN.

        Returns:
            List[Dict[str, Any]]: List of failure mode records with S, O, D, RPN, and Risk Level.
        """
        live_counts = self.get_live_error_counts()
        matrix: List[Dict[str, Any]] = []

        for mode in FAILURE_MODES_CATALOG:
            mid = mode["mode_id"]

            # Compute total live occurrences across associated error codes
            total_events = 0
            for code in mode["error_codes"]:
                total_events += live_counts.get(code, 0)

            # Compute dynamic Occurrence (O)
            occurrence_score = self.map_count_to_occurrence_score(total_events)

            # Retrieve user custom weights or fall back to baseline
            custom = self._custom_weights.get(mid, {})
            severity = custom.get("severity", mode["base_severity"])
            detection = custom.get("detection", mode["base_detection"])

            # Compute RPN = Severity x Occurrence x Detection
            rpn = severity * occurrence_score * detection

            # Risk Categorization
            if rpn >= 200 or severity >= 9:
                risk_level = "HIGH"
                risk_color = "#dc2626"      # Red
                risk_bg = "#fee2e2"
            elif rpn >= 100:
                risk_level = "MEDIUM"
                risk_color = "#d97706"    # Amber
                risk_bg = "#fef3c7"
            else:
                risk_level = "LOW"
                risk_color = "#16a34a"       # Green
                risk_bg = "#dcfce7"

            matrix.append({
                "mode_id": mid,
                "name": mode["name"],
                "process_step": mode["process_step"],
                "category": mode["category"],
                "potential_effect": mode["potential_effect"],
                "potential_causes": mode["potential_causes"],
                "severity": severity,
                "occurrence": occurrence_score,
                "detection": detection,
                "rpn": rpn,
                "risk_level": risk_level,
                "risk_color": risk_color,
                "risk_bg": risk_bg,
                "live_events": total_events,
                "poka_yoke_control": mode["poka_yoke_control"],
                "recommended_action": mode["recommended_action"],
            })

        # Sort matrix descending by RPN (highest risk first)
        matrix.sort(key=lambda x: x["rpn"], reverse=True)
        return matrix

    def update_mode_parameters(self, mode_id: str, severity: int, detection: int) -> bool:
        """Updates custom user-defined Severity and Detection scores for a failure mode.

        Args:
            mode_id (str): Failure mode identifier (e.g. 'FM-01').
            severity (int): Severity score (1-10).
            detection (int): Detection score (1-10).

        Returns:
            bool: True if updated successfully.
        """
        sev = max(1, min(10, int(severity)))
        det = max(1, min(10, int(detection)))

        self._custom_weights[mode_id] = {
            "severity": sev,
            "detection": det,
        }
        logger.info("Updated FMEA weights for %s: S=%d, D=%d", mode_id, sev, det)
        return True

    def reset_mode_parameters(self, mode_id: Optional[str] = None) -> None:
        """Resets custom weights to baseline defaults.

        Args:
            mode_id (Optional[str]): If provided, resets only that mode. Otherwise resets all.
        """
        if mode_id:
            self._custom_weights.pop(mode_id, None)
        else:
            self._custom_weights.clear()

    def get_fmea_kpis(self) -> Dict[str, Any]:
        """Calculates executive summary KPIs for the FMEA dashboard.

        Returns:
            Dict[str, Any]: Summary metrics (total modes, high/medium/low counts, avg RPN, max RPN).
        """
        matrix = self.get_fmea_matrix()
        total_modes = len(matrix)
        high_count = sum(1 for m in matrix if m["risk_level"] == "HIGH")
        med_count = sum(1 for m in matrix if m["risk_level"] == "MEDIUM")
        low_count = sum(1 for m in matrix if m["risk_level"] == "LOW")
        total_rpn = sum(m["rpn"] for m in matrix)
        avg_rpn = round(total_rpn / total_modes, 1) if total_modes > 0 else 0.0
        max_mode = matrix[0] if matrix else None

        return {
            "total_modes": total_modes,
            "high_risk_count": high_count,
            "medium_risk_count": med_count,
            "low_risk_count": low_count,
            "average_rpn": avg_rpn,
            "max_rpn": max_mode["rpn"] if max_mode else 0,
            "top_failure_mode": max_mode["name"] if max_mode else "None",
            "total_incidents_tracked": sum(m["live_events"] for m in matrix),
        }

    def export_fmea_csv(self) -> str:
        """Generates an RFC-4180 compliant CSV export of the live FMEA matrix.

        Returns:
            str: CSV text content.
        """
        from pharmacy_management.utils.helpers import generate_csv_string
        matrix = self.get_fmea_matrix()
        headers = [
            "Mode ID", "Failure Mode", "Process Step", "Category",
            "Severity (S)", "Occurrence (O)", "Detection (D)",
            "RPN", "Risk Level", "Live Incidents", "Poka-Yoke Controls", "Recommended Mitigation"
        ]
        rows = [
            [
                m["mode_id"], m["name"], m["process_step"], m["category"],
                m["severity"], m["occurrence"], m["detection"],
                m["rpn"], m["risk_level"], m["live_events"],
                m["poka_yoke_control"], m["recommended_action"]
            ]
            for m in matrix
        ]
        return generate_csv_string(headers, rows)


# Global singleton instance
fmea_service = FMEAService()

