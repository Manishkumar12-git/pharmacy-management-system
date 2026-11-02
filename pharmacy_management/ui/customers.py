"""
================================================================================
Pharmacy Management System - Customer Registry & Loyalty View
================================================================================
Module: pharmacy_management.ui.customers
Quality Objective: Q10 - Improve Documentation & Customer Experience

Description:
    Provides management of retail pharmacy customers, patient profiles,
    loyalty points, and registration dialogues. Zero direct SQL in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any
from pharmacy_management.config import settings
from pharmacy_management.services.search_service import search_service
from pharmacy_management.utils.validators import validate_text, validate_phone, validate_email
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.user import User


class CustomersView(ttk.Frame):
    """View governing customer profiles, patient registries, and loyalty points."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes customer directory and loyalty management view."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self.load_customers()

    def _init_ui(self) -> None:
        # Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Customer & Patient Loyalty Directory",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        tk.Button(
            top_bar,
            text="➕ Register Customer",
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

        tk.Label(search_strip, text="Search Customer:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT, padx=(0, 5))
        self.ent_search = ttk.Entry(search_strip, width=32)
        self.ent_search.pack(side=tk.LEFT, padx=(0, 15))
        self.ent_search.bind("<KeyRelease>", lambda _: self.load_customers())

        # Table
        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        cols = ("id", "name", "phone", "email", "address", "points", "created")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Customer / Patient Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("address", text="Address")
        self.tree.heading("points", text="Loyalty Points")
        self.tree.heading("created", text="Registered On")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("phone", width=110)
        self.tree.column("email", width=160)
        self.tree.column("address", width=220)
        self.tree.column("points", width=100, anchor="center")
        self.tree.column("created", width=110, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def load_customers(self) -> None:
        """Loads and displays customer directory records into treeview."""
        for itm in self.tree.get_children():
            self.tree.delete(itm)

        q = self.ent_search.get().strip()
        customers = search_service.search_customers(q)

        for c in customers:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    c["id"],
                    c["name"],
                    c["phone"],
                    c.get("email") or "-",
                    c.get("address") or "-",
                    f"{c.get('loyalty_points', 0)} pts",
                    c.get("created_at")[:10] if c.get("created_at") else "-"
                )
            )

    def _open_add_dialog(self) -> None:
        CustomerDialog(self, title="Register New Customer", on_saved=self.load_customers)


class CustomerDialog(tk.Toplevel):
    """Modal dialog for creating customer profile."""

    def __init__(self, parent: tk.Widget, title: str, on_saved: Any):
        """Initializes customer registration dialog."""
        super().__init__(parent)
        self.title(title)
        self.geometry("420x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_saved = on_saved

        pad = tk.Frame(self, padx=25, pady=20, bg=settings.THEME["SURFACE"])
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text="Customer Registration", font=(settings.THEME["FONT_FAMILY"], 12, "bold"), fg=settings.THEME["PRIMARY"], bg=settings.THEME["SURFACE"]).pack(anchor="w", pady=(0, 15))

        grid = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        grid.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Full Name *", "ent_name"),
            ("Phone Number *", "ent_phone"),
            ("Email Address", "ent_email"),
            ("Address", "ent_addr"),
        ]

        self.entries = {}
        for idx, (label_txt, var_name) in enumerate(fields):
            tk.Label(grid, text=label_txt, font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=idx, column=0, sticky="w", pady=6)
            ent = ttk.Entry(grid, width=26)
            ent.grid(row=idx, column=1, sticky="w", pady=6, padx=(10, 0))
            self.entries[var_name] = ent

        btn_box = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        btn_box.pack(fill=tk.X, pady=(15, 0))

        tk.Button(
            btn_box,
            text="Save Customer",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            command=self._handle_save
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _handle_save(self) -> None:
        name = self.entries["ent_name"].get().strip()
        phone = self.entries["ent_phone"].get().strip()
        email = self.entries["ent_email"].get().strip()
        addr = self.entries["ent_addr"].get().strip()

        val_n = validate_text(name, "Customer Name", min_length=2)
        if not val_n:
            messagebox.showerror("Error", val_n.message)
            return

        val_p = validate_phone(phone)
        if not val_p:
            messagebox.showerror("Error", val_p.message)
            return

        if email:
            val_e = validate_email(email)
            if not val_e:
                messagebox.showerror("Error", val_e.message)
                return

        try:
            db_manager.execute_query(
                "INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
                (name, phone, email or None, addr or None)
            )
            messagebox.showinfo("Success", f"Customer '{name}' registered.")
            self.on_saved()
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to register customer (Phone may be duplicate): {str(exc)}")
