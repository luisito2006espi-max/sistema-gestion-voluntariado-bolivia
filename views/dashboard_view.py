from datetime import date
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.voluntario_controller import VoluntarioController
from controllers.actividad_controller import ActividadController
from views.ui_components import PALETTE, RoundedCard


class DashboardView(tk.Frame):
    """Panel General Ejecutivo con tarjetas curvas y paleta Rojo, Blanco, Negro y Plomo."""

    DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    MESES = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    def __init__(self, master, sesion: dict, on_navegar):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.on_navegar = on_navegar
        self.vol_controller = VoluntarioController()
        self.act_controller = ActividadController()

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._cargar_datos()

    def _fecha_actual_formateada(self) -> str:
        hoy = date.today()
        dia_sem = self.DIAS_SEMANA[hoy.weekday()]
        mes_nom = self.MESES[hoy.month - 1]
        return f"{dia_sem}, {hoy.day} de {mes_nom} de {hoy.year}"

    def _configurar_estilos_tabla(self):
        """Estiliza las tablas del panel con encabezados en plomo suave y texto negro."""
        style = tb.Style()
        style.configure(
            "Dash.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Dash.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 7)
        )
        style.map(
            "Dash.Treeview.Heading",
            background=[("active", PALETTE["plomo_borde"])]
        )
        style.map(
            "Dash.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO EJECUTIVO (Título principal en 22 pt)
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        izq_hdr = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        izq_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq_hdr,
            text=f"Panel General — ¡Hola, {self.sesion['nombre_mostrar']}!",
            font=("Segoe UI", 17, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq_hdr,
            text=f"📅  {self._fecha_actual_formateada()}   |   Resumen operativo en tiempo real",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_refresh = tk.Button(
            header,
            text="↻  Actualizar Panel",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
            command=self._cargar_datos
        )
        btn_refresh.pack(side="right", pady=8)
        btn_refresh.bind("<Enter>", lambda _e: btn_refresh.config(bg=PALETTE["rojo_hover"]))
        btn_refresh.bind("<Leave>", lambda _e: btn_refresh.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # 2. FILA DE 4 TARJETAS KPI CURVAS CON ACCESOS RÁPIDOS
        # =====================================================================
        kpi_grid = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        kpi_grid.pack(fill="x", pady=(0, 10))

        self.kpi_post_val, self.kpi_post_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=0,
            titulo="POSTULANTES PENDIENTES",
            color_acento=PALETTE["rojo"],
            texto_accion="Evaluar solicitudes →",
            destino_menu="✅  Admisión Voluntarios"
        )

        self.kpi_vol_val, self.kpi_vol_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=1,
            titulo="VOLUNTARIOS ACTIVOS",
            color_acento=PALETTE["negro"],
            texto_accion="Ver control asistencia →",
            destino_menu="📋  Control Asistencia"
        )

        self.kpi_act_val, self.kpi_act_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=2,
            titulo="ACTIVIDADES OPERATIVAS",
            color_acento=PALETTE["rojo_oscuro"],
            texto_accion="Gestionar calendario →",
            destino_menu="📅  Gestión Actividades"
        )

        self.kpi_don_val, self.kpi_don_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=3,
            titulo="RECAUDACIÓN MONETARIA",
            color_acento=PALETTE["negro_suave"],
            texto_accion="Ver reportes y gráficos →",
            destino_menu="📈  Reportes y Rendimiento"
        )

        # =====================================================================
        # 3. CUERPO CENTRAL CURVO: TABLAS SUTILES + ACCESOS RÁPIDOS INTEGRADOS
        # =====================================================================
        cuerpo = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=3, uniform="dash_body")
        cuerpo.columnconfigure(1, weight=2, uniform="dash_body")
        cuerpo.rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: PRÓXIMAS ACTIVIDADES ---
        card_act = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=18,
            expand_body=True
        )
        card_act.grid(row=0, column=0, sticky="nsew", padx=(0, 9))

        hdr_act = tk.Frame(card_act.body, bg=PALETTE["blanco"])
        hdr_act.pack(fill="x", pady=(0, 10))

        tit_act_box = tk.Frame(hdr_act, bg=PALETTE["blanco"])
        tit_act_box.pack(side="left")

        tk.Label(
            tit_act_box,
            text="📅  Próximas Actividades y Cupos",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        tk.Label(
            tit_act_box,
            text="Agenda operativa programada y en curso",
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        self._crear_boton_acceso_tabla(
            hdr_act,
            texto="Asignar Voluntarios →",
            destino_menu="👥  Asignar Voluntarios"
        ).pack(side="right", pady=2)

        cols_act = ("actividad", "fecha", "horario", "lugar", "cupos", "estado")
        self.tabla_act = tb.Treeview(
            card_act.body,
            columns=cols_act,
            show="headings",
            height=6,
            style="Dash.Treeview"
        )
        cfg_act = {
            "actividad": ("Actividad", 175),
            "fecha": ("Fecha", 95),
            "horario": ("Horario", 110),
            "lugar": ("Lugar", 135),
            "cupos": ("Cupos", 75),
            "estado": ("Estado", 95)
        }
        for c, (tit, w) in cfg_act.items():
            self.tabla_act.heading(c, text=tit)
            self.tabla_act.column(c, width=w, anchor="center" if c not in ("actividad", "lugar") else "w")

        self.tabla_act.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_act.tag_configure("impar", background="#F9FAFB")
        self.tabla_act.pack(fill=BOTH, expand=True)

        # --- PANEL DERECHO: ÚLTIMAS DONACIONES RECIBIDAS ---
        card_don = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=18,
            expand_body=True
        )
        card_don.grid(row=0, column=1, sticky="nsew", padx=(9, 0))

        hdr_don = tk.Frame(card_don.body, bg=PALETTE["blanco"])
        hdr_don.pack(fill="x", pady=(0, 10))

        tit_don_box = tk.Frame(hdr_don, bg=PALETTE["blanco"])
        tit_don_box.pack(side="left")

        tk.Label(
            tit_don_box,
            text="🎁  Últimas Donaciones",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        tk.Label(
            tit_don_box,
            text="Aportes monetarios y en especie recientes",
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        self._crear_boton_acceso_tabla(
            hdr_don,
            texto="+ Nueva Donación",
            destino_menu="🎁  Gestión Donaciones"
        ).pack(side="right", pady=2)

        cols_don = ("fecha", "donante", "tipo", "aporte")
        self.tabla_don = tb.Treeview(
            card_don.body,
            columns=cols_don,
            show="headings",
            height=9,
            style="Dash.Treeview"
        )
        cfg_don = {
            "fecha": ("Fecha", 85),
            "donante": ("Donante", 150),
            "tipo": ("Tipo", 75),
            "aporte": ("Monto / Detalle", 115)
        }
        for c, (tit, w) in cfg_don.items():
            self.tabla_don.heading(c, text=tit)
            self.tabla_don.column(c, width=w, anchor="center" if c in ("fecha", "tipo") else "w")

        self.tabla_don.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_don.tag_configure("impar", background="#F9FAFB")
        self.tabla_don.pack(fill=BOTH, expand=True)

    def _crear_boton_acceso_tabla(self, parent, texto: str, destino_menu: str):
        """Botón de acceso rápido discreto en plomo y negro con realce rojo al pasar el cursor."""
        btn = tk.Button(
            parent,
            text=texto,
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_navegar(destino_menu)
        )
        btn.bind("<Enter>", lambda _e: btn.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"]))
        btn.bind("<Leave>", lambda _e: btn.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"]))
        return btn

    def _crear_tarjeta_kpi(
        self,
        parent,
        col: int,
        titulo: str,
        color_acento: str,
        texto_accion: str,
        destino_menu: str
    ):
        parent.columnconfigure(col, weight=1, uniform="kpi_exec")
        padx = (0, 8) if col == 0 else ((8, 0) if col == 3 else 8)

        card = RoundedCard(
            parent,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=10,
            expand_body=False
        )
        card.grid(row=0, column=col, sticky="nsew", padx=padx)

        b = card.body

        # Barra superior de acento
        tk.Frame(b, bg=color_acento, height=4).pack(fill="x", pady=(0, 11))

        tk.Label(
            b,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            anchor="w"
        ).pack(fill="x")

        lbl_val = tk.Label(
            b,
            text="0",
            font=("Segoe UI", 20, "bold"),
            bg=PALETTE["blanco"],
            fg=color_acento,
            anchor="w"
        )
        lbl_val.pack(fill="x", pady=(4, 4))

        lbl_sub = tk.Label(
            b,
            text="Cargando...",
            font=("Segoe UI", 9),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            anchor="w"
        )
        lbl_sub.pack(fill="x", pady=(0, 6))

        btn_link = tk.Button(
            b,
            text=texto_accion,
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            anchor="w",
            command=lambda: self.on_navegar(destino_menu)
        )
        btn_link.pack(fill="x")
        btn_link.bind("<Enter>", lambda _e: btn_link.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"]))
        btn_link.bind("<Leave>", lambda _e: btn_link.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"]))

        return lbl_val, lbl_sub

    def _cargar_datos(self):
        try:
            self.act_controller.model.sincronizar_estados_por_horario()
        except Exception:
            pass

        datos = self.vol_controller.obtener_resumen_dashboard()

        self.kpi_post_val.config(text=str(datos["postulantes"]))
        self.kpi_post_sub.config(
            text="Solicitudes por revisar" if datos["postulantes"] > 0 else "Sin postulantes pendientes"
        )

        self.kpi_vol_val.config(text=str(datos["admitidos"]))
        self.kpi_vol_sub.config(text=f"⏱ {datos['horas_totales']:,.1f} hrs de servicio acumuladas")

        self.kpi_act_val.config(text=str(datos["actividades_total"]))
        self.kpi_act_sub.config(
            text=f"{datos['actividades_programadas']} programadas • {datos['actividades_en_curso']} en curso"
        )

        self.kpi_don_val.config(text=f"Bs. {datos['total_dinero']:,.2f}")
        self.kpi_don_sub.config(text=f"📦 {datos['donaciones_material']} donaciones en especie")

        for w in self.tabla_act.get_children():
            self.tabla_act.delete(w)

        proximas = datos["proximas_actividades"]
        if not proximas:
            self.tabla_act.insert(
                "", tk.END,
                values=("Sin actividades próximas", "-", "-", "-", "-", "-"),
                tags=("par",)
            )
        else:
            for idx, act in enumerate(proximas):
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla_act.insert("", tk.END, values=(
                    act["nombre"],
                    str(act["fecha"]),
                    act["horario"],
                    act["lugar"],
                    act["cupos_str"],
                    act["estado"]
                ), tags=(tag,))

        for w in self.tabla_don.get_children():
            self.tabla_don.delete(w)

        ultimas = datos["ultimas_donaciones"]
        if not ultimas:
            self.tabla_don.insert(
                "", tk.END,
                values=("-", "Sin donaciones registradas", "-", "-"),
                tags=("par",)
            )
        else:
            for idx, don in enumerate(ultimas):
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla_don.insert("", tk.END, values=(
                    str(don["fecha_donacion"]),
                    don["donante"],
                    don["tipo"],
                    don["detalle_str"]
                ), tags=(tag,))