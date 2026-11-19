"""
Recetario «Cocina Rápida» — versión de escritorio (customtkinter).

Elige cuántos platos quieres de cada categoría, genera un menú aleatorio y
exporta a PDF las recetas y la lista de la compra (siempre del MISMO menú).
"""
import os
import subprocess
import sys
from datetime import datetime
from xml.sax.saxutils import escape

import customtkinter as ctk
import tkinter.messagebox as messagebox
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import desktop_theme as T
import functions

T.apply_theme()


def output_dir():
    """Carpeta donde se guardan los PDF: Documentos/Cocina Rápida."""
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    if not os.path.isdir(docs):
        docs = os.path.expanduser("~")
    path = os.path.join(docs, "Cocina Rápida")
    os.makedirs(path, exist_ok=True)
    return path


def open_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as exc:
        print(f"No se pudo abrir {path}: {exc}")


def pdf_fonts():
    """Usa Calibri si existe (Windows); si no, Helvetica (evita el error de fuente no registrada)."""
    regular, bold = r"C:\Windows\Fonts\calibri.ttf", r"C:\Windows\Fonts\calibrib.ttf"
    try:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Calibri", regular))
            pdfmetrics.registerFont(TTFont("Calibri-Bold", bold))
            return "Calibri", "Calibri-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"


class CategoryRow(ctk.CTkFrame):
    """Fila: nombre de la categoría, disponibles y selector − n +."""

    def __init__(self, master, name, on_change, **kwargs):
        super().__init__(master, fg_color=T.SURFACE, border_width=1, border_color=T.BORDER,
                         corner_radius=12, **kwargs)
        self.name, self.on_change, self.value, self.maximum = name, on_change, 0, 0
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=name, font=(T.FONT, 15, "bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(10, 0))
        self.avail = ctk.CTkLabel(self, text="", font=(T.FONT, 12), text_color=T.INK_SOFT, anchor="w")
        self.avail.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))
        self.minus = T.secondary_button(self, text="−", width=36, height=36, corner_radius=18,
                                        font=(T.FONT, 18, "bold"), command=lambda: self.set(self.value - 1))
        self.minus.grid(row=0, column=1, rowspan=2, padx=4)
        self.lbl = ctk.CTkLabel(self, text="0", width=34, font=(T.FONT, 16, "bold"))
        self.lbl.grid(row=0, column=2, rowspan=2)
        self.plus = T.secondary_button(self, text="+", width=36, height=36, corner_radius=18,
                                       font=(T.FONT, 18, "bold"), command=lambda: self.set(self.value + 1))
        self.plus.grid(row=0, column=3, rowspan=2, padx=(4, 14))

    def set_maximum(self, maximum):
        self.maximum = maximum
        self.avail.configure(text=f"{maximum} disponibles" if maximum else "Ninguna con este filtro")
        if self.value > maximum:
            self.set(maximum)
        self._paint()

    def set(self, value, notify=True):
        value = max(0, min(int(value), self.maximum))
        changed = value != self.value
        self.value = value
        self._paint()
        if changed and notify:
            self.on_change()

    def _paint(self):
        self.lbl.configure(text=str(self.value))
        self.minus.configure(state="normal" if self.value > 0 else "disabled")
        self.plus.configure(state="normal" if self.value < self.maximum else "disabled")


class CocinaArguinyano(ctk.CTk):
    def __init__(self):
        super().__init__()
        T.set_window_icon(self, "main_logo.ico")
        self.title("Recetario - Cocina Rápida")
        self.geometry("620x760")
        self.minsize(520, 600)
        self.actual_date = datetime.now().strftime("%Y-%m-%d")
        self.menu = None          # menú generado; se invalida al cambiar la selección
        self.recipes_table, self.source = {}, ""
        try:
            self.recipes_table = self.load_recipes()
        except Exception as exc:
            messagebox.showerror("Sin recetas", f"No se pudieron cargar las recetas:\n{exc}")
        self.setup_ui()

    # --- datos ---------------------------------------------------------------
    def load_recipes(self):
        cache = os.path.join(os.path.expanduser("~"), ".cocinarapida", "CocinaArguinyano.json")
        local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "CocinaArguinyano.json")
        db, self.source = functions.load_recipes_with_cache(cache, [local])
        return {cat: [functions.normalize_recipe(r) for r in recs] for cat, recs in db.items()}

    @property
    def active_filter(self):
        label = self.filter_btn.get()
        return {"Sin gluten": "Gluten Free"}.get(label, label)

    @property
    def selected_dishes(self):
        return {name: row.value for name, row in self.rows.items() if row.value > 0}

    # --- interfaz ---------------------------------------------------------------
    def setup_ui(self):
        total = sum(len(v) for v in self.recipes_table.values())
        origin = {"online": "actualizado", "cache": "sin conexión (copia guardada)",
                  "local": "copia local"}.get(self.source, "sin datos")
        T.header(self, "main_logo.ico", "Cocina Rápida", f"{total} recetas · {origin}",
                 on_help=self.show_help).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(14, 0))
        ctk.CTkLabel(body, text="Tipo de dieta", font=(T.FONT, 15, "bold")).pack(anchor="w")
        self.filter_btn = ctk.CTkSegmentedButton(body, values=["Todo", "Vegetariano", "Sin gluten"],
                                                 command=lambda _v: self.on_filter_change(),
                                                 font=(T.FONT, 13), height=34)
        self.filter_btn.set("Todo")
        self.filter_btn.pack(fill="x", pady=(6, 14))

        ctk.CTkLabel(body, text="¿Cuántos platos de cada tipo?", font=(T.FONT, 15, "bold")).pack(anchor="w")
        scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=(6, 0))
        scroll.grid_columnconfigure(0, weight=1)
        self.rows = {}
        for i, cat in enumerate(self.recipes_table):
            row = CategoryRow(scroll, cat, self.on_selection_change)
            row.grid(row=i, column=0, sticky="ew", pady=4, padx=(0, 6))
            self.rows[cat] = row
        self.on_filter_change()

        bottom = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=0)
        bottom.pack(fill="x", side="bottom")
        self.total_lbl = ctk.CTkLabel(bottom, text="", font=(T.FONT, 13, "bold"))
        self.total_lbl.pack(side="left", padx=20, pady=14)
        self.btn_both = ctk.CTkButton(bottom, text="Recetas + compra (PDF)", height=40,
                                      font=(T.FONT, 14, "bold"), command=self.generate_list)
        self.btn_both.pack(side="right", padx=(6, 20), pady=14)
        self.btn_shop = T.secondary_button(bottom, text="Compra", height=40, width=96,
                                           font=(T.FONT, 14, "bold"),
                                           command=lambda: self.export_shopping(self.get_menu()))
        self.btn_shop.pack(side="right", padx=6)
        self.btn_rec = T.secondary_button(bottom, text="Recetas", height=40, width=96,
                                          font=(T.FONT, 14, "bold"),
                                          command=lambda: self.export_recipes(self.get_menu()))
        self.btn_rec.pack(side="right", padx=6)
        self.on_selection_change()

    def show_help(self):
        messagebox.showinfo("Ayuda / Soporte",
                            "Elige cuántos platos quieres de cada tipo y pulsa un botón de exportar.\n"
                            "Los PDF se guardan en Documentos\\Cocina Rápida.\n\n"
                            "Ayuda o sugerencias: alherca25@gmail.com")

    def on_filter_change(self):
        for cat, row in self.rows.items():
            row.set_maximum(functions.count_available(self.recipes_table, cat, self.active_filter))
        self.on_selection_change()

    def on_selection_change(self):
        self.menu = None
        if not hasattr(self, "total_lbl"):
            return
        total = sum(self.selected_dishes.values())
        self.total_lbl.configure(text=f"{total} plato{'s' if total != 1 else ''}")
        state = "normal" if total else "disabled"
        for b in (self.btn_both, self.btn_shop, self.btn_rec):
            b.configure(state=state)

    # --- menú y PDF ---------------------------------------------------------------
    def get_menu(self):
        """El mismo menú para «Recetas» y «Compra» hasta que cambie la selección."""
        if self.menu is None:
            self.menu = functions.build_menu(self.recipes_table, self.selected_dishes, self.active_filter)
        return self.menu

    def generate_list(self):
        menu = self.get_menu()
        recipes = self.export_recipes(menu, open_after=False)
        shopping = self.export_shopping(menu, open_after=False)
        if recipes and shopping:
            messagebox.showinfo("Completado", f"PDF generados en:\n{os.path.dirname(recipes)}")
            open_file(os.path.dirname(recipes))

    def export_shopping(self, menu, open_after=True):
        items = functions.aggregate_ingredients(menu)
        if not items:
            messagebox.showwarning("Aviso", "No hay ingredientes que exportar.")
            return None
        path = os.path.join(output_dir(), f"Compra-{self.actual_date}.pdf")
        regular, bold = pdf_fonts()
        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=50, rightMargin=50,
                                topMargin=50, bottomMargin=50, title="Lista de la compra")
        styles = getSampleStyleSheet()
        title = ParagraphStyle("t", parent=styles["Heading1"], fontName=bold, fontSize=18,
                               textColor=colors.HexColor(T.INK))
        rows = [["", "Ingrediente", "Cantidad", "Unidad"]] + \
               [["", i["nombre"], i["cantidad"], i["unidad"]] for i in items]
        table = Table(rows, colWidths=[24, 266, 90, 80], repeatRows=1)
        # Casilla para tachar: un recuadro pequeño en la primera columna.
        boxes = [("BOX", (0, r), (0, r), 0.8, colors.HexColor(T.INK_SOFT)) for r in range(1, len(rows))]
        table.setStyle(TableStyle(boxes + [
            ("FONTNAME", (0, 0), (-1, -1), regular),
            ("FONTNAME", (0, 0), (-1, 0), bold),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(T.INK)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(T.SURFACE_ALT)]),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor(T.BORDER)),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        doc.build([Paragraph(f"Lista de la compra · {self.actual_date}", title), Spacer(1, 10), table])
        if open_after:
            open_file(path)
        return path

    def export_recipes(self, menu, open_after=True):
        if not menu:
            messagebox.showwarning("Aviso", "No hay platos seleccionados.")
            return None
        path = os.path.join(output_dir(), f"Recetas-{self.actual_date}.pdf")
        regular, bold = pdf_fonts()
        styles = getSampleStyleSheet()
        ink = colors.HexColor(T.INK)
        h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName=bold, fontSize=18,
                            leading=22, textColor=ink, alignment=TA_LEFT)
        meta = ParagraphStyle("m", parent=styles["BodyText"], fontName=regular, fontSize=11,
                              textColor=colors.HexColor(T.ACCENT))
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=bold, fontSize=14,
                            textColor=ink, spaceBefore=10)
        body = ParagraphStyle("b", parent=styles["BodyText"], fontName=regular, fontSize=12,
                              leading=16, textColor=ink)
        story = []
        for i, r in enumerate(menu):
            info = r.get("Tipo", "")
            page = functions.format_page(r.get("pagina", ""))
            if page:
                info += f" · página {page}"
            story += [Paragraph(escape(r["nombre"]), h1), Paragraph(escape(info), meta),
                      Paragraph("Ingredientes", h2)]
            ings = "<br/>".join("• " + escape(functions.format_ingredient(x)) for x in r["ingredientes"])
            story.append(Paragraph(ings or "Sin ingredientes.", body))
            story.append(Paragraph("Elaboración", h2))
            for para in (r.get("elaboracion") or "Sin elaboración.").split("\n"):
                if para.strip():
                    story += [Paragraph(escape(para.strip()), body), Spacer(1, 6)]
            if i < len(menu) - 1:
                story.append(PageBreak())
        SimpleDocTemplate(path, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50,
                          bottomMargin=50, title="Recetas").build(story)
        if open_after:
            open_file(path)
        return path


if __name__ == "__main__":
    app = CocinaArguinyano()
    app.mainloop()
