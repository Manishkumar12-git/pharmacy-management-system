"""
================================================================================
Pharmacy Management System - Main Dashboard & Navigation Shell
================================================================================
Module: pharmacy_management.ui.dashboard
Quality Objective: Q10 - Improve Documentation & User Experience

Description:
    Renders the master application shell with a top header bar, left navigation
    sidebar, role-based screen routing, and the central dashboard KPI view.
    Zero SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from pharmacy_management.config import settings
from pharmacy_management.services.auth_service import auth_service
from pharmacy_management.services.inventory_service import inventory_service
from pharmacy_management.services.report_service import report_service
from pharmacy_management.services.sales_service import sales_service
from pharmacy_management.models.user import User
from pharmacy_management.utils.helpers import format_currency, get_expiry_status


class DashboardShell(ttk.Frame):
    """Main application container housing the navigation sidebar, header, and screen router."""

    def __init__(self, parent: tk.Widget, user: User, on_logout: Callable[[], None]):
        """Initializes dashboard shell.

        Args:
            parent (tk.Widget): Root window.
            user (User): Authenticated user.
            on_logout (Callable[[], None]): Logout handler.
        """
        super().__init__(parent)
        self.user = user
        self.on_logout = on_logout
        self.pack(fill=tk.BOTH, expand=True)

        self._active_tab_btn = None
        self._current_view = None

        self._init_layout()
        self.show_dashboard_home()

    def _init_layout(self) -> None:
        """Constructs top header, left sidebar, and content area."""
        # 1. Header Bar
        self.header = tk.Frame(self, bg=settings.THEME["PRIMARY"], height=52)
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.header.pack_propagate(False)

        # Title on Left
        title_box = tk.Frame(self.header, bg=settings.THEME["PRIMARY"])
        title_box.pack(side=tk.LEFT, padx=15, pady=8)

        lbl_app = tk.Label(
            title_box,
            text=f"⚕ {settings.APP_NAME}",
            font=(settings.THEME["FONT_FAMILY"], 12, "bold"),
            fg=settings.THEME["TEXT_LIGHT"],
            bg=settings.THEME["PRIMARY"]
        )
        lbl_app.pack(side=tk.LEFT)

        lbl_sub = tk.Label(
            title_box,
            text=f" | {settings.TQM_OBJECTIVE}",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["PRIMARY_LIGHT"],
            bg=settings.THEME["PRIMARY"]
        )
        lbl_sub.pack(side=tk.LEFT, padx=5)

        # User Info & Logout on Right
        user_box = tk.Frame(self.header, bg=settings.THEME["PRIMARY"])
        user_box.pack(side=tk.RIGHT, padx=15, pady=8)

        lbl_user = tk.Label(
            user_box,
            text=f"👤 {self.user.full_name} ({self.user.role})",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            fg=settings.THEME["TEXT_LIGHT"],
            bg=settings.THEME["PRIMARY"]
        )
        lbl_user.pack(side=tk.LEFT, padx=10)

        btn_help = tk.Button(
            user_box,
            text="❓ Help (F1)",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            bg=settings.THEME["PRIMARY_HOVER"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.show_help
        )
        btn_help.pack(side=tk.LEFT, padx=5)

        btn_logout = tk.Button(
            user_box,
            text="🚪 Sign Out",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            bg="#b91c1c",
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._handle_logout
        )
        btn_logout.pack(side=tk.LEFT, padx=5)

        # 2. Main Work Area (Sidebar + Dynamic Content)
        self.work_area = tk.Frame(self, bg=settings.THEME["BACKGROUND"])
        self.work_area.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Sidebar Frame
        self.sidebar = tk.Frame(
            self.work_area,
            bg=settings.THEME["SURFACE"],
            width=210,
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Content View Frame
        self.content_container = tk.Frame(self.work_area, bg=settings.THEME["BACKGROUND"])
        self.content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Build Sidebar Navigation Items
        self._build_sidebar_menu()

    def _build_sidebar_menu(self) -> None:
        """Constructs navigation menu links with role-based visibility."""
        lbl_nav = tk.Label(
            self.sidebar,
            text="NAVIGATION",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"],
            padx=15,
            pady=10
        )
        lbl_nav.pack(anchor="w")

        self.nav_buttons = {}

        items = [
            ("dashboard", "📊 Dashboard", self.show_dashboard_home),
            ("billing", "🛒 Billing / POS", self.show_billing),
            ("medicines", "💊 Medicines Catalog", self.show_medicines),
            ("inventory", "📦 Inventory & Expiry", self.show_inventory),
            ("purchases", "🚚 Purchases / Restock", self.show_purchases),
            ("suppliers", "🏢 Suppliers", self.show_suppliers),
            ("customers", "👥 Customers", self.show_customers),
            ("search", "🔍 Universal Search", self.show_search),
            ("traceability", "🧬 Batch Traceability", self.show_traceability),
            ("fmea", "🛡️ FMEA Risk Matrix", self.show_fmea),
            ("pareto", "📊 Pareto Error Chart", self.show_pareto),
            ("reports", "📈 Reports & Audits", self.show_reports),
        ]

        if self.user.is_admin:
            items.append(("users", "👤 User Accounts", self.show_users))

        # Bottom Q10 Items
        items.extend([
            ("help", "❓ Help & FAQ (Q10)", self.show_help),
            ("about", "ℹ️ About & TQM", self.show_about),
        ])

        for key, text, cmd in items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=(settings.THEME["FONT_FAMILY"], 9),
                fg=settings.THEME["TEXT_MAIN"],
                bg=settings.THEME["SURFACE"],
                activebackground=settings.THEME["PRIMARY_LIGHT"],
                activeforeground=settings.THEME["PRIMARY"],
                anchor="w",
                relief=tk.FLAT,
                cursor="hand2",
                padx=16,
                pady=7,
                command=lambda k=key, c=cmd: self._select_nav_item(k, c)
            )
            btn.pack(fill=tk.X)
            self.nav_buttons[key] = btn

    def _select_nav_item(self, key: str, cmd: Callable[[], None]) -> None:
        """Highlights active navigation button and switches screen."""
        for k, b in self.nav_buttons.items():
            if k == key:
                b.configure(
                    bg=settings.THEME["PRIMARY_LIGHT"],
                    fg=settings.THEME["PRIMARY"],
                    font=(settings.THEME["FONT_FAMILY"], 9, "bold")
                )
            else:
                b.configure(
                    bg=settings.THEME["SURFACE"],
                    fg=settings.THEME["TEXT_MAIN"],
                    font=(settings.THEME["FONT_FAMILY"], 9)
                )
        cmd()

    def set_content_view(self, view_class, *args, **kwargs) -> tk.Widget:
        """Destroys previous content view and mounts the requested frame cleanly."""
        # 1. Unpack and destroy all existing children in content_container
        for child in list(self.content_container.winfo_children()):
            try:
                child.pack_forget()
                child.destroy()
            except Exception:
                pass
        self._current_view = None

        # 2. Flush pending UI geometry events to prevent ghost/lingering frames
        try:
            self.content_container.update_idletasks()
        except Exception:
            pass

        # 3. Mount and pack requested view frame
        self._current_view = view_class(self.content_container, *args, **kwargs)
        self._current_view.pack(fill=tk.BOTH, expand=True)
        return self._current_view

    # Navigation Handlers
    def show_dashboard_home(self) -> None:
        """Mounts the executive KPI dashboard home view."""
        self.set_content_view(DashboardHomeView, shell=self)

    def show_billing(self) -> None:
        """Mounts the POS counter retail checkout billing view."""
        from pharmacy_management.ui.billing import BillingView
        self.set_content_view(BillingView, user=self.user)

    def show_medicines(self) -> None:
        """Mounts the pharmaceutical medicine catalog view."""
        from pharmacy_management.ui.medicines import MedicinesView
        self.set_content_view(MedicinesView, user=self.user)

    def show_inventory(self) -> None:
        """Mounts the warehouse inventory and expiry tracking view."""
        from pharmacy_management.ui.inventory import InventoryView
        self.set_content_view(InventoryView, user=self.user)

    def show_purchases(self) -> None:
        """Mounts the supplier purchases and restock view."""
        from pharmacy_management.ui.purchases import PurchasesView
        self.set_content_view(PurchasesView, user=self.user)

    def show_suppliers(self) -> None:
        """Mounts the certified supplier directory view."""
        from pharmacy_management.ui.suppliers import SuppliersView
        self.set_content_view(SuppliersView, user=self.user)

    def show_customers(self) -> None:
        """Mounts the customer directory and loyalty view."""
        from pharmacy_management.ui.customers import CustomersView
        self.set_content_view(CustomersView, user=self.user)

    def show_search(self) -> None:
        """Mounts the universal multi-criteria search center."""
        from pharmacy_management.ui.search import SearchView
        self.set_content_view(SearchView)

    def show_traceability(self) -> None:
        """Mounts the digital batch traceability and recall lineage view."""
        from pharmacy_management.ui.traceability import BatchTraceabilityView
        self.set_content_view(BatchTraceabilityView, user=self.user)

    def show_fmea(self) -> None:
        """Mounts the automated Failure Mode and Effects Analysis (FMEA) dashboard."""
        from pharmacy_management.ui.fmea_dashboard import FMEADashboardView
        self.set_content_view(FMEADashboardView, user=self.user)

    def show_pareto(self) -> None:
        """Mounts the interactive Six Sigma Pareto error chart view."""
        from pharmacy_management.ui.pareto_chart import ParetoChartView
        self.set_content_view(ParetoChartView, user=self.user)

    def show_reports(self) -> None:
        """Mounts the management reporting and quality audit view."""
        from pharmacy_management.reports.sales_report import SalesReportGenerator
        from pharmacy_management.reports.inventory_report import InventoryReportGenerator
        from pharmacy_management.reports.expiry_report import ExpiryReportGenerator
        from pharmacy_management.reports.tqm_report import TQMReportGenerator

        # Render Reports View dialog or panel
        from pharmacy_management.ui.about import AboutView
        self.set_content_view(AboutView, user=self.user)

    def show_users(self) -> None:
        """Mounts the admin user accounts management view."""
        from pharmacy_management.ui.users import UsersView
        self.set_content_view(UsersView, user=self.user)

    def show_help(self) -> None:
        """Mounts the in-app searchable FAQ and documentation view."""
        from pharmacy_management.ui.help_faq import HelpFaqView
        self.set_content_view(HelpFaqView)

    def show_about(self) -> None:
        """Mounts the about screen and TQM quality scorecard view."""
        from pharmacy_management.ui.about import AboutView
        self.set_content_view(AboutView, user=self.user)

    def _handle_logout(self) -> None:
        if messagebox.askyesno("Confirm Sign Out", "Are you sure you want to log out of PharmaCare?"):
            auth_service.logout()
            self.on_logout()


class DashboardHomeView(ttk.Frame):
    """Home view inside dashboard showing KPI cards and recent activities."""

    def __init__(self, parent: tk.Widget, shell: DashboardShell):
        """Initializes dashboard home view with KPI cards and activity tables."""
        super().__init__(parent)
        self.shell = shell
        self.pack(fill=tk.BOTH, expand=True)

        self._init_view()

    def _init_view(self) -> None:
        # Title Header
        header_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=15)
        header_bar.pack(fill=tk.X)

        tk.Label(
            header_bar,
            text="Executive Performance Dashboard",
            font=(settings.THEME["FONT_FAMILY"], 16, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        today_str = datetime.now().strftime("%A, %d %B %Y")
        tk.Label(
            header_bar,
            text=f"📅 {today_str}",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.RIGHT)

        # 4 KPI Cards Container
        cards_frame = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=5)
        cards_frame.pack(fill=tk.X)

        # Fetch Data via downstream Services
        inv_summary = inventory_service.get_inventory_summary()
        today_date = datetime.now().strftime("%Y-%m-%d")
        sales_today = report_service.get_sales_analytics(start_date=today_date, end_date=today_date)

        self._create_kpi_card(
            cards_frame,
            title="TODAY'S SALES",
            value=format_currency(sales_today["total_revenue"]),
            subtitle=f"{sales_today['total_invoices']} transactions today",
            color=settings.THEME["PRIMARY"],
            col=0
        )

        self._create_kpi_card(
            cards_frame,
            title="TOTAL ACTIVE SKUs",
            value=str(inv_summary["total_medicines"]),
            subtitle=f"{inv_summary['total_units']} total units in stock",
            color=settings.THEME["SECONDARY"],
            col=1
        )

        self._create_kpi_card(
            cards_frame,
            title="LOW STOCK ALERTS",
            value=str(inv_summary["low_stock_count"]),
            subtitle="Batches below reorder point",
            color=settings.THEME["WARNING"],
            col=2
        )

        self._create_kpi_card(
            cards_frame,
            title="EXPIRING SOON",
            value=str(inv_summary["expiring_soon_count"]),
            subtitle=f"Within {settings.EXPIRY_WARNING_DAYS} days (Quarantined: {inv_summary['expired_count']})",
            color=settings.THEME["DANGER"],
            col=3
        )

        # Quick Actions Bar
        actions_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=10)
        actions_bar.pack(fill=tk.X)

        tk.Button(
            actions_bar,
            text="➕ New POS Sale",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_billing
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            actions_bar,
            text="💊 Add Medicine",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_medicines
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            actions_bar,
            text="⚠️ Inspect Expiries",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_inventory
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            actions_bar,
            text="🛡️ FMEA Risk Matrix",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_fmea
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            actions_bar,
            text="📊 Pareto Chart",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_pareto
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            actions_bar,
            text="🧬 Batch Traceability",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_traceability
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            actions_bar,
            text="ℹ️ Quality Audit & TQM",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.shell.show_about
        ).pack(side=tk.LEFT)

        # Bottom Split Area: Recent Sales & Stock Alerts
        bottom_area = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=10)
        bottom_area.pack(fill=tk.BOTH, expand=True)

        # Left Column: Recent Sales
        left_col = tk.Frame(
            bottom_area,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=12,
            pady=10
        )
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            left_col,
            text="Recent Sales Transactions",
            font=(settings.THEME["FONT_FAMILY"], 11, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 8))

        sales_tree = ttk.Treeview(
            left_col,
            columns=("invoice", "customer", "amount", "method", "time"),
            show="headings",
            height=8
        )
        sales_tree.heading("invoice", text="Invoice #")
        sales_tree.heading("customer", text="Customer")
        sales_tree.heading("amount", text="Total")
        sales_tree.heading("method", text="Payment")
        sales_tree.heading("time", text="Time")

        sales_tree.column("invoice", width=120)
        sales_tree.column("customer", width=110)
        sales_tree.column("amount", width=80, anchor="e")
        sales_tree.column("method", width=70, anchor="center")
        sales_tree.column("time", width=100)
        sales_tree.pack(fill=tk.BOTH, expand=True)

        recent_sales = sales_service.get_recent_sales(limit=10)
        for s in recent_sales:
            sales_tree.insert(
                "",
                tk.END,
                values=(
                    s["invoice_number"],
                    s.get("customer_name") or "Walk-in",
                    format_currency(s["grand_total"]),
                    s["payment_method"],
                    s["sale_date"][:16] if s.get("sale_date") else ""
                )
            )

        # Right Column: Expiry & Low Stock Attention
        right_col = tk.Frame(
            bottom_area,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=12,
            pady=10
        )
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_col,
            text="Quality Attention Items (Stock & Expiry)",
            font=(settings.THEME["FONT_FAMILY"], 11, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 8))

        alert_tree = ttk.Treeview(
            right_col,
            columns=("name", "stock", "expiry", "status"),
            show="headings",
            height=8
        )
        alert_tree.heading("name", text="Medicine")
        alert_tree.heading("stock", text="Stock")
        alert_tree.heading("expiry", text="Expiry")
        alert_tree.heading("status", text="Alert Status")

        alert_tree.column("name", width=130)
        alert_tree.column("stock", width=60, anchor="center")
        alert_tree.column("expiry", width=85, anchor="center")
        alert_tree.column("status", width=95, anchor="center")
        alert_tree.pack(fill=tk.BOTH, expand=True)

        # Populate with low-stock or near-expiry
        low_items = inventory_service.get_low_stock_items()[:6]
        for item in low_items:
            status_lbl, _, _ = get_expiry_status(item.expiry_date)
            alert_tree.insert(
                "",
                tk.END,
                values=(
                    item.name,
                    f"{item.stock_quantity} units",
                    item.expiry_date,
                    f"Low Stock ({item.stock_quantity})" if not item.is_expired else "EXPIRED"
                )
            )

    def _create_kpi_card(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
        subtitle: str,
        color: str,
        col: int
    ) -> None:
        """Helper generating stylized metric summary card."""
        card = tk.Frame(
            parent,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=15,
            pady=12
        )
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        tk.Label(
            card,
            text=title,
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            fg=color,
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w")

        tk.Label(
            card,
            text=value,
            font=(settings.THEME["FONT_FAMILY"], 16, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            card,
            text=subtitle,
            font=(settings.THEME["FONT_FAMILY"], 8),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(2, 0))
