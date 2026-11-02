"""
================================================================================
Pharmacy Management System - Automated FMEA Dashboard View
================================================================================
Module: pharmacy_management.ui.fmea_dashboard
Quality Objective: Total Quality Management (TQM) & Six Sigma Risk Prioritization

Description:
    Renders the Failure Mode and Effects Analysis (FMEA) dashboard.
    Visualizes the Risk Priority Number (RPN = S x O x D) for pharmacy processes,
    computes Occurrence dynamically from live error/poka-yoke logs, and allows
    interactive adjustment of Severity and Detection weights.
    Zero direct SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
from pharmacy_management.config import settings
from pharmacy_management.services.fmea_service import fmea_service
from pharmacy_management.models.user import User


class FMEADashboardView(ttk.Frame):
    """View governing automated FMEA risk analysis and live RPN calculation."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes FMEA dashboard view.

        Args:
            parent (tk.Widget): Parent container.
            user (User): Active operator account.
        """
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self.selected_mode: Optional[Dict[str, Any]] = None
        self.current_filter = "ALL"

        self._init_ui()
        self.load_fmea_data()

    def _init_ui(self) -> None:
        """Constructs layout components: Header, KPI cards, table, and adjustment panel."""
        # Top Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        title_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        title_box.pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="🛡️ Automated FMEA Risk Analysis Dashboard",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Dynamic Risk Priority Number (RPN = S × O × D) based on live error & Poka-Yoke logs",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(anchor="w")

        btn_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(side=tk.RIGHT)

        tk.Button(
            btn_box,
            text="🔄 Refresh Live Logs",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.load_fmea_data
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_box,
            text="📥 Export FMEA to CSV",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._handle_export_csv
        ).pack(side=tk.LEFT, padx=5)

        # KPI Summary Cards Ribbon
        self.kpi_frame = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=4)
        self.kpi_frame.pack(fill=tk.X)

        self.kpi_widgets: Dict[str, tk.Label] = {}
        self._build_kpi_cards()

        # Filter Strip
        filter_strip = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=8)
        filter_strip.pack(fill=tk.X, padx=20, pady=(6, 8))

        tk.Label(
            filter_strip,
            text="Filter by Risk Priority:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.combo_filter = ttk.Combobox(
            filter_strip,
            state="readonly",
            values=["All Failure Modes", "High Risk (RPN >= 200 or S >= 9)", "Medium Risk (100 <= RPN < 200)", "Low Risk (RPN < 100)"],
            width=36
        )
        self.combo_filter.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_filter.current(0)
        self.combo_filter.bind("<<ComboboxSelected>>", lambda _: self._on_filter_changed())

        tk.Label(
            filter_strip,
            text="Formula: RPN = Severity (1–10) × Occurrence (Live 1–10) × Detection (1–10)",
            font=(settings.THEME["FONT_FAMILY"], 8, "italic"),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.RIGHT)

        # Main Table Container
        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        cols = ("id", "name", "step", "s", "o", "d", "rpn", "risk", "events", "control")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8, selectmode="browse")

        self.tree.heading("id", text="Mode ID")
        self.tree.heading("name", text="Potential Failure Mode")
        self.tree.heading("step", text="Process Step")
        self.tree.heading("s", text="S")
        self.tree.heading("o", text="O (Live)")
        self.tree.heading("d", text="D")
        self.tree.heading("rpn", text="RPN")
        self.tree.heading("risk", text="Risk Level")
        self.tree.heading("events", text="Incidents")
        self.tree.heading("control", text="Current Poka-Yoke Controls")

        self.tree.column("id", width=65, anchor="center")
        self.tree.column("name", width=220)
        self.tree.column("step", width=180)
        self.tree.column("s", width=35, anchor="center")
        self.tree.column("o", width=55, anchor="center")
        self.tree.column("d", width=35, anchor="center")
        self.tree.column("rpn", width=60, anchor="center")
        self.tree.column("risk", width=85, anchor="center")
        self.tree.column("events", width=65, anchor="center")
        self.tree.column("control", width=300)

        # Tag configurations for color-coded risk display
        self.tree.tag_configure("HIGH", background="#fee2e2", foreground="#991b1b")
        self.tree.tag_configure("MEDIUM", background="#fef3c7", foreground="#92400e")
        self.tree.tag_configure("LOW", background="#f0fdf4", foreground="#166534")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_mode_selected)

        # Bottom Interactive Weight Adjustment & Mitigation Card
        self.detail_card = tk.LabelFrame(
            self,
            text=" Failure Mode Parameter Adjustment & Mitigation Controls ",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"],
            padx=18,
            pady=10
        )
        self.detail_card.pack(fill=tk.X, padx=20, pady=(0, 15))

        self._build_adjustment_panel()

    def _build_kpi_cards(self) -> None:
        """Builds top metric indicator cards."""
        card_specs = [
            ("TOTAL_MODES", "FAILURE MODES", "0", "Evaluated in Pharmacy Process", settings.THEME["PRIMARY"]),
            ("HIGH_RISK", "HIGH RISK (RPN >= 200)", "0", "Immediate Mitigation Required", settings.THEME["DANGER"]),
            ("MED_RISK", "MEDIUM RISK", "0", "Monitored with Controls", settings.THEME["WARNING"]),
            ("LOW_RISK", "LOW RISK", "0", "Safeguarded by Poka-Yoke", settings.THEME["SUCCESS"]),
            ("AVG_RPN", "AVERAGE RPN", "0.0", "System Aggregate Risk Score", settings.THEME["SECONDARY"]),
        ]

        for key, title, val, sub, col in card_specs:
            box = tk.Frame(
                self.kpi_frame,
                bg=settings.THEME["SURFACE"],
                highlightbackground=settings.THEME["BORDER_LIGHT"],
                highlightthickness=1,
                padx=14,
                pady=10
            )
            box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

            tk.Label(box, text=title, font=(settings.THEME["FONT_FAMILY"], 8, "bold"), fg=col, bg=settings.THEME["SURFACE"]).pack(anchor="w")
            lbl_val = tk.Label(box, text=val, font=(settings.THEME["FONT_FAMILY"], 15, "bold"), fg=settings.THEME["TEXT_MAIN"], bg=settings.THEME["SURFACE"])
            lbl_val.pack(anchor="w", pady=(1, 0))
            tk.Label(box, text=sub, font=(settings.THEME["FONT_FAMILY"], 7), fg=settings.THEME["TEXT_MUTED"], bg=settings.THEME["SURFACE"]).pack(anchor="w")

            self.kpi_widgets[key] = lbl_val

    def _build_adjustment_panel(self) -> None:
        """Constructs interactive weight adjusters and effect description."""
        top_info = tk.Frame(self.detail_card, bg=settings.THEME["SURFACE"])
        top_info.pack(fill=tk.X, pady=(0, 8))

        self.lbl_selected_title = tk.Label(
            top_info,
            text="Select any failure mode from the table above to adjust Severity (S) or Detection (D) ratings.",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_selected_title.pack(anchor="w")

        self.lbl_selected_effect = tk.Label(
            top_info,
            text="Potential Clinical Effect: - | Recommended Action: -",
            font=(settings.THEME["FONT_FAMILY"], 8),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"],
            wraplength=950,
            justify=tk.LEFT
        )
        self.lbl_selected_effect.pack(anchor="w", pady=(2, 0))

        # Controls Row
        ctrl_row = tk.Frame(self.detail_card, bg=settings.THEME["SURFACE"])
        ctrl_row.pack(fill=tk.X)

        # Severity Spinbox
        tk.Label(ctrl_row, text="Severity (S: 1–10):", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT, padx=(0, 4))
        self.spin_s = tk.Spinbox(ctrl_row, from_=1, to=10, width=4, font=(settings.THEME["FONT_FAMILY"], 9), command=self._recalculate_preview_rpn)
        self.spin_s.pack(side=tk.LEFT, padx=(0, 15))
        self.spin_s.bind("<KeyRelease>", lambda _: self._recalculate_preview_rpn())

        # Occurrence Display (Fixed live from database)
        tk.Label(ctrl_row, text="Occurrence (O: Live):", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT, padx=(0, 4))
        self.lbl_o_val = tk.Label(ctrl_row, text="1", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), fg=settings.THEME["PRIMARY"], bg=settings.THEME["SURFACE_ALT"], width=4, relief=tk.SOLID, bd=1)
        self.lbl_o_val.pack(side=tk.LEFT, padx=(0, 15))

        # Detection Spinbox
        tk.Label(ctrl_row, text="Detection (D: 1–10):", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT, padx=(0, 4))
        self.spin_d = tk.Spinbox(ctrl_row, from_=1, to=10, width=4, font=(settings.THEME["FONT_FAMILY"], 9), command=self._recalculate_preview_rpn)
        self.spin_d.pack(side=tk.LEFT, padx=(0, 15))
        self.spin_d.bind("<KeyRelease>", lambda _: self._recalculate_preview_rpn())

        # Calculated Live RPN Badge
        tk.Label(ctrl_row, text="Projected RPN:", font=(settings.THEME["FONT_FAMILY"], 9, "bold"), bg=settings.THEME["SURFACE"]).pack(side=tk.LEFT, padx=(0, 4))
        self.lbl_preview_rpn = tk.Label(ctrl_row, text="-", font=(settings.THEME["FONT_FAMILY"], 11, "bold"), fg=settings.THEME["TEXT_MAIN"], bg=settings.THEME["SURFACE_ALT"], width=8, relief=tk.SOLID, bd=1)
        self.lbl_preview_rpn.pack(side=tk.LEFT, padx=(0, 20))

        # Action Buttons
        tk.Button(
            ctrl_row,
            text="💾 Save Weight Changes",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._handle_apply_weights
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            ctrl_row,
            text="↩ Reset Mode",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._handle_reset_weights
        ).pack(side=tk.LEFT, padx=5)

    def load_fmea_data(self) -> None:
        """Queries FMEAService to refresh KPI cards and table matrix."""
        # 1. Update KPIs
        kpis = fmea_service.get_fmea_kpis()
        self.kpi_widgets["TOTAL_MODES"].config(text=str(kpis["total_modes"]))
        self.kpi_widgets["HIGH_RISK"].config(text=str(kpis["high_risk_count"]))
        self.kpi_widgets["MED_RISK"].config(text=str(kpis["medium_risk_count"]))
        self.kpi_widgets["LOW_RISK"].config(text=str(kpis["low_risk_count"]))
        self.kpi_widgets["AVG_RPN"].config(text=str(kpis["average_rpn"]))

        # 2. Populate Treeview Table
        for item in self.tree.get_children():
            self.tree.delete(item)

        matrix = fmea_service.get_fmea_matrix()
        self.full_matrix = matrix

        # Apply Risk Level Filter
        filter_val = self.combo_filter.get()
        if "High Risk" in filter_val:
            filtered = [m for m in matrix if m["risk_level"] == "HIGH"]
        elif "Medium Risk" in filter_val:
            filtered = [m for m in matrix if m["risk_level"] == "MEDIUM"]
        elif "Low Risk" in filter_val:
            filtered = [m for m in matrix if m["risk_level"] == "LOW"]
        else:
            filtered = matrix

        for m in filtered:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    m["mode_id"],
                    m["name"],
                    m["process_step"],
                    m["severity"],
                    m["occurrence"],
                    m["detection"],
                    m["rpn"],
                    m["risk_level"],
                    m["live_events"],
                    m["poka_yoke_control"]
                ),
                tags=(m["risk_level"],)
            )

    def _on_filter_changed(self) -> None:
        """Callback when user selects a different risk filter."""
        self.load_fmea_data()

    def _on_mode_selected(self, event: Any) -> None:
        """Loads selected failure mode details into the parameter adjustment panel."""
        sel = self.tree.selection()
        if not sel:
            return
        item_vals = self.tree.item(sel[0], "values")
        mode_id = item_vals[0]

        # Find matching mode dict
        mode = next((m for m in self.full_matrix if m["mode_id"] == mode_id), None)
        if not mode:
            return

        self.selected_mode = mode

        # Update Header & Description
        self.lbl_selected_title.config(text=f"[{mode['mode_id']}] {mode['name']} ({mode['category']})")
        self.lbl_selected_effect.config(
            text=f"Potential Clinical Effect: {mode['potential_effect']}\nRecommended Action: {mode['recommended_action']}"
        )

        # Set Spinboxes
        self.spin_s.delete(0, tk.END)
        self.spin_s.insert(0, str(mode["severity"]))

        self.lbl_o_val.config(text=str(mode["occurrence"]))

        self.spin_d.delete(0, tk.END)
        self.spin_d.insert(0, str(mode["detection"]))

        self._recalculate_preview_rpn()

    def _recalculate_preview_rpn(self) -> None:
        """Live updates projected RPN badge based on current spinbox inputs."""
        try:
            s = int(self.spin_s.get().strip())
            d = int(self.spin_d.get().strip())
            o = int(self.lbl_o_val.cget("text").strip())

            s = max(1, min(10, s))
            d = max(1, min(10, d))
            rpn = s * o * d

            color = "#dc2626" if (rpn >= 200 or s >= 9) else ("#d97706" if rpn >= 100 else "#16a34a")
            self.lbl_preview_rpn.config(text=f"{rpn}", fg=color)
        except Exception:
            self.lbl_preview_rpn.config(text="-")

    def _handle_apply_weights(self) -> None:
        """Saves user customized weights via FMEAService."""
        if not self.selected_mode:
            messagebox.showwarning("Selection Required", "Please select a failure mode from the table first.")
            return

        try:
            s = int(self.spin_s.get().strip())
            d = int(self.spin_d.get().strip())
            mode_id = self.selected_mode["mode_id"]

            fmea_service.update_mode_parameters(mode_id, s, d)
            self.load_fmea_data()
            messagebox.showinfo("Parameters Updated", f"FMEA weights for {mode_id} updated. RPN recalculated.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Severity and Detection must be integers between 1 and 10.")

    def _handle_reset_weights(self) -> None:
        """Resets custom weights to standard baseline."""
        if not self.selected_mode:
            return
        mode_id = self.selected_mode["mode_id"]
        fmea_service.reset_mode_parameters(mode_id)
        self.load_fmea_data()
        messagebox.showinfo("Reset Complete", f"Failure mode {mode_id} reset to standard baseline ratings.")

    def _handle_export_csv(self) -> None:
        """Exports FMEA matrix to CSV."""
        csv_text = fmea_service.export_fmea_csv()
        self.clipboard_clear()
        self.clipboard_append(csv_text)
        messagebox.showinfo("Export Successful", "Live FMEA matrix exported to CSV and copied to clipboard.")

