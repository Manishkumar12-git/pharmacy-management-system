"""
================================================================================
Pharmacy Management System - In-App Help & Searchable FAQ Screen [Q10 Feature]
================================================================================
Module: pharmacy_management.ui.help_faq
Quality Objective: Q10 - Improve Documentation & User Self-Sufficiency

Description:
    Implements a searchable knowledge center inside the desktop application:
      - Interactive search over categorized FAQs and Poka-Yoke error codes.
      - Integrated markdown viewer for the complete End-User Operations Manual.
      - Rapid keyboard shortcuts reference card.
    Directly satisfies Quality Goal Q10: Improve Documentation.
================================================================================
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, List
from pharmacy_management.config import settings
from pharmacy_management.services.help_service import help_service


class HelpFaqView(ttk.Frame):
    """Knowledge base, searchable FAQ, and documentation browser view."""

    def __init__(self, parent: tk.Widget):
        """Initializes searchable help center and loads FAQ knowledge base."""
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self._load_faqs()

    def _init_ui(self) -> None:
        # Header Bar
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Knowledge Center & In-App Help [TQM Q10]",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar,
            text=f"Quality Objective: {settings.TQM_OBJECTIVE}",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.RIGHT)

        # Tabbed Notebook (FAQs, User Manual, Keyboard Shortcuts)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Tab 1: Searchable FAQ
        self.tab_faq = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_faq, text="🔍 Searchable FAQs & Error Codes")
        self._init_faq_tab()

        # Tab 2: User Manual
        self.tab_manual = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_manual, text="📖 End-User Operations Manual")
        self._init_manual_tab()

        # Tab 3: Shortcuts
        self.tab_shortcuts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_shortcuts, text="⌨️ Keyboard Shortcuts Reference")
        self._init_shortcuts_tab()

    def _init_faq_tab(self) -> None:
        """Constructs interactive FAQ search, category filter, and answer pane."""
        search_strip = tk.Frame(self.tab_faq, bg=settings.THEME["SURFACE"], padx=15, pady=10)
        search_strip.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_strip,
            text="Search Help:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.ent_faq_query = ttk.Entry(search_strip, width=32, font=(settings.THEME["FONT_FAMILY"], 9))
        self.ent_faq_query.pack(side=tk.LEFT, padx=(0, 15))
        self.ent_faq_query.bind("<KeyRelease>", lambda _: self._load_faqs())

        tk.Label(
            search_strip,
            text="Category:",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["SURFACE"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.combo_faq_cat = ttk.Combobox(search_strip, state="readonly", width=26)
        self.combo_faq_cat.pack(side=tk.LEFT, padx=(0, 15))

        cats = ["All Categories"] + help_service.get_categories()
        self.combo_faq_cat["values"] = cats
        self.combo_faq_cat.current(0)
        self.combo_faq_cat.bind("<<ComboboxSelected>>", lambda _: self._load_faqs())

        # Split Body (List on Left, Answer on Right)
        split_body = tk.Frame(self.tab_faq, bg=settings.THEME["BACKGROUND"])
        split_body.pack(fill=tk.BOTH, expand=True)

        # Questions List (Left)
        left_pane = tk.Frame(split_body, bg=settings.THEME["SURFACE"], width=380)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_pane.pack_propagate(False)

        tk.Label(
            left_pane,
            text="Frequently Asked Questions",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            bg=settings.THEME["SURFACE"],
            padx=10,
            pady=8
        ).pack(anchor="w")

        self.tree_faqs = ttk.Treeview(left_pane, columns=("id", "question"), show="headings", selectmode="browse")
        self.tree_faqs.heading("id", text="Code")
        self.tree_faqs.heading("question", text="Question / Topic")
        self.tree_faqs.column("id", width=70, anchor="center")
        self.tree_faqs.column("question", width=290)

        faq_scroll = ttk.Scrollbar(left_pane, orient=tk.VERTICAL, command=self.tree_faqs.yview)
        self.tree_faqs.configure(yscrollcommand=faq_scroll.set)
        self.tree_faqs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        faq_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_faqs.bind("<<TreeviewSelect>>", self._on_faq_select)

        # Answer Viewer (Right)
        right_pane = tk.Frame(split_body, bg=settings.THEME["SURFACE"], padx=15, pady=12)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.lbl_ans_title = tk.Label(
            right_pane,
            text="Select a question from the list to view detailed resolution.",
            font=(settings.THEME["FONT_FAMILY"], 11, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"],
            wraplength=480,
            justify=tk.LEFT
        )
        self.lbl_ans_title.pack(anchor="w", pady=(0, 6))

        self.lbl_ans_cat = tk.Label(
            right_pane,
            text="",
            font=(settings.THEME["FONT_FAMILY"], 8, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        )
        self.lbl_ans_cat.pack(anchor="w", pady=(0, 10))

        self.txt_ans = tk.Text(
            right_pane,
            wrap=tk.WORD,
            font=(settings.THEME["FONT_FAMILY"], 10),
            bg=settings.THEME["SURFACE_ALT"],
            relief=tk.FLAT,
            padx=12,
            pady=12
        )
        self.txt_ans.pack(fill=tk.BOTH, expand=True)

    def _load_faqs(self) -> None:
        for itm in self.tree_faqs.get_children():
            self.tree_faqs.delete(itm)

        q = self.ent_faq_query.get().strip()
        cat = self.combo_faq_cat.get()

        self.displayed_faqs = help_service.search_faqs(query=q, category=cat)
        for idx, f in enumerate(self.displayed_faqs):
            self.tree_faqs.insert("", tk.END, values=(f.get("id", f"FAQ-{idx}"), f["question"]))

    def _on_faq_select(self, event: Any) -> None:
        sel = self.tree_faqs.selection()
        if not sel:
            return
        idx = self.tree_faqs.index(sel[0])
        faq = self.displayed_faqs[idx]

        self.lbl_ans_title.config(text=f"[{faq.get('id', 'FAQ')}] {faq['question']}")
        tags_str = ", ".join(faq.get("tags", []))
        self.lbl_ans_cat.config(text=f"Category: {faq.get('category')} | Tags: {tags_str} | Importance: {faq.get('importance', 'Normal')}")

        self.txt_ans.config(state="normal")
        self.txt_ans.delete("1.0", tk.END)
        self.txt_ans.insert("1.0", faq["answer"])
        self.txt_ans.config(state="disabled")

    def _init_manual_tab(self) -> None:
        """Constructs markdown manual reader with scrollbar."""
        pad = tk.Frame(self.tab_manual, bg=settings.THEME["SURFACE"], padx=15, pady=12)
        pad.pack(fill=tk.BOTH, expand=True)

        manual_text = help_service.get_user_manual_content()

        txt = tk.Text(
            pad,
            wrap=tk.WORD,
            font=(settings.THEME["FONT_FAMILY"], 10),
            bg=settings.THEME["SURFACE"],
            padx=15,
            pady=15
        )
        scroll = ttk.Scrollbar(pad, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)

        txt.insert("1.0", manual_text)
        txt.configure(state="disabled")

        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _init_shortcuts_tab(self) -> None:
        """Constructs keyboard shortcuts sheet."""
        pad = tk.Frame(self.tab_shortcuts, bg=settings.THEME["SURFACE"], padx=20, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            pad,
            text="Global System Keyboard Accelerators",
            font=(settings.THEME["FONT_FAMILY"], 12, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        ).pack(anchor="w", pady=(0, 10))

        tree = ttk.Treeview(pad, columns=("key", "action", "scope"), show="headings", height=8)
        tree.heading("key", text="Shortcut Key")
        tree.heading("action", text="Action Performed")
        tree.heading("scope", text="Context Scope")

        tree.column("key", width=140, anchor="center")
        tree.column("action", width=340)
        tree.column("scope", width=160, anchor="center")

        shortcuts = help_service.get_keyboard_shortcuts()
        for sc in shortcuts:
            tree.insert("", tk.END, values=(sc["key"], sc["action"], sc["scope"]))

        tree.pack(fill=tk.BOTH, expand=True)
