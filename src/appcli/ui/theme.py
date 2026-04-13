"""Configuración visual de la aplicación."""

import tkinter as tk
from tkinter import ttk

# Paleta de colores
BG_DARK      = "#1c2333"
BG_PANEL     = "#242d40"
BG_SURFACE   = "#2e3a52"
BG_HEADER    = "#1a2a42"
FG_PRIMARY   = "#e2e8f0"
FG_SECONDARY = "#7a8ba8"
FG_HEADING   = "#94b8e0"
ACCENT       = "#4f9cf9"
BORDER       = "#374561"
SELECT_BG    = "#2d5a9e"
SELECT_FG    = "#ffffff"

# Fuentes
FONT_UI    = ("Segoe UI", 10)
FONT_MONO  = ("Consolas", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_BOLD  = ("Segoe UI", 10, "bold")


def apply(root: tk.Tk):
    """Aplica el tema a la ventana raíz (debe llamarse después de ThemedTk)."""
    root.configure(bg=BG_DARK)

    style = ttk.Style(root)

    # --- Marcos ---
    style.configure("TFrame", background=BG_PANEL)
    style.configure("TPanedwindow", background=BG_DARK)

    # --- Treeview ---
    style.configure("Treeview",
        background=BG_PANEL,
        foreground=FG_PRIMARY,
        fieldbackground=BG_PANEL,
        borderwidth=0,
        font=FONT_UI,
        rowheight=26,
    )
    style.configure("Treeview.Heading",
        background=BG_HEADER,
        foreground=FG_HEADING,
        font=FONT_BOLD,
        borderwidth=0,
        relief="flat",
    )
    style.map("Treeview",
        background=[("selected", SELECT_BG)],
        foreground=[("selected", SELECT_FG)],
    )
    style.map("Treeview.Heading",
        background=[("active", BG_SURFACE)],
        relief=[("active", "flat")],
    )

    # --- Scrollbar (equilux la hace delgada y plana) ---
    style.configure("TScrollbar",
        background=BG_SURFACE,
        troughcolor=BG_PANEL,
        borderwidth=0,
        arrowsize=0,
        relief="flat",
    )
    style.map("TScrollbar",
        background=[("active", ACCENT), ("pressed", "#3a82d6")],
    )

    # --- Separator ---
    style.configure("TSeparator", background=BORDER)
