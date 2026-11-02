"""
================================================================================
Pharmacy Management System - User Authentication Screen
================================================================================
Module: pharmacy_management.ui.login
Quality Objective: Q10 - Improve Documentation & User Experience

Description:
    Renders the modern login screen, provides rapid-fill demo credentials,
    validates non-empty input, and invokes the AuthService downstream.
    Strictly free of SQL queries.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from pharmacy_management.config import settings
from pharmacy_management.services.auth_service import auth_service
from pharmacy_management.models.user import User


class LoginFrame(ttk.Frame):
    """User authentication view providing secure login and role switching."""

    def __init__(self, parent: tk.Widget, on_login_success: Callable[[User], None]):
        """Initializes login view.

        Args:
            parent (tk.Widget): Host container.
            on_login_success (Callable[[User], None]): Callback triggered upon successful authentication.
        """
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()

    def _init_ui(self) -> None:
        """Constructs layout components, cards, and input fields."""
        # Main background container
        self.configure(style="Main.TFrame")

        # Center card container
        card_outer = tk.Frame(self, bg=settings.THEME["BACKGROUND"])
        card_outer.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        card = tk.Frame(
            card_outer,
            bg=settings.THEME["SURFACE"],
            highlightbackground=settings.THEME["BORDER"],
            highlightthickness=1,
            padx=40,
            pady=35
        )
        card.pack()

        # Medical Cross Icon Header
        lbl_icon = tk.Label(
            card,
            text="⚕ PharmaCare Quality PMS",
            font=(settings.THEME["FONT_FAMILY"], 18, "bold"),
            fg=settings.THEME["PRIMARY"],
            bg=settings.THEME["SURFACE"]
        )
        lbl_icon.pack(pady=(0, 4))

        lbl_sub = tk.Label(
            card,
            text=f"Total Quality Management Suite ({settings.TQM_OBJECTIVE})",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        )
        lbl_sub.pack(pady=(0, 25))

        # Username Field
        lbl_user = tk.Label(
            card,
            text="Username",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        )
        lbl_user.pack(anchor="w", pady=(0, 2))

        self.ent_user = ttk.Entry(card, width=32, font=(settings.THEME["FONT_FAMILY"], 10))
        self.ent_user.pack(fill="x", pady=(0, 15))
        self.ent_user.focus_set()

        # Password Field
        lbl_pwd = tk.Label(
            card,
            text="Password",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["SURFACE"]
        )
        lbl_pwd.pack(anchor="w", pady=(0, 2))

        self.ent_pwd = ttk.Entry(card, width=32, show="•", font=(settings.THEME["FONT_FAMILY"], 10))
        self.ent_pwd.pack(fill="x", pady=(0, 20))
        self.ent_pwd.bind("<Return>", lambda _: self._handle_login())

        # Error / Status Banner
        self.lbl_error = tk.Label(
            card,
            text="",
            font=(settings.THEME["FONT_FAMILY"], 9),
            fg=settings.THEME["DANGER"],
            bg=settings.THEME["SURFACE"],
            wraplength=280
        )
        self.lbl_error.pack(fill="x", pady=(0, 10))

        # Sign In Button
        btn_login = tk.Button(
            card,
            text="Sign In to System",
            font=(settings.THEME["FONT_FAMILY"], 10, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            activebackground=settings.THEME["PRIMARY_HOVER"],
            activeforeground=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            pady=8,
            command=self._handle_login
        )
        btn_login.pack(fill="x", pady=(0, 20))

        # Separator for Demo Logins
        sep_frame = tk.Frame(card, bg=settings.THEME["SURFACE"])
        sep_frame.pack(fill="x", pady=(0, 10))
        tk.Label(
            sep_frame,
            text="── Quick-Fill Demo Profiles ──",
            font=(settings.THEME["FONT_FAMILY"], 8),
            fg=settings.THEME["TEXT_MUTED"],
            bg=settings.THEME["SURFACE"]
        ).pack()

        # Demo Fill Buttons
        demo_btn_frame = tk.Frame(card, bg=settings.THEME["SURFACE"])
        demo_btn_frame.pack(fill="x")

        tk.Button(
            demo_btn_frame,
            text="Admin",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.GROOVE,
            cursor="hand2",
            command=lambda: self._set_credentials("admin", "admin123")
        ).pack(side=tk.LEFT, expand=True, fill="x", padx=2)

        tk.Button(
            demo_btn_frame,
            text="Pharmacist",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.GROOVE,
            cursor="hand2",
            command=lambda: self._set_credentials("pharmacist", "pharm123")
        ).pack(side=tk.LEFT, expand=True, fill="x", padx=2)

        tk.Button(
            demo_btn_frame,
            text="Cashier",
            font=(settings.THEME["FONT_FAMILY"], 8),
            bg=settings.THEME["SURFACE_ALT"],
            fg=settings.THEME["TEXT_MAIN"],
            relief=tk.GROOVE,
            cursor="hand2",
            command=lambda: self._set_credentials("cashier", "cash123")
        ).pack(side=tk.LEFT, expand=True, fill="x", padx=2)

    def _set_credentials(self, u: str, p: str) -> None:
        """Pre-fills login credentials for quick testing."""
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, u)
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, p)
        self.lbl_error.config(text="")

    def _handle_login(self) -> None:
        """Gathers input, queries downstream AuthService, and handles outcomes."""
        username = self.ent_user.get().strip()
        password = self.ent_pwd.get().strip()

        if not username or not password:
            self.lbl_error.config(text="Please enter both username and password.")
            return

        success, user, message = auth_service.login(username, password)
        if success and user:
            self.lbl_error.config(text="")
            self.on_login_success(user)
        else:
            self.lbl_error.config(text=message)

