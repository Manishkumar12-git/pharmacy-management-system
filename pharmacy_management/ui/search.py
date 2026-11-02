"""
================================================================================
Pharmacy Management System - Universal Search Screen
================================================================================
Module: pharmacy_management.ui.search
Quality Objective: Q10 - Improve Documentation & Rapid Data Retrieval

Description:
    Provides a consolidated global lookup center spanning pharmaceutical SKUs,
    past sales invoices, customer loyalty registers, and supplier distributors.
    Zero direct SQL in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pharmacy_management.config import settings
from pharmacy_management.services.search_service import search_service
from pharmacy_management.utils.helpers import format_currency, get_expiry_status


class SearchView(ttk.Frame):
    """Universal cross-entity search console."""

    def __init__(self, parent: tk.Widget):
        """Initializes universal search console and builds input controls."""
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self._execute_search()

    def _init_ui(self) -> None:
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Universal Cross-Entity Search Center",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        # Search Bar
        search_box = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=12)
        search_box.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            search_box,
            text="Keyword / Query:",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.ent_query = ttk.Entry(search_box, width=38, font=(settings.THEME["FONT_FAMILY"], 10))
        self.ent_query.pack(side=tk.LEFT, padx=(0, 10))
        self.ent_query.bind("<KeyRelease>", lambda _: self._execute_search())
        self.ent_query.focus_set()

        # Scope Selector
        self.combo_scope = ttk.Combobox(
            search_box,
            values=["Medicines Catalog", "Sales Invoices", "Customers Registry", "Suppliers Directory"],
            state="readonly",
            width=20
        )
        self.combo_scope.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_scope.current(0)
        self.combo_scope.bind("<<ComboboxSelected>>", lambda _: self._execute_search())

        # Results Notebook / Tab Container
        self.results_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Dynamic Treeview
        self.tree = ttk.Treeview(self.results_frame, show="headings")
        scroll = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _execute_search(self) -> None:
        q = self.ent_query.get().strip()
        scope = self.combo_scope.get()

        for itm in self.tree.get_children():
            self.tree.delete(itm)

        if scope == "Medicines Catalog":
            self._render_medicines(q)
        elif scope == "Sales Invoices":
            self._render_sales(q)
        elif scope == "Customers Registry":
            self._render_customers(q)
        elif scope == "Suppliers Directory":
            self._render_suppliers(q)

    def _render_medicines(self, q: str) -> None:
        self.tree["columns"] = ("name", "generic", "batch", "barcode", "stock", "price", "expiry", "status")
        self.tree.heading("name", text="Medicine")
        self.tree.heading("generic", text="Generic")
        self.tree.heading("batch", text="Batch #")
        self.tree.heading("barcode", text="Barcode")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("price", text="Price")
        self.tree.heading("expiry", text="Expiry")
        self.tree.heading("status", text="Safety")

        results = search_service.search_medicines(q)
        for m in results:
            stat, _, _ = get_expiry_status(m.expiry_date)
            self.tree.insert("", tk.END, values=(m.name, m.generic_name or "-", m.batch_number, m.barcode or "-", m.stock_quantity, format_currency(m.unit_price), m.expiry_date, stat))

    def _render_sales(self, q: str) -> None:
        self.tree["columns"] = ("inv", "customer", "phone", "date", "total", "method", "cashier")
        self.tree.heading("inv", text="Invoice #")
        self.tree.heading("customer", text="Customer")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("date", text="Date")
        self.tree.heading("total", text="Total")
        self.tree.heading("method", text="Payment")
        self.tree.heading("cashier", text="Cashier")

        results = search_service.search_sales(q)
        for s in results:
            self.tree.insert("", tk.END, values=(s["invoice_number"], s.get("customer_name") or "Walk-in", s.get("phone") or "-", s.get("sale_date", "")[:16], format_currency(s["grand_total"]), s["payment_method"], s.get("cashier_name") or "-"))

    def _render_customers(self, q: str) -> None:
        self.tree["columns"] = ("name", "phone", "email", "points", "address")
        self.tree.heading("name", text="Customer")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("points", text="Points")
        self.tree.heading("address", text="Address")

        results = search_service.search_customers(q)
        for c in results:
            self.tree.insert("", tk.END, values=(c["name"], c["phone"], c.get("email") or "-", c.get("loyalty_points", 0), c.get("address") or "-"))

    def _render_suppliers(self, q: str) -> None:
        self.tree["columns"] = ("name", "contact", "phone", "email", "gst")
        self.tree.heading("name", text="Supplier")
        self.tree.heading("contact", text="Contact")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("gst", text="GST")

        results = search_service.search_suppliers(q)
        for s in results:
            self.tree.insert("", tk.END, values=(s["name"], s.get("contact_person") or "-", s["phone"], s.get("email") or "-", s.get("gst_tax_id") or "-"))
