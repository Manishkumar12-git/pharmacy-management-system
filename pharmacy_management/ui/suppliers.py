"""
================================================================================
Pharmacy Management System - Supplier Management View
================================================================================
Module: pharmacy_management.ui.suppliers
Quality Objective: Q10 - Improve Documentation & Traceability

Description:
    Provides management of certified pharmaceutical wholesale distributors,
    their contact points, tax numbers, and communication directories.
    Zero SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any
from pharmacy_management.config import settings
from pharmacy_management.services.purchase_service import purchase_service
from pharmacy_management.services.search_service import search_service
from pharmacy_management.models.user import User


class SuppliersView(ttk.Frame):
    """View governing certified pharmaceutical wholesale suppliers."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes certified supplier directory view."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self.load_suppliers()

    def _init_ui(self) -> None:
        # Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Certified Wholesale Suppliers Directory",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        if self.user.role in (settings.ROLE_ADMIN, settings.ROLE_PHARMACIST):
            tk.Button(
                top_bar,
                text="➕ Register Supplier",
                font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
                bg=settings.THEME["PRIMARY"],
                fg=settings.THEME["TEXT_LIGHT"],
                relief=tk.FLAT,
                cursor="hand2",
                padx=12,
                pady=5,
                command=self._open_add_dialog
            ).pack(side=tk.RIGHT)

        # Search Strip
        search_strip = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        search_strip.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(search_strip, text="Search Supplier:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT, padx=(0, 5))
        self.ent_search = ttk.Entry(search_strip, width=32)
        self.ent_search.pack(side=tk.LEFT, padx=(0, 15))
        self.ent_search.bind("<KeyRelease>", lambda _: self.load_suppliers())

        # Table
        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        cols = ("id", "name", "contact", "phone", "email", "gst", "address")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Company / Distributor")
        self.tree.heading("contact", text="Contact Person")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("gst", text="GST / Tax ID")
        self.tree.heading("address", text="Logistics Address")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=220)
        self.tree.column("contact", width=140)
        self.tree.column("phone", width=110)
        self.tree.column("email", width=160)
        self.tree.column("gst", width=140)
        self.tree.column("address", width=220)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def load_suppliers(self) -> None:
        """Loads and updates suppliers list in treeview based on search query."""
        for itm in self.tree.get_children():
            self.tree.delete(itm)

        q = self.ent_search.get().strip()
        suppliers = search_service.search_suppliers(q)

        for s in suppliers:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    s["id"],
                    s["name"],
                    s.get("contact_person") or "-",
                    s["phone"],
                    s.get("email") or "-",
                    s.get("gst_tax_id") or "-",
                    s.get("address") or "-"
                )
            )

    def _open_add_dialog(self) -> None:
        SupplierDialog(self, on_saved=self.load_suppliers)


class SupplierDialog(tk.Toplevel):
    """Modal dialog for registering a new wholesale supplier."""

    def __init__(self, parent: tk.Widget, on_saved: Any):
        """Initializes supplier registration modal dialog."""
        super().__init__(parent)
        self.title("Register Pharmaceutical Supplier")
        self.geometry("450x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_saved = on_saved

        pad = tk.Frame(self, padx=25, pady=20, bg=settings.THEME["SURFACE"])
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text="Supplier Details", font=(settings.THEME["FONT_FAMILY"], 12, "bold"), fg=settings.THEME["PRIMARY"], bg=settings.THEME["SURFACE"]).pack(anchor="w", pady=(0, 15))

        grid = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        grid.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Company Name *", "ent_name"),
            ("Contact Person", "ent_contact"),
            ("Phone Number *", "ent_phone"),
            ("Email Address", "ent_email"),
            ("GST / Tax ID", "ent_gst"),
            ("Address", "ent_addr"),
        ]

        self.entries = {}
        for idx, (label_txt, var_name) in enumerate(fields):
            tk.Label(grid, text=label_txt, font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=idx, column=0, sticky="w", pady=4)
            ent = ttk.Entry(grid, width=28)
            ent.grid(row=idx, column=1, sticky="w", pady=4, padx=(10, 0))
            self.entries[var_name] = ent

        btn_box = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        btn_box.pack(fill=tk.X, pady=(15, 0))

        tk.Button(
            btn_box,
            text="Save Supplier",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            command=self._handle_save
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _handle_save(self) -> None:
        payload = {
            "name": self.entries["ent_name"].get(),
            "contact_person": self.entries["ent_contact"].get(),
            "phone": self.entries["ent_phone"].get(),
            "email": self.entries["ent_email"].get(),
            "gst_tax_id": self.entries["ent_gst"].get(),
            "address": self.entries["ent_addr"].get(),
        }

        ok, msg = purchase_service.add_supplier(payload)
        if ok:
            messagebox.showinfo("Success", msg)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
