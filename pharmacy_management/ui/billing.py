"""
================================================================================
Pharmacy Management System - Point of Sale (POS) Billing View
================================================================================
Module: pharmacy_management.ui.billing
Quality Objective: Q10 - Improve Documentation & Poka-Yoke Error Prevention

Description:
    Renders the retail pharmacy counter POS checkout screen.
    Enforces strict Poka-Yoke mistake-proofing before items can enter the cart:
      - Blocks expired medicines from being billed.
      - Blocks quantities exceeding on-hand inventory balances.
      - Decrements inventory counts atomically via SalesService.
      - Displays formatted ASCII thermal receipts upon completion.
    Zero SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
from pharmacy_management.config import settings
from pharmacy_management.services.sales_service import sales_service
from pharmacy_management.services.medicine_service import medicine_service
from pharmacy_management.services.search_service import search_service
from pharmacy_management.models.user import User
from pharmacy_management.models.medicine import Medicine
from pharmacy_management.utils.helpers import format_currency, get_expiry_status, generate_receipt_text


class BillingView(ttk.Frame):
    """Point-of-Sale (POS) counter dispensing and customer billing view."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes POS billing interface and shopping cart ledger."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self.cart_items: List[Dict[str, Any]] = []
        self.selected_medicine: Optional[Medicine] = None

        self._init_ui()
        self._load_customers()

    def _init_ui(self) -> None:
        """Constructs split POS interface: Cart & Entry on Left, Summary on Right."""
        # Top Header
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Point of Sale (POS) Counter Billing",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        # Main Split Workspace
        workspace = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=5)
        workspace.pack(fill=tk.BOTH, expand=True)

        # Left Column: Item Selection + Cart Table
        left_box = tk.Frame(workspace, bg=settings.THEME["BACKGROUND"])
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # 1. Customer & Product Entry Strip
        entry_panel = tk.Frame(
            left_box,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=15,
            pady=12
        )
        entry_panel.pack(fill=tk.X, pady=(0, 10))

        # Customer Selection Row
        cust_row = tk.Frame(entry_panel, bg=settings.THEME["SURFACE"])
        cust_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            cust_row,
            text="Customer / Patient:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.combo_customer = ttk.Combobox(cust_row, state="readonly", width=32)
        self.combo_customer.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            cust_row,
            text="➕ New Customer",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            cursor="hand2",
            command=self._open_new_customer_dialog
        ).pack(side=tk.LEFT)

        # Medicine Search & Selection Row
        med_row = tk.Frame(entry_panel, bg=settings.THEME["SURFACE"])
        med_row.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            med_row,
            text="Medicine / Barcode:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.ent_med_search = ttk.Entry(med_row, width=28)
        self.ent_med_search.pack(side=tk.LEFT, padx=(0, 10))
        self.ent_med_search.bind("<KeyRelease>", lambda _: self._on_med_search_typing())

        tk.Label(
            med_row,
            text="Qty:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.ent_qty = ttk.Entry(med_row, width=6)
        self.ent_qty.pack(side=tk.LEFT, padx=(0, 10))
        self.ent_qty.insert(0, "1")

        btn_add = tk.Button(
            med_row,
            text="➕ Add to Cart",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=3,
            command=self._handle_add_to_cart
        )
        btn_add.pack(side=tk.LEFT)

        # Candidate Medicine Results Listbox
        self.listbox_meds = tk.Listbox(entry_panel, height=4, font=(settings.THEME["FONT_FAMILY"], 9))
        self.listbox_meds.pack(fill=tk.X, pady=(4, 6))
        self.listbox_meds.bind("<<ListboxSelect>>", self._on_medicine_selected_from_list)

        # Item Info Strip (Stock & Expiry Display)
        self.lbl_selected_info = tk.Label(
            entry_panel,
            text="Select an item above to verify inventory and expiration status.",
            font=(settings.THEME["FONT_FAMILY"], 8),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_selected_info.pack(anchor="w")

        # 2. Cart Table
        cart_panel = tk.Frame(
            left_box,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=12,
            pady=10
        )
        cart_panel.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            cart_panel,
            text="Shopping Cart / Dispense Ledger",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 6))

        cols = ("idx", "name", "batch", "unit_price", "qty", "total", "expiry")
        self.cart_tree = ttk.Treeview(cart_panel, columns=cols, show="headings", height=10)
        self.cart_tree.heading("idx", text="#")
        self.cart_tree.heading("name", text="Medicine")
        self.cart_tree.heading("batch", text="Batch #")
        self.cart_tree.heading("unit_price", text="Price")
        self.cart_tree.heading("qty", text="Qty")
        self.cart_tree.heading("total", text="Total")
        self.cart_tree.heading("expiry", text="Expiry")

        self.cart_tree.column("idx", width=30, anchor="center")
        self.cart_tree.column("name", width=180)
        self.cart_tree.column("batch", width=90, anchor="center")
        self.cart_tree.column("unit_price", width=75, anchor="e")
        self.cart_tree.column("qty", width=50, anchor="center")
        self.cart_tree.column("total", width=80, anchor="e")
        self.cart_tree.column("expiry", width=85, anchor="center")

        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        btn_remove = tk.Button(
            cart_panel,
            text="🗑️ Remove Selected Item",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            fg=settings.THEME["DANGER"],
            cursor="hand2",
            command=self._handle_remove_cart_item
        )
        btn_remove.pack(anchor="w", pady=(6, 0))

        # Right Column: Financial Calculation Card
        right_box = tk.Frame(
            workspace,
            bg=settings.THEME["SURFACE"],
            width=300,
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=20,
            pady=18
        )
        right_box.pack(side=tk.RIGHT, fill=tk.Y)
        right_box.pack_propagate(False)

        tk.Label(
            right_box,
            text="Invoice Summary",
            font=(settings.THEME["FONT_FAMILY"], 13, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 15))

        # Subtotal
        self.lbl_subtotal_val = self._create_summary_row(right_box, "Subtotal:", "₹0.00")

        # Discount Entry
        disc_frame = tk.Frame(right_box, bg=settings.THEME["SURFACE"])
        disc_frame.pack(fill=tk.X, pady=6)
        tk.Label(disc_frame, text="Discount (%):", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT)
        self.ent_discount = ttk.Entry(disc_frame, width=8)
        self.ent_discount.pack(side=tk.RIGHT)
        self.ent_discount.insert(0, "0")
        self.ent_discount.bind("<KeyRelease>", lambda _: self._recalculate_totals())

        # Tax Entry
        tax_frame = tk.Frame(right_box, bg=settings.THEME["SURFACE"])
        tax_frame.pack(fill=tk.X, pady=6)
        tk.Label(tax_frame, text=f"Tax Rate ({settings.DEFAULT_TAX_PERCENT}%):", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT)
        self.lbl_tax_val = tk.Label(tax_frame, text="₹0.00", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"])
        self.lbl_tax_val.pack(side=tk.RIGHT)

        ttk.Separator(right_box, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        # Grand Total Display
        tk.Label(
            right_box,
            text="GRAND TOTAL",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w")

        self.lbl_grand_total = tk.Label(
            right_box,
            text="₹0.00",
            font=(settings.THEME["FONT_FAMILY"], 22, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_grand_total.pack(anchor="w", pady=(2, 15))

        # Payment Method Dropdown
        tk.Label(
            right_box,
            text="Payment Method:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 4))

        self.combo_payment = ttk.Combobox(right_box, state="readonly", values=["Cash", "Card", "UPI", "Insurance"])
        self.combo_payment.pack(fill=tk.X, pady=(0, 20))
        self.combo_payment.current(0)

        # Checkout Button
        self.btn_checkout = tk.Button(
            right_box,
            text="Complete Sale & Receipt",
            font=(settings.THEME["FONT_FAMILY"], 11, "bold"),
            bg=settings.THEME["SUCCESS"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            pady=10,
            command=self._handle_checkout
        )
        self.btn_checkout.pack(fill=tk.X, pady=(0, 10))

        # Clear Cart Button
        tk.Button(
            right_box,
            text="Clear Cart",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._clear_cart
        ).pack(fill=tk.X)

    def _create_summary_row(self, parent: tk.Widget, label: str, default: str) -> tk.Label:
        row = tk.Frame(parent, bg=settings.THEME["SURFACE"])
        row.pack(fill=tk.X, pady=4)
        tk.Label(row, text=label, font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT)
        val_lbl = tk.Label(row, text=default, font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"])
        val_lbl.pack(side=tk.RIGHT)
        return val_lbl

    def _load_customers(self) -> None:
        """Fetches customer records via SearchService downstream."""
        customers = search_service.search_customers("")
        self.customer_map = {"Walk-in Customer": None}
        cust_list = ["Walk-in Customer"]
        for c in customers:
            display_name = f"{c['name']} ({c['phone']})"
            cust_list.append(display_name)
            self.customer_map[display_name] = c["id"]
        self.combo_customer["values"] = cust_list
        self.combo_customer.current(0)

    def _on_med_search_typing(self) -> None:
        """Dynamically queries medicines as user types into search box."""
        q = self.ent_med_search.get().strip()
        self.listbox_meds.delete(0, tk.END)
        if len(q) < 1:
            return

        results = search_service.search_medicines(q, active_only=True)[:6]
        self.search_results = results
        for idx, m in enumerate(results):
            self.listbox_meds.insert(
                tk.END,
                f"{m.name} | Batch: {m.batch_number} | Stock: {m.stock_quantity} | Exp: {m.expiry_date} | ₹{m.unit_price}"
            )

    def _on_medicine_selected_from_list(self, event: Any) -> None:
        """Handles selection of a candidate medicine from search results list."""
        sel = self.listbox_meds.curselection()
        if not sel or not hasattr(self, "search_results"):
            return
        self.selected_medicine = self.search_results[sel[0]]

        # Display health info
        status_text, fg_color, _ = get_expiry_status(self.selected_medicine.expiry_date)
        info_str = (
            f"Selected: {self.selected_medicine.name} | Available Stock: {self.selected_medicine.stock_quantity} | "
            f"Expiry: {self.selected_medicine.expiry_date} ({status_text})"
        )
        self.lbl_selected_info.config(text=info_str, fg=fg_color)

    def _handle_add_to_cart(self) -> None:
        """Poka-Yoke Gate: Validates stock and expiry before appending item to cart."""
        if not self.selected_medicine:
            messagebox.showwarning("Item Required", "Please search and select a medicine first.")
            return

        qty_str = self.ent_qty.get().strip()
        if not qty_str.isdigit() or int(qty_str) <= 0:
            messagebox.showerror("Validation Error", "Please specify a positive integer quantity.")
            return

        qty = int(qty_str)

        # Call downstream SalesService Poka-Yoke check
        is_valid, err_msg, _ = sales_service.validate_cart_item(self.selected_medicine.id, qty)
        if not is_valid:
            messagebox.showerror("Poka-Yoke Safeguard Rejection", err_msg)
            return

        # Check if already in cart
        for item in self.cart_items:
            if item["medicine_id"] == self.selected_medicine.id:
                new_qty = item["quantity"] + qty
                is_valid2, err2, _ = sales_service.validate_cart_item(self.selected_medicine.id, new_qty)
                if not is_valid2:
                    messagebox.showerror("Poka-Yoke Safeguard Rejection", err2)
                    return
                item["quantity"] = new_qty
                item["total"] = round(new_qty * item["unit_price"], 2)
                self._refresh_cart_tree()
                self._recalculate_totals()
                return

        # Append new cart item
        self.cart_items.append({
            "medicine_id": self.selected_medicine.id,
            "name": self.selected_medicine.name,
            "batch_number": self.selected_medicine.batch_number,
            "unit_price": self.selected_medicine.unit_price,
            "quantity": qty,
            "total": round(qty * self.selected_medicine.unit_price, 2),
            "expiry_date": self.selected_medicine.expiry_date,
        })

        self._refresh_cart_tree()
        self._recalculate_totals()

    def _refresh_cart_tree(self) -> None:
        for itm in self.cart_tree.get_children():
            self.cart_tree.delete(itm)

        for i, item in enumerate(self.cart_items, 1):
            self.cart_tree.insert(
                "",
                tk.END,
                values=(
                    i,
                    item["name"],
                    item["batch_number"],
                    format_currency(item["unit_price"]),
                    item["quantity"],
                    format_currency(item["total"]),
                    item["expiry_date"]
                )
            )

    def _handle_remove_cart_item(self) -> None:
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        del self.cart_items[idx]
        self._refresh_cart_tree()
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        subtotal = sum(item["total"] for item in self.cart_items)
        self.lbl_subtotal_val.config(text=format_currency(subtotal))

        disc_str = self.ent_discount.get().strip()
        try:
            disc_rate = float(disc_str)
        except ValueError:
            disc_rate = 0.0

        if disc_rate > settings.MAX_DISCOUNT_PERCENT:
            disc_rate = settings.MAX_DISCOUNT_PERCENT

        disc_amt = round(subtotal * (disc_rate / 100.0), 2)
        after_disc = subtotal - disc_amt
        tax_amt = round(after_disc * (settings.DEFAULT_TAX_PERCENT / 100.0), 2)
        grand_total = round(after_disc + tax_amt, 2)

        self.lbl_tax_val.config(text=format_currency(tax_amt))
        self.lbl_grand_total.config(text=format_currency(grand_total))

    def _handle_checkout(self) -> None:
        """Processes complete sale transaction atomically downstream."""
        if not self.cart_items:
            messagebox.showwarning("Cart Empty", "Please add items to cart before completing sale.")
            return

        cust_sel = self.combo_customer.get()
        cust_id = self.customer_map.get(cust_sel)
        pay_method = self.combo_payment.get()

        try:
            disc_rate = float(self.ent_discount.get().strip() or "0")
        except ValueError:
            disc_rate = 0.0

        # Downstream execution
        success, msg, sale_summary = sales_service.process_sale(
            cart_items=self.cart_items,
            user_id=self.user.id,
            customer_id=cust_id,
            discount_percent=disc_rate,
            payment_method=pay_method
        )

        if success and sale_summary:
            sale_summary["customer_name"] = cust_sel
            sale_summary["cashier_name"] = self.user.full_name
            ReceiptModal(self, sale_summary=sale_summary, items=self.cart_items)
            self._clear_cart()
        else:
            messagebox.showerror("Checkout Failed", msg)

    def _clear_cart(self) -> None:
        self.cart_items.clear()
        self._refresh_cart_tree()
        self.ent_med_search.delete(0, tk.END)
        self.listbox_meds.delete(0, tk.END)
        self.lbl_selected_info.config(text="")
        self.selected_medicine = None
        self._recalculate_totals()

    def _open_new_customer_dialog(self) -> None:
        from pharmacy_management.ui.customers import CustomerDialog
        CustomerDialog(self, title="Register New Customer", on_saved=self._load_customers)


class ReceiptModal(tk.Toplevel):
    """Modal displaying formatted ASCII thermal receipt with print/export options."""

    def __init__(self, parent: tk.Widget, sale_summary: Dict[str, Any], items: List[Dict[str, Any]]):
        """Initializes thermal receipt preview modal."""
        super().__init__(parent)
        self.title("Transaction Finalized - Thermal Receipt")
        self.geometry("480x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.receipt_text = generate_receipt_text(sale_summary, items)
        self._init_ui()

    def _init_ui(self) -> None:
        txt = tk.Text(self, font=(settings.THEME["FONT_FAMILY_MONO"], 9), bg="#ffffff", padx=10, pady=10)
        txt.insert("1.0", self.receipt_text)
        txt.configure(state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)

        btn_box = tk.Frame(self, padx=10, pady=8, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(fill=tk.X)

        tk.Button(
            btn_box,
            text="Close",
            font=(settings.THEME["FONT_FAMILY"], 9),
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_box,
            text="Copy Receipt",
            font=(settings.THEME["FONT_FAMILY"], 9),
            command=self._copy_receipt
        ).pack(side=tk.RIGHT, padx=5)

    def _copy_receipt(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.receipt_text)
        messagebox.showinfo("Copied", "Receipt copied to system clipboard.")
