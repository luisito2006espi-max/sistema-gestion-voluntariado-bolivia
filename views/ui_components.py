import re
import tkinter as tk


# Paleta Institucional: Save the Children Bolivia (Rojo, Blanco, Negro y Plomo)
PALETTE = {
    "rojo": "#DA291C",          # Rojo principal Save the Children
    "rojo_oscuro": "#B00E28",   # Rojo profundo para fondos y acentos
    "rojo_hover": "#991B1B",    # Rojo intenso al pasar el cursor
    "rojo_suave": "#FEE2E2",    # Tinte rojo sutil para estados/alertas
    "blanco": "#FFFFFF",        # Blanco puro para tarjetas y texto invertido
    "negro": "#111827",         # Negro carbón para títulos y barra superior
    "negro_suave": "#1F2937",   # Gris carbón oscuro para contenedores oscuros
    "plomo_fondo": "#F3F4F6",   # Plomo claro neutro para el fondo general
    "plomo_borde": "#D1D5DB",   # Plomo medio para bordes de tarjetas e inputs
    "plomo_texto": "#4B5563",   # Plomo oscuro para subtítulos y descripciones
    "plomo_claro": "#9CA3AF",   # Plomo claro para textos secundarios
}


class InputValidators:
    """Filtros de validación en tiempo real por teclado para campos Entry."""

    _RE_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]*$")
    _RE_ENTEROS = re.compile(r"^\d*$")
    _RE_DECIMALES = re.compile(r"^\d*(\.\d{0,2})?$")
    _RE_CI = re.compile(r"^[0-9]*(-[0-9A-Za-z]{0,3})?$")

    @classmethod
    def solo_letras(cls, nuevo_valor: str) -> bool:
        return bool(cls._RE_LETRAS.match(nuevo_valor))

    @classmethod
    def solo_enteros(cls, nuevo_valor: str) -> bool:
        return bool(cls._RE_ENTEROS.match(nuevo_valor))

    @classmethod
    def solo_decimales(cls, nuevo_valor: str) -> bool:
        return bool(cls._RE_DECIMALES.match(nuevo_valor))

    @classmethod
    def solo_ci(cls, nuevo_valor: str) -> bool:
        return bool(cls._RE_CI.match(nuevo_valor))

    @classmethod
    def aplicar(cls, entry_widget, tipo: str):
        """
        Engancha la validación al Entry indicado.
        Tipos disponibles: 'letras', 'enteros', 'decimales', 'ci'.
        """
        mapa = {
            "letras": cls.solo_letras,
            "enteros": cls.solo_enteros,
            "decimales": cls.solo_decimales,
            "ci": cls.solo_ci,
        }
        funcion = mapa.get(tipo)
        if not funcion:
            return
        vcmd = entry_widget.register(funcion)
        entry_widget.configure(validate="key", validatecommand=(vcmd, "%P"))


class SaveTheChildrenLogo(tk.Canvas):
    """Emblema institucional vectorizado de Save the Children."""

    def __init__(self, master, size: int = 56, bg: str = PALETTE["blanco"]):
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
        self._dibujar(size)

    def _dibujar(self, s: int):
        pad = 2
        self.create_oval(
            pad, pad, s - pad, s - pad,
            fill=PALETTE["rojo"],
            outline=PALETTE["rojo"]
        )
        cx = s * 0.50
        head_r = s * 0.13
        head_y = s * 0.31
        self.create_oval(
            cx - head_r, head_y - head_r,
            cx + head_r, head_y + head_r,
            fill=PALETTE["blanco"],
            outline=""
        )
        lw = max(2, int(s * 0.085))
        self.create_arc(
            s * 0.22, s * 0.26, s * 0.78, s * 0.72,
            start=200, extent=140,
            style="arc",
            outline=PALETTE["blanco"],
            width=lw
        )
        self.create_line(
            cx, s * 0.48, cx, s * 0.78,
            fill=PALETTE["blanco"],
            width=lw,
            capstyle="round"
        )


class RoundedCard(tk.Canvas):
    """
    Contenedor responsivo con esquinas redondeadas reales.
    Agrega widgets dentro de `card.body`.
    """

    def __init__(
        self,
        master,
        radius: int = 18,
        bg_color: str = PALETTE["blanco"],
        border_color: str = PALETTE["plomo_borde"],
        padx: int = 20,
        pady: int = 18,
        expand_body: bool = False,
        **kwargs
    ):
        parent_bg = kwargs.pop("canvas_bg", None)
        if parent_bg is None:
            try:
                parent_bg = master.cget("bg")
            except Exception:
                parent_bg = PALETTE["plomo_fondo"]

        super().__init__(master, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.radius = radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.pad_x = padx
        self.pad_y = pady
        self.expand_body = expand_body

        self.body = tk.Frame(self, bg=bg_color)
        self._win_id = self.create_window(self.pad_x, self.pad_y, window=self.body, anchor="nw")

        self.bind("<Configure>", self._on_canvas_configure)
        if not self.expand_body:
            self.body.bind("<Configure>", self._on_body_configure)

    def lift(self, aboveThis=None):
        """Eleva la tarjeta completa en la ventana sin confundirse con Canvas.tag_raise."""
        tk.Misc.lift(self, aboveThis)

    def lower(self, belowThis=None):
        """Envía la tarjeta completa al fondo sin confundirse con Canvas.tag_lower."""
        tk.Misc.lower(self, belowThis)

    @staticmethod
    def _puntos_redondeados(x1: float, y1: float, x2: float, y2: float, r: float) -> list[float]:
        return [
            x1 + r, y1,
            x1 + r, y1,
            x2 - r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r,
            x1, y1,
        ]

    def _on_body_configure(self, _event=None):
        req_h = self.body.winfo_reqheight() + (self.pad_y * 2)
        if abs(self.winfo_height() - req_h) > 1:
            self.configure(height=req_h)

    def _on_canvas_configure(self, event):
        w, h = event.width, event.height
        if w < 6 or h < 6:
            return

        self.delete("card_bg")
        r = min(self.radius, w // 2, h // 2)

        if self.border_color:
            pts_borde = self._puntos_redondeados(0, 0, w - 1, h - 1, r)
            self.create_polygon(
                pts_borde,
                smooth=True,
                fill=self.border_color,
                outline=self.border_color,
                tags="card_bg"
            )
            pts_inner = self._puntos_redondeados(1, 1, w - 2, h - 2, max(2, r - 1))
            self.create_polygon(
                pts_inner,
                smooth=True,
                fill=self.bg_color,
                outline=self.bg_color,
                tags="card_bg"
            )
        else:
            pts = self._puntos_redondeados(0, 0, w - 1, h - 1, r)
            self.create_polygon(
                pts,
                smooth=True,
                fill=self.bg_color,
                outline=self.bg_color,
                tags="card_bg"
            )

        self.tag_lower("card_bg")

        inner_w = max(1, w - (self.pad_x * 2))
        self.itemconfigure(self._win_id, width=inner_w)
        if self.expand_body:
            inner_h = max(1, h - (self.pad_y * 2))
            self.itemconfigure(self._win_id, height=inner_h)