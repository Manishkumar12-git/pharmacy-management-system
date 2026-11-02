"""
================================================================================
Pharmacy Management System - Pareto Analysis (80/20 Rule) Report Engine
================================================================================
Module: pharmacy_management.reports.pareto_report
Quality Objective: Total Quality Management (TQM) & Six Sigma Defect Prioritization

Description:
    Applies the Pareto Principle (80/20 rule) to operational pharmacy error logs
    and poka-yoke prevention events. Groups failure records by error code/type,
    ranks them by descending frequency, and calculates cumulative frequencies
    and cumulative percentages to isolate the "Vital Few" from the "Useful Many".
================================================================================
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pharmacy_management.database.db import db_manager
from pharmacy_management.utils.helpers import generate_csv_string
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)

# Human-readable labels for standard error codes
ERROR_CODE_LABELS: Dict[str, str] = {
    "EXPIRED_MEDICINE_BILLING_BLOCKED": "Dispensing Expired Medicine",
    "OVERSTOCK_SALE_BLOCKED": "Overselling / Stock Depleted",
    "NEGATIVE_PRICE_BLOCKED": "Negative / Invalid Selling Price",
    "BLANK_MEDICINE_NAME_BLOCKED": "Blank Medicine Name",
    "DISCOUNT_CAP_EXCEEDED": "Cashier Discount Ceiling Exceeded",
    "EXPIRED_INITIAL_STOCK_BLOCKED": "Inbound Expired Stock Rejection",
    "BLANK_BATCH_BLOCKED": "Missing / Blank Batch Number",
    "NEGATIVE_COST_BLOCKED": "Negative / Invalid Cost Price",
    "STOCK_ADJUSTMENT": "Inventory Physical Audit Discrepancy",
    "UNAUTHORIZED_USER_ACTION": "Unauthorized Role Permission Attempt",
    "ERR_EXPIRED_MEDICINE": "Dispensing Expired Medicine",
    "ERR_INSUFFICIENT_STOCK": "Overselling / Stock Depleted",
    "ERR_NON_POSITIVE_VALUE": "Negative / Invalid Selling Price",
    "ERR_BLANK_FIELD": "Blank Medicine Name",
}


class ParetoReportGenerator:
    """Generates Pareto defect distributions, cumulative curves, and Six Sigma insights."""

    @staticmethod
    def get_pareto_data(time_window_days: Optional[int] = None) -> Dict[str, Any]:
        """Calculates Pareto distribution metrics from error_logs and poka_yoke_events.

        Args:
            time_window_days (Optional[int]): Optional filter for past N days. None for all time.

        Returns:
            Dict[str, Any]: Pareto analysis packet containing ranked items, cumulative %, and summary insight.
        """
        params = []
        where_clause = ""
        if time_window_days and time_window_days > 0:
            cutoff = (datetime.now() - timedelta(days=time_window_days)).strftime("%Y-%m-%d %H:%M:%S")
            where_clause = "WHERE timestamp >= ?"
            params.append(cutoff)

        # 1. Fetch grouped counts from error_logs / poka_yoke_events
        counts_by_code: Dict[str, int] = {}
        try:
            sql = f"SELECT error_code, COUNT(*) AS cnt FROM error_logs {where_clause} GROUP BY error_code"
            rows = db_manager.fetch_all(sql, tuple(params))
            for r in rows:
                code = r.get("error_code") or "OTHER_ERROR"
                counts_by_code[code] = int(r.get("cnt", 0))
        except Exception as exc:
            logger.warning("Query on error_logs failed, querying poka_yoke_events directly: %s", exc)
            try:
                sql2 = f"SELECT rule_name, COUNT(*) AS cnt FROM poka_yoke_events {where_clause} GROUP BY rule_name"
                rows2 = db_manager.fetch_all(sql2, tuple(params))
                for r in rows2:
                    code = r.get("rule_name") or "OTHER_ERROR"
                    counts_by_code[code] = int(r.get("cnt", 0))
            except Exception as exc2:
                logger.error("Failed to query error events: %s", exc2)

        # 2. Check audit_logs for stock adjustment discrepancies
        try:
            adj_sql = "SELECT COUNT(*) AS cnt FROM audit_logs WHERE action = 'STOCK_ADJUSTMENT'"
            if time_window_days and time_window_days > 0:
                adj_sql += " AND timestamp >= ?"
                adj_row = db_manager.fetch_one(adj_sql, (cutoff,))
            else:
                adj_row = db_manager.fetch_one(adj_sql)

            if adj_row and adj_row.get("cnt") and int(adj_row["cnt"]) > 0:
                counts_by_code["STOCK_ADJUSTMENT"] = int(adj_row["cnt"])
        except Exception as exc:
            logger.debug("Could not query audit_logs for adjustments: %s", exc)

        # 3. Sort items descending by frequency
        sorted_pairs = sorted(counts_by_code.items(), key=lambda x: x[1], reverse=True)
        total_defects = sum(count for _, count in sorted_pairs)

        # If zero records, return empty baseline
        if total_defects == 0:
            return {
                "total_defects": 0,
                "categories_count": 0,
                "vital_few_count": 0,
                "items": [],
                "insight_text": "Zero defects or prevented errors recorded for the selected timeframe. Baseline is 100% defect-free.",
                "threshold_reached_rank": 0,
            }

        # 4. Compute individual percentages, cumulative frequencies, and cumulative percentages
        items: List[Dict[str, Any]] = []
        running_cumulative = 0
        vital_few_count = 0
        threshold_reached_rank = 0
        threshold_flag = False

        for rank, (code, count) in enumerate(sorted_pairs, start=1):
            running_cumulative += count
            individual_pct = round((count / total_defects) * 100.0, 1)
            cumulative_pct = round((running_cumulative / total_defects) * 100.0, 1)

            # Cap cumulative at 100.0% for precision
            if cumulative_pct > 100.0:
                cumulative_pct = 100.0

            # 80/20 Classification: Vital Few vs Useful Many
            if not threshold_flag:
                vital_few_count += 1
                classification = "Vital Few (<= 80%)"
                if cumulative_pct >= 79.5:
                    threshold_flag = True
                    threshold_reached_rank = rank
            else:
                classification = "Useful Many (> 80%)"

            friendly_label = ERROR_CODE_LABELS.get(code, code.replace("_", " ").title())

            items.append({
                "rank": rank,
                "error_code": code,
                "label": friendly_label,
                "frequency": count,
                "individual_pct": individual_pct,
                "cumulative_frequency": running_cumulative,
                "cumulative_pct": cumulative_pct,
                "classification": classification,
                "is_vital_few": (classification.startswith("Vital Few")),
            })

        # 5. Formulate dynamic Six Sigma analytical insight
        if vital_few_count > 0:
            vital_labels = [f"'{it['label']}'" for it in items[:vital_few_count]]
            vital_str = " and ".join(vital_labels[:2]) if len(vital_labels) <= 2 else f"{', '.join(vital_labels[:2])}, and {len(vital_labels) - 2} other(s)"
            vital_pct = items[vital_few_count - 1]["cumulative_pct"]
            insight = (
                f"PARETO PRINCIPLE (80/20 RULE) INSIGHT:\n"
                f"The top {vital_few_count} failure mode(s) ({vital_str}) account for {vital_pct}% "
                f"of all prevented operational defects across {total_defects} total logged incidents.\n"
                f"Six Sigma Recommendation: Prioritizing Poka-Yoke mistake-proofing controls on these "
                f"{vital_few_count} vital failure categories will resolve {vital_pct}% of systemic operational risks."
            )
        else:
            insight = "Defect distribution is uniformly dispersed. Continuous monitoring recommended."

        return {
            "total_defects": total_defects,
            "categories_count": len(items),
            "vital_few_count": vital_few_count,
            "items": items,
            "insight_text": insight,
            "threshold_reached_rank": threshold_reached_rank or vital_few_count,
        }

    @staticmethod
    def generate_csv(time_window_days: Optional[int] = None) -> str:
        """Exports Pareto tabular analysis to RFC-4180 CSV format."""
        data = ParetoReportGenerator.get_pareto_data(time_window_days)
        headers = [
            "Rank", "Error Code", "Category Label", "Frequency",
            "Individual Percent (%)", "Cumulative Frequency", "Cumulative Percent (%)", "Pareto Classification"
        ]
        rows = [
            [
                item["rank"], item["error_code"], item["label"], item["frequency"],
                item["individual_pct"], item["cumulative_frequency"], item["cumulative_pct"], item["classification"]
            ]
            for item in data["items"]
        ]
        return generate_csv_string(headers, rows)

    @staticmethod
    def generate_text_report(time_window_days: Optional[int] = None) -> str:
        """Generates an ASCII-formatted Pareto analysis report."""
        data = ParetoReportGenerator.get_pareto_data(time_window_days)
        divider = "=" * 76
        thin_divider = "-" * 76

        lines = [
            divider,
            f"{'SIX SIGMA PARETO DEFECT DISTRIBUTION REPORT (80/20 RULE)':^76}",
            f"{'Total Defects Analyzed: ' + str(data['total_defects']):^76}",
            divider,
            f"Generated On        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Time Window         : {str(time_window_days) + ' Days' if time_window_days else 'All Time Records'}",
            f"Total Defect Modes  : {data['categories_count']}",
            f"Vital Few Modes     : {data['vital_few_count']} categories constitute >=80% of total blocks",
            thin_divider,
            f"{'Rank':<6}{'Error Category':<30}{'Count':>8}{'Pct %':>8}{'Cumul':>10}{'Cumul %':>10}",
            thin_divider,
        ]

        for item in data["items"]:
            lines.append(
                f"{item['rank']:<6}{item['label'][:28]:<30}{item['frequency']:>8}"
                f"{item['individual_pct']:>8.1f}%{item['cumulative_frequency']:>10}"
                f"{item['cumulative_pct']:>9.1f}%"
            )

        lines.extend([
            thin_divider,
            data["insight_text"],
            divider,
        ])
        return "\n".join(lines)


# Global singleton instance
pareto_report = ParetoReportGenerator()

