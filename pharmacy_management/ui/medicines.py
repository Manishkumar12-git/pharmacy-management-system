"""
================================================================================
Pharmacy Management System - Medicine Catalog Management View
================================================================================
Module: pharmacy_management.ui.medicines
Quality Objective: Q10 - Improve Documentation & Poka-Yoke Error Prevention

Description:
    Provides inventory operators and pharmacists with full catalog management:
    searching, filtering by therapeutic category, adding new medicine batches
    with strict validation gates, editing pricing, and soft-discontinuing SKUs.
    Zero SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
from pharmacy_management.config import settings
from pharmacy_management.services.medicine_service import medicine_service
from pharmacy_management.models.user import User
from pharmacy_management.models.medicine import Medicine
from pharmacy_management.utils.helpers import format_currency, get_expiry_status


class MedicinesView(ttk.Frame):
    """View governing pharmaceutical product catalog, batches, and pricing."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes medicine catalog view and builds table controls."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self.load_medicines()

    def _init_ui(self) -> None:
        """Constructs search bar, filter dropdowns, action buttons, and treeview."""
        # Top Action Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=15)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Pharmaceutical Medicine Catalog",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        btn_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(side=tk.RIGHT)

        # Restrict Add/Edit actions if Cashier role
        if self.user.role in (settings.ROLE_ADMIN, settings.ROLE_PHARMACIST):
            tk.Button(
                btn_box,
                text="➕ Add Medicine",
                font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
                bg=settings.THEME["PRIMARY"],
                fg=settings.THEME["TEXT_LIGHT"],
                relief=tk.FLAT,
                cursor="hand2",
                padx=12,
                pady=5,
                command=self._open_add_dialog
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                btn_box,
                text="✏️ Edit Selected",
                font=(settings.THEME["FONT_FAMILY"], 9),
                bg=settings.THEME["SURFACE"],
                fg=settings.THEME["TEXT_MAIN"],
                relief=tk.SOLID,
                bd=1,
                cursor="hand2",
                padx=12,
                pady=5,
                command=self._open_edit_dialog
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                btn_box,
                text="🗑️ Discontinue",
                font=(settings.THEME["FONT_FAMILY"], 9),
                bg=settings.THEME["SURFACE"],
                fg=settings.THEME["DANGER"],
                relief=tk.SOLID,
                bd=1,
                cursor="hand2",
                padx=10,
                pady=5,
                command=self._handle_discontinue
            ).pack(side=tk.LEFT, padx=5)

        # Filter & Search Strip
        filter_strip = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        filter_strip.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            filter_strip,
            text="Search:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.ent_search = ttk.Entry(filter_strip, width=28)
        self.ent_search.pack(side=tk.LEFT, padx=(0, 15))
        self.ent_search.bind("<KeyRelease>", lambda _: self.load_medicines())

        tk.Label(
            filter_strip,
            text="Category:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.combo_cat = ttk.Combobox(filter_strip, state="readonly", width=22)
        self.combo_cat.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_cat.bind("<<ComboboxSelected>>", lambda _: self.load_medicines())

        # Populate categories
        categories = medicine_service.get_categories()
        self.cat_map = {"All Categories": None}
        cat_names = ["All Categories"]
        for c in categories:
            cat_names.append(c["name"])
            self.cat_map[c["name"]] = c["id"]
        self.combo_cat["values"] = cat_names
        self.combo_cat.current(0)

        tk.Button(
            filter_strip,
            text="🔄 Refresh",
            font=(settings.THEME["FONT_FAMILY"], 8),
            command=self.load_medicines
        ).pack(side=tk.LEFT)

        # Medicine Treeview Table
        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        cols = ("id", "name", "generic", "category", "batch", "stock", "price", "cost", "expiry", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Brand / Medicine Name")
        self.tree.heading("generic", text="Generic / Molecule")
        self.tree.heading("category", text="Category")
        self.tree.heading("batch", text="Batch #")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("price", text="Unit Price")
        self.tree.heading("cost", text="Cost Price")
        self.tree.heading("expiry", text="Expiry Date")
        self.tree.heading("status", text="Health Status")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("generic", width=150)
        self.tree.column("category", width=130)
        self.tree.column("batch", width=90, anchor="center")
        self.tree.column("stock", width=60, anchor="center")
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("cost", width=80, anchor="e")
        self.tree.column("expiry", width=85, anchor="center")
        self.tree.column("status", width=95, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_medicines(self) -> None:
        """Fetches catalog records via MedicineService and populates table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_cat = self.combo_cat.get()
        cat_id = self.cat_map.get(selected_cat)
        query = self.ent_search.get().strip().lower()

        from pharmacy_management.services.search_service import search_service
        if query:
            meds = search_service.search_medicines(query)
            if cat_id:
                meds = [m for m in meds if m.category_id == cat_id]
        else:
            meds = medicine_service.get_all_medicines(category_id=cat_id)

        for m in meds:
            status_text, _, _ = get_expiry_status(m.expiry_date)
            if m.is_low_stock and not m.is_expired:
                status_text += " | Low Stock"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    m.id,
                    m.name,
                    m.generic_name or "-",
                    m.category_name or "-",
                    m.batch_number,
                    f"{m.stock_quantity}",
                    format_currency(m.unit_price),
                    format_currency(m.cost_price),
                    m.expiry_date,
                    status_text
                )
            )

    def _get_selected_medicine_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a medicine from the table.")
            return None
        values = self.tree.item(selected[0], "values")
        return int(values[0])

    def _open_add_dialog(self) -> None:
        MedicineDialog(self, title="Add New Medicine Batch", on_saved=self.load_medicines)

    def _open_edit_dialog(self) -> None:
        med_id = self._get_selected_medicine_id()
        if not med_id:
            return
        med = medicine_service.get_medicine_by_id(med_id)
        if med:
            MedicineDialog(self, title="Edit Medicine Record", medicine=med, on_saved=self.load_medicines)

    def _handle_discontinue(self) -> None:
        med_id = self._get_selected_medicine_id()
        if not med_id:
            return
        if messagebox.askyesno("Confirm Discontinue", "Are you sure you want to mark this medicine as Discontinued?"):
            ok, msg = medicine_service.delete_medicine(med_id)
            if ok:
                messagebox.showinfo("Success", msg)
                self.load_medicines()
            else:
                messagebox.showerror("Error", msg)


class MedicineDialog(tk.Toplevel):
    """Modal dialog for creating and updating medicine records."""

    def __init__(self, parent: tk.Widget, title: str, on_saved: Any, medicine: Optional[Medicine] = None):
        """Initializes medicine create/edit modal dialog."""
        super().__init__(parent)
        self.title(title)
        self.geometry("540x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_saved = on_saved
        self.medicine = medicine

        self._init_form()

    def _init_form(self) -> None:
        form_frame = tk.Frame(self, padx=25, pady=20, bg=settings.THEME["SURFACE"])
        form_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            form_frame,
            text=self.title(),
            font=(settings.THEME["FONT_FAMILY"], 13, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 15))

        # Grid container for inputs
        grid = tk.Frame(form_frame, bg=settings.THEME["SURFACE"])
        grid.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Medicine Name *", "ent_name"),
            ("Generic / Molecule", "ent_generic"),
            ("Batch Number *", "ent_batch"),
            ("Barcode / EAN", "ent_barcode"),
            ("Manufacturer", "ent_mfg"),
            ("Dispense Unit (e.g. Strip)", "ent_unit"),
            ("Unit Selling Price (₹) *", "ent_price"),
            ("Unit Cost Price (₹) *", "ent_cost"),
            ("Stock Quantity *", "ent_stock"),
            ("Reorder Threshold", "ent_reorder"),
            ("Expiry Date (YYYY-MM-DD) *", "ent_expiry"),
        ]

        self.entries = {}
        for row_idx, (label_text, var_name) in enumerate(fields):
            lbl = tk.Label(grid, text=label_text, font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"])
            lbl.grid(row=row_idx, column=0, sticky="w", pady=4, padx=(0, 10))

            ent = ttk.Entry(grid, width=32)
            ent.grid(row=row_idx, column=1, sticky="w", pady=4)
            self.entries[var_name] = ent

        # Pre-fill if editing
        if self.medicine:
            self.entries["ent_name"].insert(0, self.medicine.name)
            self.entries["ent_generic"].insert(0, self.medicine.generic_name or "")
            self.entries["ent_batch"].insert(0, self.medicine.batch_number)
            self.entries["ent_barcode"].insert(0, self.medicine.barcode or "")
            self.entries["ent_mfg"].insert(0, self.medicine.manufacturer or "")
            self.entries["ent_unit"].insert(0, self.medicine.unit)
            self.entries["ent_price"].insert(0, str(self.medicine.unit_price))
            self.entries["ent_cost"].insert(0, str(self.medicine.cost_price))
            self.entries["ent_stock"].insert(0, str(self.medicine.stock_quantity))
            self.entries["ent_reorder"].insert(0, str(self.medicine.reorder_level))
            self.entries["ent_expiry"].insert(0, self.medicine.expiry_date)
        else:
            self.entries["ent_unit"].insert(0, "Strips")
            self.entries["ent_stock"].insert(0, "0")
            self.entries["ent_reorder"].insert(0, "10")

        # Action Buttons
        btn_box = tk.Frame(form_frame, bg=settings.THEME["SURFACE"])
        btn_box.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            btn_box,
            text="Save Medicine",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=6,
            command=self._handle_save
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_box,
            text="Cancel",
            font=(settings.THEME["FONT_FAMILY"], 9),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _handle_save(self) -> None:
        payload = {
            "name": self.entries["ent_name"].get(),
            "generic_name": self.entries["ent_generic"].get(),
            "batch_number": self.entries["ent_batch"].get(),
            "barcode": self.entries["ent_barcode"].get(),
            "manufacturer": self.entries["ent_mfg"].get(),
            "unit": self.entries["ent_unit"].get(),
            "unit_price": self.entries["ent_price"].get(),
            "cost_price": self.entries["ent_cost"].get(),
            "stock_quantity": self.entries["ent_stock"].get(),
            "reorder_level": self.entries["ent_reorder"].get(),
            "expiry_date": self.entries["ent_expiry"].get(),
        }

        if self.medicine:
            ok, msg = medicine_service.update_medicine(self.medicine.id, payload)
        else:
            ok, msg, _ = medicine_service.add_medicine(payload)

        if ok:
            messagebox.showinfo("Success", msg)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Validation Rejected (Poka-Yoke)", msg)
