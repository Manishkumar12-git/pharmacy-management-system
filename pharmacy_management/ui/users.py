"""
================================================================================
Pharmacy Management System - User Accounts Management View
================================================================================
Module: pharmacy_management.ui.users
Quality Objective: Q10 - Improve Documentation & Security Governance

Description:
    Provides system administrators with operator account provisioning,
    role assignments (Admin, Pharmacist, Cashier), password resets,
    and active status toggling. Zero direct SQL in UI.
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any
from pharmacy_management.config import settings
from pharmacy_management.services.auth_service import auth_service
from pharmacy_management.models.user import User


class UsersView(ttk.Frame):
    """View governing operator accounts and role-based permissions."""

    def __init__(self, parent: tk.Widget, user: User):
        """Initializes user account administration view."""
        super().__init__(parent)
        self.user = user
        self.pack(fill=tk.BOTH, expand=True)

        self._init_ui()
        self.load_users()

    def _init_ui(self) -> None:
        top_bar = tk.Frame(self, bg=settings.THEME["BACKGROUND"], padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="Staff & Operator Accounts Management",
            font=(settings.THEME["FONT_FAMILY"], 15, "bold"),
            fg=settings.THEME["TEXT_MAIN"],
            bg=settings.THEME["BACKGROUND"]
        ).pack(side=tk.LEFT)

        btn_box = tk.Frame(top_bar, bg=settings.THEME["BACKGROUND"])
        btn_box.pack(side=tk.RIGHT)

        tk.Button(
            btn_box,
            text="➕ Create User",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=5,
            command=self._open_create_dialog
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_box,
            text="✏️ Edit / Reset Password",
            font=(settings.THEME["FONT_FAMILY"], 9),
            bg=settings.THEME["SURFACE"],
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            padx=12,
            pady=5,
            command=self._open_edit_dialog
        ).pack(side=tk.LEFT, padx=5)

        # Users Table
        table_frame = tk.Frame(self, bg=settings.THEME["SURFACE"], padx=20, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        cols = ("id", "username", "fullname", "role", "email", "phone", "status", "last_login")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Username")
        self.tree.heading("fullname", text="Full Name")
        self.tree.heading("role", text="Role")
        self.tree.heading("email", text="Email")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("status", text="Account Status")
        self.tree.heading("last_login", text="Last Login")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("username", width=110)
        self.tree.column("fullname", width=160)
        self.tree.column("role", width=95, anchor="center")
        self.tree.column("email", width=170)
        self.tree.column("phone", width=110)
        self.tree.column("status", width=95, anchor="center")
        self.tree.column("last_login", width=130, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def load_users(self) -> None:
        """Loads and updates user accounts table."""
        for itm in self.tree.get_children():
            self.tree.delete(itm)

        users = auth_service.get_all_users()
        for u in users:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    u.id,
                    u.username,
                    u.full_name,
                    u.role,
                    u.email or "-",
                    u.phone or "-",
                    u.status,
                    u.last_login or "Never"
                )
            )

    def _get_selected_user_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select User", "Please select a user account from the table.")
            return None
        return int(self.tree.item(sel[0], "values")[0])

    def _open_create_dialog(self) -> None:
        UserFormDialog(self, title="Create New Operator Account", on_saved=self.load_users)

    def _open_edit_dialog(self) -> None:
        uid = self._get_selected_user_id()
        if not uid:
            return
        user_obj = auth_service.get_user_by_id(uid)
        if user_obj:
            UserFormDialog(self, title="Edit Account / Reset Password", target_user=user_obj, on_saved=self.load_users)


class UserFormDialog(tk.Toplevel):
    """Modal dialog for creating and modifying user accounts."""

    def __init__(self, parent: tk.Widget, title: str, on_saved: Any, target_user: Optional[User] = None):
        """Initializes user creation/edit modal dialog."""
        super().__init__(parent)
        self.title(title)
        self.geometry("440x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_saved = on_saved
        self.target_user = target_user

        pad = tk.Frame(self, padx=25, pady=20, bg=settings.THEME["SURFACE"])
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text=title, font=(settings.THEME["FONT_FAMILY"], 12, "bold"), fg=settings.THEME["PRIMARY"], bg=settings.THEME["SURFACE"]).pack(anchor="w", pady=(0, 15))

        grid = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        grid.pack(fill=tk.BOTH, expand=True)

        # Fields
        tk.Label(grid, text="Username *:", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_user = ttk.Entry(grid, width=24)
        self.ent_user.grid(row=0, column=1, sticky="w", pady=5)

        tk.Label(grid, text="Full Name *:", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=1, column=0, sticky="w", pady=5)
        self.ent_name = ttk.Entry(grid, width=24)
        self.ent_name.grid(row=1, column=1, sticky="w", pady=5)

        tk.Label(grid, text="Role *:", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=2, column=0, sticky="w", pady=5)
        self.combo_role = ttk.Combobox(grid, values=settings.ALL_ROLES, state="readonly", width=22)
        self.combo_role.grid(row=2, column=1, sticky="w", pady=5)
        self.combo_role.current(2)  # Cashier by default

        tk.Label(grid, text="Email:", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=3, column=0, sticky="w", pady=5)
        self.ent_email = ttk.Entry(grid, width=24)
        self.ent_email.grid(row=3, column=1, sticky="w", pady=5)

        tk.Label(grid, text="Phone:", font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=4, column=0, sticky="w", pady=5)
        self.ent_phone = ttk.Entry(grid, width=24)
        self.ent_phone.grid(row=4, column=1, sticky="w", pady=5)

        pwd_lbl_txt = "Password *:" if not target_user else "Reset Password (Optional):"
        tk.Label(grid, text=pwd_lbl_txt, font=(settings.THEME["FONT_FAMILY"], 9), bg=settings.THEME["SURFACE"]).grid(row=5, column=0, sticky="w", pady=5)
        self.ent_pwd = ttk.Entry(grid, width=24, show="•")
        self.ent_pwd.grid(row=5, column=1, sticky="w", pady=5)

        # Pre-fill
        if target_user:
            self.ent_user.insert(0, target_user.username)
            self.ent_user.configure(state="disabled")
            self.ent_name.insert(0, target_user.full_name)
            self.combo_role.set(target_user.role)
            self.ent_email.insert(0, target_user.email or "")
            self.ent_phone.insert(0, target_user.phone or "")

        btn_box = tk.Frame(pad, bg=settings.THEME["SURFACE"])
        btn_box.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            btn_box,
            text="Save Account",
            font=(settings.THEME["FONT_FAMILY"], 9, "bold"),
            bg=settings.THEME["PRIMARY"],
            fg=settings.THEME["TEXT_LIGHT"],
            command=self._handle_save
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _handle_save(self) -> None:
        fullname = self.ent_name.get().strip()
        role = self.combo_role.get()
        email = self.ent_email.get().strip() or None
        phone = self.ent_phone.get().strip() or None
        pwd = self.ent_pwd.get().strip()

        if self.target_user:
            ok, msg = auth_service.update_user(
                user_id=self.target_user.id,
                full_name=fullname,
                role=role,
                email=email,
                phone=phone,
                status="Active",
                new_password=pwd if pwd else None
            )
        else:
            uname = self.ent_user.get().strip()
            ok, msg = auth_service.create_user(
                username=uname,
                password=pwd,
                full_name=fullname,
                role=role,
                email=email,
                phone=phone
            )

        if ok:
            messagebox.showinfo("Success", msg)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
