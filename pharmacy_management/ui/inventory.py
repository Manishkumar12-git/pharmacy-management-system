"""
================================================================================
Pharmacy Management System - Inventory & Expiry Control View
================================================================================
Module: pharmacy_management.ui.inventory
Quality Objective: Q10 - Improve Documentation & Quality Bounds

Description:
    Provides warehouse managers and pharmacists with comprehensive stock
    health tracking, low-stock reorder filters, near-expiry warnings,
    regulatory quarantine of expired lots, and auditable stock adjustments.
    Zero direct SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from pharmacy_management.config import settings
from pharmacy_management.services.inventory_service import inventory_service
from pharmacy_management.models.user import User
from pharmacy_management.models.medicine import Medicine
from pharmacy_management.utils.helpers import format_currency, get_expiry_status


class InventoryView(ttk.Frame):
    """View governing physical inventory health, reorders, and quarantine."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes warehouse inventory and expiry tracking view."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self.current_filter = "ALL"
        self._init_ui()
        self.load_inventory()

    def _init_ui(self) -> None:
        # Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Warehouse Inventory & Expiry Tracking",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        btn_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(side=tk.RIGHT)

        if self.user.role in (settings.ROLE_ADMIN, settings.ROLE_PHARMACIST):
            tk.Button(
                btn_box,
                text="⚖️ Adjust Stock Count",
                font=(settings.THEME["FONT_FAMILY"], 9),
                bg=settings.THEME["SURFACE"],
                fg=settings.THEME["TEXT_MAIN"],
                relief=tk.SOLID,
                bd=1,
                cursor="hand2",
                padx=10,
                pady=5,
                command=self._open_stock_adjustment_dialog
            ).pack(side=tk.LEFT, padx=5)

        # KPI Summary Ribbon
        self.summary_bar = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        self.summary_bar.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.lbl_sum_val = tk.Label(
            self.summary_bar,
            text="Loading inventory valuation...",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_sum_val.pack(side=tk.LEFT)

        # Tab / Filter Buttons
        tab_frame = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20)
        tab_frame.pack(fill=tk.X, pady=(0, 10))

        filters = [
            ("ALL", "📦 All Inventory"),
            ("LOW_STOCK", "⚠️ Low Stock Alerts"),
            ("EXPIRING", "⏳ Expiring Soon (<60d)"),
            ("EXPIRED", "⛔ Quarantined / Expired"),
        ]

        self.filter_buttons = {}
        for key, text in filters:
            btn = tk.Button(
                tab_frame,
                text=text,
                font=(settings.THEME["FONT_FAMILY"], 9),
                bg=settings.THEME["SURFACE"],
                relief=tk.SOLID,
                bd=1,
                padx=12,
                pady=5,
                cursor="hand2",
                command=lambda k=key: self._set_filter(k)
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.filter_buttons[key] = btn

        # Inventory Treeview
        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        cols = ("id", "name", "category", "batch", "stock", "reorder", "cost", "price", "expiry", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Medicine")
        self.tree.heading("category", text="Category")
        self.tree.heading("batch", text="Batch #")
        self.tree.heading("stock", text="In Stock")
        self.tree.heading("reorder", text="Reorder Pt")
        self.tree.heading("cost", text="Cost Val")
        self.tree.heading("price", text="Retail Val")
        self.tree.heading("expiry", text="Expiry")
        self.tree.heading("status", text="Safety Status")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("category", width=130)
        self.tree.column("batch", width=90, anchor="center")
        self.tree.column("stock", width=65, anchor="center")
        self.tree.column("reorder", width=75, anchor="center")
        self.tree.column("cost", width=85, anchor="e")
        self.tree.column("price", width=85, anchor="e")
        self.tree.column("expiry", width=85, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _set_filter(self, key: str) -> None:
        self.current_filter = key
        for k, b in self.filter_buttons.items():
            if k == key:
                b.configure(bg=settings.THEME["PRIMARY_LIGHT"], fg=settings.THEME["PRIMARY"], font=(settings.THEME["FONT_FAMILY"], 9, "bold"))
            else:
                b.configure(bg=settings.THEME["SURFACE"], fg=settings.THEME["TEXT_MAIN"], font=(settings.THEME["FONT_FAMILY"], 9))
        self.load_inventory()

    def load_inventory(self) -> None:
        """Loads and updates inventory table based on the active filter."""
        for itm in self.tree.get_children():
            self.tree.delete(itm)

        # Update Summary
        s = inventory_service.get_inventory_summary()
        self.lbl_sum_val.config(
            text=(
                f"Total SKUs: {s['total_medicines']} | Total Units: {s['total_units']} | "
                f"Cost Asset: {format_currency(s['total_cost_value'])} | "
                f"Retail Asset: {format_currency(s['total_retail_value'])} | "
                f"Low Stock: {s['low_stock_count']} | Expired Quarantine: {s['expired_count']}"
            )
        )

        # Fetch Data based on filter
        if self.current_filter == "LOW_STOCK":
            items = inventory_service.get_low_stock_items()
        elif self.current_filter == "EXPIRING":
            items = inventory_service.get_expiring_soon_items()
        elif self.current_filter == "EXPIRED":
            items = inventory_service.get_expired_items()
        else:
            from pharmacy_management.services.medicine_service import medicine_service
            items = medicine_service.get_all_medicines()

        for m in items:
            status_text, _, _ = get_expiry_status(m.expiry_date)
            cost_val = round(m.stock_quantity * m.cost_price, 2)
            retail_val = round(m.stock_quantity * m.unit_price, 2)

            self.tree.insert(
                "",
                tk.END,
                values=(
                    m.id,
                    m.name,
                    m.category_name or "-",
                    m.batch_number,
                    f"{m.stock_quantity}",
                    f"{m.reorder_level}",
                    format_currency(cost_val),
                    format_currency(retail_val),
                    m.expiry_date,
                    status_text
                )
            )

    def _open_stock_adjustment_dialog(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select Item", "Please select a medicine batch to adjust.")
            return

        med_id = int(self.tree.item(sel[0], "values")[0])
        med_name = self.tree.item(sel[0], "values")[1]
        cur_stock = self.tree.item(sel[0], "values")[4]

        StockAdjustmentDialog(self, med_id=med_id, med_name=med_name, current_stock=cur_stock, user=self.user, on_saved=self.load_inventory)


class StockAdjustmentDialog(tk.Toplevel):
    """Modal dialog for audited manual stock adjustments."""

    def __init__(self, parent: tk.Widget, med_id: int, med_name: str, current_stock: str, user: User, on_saved: Any):
        """Initializes audited stock adjustment dialog."""
        super().__init__(parent)
        self.title("Audited Stock Adjustment")
        self.geometry("400x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.med_id = med_id
        self.user = user
        self.on_saved = on_saved

        pad = tk.Frame(self, padx=25, pady=20, bg=settings.THEME["SURFACE"])
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text=f"Item: {med_name}", font=(settings.THEME["FONT_FAMILY"], 11, "bold"), bg=settings.THEME["SURFACE"]).pack(anchor="w")
        tk.Label(pad, text=f"Current Stock: {current_stock} units", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).pack(anchor="w", pady=(0, 15))

        tk.Label(pad, text="Verified Physical Quantity *:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(anchor="w")
        self.ent_new_qty = ttk.Entry(pad, width=20)
        self.ent_new_qty.pack(anchor="w", pady=(2, 12))
        self.ent_new_qty.insert(0, current_stock)

        tk.Label(pad, text="Reason for Discrepancy *:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(anchor="w")
        self.combo_reason = ttk.Combobox(pad, values=["Periodic Physical Audit", "Damaged / Broken", "Supplier Discrepancy", "Other Discrepancy"], state="readonly")
        self.combo_reason.pack(fill=tk.X, pady=(2, 20))
        self.combo_reason.current(0)

        btn_box = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        btn_box.pack(fill=tk.X)

        tk.Button(
            btn_box,
            text="Confirm Adjustment",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            command=self._handle_save
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _handle_save(self) -> None:
        qty_str = self.ent_new_qty.get().strip()
        if not qty_str.isdigit() or int(qty_str) < 0:
            messagebox.showerror("Error", "Quantity must be a non-negative integer.")
            return

        new_qty = int(qty_str)
        reason = self.combo_reason.get()

        ok, msg = inventory_service.adjust_stock(self.med_id, new_qty, reason, self.user.id)
        if ok:
            messagebox.showinfo("Success", msg)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
