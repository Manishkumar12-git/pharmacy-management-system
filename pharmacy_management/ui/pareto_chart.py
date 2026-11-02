"""
================================================================================
Pharmacy Management System - Interactive Pareto Chart Generator View
================================================================================
Module: pharmacy_management.ui.pareto_chart
Quality Objective: Total Quality Management (TQM) & Six Sigma Defect Prioritization

Description:
    Renders an interactive, canvas-based Pareto bar and cumulative line chart.
    Visualizes the 80/20 rule for pharmacy defects, displays an 80% reference
    threshold, provides dynamic insight explanations, and lists full tabular
    cumulative breakdowns.
    Zero direct SQL executed in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
from pharmacy_management.config import settings
from pharmacy_management.reports.pareto_report import pareto_report
from pharmacy_management.models.user import User


class ParetoChartView(ttk.Frame):
    """View rendering interactive Pareto dual-axis defect chart and 80/20 distribution."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes Pareto chart view.

        Args:
            parent (tk.Widget): Parent frame container.
            user (User): Authenticated operator account.
        """
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self.current_days_filter: Optional[int] = None
        self.pareto_data: Dict[str, Any] = {}

        self._init_ui()
        self.load_pareto_chart()

    def _init_ui(self) -> None:
        """Constructs layout: Header, filter toolbar, dual-axis canvas, and insight card."""
        # Top Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        title_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        title_box.pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="📊 Six Sigma Pareto Defect Distribution (80/20 Rule)",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Identify the 'Vital Few' defect categories that account for 80% of operational pharmacy blocks",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(anchor="w")

        btn_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(side=tk.RIGHT)

        tk.Button(
            btn_box,
            text="🔄 Refresh Analysis",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.load_pareto_chart
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_box,
            text="📥 Export to CSV",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._handle_export_csv
        ).pack(side=tk.LEFT, padx=5)

        # Filter Strip
        filter_strip = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=8)
        filter_strip.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            filter_strip,
            text="Operational Time Horizon:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.combo_window = ttk.Combobox(
            filter_strip,
            state="readonly",
            values=["All Time Records", "Past 90 Days", "Past 30 Days", "Past 7 Days", "Today Only"],
            width=22
        )
        self.combo_window.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_window.current(0)
        self.combo_window.bind("<<ComboboxSelected>>", lambda _: self._on_window_changed())

        self.lbl_stats = tk.Label(
            filter_strip,
            text="Total Defects: 0 | Categories: 0 | Vital Few: 0",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_stats.pack(side=tk.RIGHT)

        # Scrollable Body Container (Canvas + Insight Card + Tabular breakdown)
        outer_container = tk.Frame(self, bg=settings.THEME["BACKGROUND"])
        outer_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # 1. Dual-Axis Pareto Canvas
        canvas_card = tk.Frame(
            outer_container,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=10,
            pady=8
        )
        canvas_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.canvas = tk.Canvas(
            canvas_card,
            bg="#ffffff",
            height=280,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw_chart())

        # 2. Six Sigma Pareto Insight Text Box
        self.insight_box = tk.Frame(
            outer_container,
            bg="#f0fdf4",
            highlightbackground="#86efac",
            highlightthickness=1,
            padx=15,
            pady=10
        )
        self.insight_box.pack(fill=tk.X, pady=(0, 10))

        self.lbl_insight = tk.Label(
            self.insight_box,
            text="Loading Pareto defect analysis...",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg="#14532d",
            bg="#f0fdf4",
            justify=tk.LEFT,
            wraplength=960
        )
        self.lbl_insight.pack(anchor="w")

        # 3. Tabular Breakdown Table
        table_card = tk.Frame(
            outer_container,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER_LIGHT"],
            highlightthickness=1,
            padx=12,
            pady=8
        )
        table_card.pack(fill=tk.X)

        tk.Label(
            table_card,
            text="Defect Distribution & Cumulative Breakdown Matrix",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 6))

        cols = ("rank", "code", "label", "count", "pct", "cum_count", "cum_pct", "class")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", height=5)

        self.tree.heading("rank", text="Rank")
        self.tree.heading("code", text="Error Code")
        self.tree.heading("label", text="Failure Category Description")
        self.tree.heading("count", text="Frequency")
        self.tree.heading("pct", text="Share (%)")
        self.tree.heading("cum_count", text="Cum. Count")
        self.tree.heading("cum_pct", text="Cum. %")
        self.tree.heading("class", text="Six Sigma Classification")

        self.tree.column("rank", width=50, anchor="center")
        self.tree.column("code", width=180)
        self.tree.column("label", width=220)
        self.tree.column("count", width=75, anchor="center")
        self.tree.column("pct", width=75, anchor="center")
        self.tree.column("cum_count", width=85, anchor="center")
        self.tree.column("cum_pct", width=85, anchor="center")
        self.tree.column("class", width=160, anchor="center")

        self.tree.tag_configure("VITAL", background="#fee2e2", foreground="#991b1b")
        self.tree.tag_configure("USEFUL", background="#ffffff", foreground="#334155")

        self.tree.pack(fill=tk.X)

    def _on_window_changed(self) -> None:
        """Handles timeframe dropdown selection change."""
        sel = self.combo_window.get()
        if "90" in sel:
            self.current_days_filter = 90
        elif "30" in sel:
            self.current_days_filter = 30
        elif "7" in sel:
            self.current_days_filter = 7
        elif "Today" in sel:
            self.current_days_filter = 1
        else:
            self.current_days_filter = None

        self.load_pareto_chart()

    def load_pareto_chart(self) -> None:
        """Fetches data from pareto_report and redraws chart and table."""
        self.pareto_data = pareto_report.get_pareto_data(self.current_days_filter)

        # Update stats
        self.lbl_stats.config(
            text=(
                f"Total Incidents: {self.pareto_data['total_defects']} | "
                f"Defect Categories: {self.pareto_data['categories_count']} | "
                f"Vital Few (<=80%): {self.pareto_data['vital_few_count']}"
            )
        )

        # Update Insight Text
        self.lbl_insight.config(text=self.pareto_data["insight_text"])

        # Populate Table
        for item in self.tree.get_children():
            self.tree.delete(item)

        for itm in self.pareto_data.get("items", []):
            tag = "VITAL" if itm["is_vital_few"] else "USEFUL"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    f"#{itm['rank']}",
                    itm["error_code"],
                    itm["label"],
                    itm["frequency"],
                    f"{itm['individual_pct']:.1f}%",
                    itm["cumulative_frequency"],
                    f"{itm['cumulative_pct']:.1f}%",
                    itm["classification"]
                ),
                tags=(tag,)
            )

        # Draw Canvas Chart
        self._draw_chart()

    def _draw_chart(self) -> None:
        """Draws the dual-axis Pareto bar chart, cumulative curve, and 80% line on canvas."""
        self.canvas.delete("all")

        items = self.pareto_data.get("items", [])
        if not items:
            w = self.canvas.winfo_width() or 600
            h = self.canvas.winfo_height() or 240
            self.canvas.create_text(
                w / 2, h / 2,
                text="Zero defects recorded for the selected timeframe. All processes 100% compliant.",
                font=(settings.THEME["FONT_FAMILY"], 11, "italic"),
                fill="#64748b"
            )
            return

        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 260

        # Margins
        margin_left = 60
        margin_right = 65
        margin_top = 35
        margin_bottom = 60

        plot_w = max(100, w - margin_left - margin_right)
        plot_h = max(80, h - margin_top - margin_bottom)

        y_zero = margin_top + plot_h

        # Calculate Scales
        max_freq = max(item["frequency"] for item in items)
        # Round max_freq up to clean tick
        if max_freq <= 5:
            axis_max_freq = 5
        elif max_freq <= 10:
            axis_max_freq = 10
        elif max_freq <= 25:
            axis_max_freq = 25
        elif max_freq <= 50:
            axis_max_freq = 50
        else:
            axis_max_freq = ((max_freq // 20) + 1) * 20

        # 1. Draw Grid Lines and Y-Axes
        # Left Y-Axis (Frequency)
        num_y_ticks = 5
        for i in range(num_y_ticks + 1):
            val = int(axis_max_freq * (i / num_y_ticks))
            y_pos = y_zero - (i / num_y_ticks) * plot_h

            # Subtle grid line
            self.canvas.create_line(margin_left, y_pos, margin_left + plot_w, y_pos, fill="#f1f5f9", width=1)

            # Left Y Tick & Label
            self.canvas.create_line(margin_left - 4, y_pos, margin_left, y_pos, fill="#64748b")
            self.canvas.create_text(margin_left - 8, y_pos, text=str(val), font=(settings.THEME["FONT_FAMILY"], 8), anchor="e", fill="#475569")

            # Right Y Tick & Label (Percentage: 0% to 100%)
            pct_val = int(100 * (i / num_y_ticks))
            self.canvas.create_line(margin_left + plot_w, y_pos, margin_left + plot_w + 4, y_pos, fill="#d97706")
            self.canvas.create_text(margin_left + plot_w + 8, y_pos, text=f"{pct_val}%", font=(settings.THEME["FONT_FAMILY"], 8), anchor="w", fill="#d97706")

        # Left Y Axis Line
        self.canvas.create_line(margin_left, margin_top, margin_left, y_zero, fill="#94a3b8", width=1.5)
        # Right Y Axis Line
        self.canvas.create_line(margin_left + plot_w, margin_top, margin_left + plot_w, y_zero, fill="#f59e0b", width=1.5)
        # Baseline X Axis Line
        self.canvas.create_line(margin_left, y_zero, margin_left + plot_w, y_zero, fill="#94a3b8", width=1.5)

        # Axis Titles
        self.canvas.create_text(margin_left - 10, margin_top - 15, text="Frequency", font=(settings.THEME["FONT_FAMILY"], 8, "bold"), fill="#0f766e", anchor="w")
        self.canvas.create_text(margin_left + plot_w + 10, margin_top - 15, text="Cumulative %", font=(settings.THEME["FONT_FAMILY"], 8, "bold"), fill="#d97706", anchor="e")

        # 2. Draw 80% Pareto Reference Line
        y_80 = y_zero - 0.80 * plot_h
        self.canvas.create_line(margin_left, y_80, margin_left + plot_w, y_80, fill="#dc2626", dash=(5, 3), width=2)
        self.canvas.create_text(
            margin_left + plot_w - 6, y_80 - 8,
            text="80% Cutoff (Vital Few)",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            fill="#dc2626",
            anchor="e"
        )

        # 3. Draw Bars and Points
        num_items = len(items)
        slot_w = plot_w / num_items
        bar_pad = max(4, slot_w * 0.15)
        bar_w = slot_w - (2 * bar_pad)

        cum_points = []

        for idx, itm in enumerate(items):
            x_left = margin_left + idx * slot_w + bar_pad
            x_right = x_left + bar_w
            x_center = x_left + bar_w / 2

            # Bar height
            freq = itm["frequency"]
            bar_h = (freq / axis_max_freq) * plot_h
            y_bar_top = y_zero - bar_h

            # Choose bar color (Teal for Vital Few, Muted Slate for Useful Many)
            bar_color = "#0f766e" if itm["is_vital_few"] else "#0284c7"

            # Draw Bar
            self.canvas.create_rectangle(
                x_left, y_bar_top, x_right, y_zero,
                fill=bar_color,
                outline="#042f2e",
                width=1
            )

            # Frequency count text on top of bar
            self.canvas.create_text(
                x_center, y_bar_top - 7,
                text=str(freq),
                font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
                fill="#0f172a"
            )

            # X-Axis Category Label (Abbreviated/wrapped if needed)
            lbl_short = itm["label"]
            if len(lbl_short) > 16:
                lbl_short = lbl_short[:14] + ".."
            self.canvas.create_text(
                x_center, y_zero + 14,
                text=lbl_short,
                font=(settings.THEME["FONT_FAMILY"], 7, "bold"),
                fill="#1e293b",
                anchor="n"
            )

            # Rank tag below label
            self.canvas.create_text(
                x_center, y_zero + 32,
                text=f"#{itm['rank']} ({itm['individual_pct']:.0f}%)",
                font=(settings.THEME["FONT_FAMILY"], 7),
                fill="#64748b",
                anchor="n"
            )

            # Cumulative curve point
            cum_pct = itm["cumulative_pct"]
            y_cum = y_zero - (cum_pct / 100.0) * plot_h
            cum_points.append((x_center, y_cum, cum_pct))

        # 4. Draw Cumulative Line Curve
        for i in range(len(cum_points) - 1):
            p1 = cum_points[i]
            p2 = cum_points[i + 1]
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#d97706", width=2.5)

        # 5. Draw Cumulative Points and Percent Text
        for pt in cum_points:
            cx, cy, cpct = pt
            # Node circle
            r = 4
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#d97706", outline="#ffffff", width=1.5)
            # Label
            self.canvas.create_text(
                cx, cy - 8,
                text=f"{cpct:.0f}%",
                font=(settings.THEME["FONT_FAMILY"], 7, "bold"),
                fill="#b45309"
            )

        # 6. Chart Legend at Top
        legend_x = margin_left + 15
        legend_y = margin_top - 15

        # Bar legend
        self.canvas.create_rectangle(legend_x, legend_y - 4, legend_x + 12, legend_y + 4, fill="#0f766e", outline="")
        self.canvas.create_text(legend_x + 16, legend_y, text="Vital Defect Bar", font=(settings.THEME["FONT_FAMILY"], 7), anchor="w", fill="#475569")

        # Line legend
        self.canvas.create_line(legend_x + 95, legend_y, legend_x + 115, legend_y, fill="#d97706", width=2)
        self.canvas.create_oval(legend_x + 103, legend_y - 2, legend_x + 107, legend_y + 2, fill="#d97706", outline="")
        self.canvas.create_text(legend_x + 120, legend_y, text="Cumulative %", font=(settings.THEME["FONT_FAMILY"], 7), anchor="w", fill="#475569")

    def _handle_export_csv(self) -> None:
        """Exports Pareto dataset to CSV format."""
        csv_text = pareto_report.generate_csv(self.current_days_filter)
        self.clipboard_clear()
        self.clipboard_append(csv_text)
        messagebox.showinfo("Export Complete", "Pareto 80/20 defect matrix copied to system clipboard in CSV format.")

