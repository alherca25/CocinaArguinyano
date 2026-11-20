"""Tema visual de las apps de escritorio (customtkinter), a juego con las apps móviles.

Paleta de los logos: fondo crema, tinta marrón, acento terracota.
"""
import json
import os
import sys
import tempfile

import customtkinter as ctk

ACCENT = "#C8553D"
ACCENT_HOVER = "#A8432E"
INK = "#3B2F25"
INK_SOFT = "#7A6A5C"
BG = "#FBF7F1"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F4ECE2"
BORDER = "#E6DACB"
PEACH = "#F6DCC4"
DANGER = "#B3261E"
DANGER_HOVER = "#8E1E18"
GREEN = "#5E8C4A"

FONT = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"


def resource_path(relative_path):
    """Ruta a un recurso, tanto ejecutando el .py como el .exe de PyInstaller."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, os.path.basename(relative_path))
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)  # shared/assets/...


def apply_theme():
    """Carga el tema «blue» de customtkinter y sustituye sus colores por la paleta."""
    ctk.set_appearance_mode("Light")
    base = os.path.join(os.path.dirname(ctk.__file__), "assets", "themes", "blue.json")
    try:
        with open(base, "r", encoding="utf-8") as f:
            theme = json.load(f)
    except OSError:
        ctk.set_default_color_theme("blue")
        return

    def both(color):
        return [color, color]

    theme["CTk"]["fg_color"] = both(BG)
    theme["CTkToplevel"]["fg_color"] = both(BG)
    theme["CTkFrame"].update(fg_color=both(SURFACE), top_fg_color=both(SURFACE_ALT),
                             border_color=both(BORDER), corner_radius=12)
    theme["CTkButton"].update(fg_color=both(ACCENT), hover_color=both(ACCENT_HOVER),
                              text_color=both("#FFFFFF"), border_color=both(BORDER), corner_radius=10)
    theme["CTkLabel"]["text_color"] = both(INK)
    theme["CTkEntry"].update(fg_color=both(SURFACE), border_color=both(BORDER),
                             text_color=both(INK), placeholder_text_color=both(INK_SOFT), corner_radius=8)
    theme["CTkTextbox"].update(fg_color=both(SURFACE), border_color=both(BORDER),
                               text_color=both(INK))
    theme["CTkCheckBox"].update(fg_color=both(GREEN), hover_color=both(GREEN), border_color=both(INK_SOFT),
                                checkmark_color=both("#FFFFFF"), text_color=both(INK))
    for key in ("CTkComboBox", "CTkOptionMenu"):
        if key in theme:
            theme[key].update(fg_color=both(SURFACE) if key == "CTkComboBox" else both(PEACH),
                              text_color=both(INK))
            if "button_color" in theme[key]:
                theme[key]["button_color"] = both(PEACH)
                theme[key]["button_hover_color"] = both("#EFC9A6")
            if "border_color" in theme[key]:
                theme[key]["border_color"] = both(BORDER)
    if "DropdownMenu" in theme:
        theme["DropdownMenu"].update(fg_color=both(SURFACE), hover_color=both(SURFACE_ALT),
                                     text_color=both(INK))
    theme["CTkScrollableFrame"]["label_fg_color"] = both(SURFACE_ALT)
    theme["CTkScrollbar"].update(button_color=both(BORDER), button_hover_color=both(INK_SOFT))
    seg = theme.get("CTkSegmentedButton")
    if seg:
        # customtkinter usa un único color de texto: selección en melocotón oscuro + texto tinta.
        seg.update(fg_color=both(SURFACE_ALT), selected_color=both("#E9B98F"),
                   selected_hover_color=both("#E0AB7E"), unselected_color=both(SURFACE_ALT),
                   unselected_hover_color=both(BORDER), text_color=both(INK))

    path = os.path.join(tempfile.gettempdir(), "cocina_rapida_theme.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(theme, f)
    ctk.set_default_color_theme(path)


def set_window_icon(window, ico_name):
    """Icono de la ventana y de la barra de tareas (Windows)."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f"alherca25.cocinarapida.{ico_name}")
        except Exception:
            pass
    path = resource_path(os.path.join("assets", ico_name))
    if os.path.exists(path):
        try:
            window.iconbitmap(path)
        except Exception as exc:
            print(f"No se pudo cargar el icono: {exc}")


def logo_image(ico_name, size=56):
    """CTkImage con el logo (se lee del .ico, que se incluye también en el .exe)."""
    path = resource_path(os.path.join("assets", ico_name))
    try:
        from PIL import Image
        img = Image.open(path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    except Exception:
        return None


def header(master, ico_name, title, subtitle, on_help=None):
    """Cabecera con logo, título y subtítulo."""
    bar = ctk.CTkFrame(master, fg_color=SURFACE, corner_radius=0, border_width=0)
    logo = logo_image(ico_name)
    if logo:
        ctk.CTkLabel(bar, image=logo, text="").pack(side="left", padx=(18, 10), pady=10)
    texts = ctk.CTkFrame(bar, fg_color="transparent")
    texts.pack(side="left", pady=10)
    ctk.CTkLabel(texts, text=title, font=(FONT, 20, "bold"), anchor="w").pack(anchor="w")
    sub = ctk.CTkLabel(texts, text=subtitle, font=(FONT, 12), text_color=INK_SOFT, anchor="w")
    sub.pack(anchor="w")
    if on_help:
        ctk.CTkButton(bar, text="?", width=34, height=34, corner_radius=17, fg_color=PEACH,
                      hover_color="#EFC9A6", text_color=INK, font=(FONT, 15, "bold"),
                      command=on_help).pack(side="right", padx=18)
    bar.subtitle = sub
    return bar


def secondary_button(master, **kwargs):
    kwargs.setdefault("fg_color", PEACH)
    kwargs.setdefault("hover_color", "#EFC9A6")
    kwargs.setdefault("text_color", INK)
    return ctk.CTkButton(master, **kwargs)


def danger_button(master, **kwargs):
    kwargs.setdefault("fg_color", SURFACE)
    kwargs.setdefault("hover_color", "#F7E1DF")
    kwargs.setdefault("text_color", DANGER)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", "#E8B4AF")
    return ctk.CTkButton(master, **kwargs)
