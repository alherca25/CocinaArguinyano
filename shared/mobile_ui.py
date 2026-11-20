"""
Componentes visuales compartidos por las apps móviles (Kivy).

Paleta inspirada en los logos de assets/: fondo crema, tinta marrón,
melocotón suave y un acento terracota.
"""
import os

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, InstructionGroup, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget


def hex_color(value, alpha=1.0):
    value = value.lstrip("#")
    return [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [alpha]


class C:
    """Paleta de colores."""
    BG = hex_color("FBF7F1")          # crema (fondo de los logos)
    SURFACE = hex_color("FFFFFF")
    SURFACE_ALT = hex_color("F4ECE2")
    BORDER = hex_color("E6DACB")
    INK = hex_color("3B2F25")         # marrón de las líneas del logo
    INK_SOFT = hex_color("7A6A5C")
    PEACH = hex_color("F6DCC4")
    ACCENT = hex_color("C8553D")      # terracota
    ACCENT_DARK = hex_color("A8432E")
    GREEN = hex_color("5E8C4A")
    GREEN_SOFT = hex_color("E3EEDC")
    BLUE = hex_color("3E6E8E")
    DANGER = hex_color("B3261E")
    WHITE = [1, 1, 1, 1]


def asset_path(name):
    """Busca un recurso en ./assets (APK) o ../assets (repositorio)."""
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (os.path.join(here, "assets"), os.path.join(os.path.dirname(here), "assets")):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return ""


def setup_window():
    Window.clearcolor = C.BG
    # El teclado virtual empuja el contenido en lugar de taparlo (Android).
    Window.softinput_mode = "below_target"


# ---------------------------------------------------------------------------
# Básicos
# ---------------------------------------------------------------------------
class _Rounded:
    """Mezcla: fondo redondeado con borde opcional."""

    def _init_bg(self, fill, radius=dp(14), border=None, border_width=1.0):
        # Se inserta al principio de canvas.before para que las instrucciones propias
        # del widget (p. ej. el color del texto de TextInput) se apliquen después.
        group = InstructionGroup()
        self._fill_color = Color(*fill)
        self._fill = RoundedRectangle(radius=[radius])
        group.add(self._fill_color)
        group.add(self._fill)
        self._border = None
        if border:
            self._border_color = Color(*border)
            self._border = Line(rounded_rectangle=(0, 0, 1, 1, radius), width=border_width)
            group.add(self._border_color)
            group.add(self._border)
        self.canvas.before.insert(0, group)
        self._radius = radius
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._fill.pos = self.pos
        self._fill.size = self.size
        if self._border is not None:
            self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, self._radius)

    def set_fill(self, rgba):
        self._fill_color.rgba = rgba

    def set_border(self, rgba):
        if self._border is not None:
            self._border_color.rgba = rgba


class Card(_Rounded, BoxLayout):
    def __init__(self, fill=None, border=True, radius=dp(16), **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(14))
        kwargs.setdefault("spacing", dp(8))
        super().__init__(**kwargs)
        self._init_bg(fill or C.SURFACE, radius, C.BORDER if border else None)


class AutoLabel(Label):
    """Etiqueta que ajusta el texto al ancho y su altura al contenido."""

    def __init__(self, **kwargs):
        kwargs.setdefault("color", C.INK)
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("font_size", sp(15))
        super().__init__(**kwargs)
        self.bind(width=self._wrap, texture_size=self._fit)
        self._wrap()

    def _wrap(self, *_):
        self.text_size = (self.width, None)

    def _fit(self, *_):
        self.height = max(self.texture_size[1], dp(18))


def title_label(text, size=20, color=None, **kw):
    return AutoLabel(text=text, font_size=sp(size), bold=True, color=color or C.INK, **kw)


def muted_label(text, size=13, **kw):
    return AutoLabel(text=text, font_size=sp(size), color=C.INK_SOFT, **kw)


def spacer(height=None):
    if height is None:
        return Widget()
    return Widget(size_hint_y=None, height=height)


# ---------------------------------------------------------------------------
# Botones
# ---------------------------------------------------------------------------
VARIANTS = {
    # variante: (relleno, relleno pulsado, texto, borde)
    "primary": (C.ACCENT, C.ACCENT_DARK, C.WHITE, None),
    "secondary": (C.PEACH, hex_color("EFC9A6"), C.INK, None),
    "ghost": (C.SURFACE, C.SURFACE_ALT, C.INK, C.BORDER),
    "green": (C.GREEN, hex_color("4B7539"), C.WHITE, None),
    "danger": (C.SURFACE, hex_color("F7E1DF"), C.DANGER, hex_color("E8B4AF")),
    "flat": ([0, 0, 0, 0], C.SURFACE_ALT, C.INK, None),
}


class RoundButton(_Rounded, Button):
    def __init__(self, variant="primary", radius=dp(14), **kwargs):
        fill, pressed, text_color, border = VARIANTS[variant]
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(50))
        kwargs.setdefault("font_size", sp(15))
        kwargs.setdefault("bold", True)
        super().__init__(background_normal="", background_down="",
                         background_disabled_normal="", background_color=(0, 0, 0, 0),
                         color=text_color, **kwargs)
        self._fills = (fill, pressed)
        self._init_bg(fill, radius, border, 1.1)
        self.bind(state=self._on_state, disabled=self._on_disabled)

    def _on_state(self, *_):
        self.set_fill(self._fills[1] if self.state == "down" else self._fills[0])

    def _on_disabled(self, *_):
        self.opacity = 0.45 if self.disabled else 1


class IconButton(RoundButton):
    """Botón cuadrado pequeño (−, +, ←, ×)."""

    def __init__(self, text, variant="ghost", size=dp(40), **kwargs):
        super().__init__(text=text, variant=variant, radius=size / 2, size_hint=(None, None),
                         size=(size, size), font_size=sp(20), **kwargs)


class Chip(_Rounded, ToggleButton):
    """Botón tipo «chip» para filtros y pestañas."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(38))
        kwargs.setdefault("font_size", sp(14))
        super().__init__(background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), **kwargs)
        self._init_bg(C.SURFACE, dp(19), C.BORDER, 1.1)
        self.bind(state=self._on_state)
        self._on_state()

    def _on_state(self, *_):
        active = self.state == "down"
        self.set_fill(C.INK if active else C.SURFACE)
        self.set_border(C.INK if active else C.BORDER)
        self.color = C.WHITE if active else C.INK
        self.bold = active

    def on_touch_down(self, touch):
        # Un chip de grupo no se puede desactivar pulsándolo otra vez.
        if self.group and self.state == "down" and self.collide_point(*touch.pos):
            return True
        return super().on_touch_down(touch)


class TickBox(_Rounded, Button):
    """Casilla de verificación con el estilo de la app."""
    active = BooleanProperty(False)

    def __init__(self, active=False, size=dp(28), **kwargs):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), size_hint=(None, None),
                         size=(size, size), bold=True, font_size=sp(16), **kwargs)
        self._init_bg(C.SURFACE, dp(8), C.INK_SOFT, 1.3)
        self.bind(active=self._paint, on_release=self._toggle)
        self.active = active
        self._paint()

    def _toggle(self, *_):
        self.active = not self.active

    def _paint(self, *_):
        self.set_fill(C.GREEN if self.active else C.SURFACE)
        self.set_border(C.GREEN if self.active else C.INK_SOFT)
        self.color = C.WHITE
        self.text = "x" if self.active else ""


class Field(_Rounded, TextInput):
    """Campo de texto redondeado."""

    def __init__(self, **kwargs):
        multiline = kwargs.get("multiline", False)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48) if not multiline else dp(140))
        kwargs.setdefault("font_size", sp(15))
        kwargs.setdefault("write_tab", False)
        super().__init__(background_normal="", background_active="",
                         background_color=(0, 0, 0, 0), foreground_color=C.INK,
                         hint_text_color=C.INK_SOFT, cursor_color=C.ACCENT,
                         padding=[dp(12), dp(13), dp(12), dp(10)], **kwargs)
        self._init_bg(C.SURFACE, dp(12), C.BORDER, 1.1)
        self.bind(focus=lambda *_: self.set_border(C.ACCENT if self.focus else C.BORDER))


class Stepper(BoxLayout):
    """Selector numérico − valor +."""
    value = NumericProperty(0)
    maximum = NumericProperty(99)

    def __init__(self, on_change=None, **kwargs):
        super().__init__(orientation="horizontal", size_hint=(None, None),
                         size=(dp(132), dp(42)), spacing=dp(6), **kwargs)
        self._on_change = on_change
        self.btn_minus = IconButton("-", size=dp(42))
        self.lbl = Label(text="0", color=C.INK, bold=True, font_size=sp(18))
        self.btn_plus = IconButton("+", variant="secondary", size=dp(42))
        self.btn_minus.bind(on_release=lambda *_: self.set(self.value - 1))
        self.btn_plus.bind(on_release=lambda *_: self.set(self.value + 1))
        for w in (self.btn_minus, self.lbl, self.btn_plus):
            self.add_widget(w)
        self.bind(value=self._refresh, maximum=self._refresh)
        self._refresh()

    def set(self, value):
        value = max(0, min(int(value), int(self.maximum)))
        if value != self.value:
            self.value = value
            if self._on_change:
                self._on_change(value)

    def _refresh(self, *_):
        self.lbl.text = str(int(self.value))
        self.btn_minus.disabled = self.value <= 0
        self.btn_plus.disabled = self.value >= self.maximum


# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------
class AppBar(BoxLayout):
    def __init__(self, title, subtitle="", logo="", on_back=None, actions=(), **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(72),
                         padding=[dp(14), dp(10)], spacing=dp(12), **kwargs)
        with self.canvas.before:
            Color(*C.SURFACE)
            self._bg = RoundedRectangle(radius=[0, 0, dp(22), dp(22)])
            Color(*C.BORDER)
            self._line = Line(points=[], width=1)
        self.bind(pos=self._redraw, size=self._redraw)

        if on_back:
            back = IconButton("<", size=dp(42))
            back.bind(on_release=lambda *_: on_back())
            self.add_widget(back)
        elif logo and asset_path(logo):
            self.add_widget(Image(source=asset_path(logo), size_hint=(None, None),
                                  size=(dp(50), dp(50)), fit_mode="contain"))

        texts = BoxLayout(orientation="vertical", spacing=dp(1))
        self.title_lbl = Label(text=title, color=C.INK, bold=True, font_size=sp(20),
                               halign="left", valign="bottom", shorten=True)
        self.sub_lbl = Label(text=subtitle, color=C.INK_SOFT, font_size=sp(13),
                             halign="left", valign="top", shorten=True)
        for lbl in (self.title_lbl, self.sub_lbl):
            lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            texts.add_widget(lbl)
        self.add_widget(texts)
        for action in actions:
            self.add_widget(action)

    def _redraw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def set_subtitle(self, text):
        self.sub_lbl.text = text

    def set_title(self, text):
        self.title_lbl.text = text


class TabBar(BoxLayout):
    """Barra de pestañas con chips. on_select(nombre)."""

    def __init__(self, tabs, on_select, group, selected=None, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(38),
                         spacing=dp(8), **kwargs)
        self.chips = {}
        for name in tabs:
            chip = Chip(text=name, group=group, allow_no_selection=False,
                        state="down" if name == (selected or tabs[0]) else "normal")
            chip.bind(on_release=lambda c: on_select(c.text))
            self.chips[name] = chip
            self.add_widget(chip)

    def select(self, name):
        for n, chip in self.chips.items():
            chip.state = "down" if n == name else "normal"


# ---------------------------------------------------------------------------
# Diálogos
# ---------------------------------------------------------------------------
class Dialog(ModalView):
    """Diálogo con tarjeta redondeada, título, mensaje y botones."""

    def __init__(self, title, message="", buttons=(("Aceptar", "primary", None),),
                 content=None, **kwargs):
        super().__init__(size_hint=(0.9, None), background="", background_color=(0, 0, 0, 0),
                         overlay_color=(0.13, 0.09, 0.06, 0.55), auto_dismiss=True, **kwargs)
        card = Card(padding=dp(20), spacing=dp(14), size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(title_label(title, size=19))
        if message:
            card.add_widget(AutoLabel(text=message, color=C.INK_SOFT))
        if content is not None:
            card.add_widget(content)
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        for text, variant, callback in buttons:
            btn = RoundButton(text=text, variant=variant, height=dp(48))
            btn.bind(on_release=lambda _b, cb=callback: self._press(cb))
            row.add_widget(btn)
        card.add_widget(row)
        self.add_widget(card)
        card.bind(height=lambda *_: setattr(self, "height", card.height))

    def _press(self, callback):
        self.dismiss()
        if callback:
            callback()


def show_info(title, message):
    Dialog(title, message).open()


def confirm(title, message, on_yes, yes_text="Sí", variant="danger"):
    Dialog(title, message, buttons=(("Cancelar", "ghost", None), (yes_text, variant, on_yes))).open()


class Toast(Label):
    """Mensaje breve en la parte inferior de la pantalla."""

    @staticmethod
    def show(text, duration=2.4):
        toast = Toast(text=text)
        Window.add_widget(toast)
        Clock.schedule_once(lambda *_: Animation(opacity=0, d=0.3).start(toast), duration)
        Clock.schedule_once(lambda *_: Window.remove_widget(toast), duration + 0.35)

    def __init__(self, **kwargs):
        super().__init__(color=C.WHITE, font_size=sp(14), size_hint=(None, None),
                         halign="center", valign="middle", **kwargs)
        self.text_size = (Window.width * 0.8, None)
        self.texture_update()
        self.size = (self.texture_size[0] + dp(32), self.texture_size[1] + dp(22))
        self.pos = ((Window.width - self.width) / 2, dp(90))
        with self.canvas.before:
            Color(*C.INK[:3], 0.92)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.height / 2])


class Busy(ModalView):
    """Indicador de «trabajando…» que bloquea la pantalla."""

    def __init__(self, text="Cargando...", **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(220), dp(90)), background="",
                         background_color=(0, 0, 0, 0), auto_dismiss=False,
                         overlay_color=(0.13, 0.09, 0.06, 0.4), **kwargs)
        card = Card(padding=dp(16))
        card.add_widget(Label(text=text, color=C.INK, bold=True, font_size=sp(15)))
        self.add_widget(card)


class Tag(_Rounded, Label):
    """Etiqueta pequeña tipo «píldora» (Vegetariano, Sin gluten, pág. 12...)."""
    STYLES = {
        "green": (C.GREEN_SOFT, C.GREEN),
        "peach": (C.PEACH, C.INK),
        "plain": (C.SURFACE_ALT, C.INK_SOFT),
    }

    def __init__(self, text, style="plain", **kwargs):
        fill, color = self.STYLES[style]
        super().__init__(text=text, color=color, font_size=sp(12), bold=True,
                         size_hint=(None, None), **kwargs)
        self.texture_update()
        self.size = (self.texture_size[0] + dp(18), dp(24))
        self._init_bg(fill, dp(12))


def tag_row(tags):
    """Fila de etiquetas: tags = [(texto, estilo), ...]."""
    row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(6))
    for text, style in tags:
        row.add_widget(Tag(text, style))
    row.add_widget(Widget())
    return row


def recipe_tags(recipe, include_category=True):
    from functions import format_page
    tags = []
    if include_category and recipe.get("Tipo"):
        tags.append((recipe["Tipo"], "peach"))
    filtros = recipe.get("filtros") or {}
    if filtros.get("vegetariano"):
        tags.append(("Vegetariano", "green"))
    if filtros.get("gluten_free"):
        tags.append(("Sin gluten", "green"))
    page = format_page(recipe.get("pagina", ""))
    if page:
        tags.append((f"pág. {page}", "plain"))
    return tags


def empty_state(text, logo=""):
    box = AnchorLayout(size_hint_y=None, height=dp(240))
    inner = BoxLayout(orientation="vertical", spacing=dp(10), size_hint=(0.85, None), height=dp(200))
    if logo and asset_path(logo):
        inner.add_widget(Image(source=asset_path(logo), size_hint_y=None, height=dp(110),
                               fit_mode="contain", opacity=0.7))
    lbl = muted_label(text, size=15)
    lbl.halign = "center"
    inner.add_widget(lbl)
    box.add_widget(inner)
    return box


# ---------------------------------------------------------------------------
# Android: compartir texto
# ---------------------------------------------------------------------------
def share_text(text, subject="Cocina Rápida"):
    """Abre el menú nativo «Compartir» de Android con el texto.

    En escritorio copia el texto al portapapeles. Devuelve un mensaje para el usuario.
    """
    from kivy.utils import platform
    if platform == "android":
        from jnius import autoclass, cast
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")
        intent = Intent()
        intent.setAction(Intent.ACTION_SEND)
        intent.setType("text/plain")
        intent.putExtra(Intent.EXTRA_SUBJECT, cast("java.lang.CharSequence", String(subject)))
        intent.putExtra(Intent.EXTRA_TEXT, cast("java.lang.CharSequence", String(text)))
        chooser = Intent.createChooser(intent, cast("java.lang.CharSequence", String("Compartir")))
        PythonActivity.mActivity.startActivity(chooser)
        return ""
    from kivy.core.clipboard import Clipboard
    Clipboard.copy(text)
    return "Copiado al portapapeles."


def user_dir():
    """Carpeta privada y persistente de la app."""
    from kivy.app import App
    app = App.get_running_app()
    path = app.user_data_dir if app else os.path.expanduser("~/.cocinarapida")
    os.makedirs(path, exist_ok=True)
    return path
