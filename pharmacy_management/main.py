"""
================================================================================
Pharmacy Management System - Main Desktop Application Entry Point
================================================================================
Module: pharmacy_management.main
Quality Objective: Q10 - Improve Documentation & Architectural Compliance

Description:
    Initializes application subsystems (logging, database migrations, security),
    configures desktop visual themes and global keyboard shortcuts, and mounts
    the authentication lifecycle controller.
================================================================================
"""

import sys
import os
from pathlib import Path

# Ensure the root package is in python system path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import ttk, messagebox

from pharmacy_management.config import settings
from pharmacy_management.utils.logger import setup_system_logging, get_logger
from pharmacy_management.database.migrations import initialize_database
from pharmacy_management.database.db import db_manager
from pharmacy_management.models.user import User
from pharmacy_management.ui.login import LoginFrame
from pharmacy_management.ui.dashboard import DashboardShell

logger = get_logger(__name__)


class PharmacyApp:
    """Master application controller governing window state and session flow."""

    def __init__(self, root: tk.Tk):
        """Initializes application subsystems and builds the primary UI container.

        Args:
            root (tk.Tk): Tkinter top-level root window.
        """
        self.root = root
        self.current_user: User = None
        self.current_view = None

        self._configure_window()
        self._configure_ttk_styles()
        self._bind_global_shortcuts()

        # Mount initial view
        self.show_login()

    def _configure_window(self) -> None:
        """Sets application window titles, dimensions, and center alignment."""
        self.root.title(f"{settings.APP_NAME} - {settings.APP_SUBTITLE} (Version {settings.APP_VERSION})")
        self.root.geometry("1180x750")
        self.root.minsize(1000, 680)

        # Center on screen
        self.root.update_idletasks()
        width = 1180
        height = 750
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_ttk_styles(self) -> None:
        """Configures cohesive healthcare theme styles across ttk widgets."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Frame styles
        style.configure("Main.TFrame", background=settings.THEME["BACKGROUND"])
        style.configure("Surface.TFrame", background=settings.THEME["SURFACE"])

        # Treeview styles (clean modern tables with alternating rows)
        style.configure(
            "Treeview",
            background=settings.THEME["SURFACE"],
            foreground=settings.THEME["TEXT_MAIN"],
            rowheight=26,
            fieldbackground=settings.THEME["SURFACE"],
            font=(settings.THEME["FONT_FAMILY"], 9)
        )
        style.configure(
            "Treeview.Heading",
            background=settings.THEME["SURFACE_ALT"],
            foreground=settings.THEME["TEXT_MAIN"],
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", settings.THEME["PRIMARY_LIGHT"])],
            foreground=[("selected", settings.THEME["PRIMARY"])]
        )

        # Notebook tabs
        style.configure(
            "TNotebook.Tab",
            padding=[12, 6],
            font=(settings.THEME["FONT_FAMILY"], 9)
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", settings.THEME["SURFACE"]), ("!selected", settings.THEME["SURFACE_ALT"])],
            foreground=[("selected", settings.THEME["PRIMARY"])]
        )

    def _bind_global_shortcuts(self) -> None:
        """Binds universal keyboard accelerators."""
        self.root.bind("<Control-b>", lambda _: self._navigate_if_logged_in("billing"))
        self.root.bind("<Control-B>", lambda _: self._navigate_if_logged_in("billing"))
        self.root.bind("<Control-m>", lambda _: self._navigate_if_logged_in("medicines"))
        self.root.bind("<Control-M>", lambda _: self._navigate_if_logged_in("medicines"))
        self.root.bind("<Control-i>", lambda _: self._navigate_if_logged_in("inventory"))
        self.root.bind("<Control-I>", lambda _: self._navigate_if_logged_in("inventory"))
        self.root.bind("<Control-f>", lambda _: self._navigate_if_logged_in("search"))
        self.root.bind("<Control-F>", lambda _: self._navigate_if_logged_in("search"))
        self.root.bind("<F1>", lambda _: self._navigate_if_logged_in("help"))

    def _navigate_if_logged_in(self, target: str) -> None:
        """Routes keyboard shortcut to active view if authenticated."""
        if isinstance(self.current_view, DashboardShell):
            if target == "billing":
                self.current_view.show_billing()
            elif target == "medicines":
                self.current_view.show_medicines()
            elif target == "inventory":
                self.current_view.show_inventory()
            elif target == "search":
                self.current_view.show_search()
            elif target == "help":
                self.current_view.show_help()

    def show_login(self) -> None:
        """Transitions application to login frame."""
        if self.current_view:
            self.current_view.destroy()
        self.current_user = None
        self.current_view = LoginFrame(self.root, on_login_success=self.on_login_success)

    def on_login_success(self, user: User) -> None:
        """Handles transition from successful login to dashboard shell."""
        if self.current_view:
            self.current_view.destroy()
        self.current_user = user
        logger.info("Session established for %s (%s)", user.username, user.role)
        self.current_view = DashboardShell(self.root, user=user, on_logout=self.show_login)

    def _on_close(self) -> None:
        """Safely terminates connections and exits."""
        try:
            db_manager.close_connection()
            logger.info("Application shutdown cleanly.")
        except Exception as exc:
            logger.warning("Error during shutdown cleanup: %s", exc)
        self.root.destroy()


def main() -> None:
    """Application bootstrap routine."""
    # 1. Setup Logging
    setup_system_logging()
    logger.info("Starting %s v%s...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Assigned TQM Objective: %s", settings.TQM_OBJECTIVE)

    # 2. Initialize Database & Migrations
    try:
        initialize_database()
    except Exception as exc:
        logger.critical("Failed to initialize database: %s", exc, exc_info=True)
        print(f"FATAL: Database initialization error: {exc}")
        sys.exit(1)

    # 3. Launch Tkinter Application
    root = tk.Tk()
    app = PharmacyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

