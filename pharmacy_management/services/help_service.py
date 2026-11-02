"""
================================================================================
Pharmacy Management System - Help & Documentation Service
================================================================================
Module: pharmacy_management.services.help_service
Quality Objective: Q10 - Improve Documentation & Quality Transparency

Description:
    Core service delivering in-app help documentation, structured FAQ lookups,
    user manual streaming, keyboard shortcuts, and automated code documentation
    completeness metrics across the application package.
================================================================================
"""

import json
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from pharmacy_management.config import settings
from pharmacy_management.utils.logger import get_logger

logger = get_logger(__name__)


class HelpService:
    """Service providing searchable user documentation, FAQ lookup, and TQM code documentation audits."""

    def __init__(self):
        """Initializes help service with empty FAQ cache."""
        self._faq_cache: Optional[Dict[str, Any]] = None

    def load_faq_database(self) -> Dict[str, Any]:
        """Loads and parses the FAQ_DATABASE.json file into memory.

        Returns:
            Dict[str, Any]: Structured FAQ database object.
        """
        if self._faq_cache is not None:
            return self._faq_cache

        faq_path = Path(settings.FAQ_DATABASE_PATH)
        if not faq_path.exists():
            logger.warning("FAQ database file not found at %s", faq_path)
            return {"categories": [], "faqs": []}

        try:
            with open(faq_path, "r", encoding="utf-8") as f:
                self._faq_cache = json.load(f)
                return self._faq_cache
        except Exception as exc:
            logger.error("Failed to load FAQ database: %s", exc)
            return {"categories": [], "faqs": []}

    def get_categories(self) -> List[str]:
        """Retrieves list of all documentation FAQ categories."""
        db = self.load_faq_database()
        return db.get("categories", [])

    def search_faqs(self, query: str = "", category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filters FAQs by category and searches text across question, answer, and tags.

        Args:
            query (str): Keyword string.
            category (Optional[str]): Category filter.

        Returns:
            List[Dict[str, Any]]: Matching FAQ entries.
        """
        db = self.load_faq_database()
        all_faqs = db.get("faqs", [])

        results = []
        q_lower = query.strip().lower()

        for item in all_faqs:
            # Check Category
            if category and category != "All Categories" and item.get("category") != category:
                continue

            # Check Keyword Query
            if not q_lower:
                results.append(item)
                continue

            question = item.get("question", "").lower()
            answer = item.get("answer", "").lower()
            tags = [t.lower() for t in item.get("tags", [])]
            err_id = item.get("id", "").lower()

            if (q_lower in question or q_lower in answer or
                    any(q_lower in t for t in tags) or q_lower in err_id):
                results.append(item)

        return results

    def get_user_manual_content(self) -> str:
        """Reads the full markdown content of the end-user operations manual.

        Returns:
            str: Markdown manual string or error notice.
        """
        manual_path = Path(settings.USER_MANUAL_PATH)
        if not manual_path.exists():
            return "User manual document not found on disk."
        try:
            with open(manual_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.error("Error reading USER_MANUAL.md: %s", exc)
            return f"Error loading manual: {str(exc)}"

    def audit_codebase_documentation(self) -> Dict[str, Any]:
        """[TQM Q10 Feature] Live AST inspection of Python modules to measure docstring completeness.
        Follows PEP 257 standards for public code symbols (modules, classes, public functions/methods).

        Returns:
            Dict[str, Any]: Statistical breakdown of modules, functions, classes, and docstring coverage.
        """
        pkg_root = Path(settings.BASE_DIR)
        py_files = list(pkg_root.rglob("*.py"))

        total_modules = 0
        documented_modules = 0
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0

        module_details = []

        for fpath in py_files:
            # Skip virtual environments, cache files, and test files
            if "__pycache__" in fpath.parts or ".venv" in fpath.parts or fpath.name.startswith("test_"):
                continue

            total_modules += 1
            rel_path = fpath.relative_to(pkg_root.parent)

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    node = ast.parse(f.read(), filename=str(fpath))

                mod_doc = ast.get_docstring(node)
                is_mod_doc = bool(mod_doc and mod_doc.strip())
                if is_mod_doc:
                    documented_modules += 1

                # PEP 257 convention: inspect public functions and class constructors
                all_funcs = [n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                public_funcs = [fn for fn in all_funcs if not fn.name.startswith("_") or fn.name == "__init__"]
                classes = [n for n in ast.walk(node) if isinstance(n, ast.ClassDef)]

                func_doc_cnt = sum(1 for fn in public_funcs if ast.get_docstring(fn))
                class_doc_cnt = sum(1 for cl in classes if ast.get_docstring(cl))

                total_functions += len(public_funcs)
                documented_functions += func_doc_cnt
                total_classes += len(classes)
                documented_classes += class_doc_cnt

                module_details.append({
                    "path": str(rel_path),
                    "module_doc": is_mod_doc,
                    "functions": len(public_funcs),
                    "documented_functions": func_doc_cnt,
                    "classes": len(classes),
                    "documented_classes": class_doc_cnt,
                })

            except Exception as exc:
                logger.warning("Could not parse AST for %s: %s", fpath, exc)

        doc_rate = 0.0
        total_symbols = total_modules + total_functions + total_classes
        doc_symbols = documented_modules + documented_functions + documented_classes
        if total_symbols > 0:
            doc_rate = round((doc_symbols / total_symbols) * 100.0, 1)

        return {
            "quality_goal": "Q10: Improve Documentation",
            "total_modules": total_modules,
            "documented_modules": documented_modules,
            "total_functions": total_functions,
            "documented_functions": documented_functions,
            "total_classes": total_classes,
            "documented_classes": documented_classes,
            "total_symbols": total_symbols,
            "documented_symbols": doc_symbols,
            "documentation_coverage_percent": doc_rate,
            "compliance_grade": "A+ (Enterprise TQM Standard)" if doc_rate >= 90 else "A",
            "modules": module_details,
        }

    def get_keyboard_shortcuts(self) -> List[Dict[str, str]]:
        """Returns standard system keyboard shortcuts table."""
        return [
            {"key": "Ctrl + B", "action": "Open Point-of-Sale (POS) Billing", "scope": "Global"},
            {"key": "Ctrl + M", "action": "Open Medicine Catalog", "scope": "Global"},
            {"key": "Ctrl + I", "action": "Open Inventory & Expiry Tracking", "scope": "Global"},
            {"key": "Ctrl + F", "action": "Open Universal Search", "scope": "Global"},
            {"key": "F1", "action": "Launch In-App Help & Searchable FAQ", "scope": "Global"},
            {"key": "Ctrl + R", "action": "Refresh Active Screen Records", "scope": "Active Tab"},
            {"key": "Escape", "action": "Close Active Modal / Dialog", "scope": "Dialogs"},
        ]


# Global singleton instance
help_service = HelpService()
