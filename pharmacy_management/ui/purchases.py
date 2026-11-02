"""
================================================================================
Pharmacy Management System - Purchases & Inbound Restocking View
================================================================================
Module: pharmacy_management.ui.purchases
Quality Objective: Q10 - Improve Documentation & Inbound Quality Control

Description:
    Renders wholesale supplier shipments, intake inspection records,
    and automatic stock replenishment. Zero direct SQL in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
from pharmacy_management.config import settings
from pharmacy_management.services.purchase_service import purchase_service
from pharmacy_management.services.medicine_service import medicine_service
from pharmacy_management.models.user import User
from pharmacy_management.utils.helpers import format_currency


class PurchasesView(ttk.Frame):
    """View governing inbound stock replenishment and supplier purchase invoices."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes supplier purchases ledger and restocking view."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self.load_purchases()

    def _init_ui(self) -> None:
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Inbound Purchases & Stock Restocking Ledger",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        if self.user.role in (settings.ROLE_ADMIN, settings.ROLE_PHARMACIST):
            tk.Button(
                top_bar,
                text="➕ Record Inbound Restock",
                font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
                bg=settings.THEME["PRIMARY"],
                fg=settings.THEME["TEXT_LIGHT"],
                relief=tk.FLAT,
                cursor="hand2",
                padx=12,
                pady=5,
                command=self._open_new_purchase_dialog
            ).pack(side=tk.RIGHT)

        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        cols = ("id", "inv", "supplier", "date", "amount", "status", "receiver", "notes")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("inv", text="Invoice / PO #")
        self.tree.heading("supplier", text="Supplier")
        self.tree.heading("date", text="Receipt Date")
        self.tree.heading("amount", text="Total Paid")
        self.tree.heading("status", text="Payment Status")
        self.tree.heading("receiver", text="Received By")
        self.tree.heading("notes", text="Inspection Notes")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("inv", width=140)
        self.tree.column("supplier", width=200)
        self.tree.column("date", width=120, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("receiver", width=140)
        self.tree.column("notes", width=180)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def load_purchases(self) -> None:
        """Loads and displays recent supplier restocking orders into treeview."""
        for itm in self.tree.get_children():
            self.tree.delete(itm)

        purchases = purchase_service.get_recent_purchases(limit=50)
        for p in purchases:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    p["id"],
                    p["invoice_number"],
                    p.get("supplier_name") or "-",
                    p["purchase_date"][:16] if p.get("purchase_date") else "-",
                    format_currency(p["total_amount"]),
                    p.get("payment_status", "Paid"),
                    p.get("receiver_name") or "-",
                    p.get("notes") or "-"
                )
            )

    def _open_new_purchase_dialog(self) -> None:
        PurchaseEntryDialog(self, user=self.user, on_saved=self.load_purchases)


class PurchaseEntryDialog(tk.Toplevel):
    """Modal dialog for receiving stock shipments."""

    def __init__(self, parent: tk.Widget, user: User, on_saved: Any):
        """Initializes supplier shipment intake dialog."""
        super().__init__(parent)
        self.title("Record Inbound Restock Order")
        self.geometry("640x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.user = user
        self.on_saved = on_saved
        self.line_items: List[Dict[str, Any]] = []

        self._init_form()

    def _init_form(self) -> None:
        pad = tk.Frame(self, padx=20, pady=15, bg=settings.THEME["SURFACE"])
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text="Supplier Shipment Intake", font=(settings.THEME["FONT_FAMILY"], 12, "bold"), fg=settings.THEME["PRIMARY"], bg=settings.THEME["SURFACE"]).pack(anchor="w", pady=(0, 10))

        # Supplier & Invoice ID
        hdr_frame = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        hdr_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(hdr_frame, text="Supplier *:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).grid(row=0, column=0, sticky="w", pady=3)
        self.combo_supplier = ttk.Combobox(hdr_frame, state="readonly", width=28)
        self.combo_supplier.grid(row=0, column=1, sticky="w", pady=3, padx=(5, 15))

        suppliers = purchase_service.get_all_suppliers()
        self.sup_map = {}
        sup_names = []
        for s in suppliers:
            sup_names.append(s.name)
            self.sup_map[s.name] = s.id
        self.combo_supplier["values"] = sup_names
        if sup_names:
            self.combo_supplier.current(0)

        tk.Label(hdr_frame, text="Invoice No *:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).grid(row=0, column=2, sticky="w", pady=3)
        self.ent_inv = ttk.Entry(hdr_frame, width=16)
        self.ent_inv.grid(row=0, column=3, sticky="w", pady=3, padx=(5, 0))

        # Item Entry Box
        item_box = tk.LabelFrame(pad, text=" Add Item to Shipment ", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), padx=10, pady=8, bg=settings.THEME["SURFACE"])
        item_box.pack(fill=tk.X, pady=(0, 10))

        tk.Label(item_box, text="Medicine:", font=(settings.THEME["FONT_FAMILY"], 8), bg=settings.THEME["SURFACE"]).grid(row=0, column=0, sticky="w")
        self.combo_med = ttk.Combobox(item_box, state="readonly", width=26)
        self.combo_med.grid(row=1, column=0, sticky="w", padx=(0, 5))

        all_meds = medicine_service.get_all_medicines()
        self.med_map = {}
        med_names = []
        for m in all_meds:
            med_names.append(m.name)
            self.med_map[m.name] = m
        self.combo_med["values"] = med_names
        if med_names:
            self.combo_med.current(0)

        tk.Label(item_box, text="Batch #:", font=(settings.THEME["FONT_FAMILY"], 8), bg=settings.THEME["SURFACE"]).grid(row=0, column=1, sticky="w")
        self.ent_batch = ttk.Entry(item_box, width=12)
        self.ent_batch.grid(row=1, column=1, sticky="w", padx=(0, 5))

        tk.Label(item_box, text="Expiry (YYYY-MM-DD):", font=(settings.THEME["FONT_FAMILY"], 8), bg=settings.THEME["SURFACE"]).grid(row=0, column=2, sticky="w")
        self.ent_expiry = ttk.Entry(item_box, width=13)
        self.ent_expiry.grid(row=1, column=2, sticky="w", padx=(0, 5))

        tk.Label(item_box, text="Qty:", font=(settings.THEME["FONT_FAMILY"], 8), bg=settings.THEME["SURFACE"]).grid(row=0, column=3, sticky="w")
        self.ent_qty = ttk.Entry(item_box, width=6)
        self.ent_qty.grid(row=1, column=3, sticky="w", padx=(0, 5))

        tk.Label(item_box, text="Unit Cost:", font=(settings.THEME["FONT_FAMILY"], 8), bg=settings.THEME["SURFACE"]).grid(row=0, column=4, sticky="w")
        self.ent_cost = ttk.Entry(item_box, width=8)
        self.ent_cost.grid(row=1, column=4, sticky="w", padx=(0, 5))

        tk.Button(
            item_box,
            text="Add Item",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            command=self._handle_add_line_item
        ).grid(row=1, column=5, sticky="w")

        # Items Table
        self.items_tree = ttk.Treeview(pad, columns=("med", "batch", "exp", "qty", "cost", "total"), show="headings", height=6)
        self.items_tree.heading("med", text="Medicine")
        self.items_tree.heading("batch", text="Batch")
        self.items_tree.heading("exp", text="Expiry")
        self.items_tree.heading("qty", text="Qty")
        self.items_tree.heading("cost", text="Cost")
        self.items_tree.heading("total", text="Total")

        self.items_tree.column("med", width=180)
        self.items_tree.column("batch", width=90)
        self.items_tree.column("exp", width=90)
        self.items_tree.column("qty", width=50, anchor="center")
        self.items_tree.column("cost", width=70, anchor="e")
        self.items_tree.column("total", width=80, anchor="e")
        self.items_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Bottom Buttons
        btn_box = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        btn_box.pack(fill=tk.X)

        tk.Button(
            btn_box,
            text="Save Purchase & Restock",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            command=self._handle_save
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _handle_add_line_item(self) -> None:
        med_name = self.combo_med.get()
        med = self.med_map.get(med_name)
        if not med:
            return

        batch = self.ent_batch.get().strip() or med.batch_number
        exp = self.ent_expiry.get().strip() or med.expiry_date
        qty_str = self.ent_qty.get().strip()
        cost_str = self.ent_cost.get().strip() or str(med.cost_price)

        if not qty_str.isdigit() or int(qty_str) <= 0:
            messagebox.showerror("Error", "Quantity must be a positive integer.")
            return

        qty = int(qty_str)
        try:
            cost = float(cost_str)
        except ValueError:
            messagebox.showerror("Error", "Unit cost must be a numeric value.")
            return

        line_tot = round(qty * cost, 2)
        self.line_items.append({
            "medicine_id": med.id,
            "medicine_name": med.name,
            "batch_number": batch,
            "expiry_date": exp,
            "quantity": qty,
            "cost_price": cost,
            "total_price": line_tot
        })

        self.items_tree.insert("", tk.END, values=(med.name, batch, exp, qty, format_currency(cost), format_currency(line_tot)))
        self.ent_qty.delete(0, tk.END)

    def _handle_save(self) -> None:
        sup_name = self.combo_supplier.get()
        sup_id = self.sup_map.get(sup_name)
        inv = self.ent_inv.get().strip()

        if not sup_id:
            messagebox.showerror("Error", "Please select a valid supplier.")
            return

        if not self.line_items:
            messagebox.showerror("Error", "Shipment has no line items.")
            return

        ok, msg, _ = purchase_service.process_purchase(
            supplier_id=sup_id,
            user_id=self.user.id,
            invoice_number=inv,
            items=self.line_items
        )

        if ok:
            messagebox.showinfo("Success", msg)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
