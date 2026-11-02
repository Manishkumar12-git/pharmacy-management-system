"""
================================================================================
Pharmacy Management System - Digital Batch Traceability Tree View
================================================================================
Module: pharmacy_management.ui.traceability
Quality Objective: Total Quality Management (TQM) & Six Sigma Batch Traceability

Description:
    Renders the Digital Batch Traceability Tree UI.
    Provides complete end-to-end forward and backward traceability for any
    pharmaceutical batch. Enables inspection of supplier purchase orders,
    on-hand storage condition, customer sales distribution logs, and one-click
    export of emergency recall patient contact lists.
    Zero direct SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List, Tuple

from pharmacy_management.config import settings
from pharmacy_management.services.traceability_service import TraceabilityService
from pharmacy_management.models.user import User


class BatchTraceabilityView(ttk.Frame):
    """View governing digital batch traceability, forward/backward lineage, and recall logs."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes batch traceability view.

        Args:
            parent (tk.Widget): Parent container.
            user (User): Current active operator.
        """
        super().__init__(parent)
        self.user = user

        self.service = TraceabilityService()
        self.current_trace: Optional[Dict[str, Any]] = None
        self.available_batches: List[Dict[str, Any]] = []

        self._init_ui()
        self.load_batch_catalog()

    def _init_ui(self) -> None:
        """Builds all UI sub-components: Header, search strip, KPI cards, and traceability panels."""
        # 1. Top Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=10)
        top_bar.pack(fill=tk.X)

        title_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        title_box.pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="🧬 Digital Batch Traceability & Recall Tree",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="End-to-End Forward & Backward Supply Chain Auditing (Supplier PO ➔ Stock ➔ Patient Sales)",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(anchor="w")

        btn_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(side=tk.RIGHT)

        tk.Button(
            btn_box,
            text="🚨 Export Recall List",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg="#d32f2f",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._export_recall_list
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_box,
            text="🔄 Refresh",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.GROOVE,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.load_batch_catalog
        ).pack(side=tk.LEFT, padx=5)

        # 2. Search & Selector Strip
        search_card = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=18, pady=8, relief=tk.GROOVE, bd=1)
        search_card.pack(fill=tk.X, padx=20, pady=(0, 8))

        tk.Label(
            search_card,
            text="Select or Search Batch Number / Medicine Name:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.batch_combo = ttk.Combobox(search_card, width=42, font=(settings.THEME["FONT_FAMILY"], 9))
        self.batch_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.batch_combo.bind("<Return>", lambda e: self.perform_trace())
        self.batch_combo.bind("<<ComboboxSelected>>", lambda e: self.perform_trace())

        tk.Button(
            search_card,
            text="🔍 Trace Batch",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.perform_trace
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.lbl_search_feedback = tk.Label(
            search_card,
            text="",
            font=(settings.THEME["FONT_FAMILY"], 9, "italic"),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_search_feedback.pack(side=tk.LEFT)

        # 3. Main Body Container
        self.main_body = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20)
        self.main_body.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Build Section Panels
        self._build_kpi_row()
        self._build_middle_split_panels()
        self._build_forward_panel()

    def _build_kpi_row(self) -> None:
        """Constructs top metric KPI summary cards."""
        self.kpi_frame = tk.Frame(self.main_body, bg=settings.THEME["BACKGROUND"])
        self.kpi_frame.pack(fill=tk.X, pady=(0, 8))

        self.kpi_cards: Dict[str, tk.Label] = {}
        metrics = [
            ("batch", "Batch Number", "---", settings.THEME["PRIMARY"]),
            ("received", "Inbound Restocked", "0 units", "#0288d1"),
            ("stock", "Current On-Hand", "0 units", "#2e7d32"),
            ("dispensed", "Dispensed to Patients", "0 units", "#ed6c02"),
            ("exposed", "Patients Impacted", "0 patients", "#d32f2f")
        ]

        for i, (key, label_txt, default_val, fg_color) in enumerate(metrics):
            card = tk.Frame(self.kpi_frame, bg=settings.THEME["SURFACE"], padx=10, pady=6, relief=tk.GROOVE, bd=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))

            tk.Label(
                card,
                text=label_txt,
                font=(settings.THEME["FONT_FAMILY"], 8),
                fg=settings.THEME["TEXT_MUTED"],
                bg=settings.THEME["SURFACE"]
            ).pack(anchor="w")

            val_lbl = tk.Label(
                card,
                text=default_val,
                font=(settings.THEME["FONT_FAMILY"], 11, "bold"),
                fg=fg_color,
                bg=settings.THEME["SURFACE"]
            )
            val_lbl.pack(anchor="w", pady=(2, 0))

            self.kpi_cards[key] = val_lbl

    def _build_middle_split_panels(self) -> None:
        """Constructs the side-by-side Backward Traceability and Current Inventory panels."""
        middle_split = tk.Frame(self.main_body, bg=settings.THEME["BACKGROUND"])
        middle_split.pack(fill=tk.X, pady=(0, 8))

        # Panel 1: Backward Traceability (Supplier)
        self.backward_frame = tk.LabelFrame(
            middle_split,
            text="  1. Inbound Supplier Source (Backward Traceability)  ",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"],
            padx=12,
            pady=6,
            relief=tk.GROOVE
        )
        self.backward_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        bg_grid = tk.Frame(self.backward_frame, bg=settings.THEME["SURFACE"])
        bg_grid.pack(fill=tk.BOTH, expand=True)

        self.lbl_supp_name = self._make_field(bg_grid, "Supplier Partner:", "---", 0, 0)
        self.lbl_supp_po = self._make_field(bg_grid, "Purchase Invoice #:", "---", 1, 0)
        self.lbl_supp_date = self._make_field(bg_grid, "Restock Date:", "---", 2, 0)
        self.lbl_supp_qty = self._make_field(bg_grid, "Received Qty & Cost:", "---", 3, 0)
        self.lbl_supp_contact = self._make_field(bg_grid, "Supplier Contact:", "---", 4, 0)
        self.lbl_supp_rec_by = self._make_field(bg_grid, "Inspected By:", "---", 5, 0)

        # Panel 2: Current Inventory Status
        self.status_frame = tk.LabelFrame(
            middle_split,
            text="  2. Current Inventory & Storage Condition  ",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"],
            padx=12,
            pady=6,
            relief=tk.GROOVE
        )
        self.status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        st_grid = tk.Frame(self.status_frame, bg=settings.THEME["SURFACE"])
        st_grid.pack(fill=tk.BOTH, expand=True)

        self.lbl_med_name = self._make_field(st_grid, "Medicine Name:", "---", 0, 0)
        self.lbl_generic = self._make_field(st_grid, "Generic Molecule:", "---", 1, 0)
        self.lbl_category = self._make_field(st_grid, "Category / Unit:", "---", 2, 0)
        self.lbl_storage = self._make_field(st_grid, "Storage Condition:", "---", 3, 0)
        self.lbl_expiry = self._make_field(st_grid, "Expiry Date & Status:", "---", 4, 0)
        self.lbl_mass_balance = self._make_field(st_grid, "Six Sigma Balance:", "---", 5, 0)

    def _build_forward_panel(self) -> None:
        """Constructs Forward Traceability Panel: Customer distribution table."""
        self.forward_frame = tk.LabelFrame(
            self.main_body,
            text="  3. Outbound Distribution & Patient Sales Log (Forward Traceability)  ",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"],
            padx=12,
            pady=6,
            relief=tk.GROOVE
        )
        self.forward_frame.pack(fill=tk.BOTH, expand=True)

        # Action sub-bar inside forward panel
        f_sub = tk.Frame(self.forward_frame, bg=settings.THEME["SURFACE"])
        f_sub.pack(fill=tk.X, pady=(0, 4))

        self.lbl_sales_summary = tk.Label(
            f_sub,
            text="0 customer dispensing transactions recorded for this batch.",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_sales_summary.pack(side=tk.LEFT)

        # Sales Distribution Treeview Table
        table_container = tk.Frame(self.forward_frame, bg=settings.THEME["SURFACE"])
        table_container.pack(fill=tk.BOTH, expand=True)

        cols = ("invoice", "date", "customer", "phone", "qty", "unit_price", "total", "cashier")
        self.sales_tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            height=5,
            selectmode="browse"
        )

        self.sales_tree.heading("invoice", text="Sale Invoice #")
        self.sales_tree.heading("date", text="Dispensed Timestamp")
        self.sales_tree.heading("customer", text="Patient / Customer")
        self.sales_tree.heading("phone", text="Phone Number")
        self.sales_tree.heading("qty", text="Qty Sold")
        self.sales_tree.heading("unit_price", text="Unit Price")
        self.sales_tree.heading("total", text="Total Price")
        self.sales_tree.heading("cashier", text="Dispensed By")

        self.sales_tree.column("invoice", width=140, anchor="w")
        self.sales_tree.column("date", width=130, anchor="center")
        self.sales_tree.column("customer", width=140, anchor="w")
        self.sales_tree.column("phone", width=105, anchor="center")
        self.sales_tree.column("qty", width=65, anchor="center")
        self.sales_tree.column("unit_price", width=75, anchor="e")
        self.sales_tree.column("total", width=80, anchor="e")
        self.sales_tree.column("cashier", width=105, anchor="w")

        tree_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=tree_scroll.set)

        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _make_field(self, parent: tk.Widget, label_text: str, default_val: str, row: int, col: int) -> tk.Label:
        """Helper to create standardized field label-value pairs."""
        f_box = tk.Frame(parent, bg=settings.THEME["SURFACE"], pady=1)
        f_box.grid(row=row, column=col, sticky="w", padx=4)

        tk.Label(
            f_box,
            text=label_text,
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"],
            width=19,
            anchor="w"
        ).pack(side=tk.LEFT)

        val_lbl = tk.Label(
            f_box,
            text=default_val,
            font=(settings.THEME["FONT_FAMILY"], 8),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"],
            anchor="w"
        )
        val_lbl.pack(side=tk.LEFT)
        return val_lbl

    def load_batch_catalog(self) -> None:
        """Loads available distinct batches from the service layer to populate the combobox."""
        try:
            self.available_batches = self.service.get_all_batches()
            options = []
            for b in self.available_batches:
                options.append(f"{b['batch_number']} | {b['medicine_name']} (Stock: {b['stock_quantity']})")

            self.batch_combo["values"] = options
            if options and not self.batch_combo.get():
                self.batch_combo.current(0)
                self.perform_trace()
            self.lbl_search_feedback.config(text=f"Loaded {len(options)} active batches from inventory.")
        except Exception as exc:
            messagebox.showerror("Traceability Error", f"Failed to retrieve batch catalog: {str(exc)}")

    def perform_trace(self) -> None:
        """Reads search/combobox input and renders the forward & backward lineage."""
        raw_val = self.batch_combo.get().strip()
        if not raw_val:
            messagebox.showwarning("Input Required", "Please select or type a Batch Number or Medicine Name.")
            return

        # If chosen from dropdown formatted as 'BATCH | MED (Stock: X)'
        if " | " in raw_val:
            query = raw_val.split(" | ")[0].strip()
        else:
            query = raw_val

        self.lbl_search_feedback.config(text=f"Tracing lineage for '{query}'...")
        result = self.service.trace_batch(query)

        if not result:
            self.lbl_search_feedback.config(text=f"No records found matching '{query}'.")
            messagebox.showinfo("Not Found", f"No pharmaceutical batch or medicine found matching:\n'{query}'")
            return

        self.current_trace = result
        self.lbl_search_feedback.config(text=f"Trace complete for Batch {result['metrics']['batch_number']}.")
        self._render_trace(result)

    def _render_trace(self, data: Dict[str, Any]) -> None:
        """Populates all panels and cards with traced data."""
        med = data["medicine"]
        metrics = data["metrics"]
        backward = data["backward_trace"]
        forward = data["forward_trace"]

        # 1. Update KPI row
        self.kpi_cards["batch"].config(text=metrics["batch_number"])
        self.kpi_cards["received"].config(text=f"{metrics['total_received']} units")
        self.kpi_cards["stock"].config(text=f"{metrics['current_stock']} units")
        self.kpi_cards["dispensed"].config(text=f"{metrics['total_sold']} units")
        self.kpi_cards["exposed"].config(text=f"{metrics['patients_affected_count']} patients")

        # 2. Update Backward Traceability (Supplier)
        if backward:
            primary_po = backward[0]
            self.lbl_supp_name.config(text=primary_po.get("supplier_name", "N/A"), fg=settings.THEME["PRIMARY"], font=(settings.THEME["FONT_FAMILY"], 8, "bold"))
            self.lbl_supp_po.config(text=f"{primary_po.get('purchase_invoice_number', 'N/A')} ({primary_po.get('payment_status', 'N/A')})")
            self.lbl_supp_date.config(text=str(primary_po.get("purchase_date", "N/A"))[:19])
            
            unit_cost = primary_po.get("cost_price", 0.0)
            self.lbl_supp_qty.config(text=f"{primary_po.get('received_quantity', 0)} units @ {settings.CURRENCY_SYMBOL} {unit_cost:.2f}")
            self.lbl_supp_contact.config(text=f"{primary_po.get('supplier_contact', 'N/A')} (Ph: {primary_po.get('supplier_phone', 'N/A')})")
            self.lbl_supp_rec_by.config(text=str(primary_po.get("received_by_user", "Authorized Staff")))
        else:
            self.lbl_supp_name.config(text="No Inbound PO Logged", fg=settings.THEME["TEXT_MUTED"])
            self.lbl_supp_po.config(text="N/A")
            self.lbl_supp_date.config(text="N/A")
            self.lbl_supp_qty.config(text="0 units")
            self.lbl_supp_contact.config(text="N/A")
            self.lbl_supp_rec_by.config(text="N/A")

        # 3. Update Current Inventory Status
        self.lbl_med_name.config(text=f"{med.get('name', 'N/A')} [ID: {med.get('medicine_id')}]", font=(settings.THEME["FONT_FAMILY"], 8, "bold"))
        self.lbl_generic.config(text=med.get("generic_name") or "Standard Formulation")
        self.lbl_category.config(text=f"{med.get('category_name', 'General')} | Unit: {med.get('unit', 'Strips')}")
        self.lbl_storage.config(text=med.get("storage_condition") or "Room Temperature (15-25°C)")
        
        # Expiry status with badge styling
        exp_txt = f"{med.get('expiry_date')} — {med.get('expiry_status')}"
        self.lbl_expiry.config(text=exp_txt, fg=med.get("expiry_color", settings.THEME["TEXT_MAIN"]), font=(settings.THEME["FONT_FAMILY"], 8, "bold"))

        # Mass Balance Six Sigma Check
        if metrics["is_balanced"]:
            mb_txt = f"BALANCED (Rcvd: {metrics['total_received']} = Sold: {metrics['total_sold']} + Stock: {metrics['current_stock']})"
            mb_fg = "#2e7d32"
        else:
            mb_txt = f"DISCREPANCY (Delta: {metrics['mass_balance_delta']:+d} units unaccounted)"
            mb_fg = "#d32f2f"
        self.lbl_mass_balance.config(text=mb_txt, fg=mb_fg, font=(settings.THEME["FONT_FAMILY"], 8, "bold"))

        # 4. Update Forward Traceability (Sales distribution table)
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)

        for s in forward:
            self.sales_tree.insert(
                "",
                tk.END,
                values=(
                    s.get("sale_invoice_number"),
                    str(s.get("sale_date"))[:19],
                    s.get("customer_name"),
                    s.get("customer_phone"),
                    s.get("quantity_sold"),
                    f"{settings.CURRENCY_SYMBOL} {s.get('unit_price', 0):.2f}",
                    f"{settings.CURRENCY_SYMBOL} {s.get('total_price', 0):.2f}",
                    s.get("dispensed_by")
                )
            )

        self.lbl_sales_summary.config(
            text=f"Total {len(forward)} dispensing sales transactions | {metrics['total_sold']} units dispensed to {metrics['patients_affected_count']} distinct patients."
        )

    def _export_recall_list(self) -> None:
        """Exports the customer recall contact list to CSV for regulatory compliance."""
        if not self.current_trace:
            messagebox.showwarning("No Batch Selected", "Please trace a batch first before exporting a recall list.")
            return

        batch_no = self.current_trace["metrics"]["batch_number"]
        med_name = self.current_trace["metrics"]["medicine_name"]
        forward = self.current_trace["forward_trace"]

        if not forward:
            messagebox.showinfo(
                "Zero Exposure",
                f"Batch {batch_no} ({med_name}) has not been dispensed to any customers.\nNo patient recall notifications required."
            )
            return

        csv_content = self.service.generate_recall_csv(self.current_trace)

        # Allow user to save file or copy to clipboard
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"RECALL_BATCH_{batch_no}.csv",
            title="Save Emergency Batch Recall Patient Notification List"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                messagebox.showinfo(
                    "Recall Export Successful",
                    f"Batch recall notification manifest exported successfully to:\n{file_path}\n\n"
                    f"Total Affected Patients: {self.current_trace['metrics']['patients_affected_count']}\n"
                    f"Total Invoices: {len(forward)}"
                )
            except Exception as exc:
                messagebox.showerror("Export Failed", f"Failed to save CSV file:\n{str(exc)}")
        else:
            # Also copy to clipboard as convenient fallback
            self.clipboard_clear()
            self.clipboard_append(csv_content)
            messagebox.showinfo(
                "Copied to Clipboard",
                f"Batch recall CSV manifest for {batch_no} ({len(forward)} records) has been copied to your clipboard."
            )

    def destroy(self) -> None:
        """Ensures clean widget disposal without lingering ghost frames."""
        for child in list(self.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass
        super().destroy()
