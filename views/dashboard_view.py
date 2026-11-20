from datetime import date
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.voluntario_controller import VoluntarioController
from controllers.actividad_controller import ActividadController


class DashboardView(tb.Frame):
    """Panel General Ejecutivo con métricas en tiempo real y agenda operativa expandida."""

    DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    MESES = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    def __init__(self, master, sesion: dict, on_navegar):
        super().__init__(master)
        self.sesion = sesion
        self.on_navegar = on_navegar
        self.vol_controller = VoluntarioController()
        self.act_controller = ActividadController()

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_datos()

    def _fecha_actual_formateada(self) -> str:
        hoy = date.today()
        dia_sem = self.DIAS_SEMANA[hoy.weekday()]
        mes_nom = self.MESES[hoy.month - 1]
        return f"{dia_sem}, {hoy.day} de {mes_nom} de {hoy.year}"

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO EJECUTIVO (Título principal en 22 pt)
        # =====================================================================
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 20))

        izq_hdr = tk.Frame(header, bg="#FFF5F5")
        izq_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq_hdr,
            text="SAVE THE CHILDREN BOLIVIA  •  CENTRO DE OPERACIONES",
            font=("Segoe UI", 9, "bold"),
            bg="#FFF5F5",
            fg="#B91C1C"
        ).pack(anchor="w")

        tk.Label(
            izq_hdr,
            text=f"Panel General — ¡Hola, {self.sesion['nombre_mostrar']}!",
            font=("Segoe UI", 22, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq_hdr,
            text=f"📅  {self._fecha_actual_formateada()}   |   Resumen operativo en tiempo real",
            font=("Segoe UI", 11),
            bg="#FFF5F5",
            fg="#475569"
        ).pack(anchor="w")

        tb.Button(
            header,
            text="↻  Actualizar Panel",
            bootstyle="danger",
            command=self._cargar_datos
        ).pack(side="right", ipady=8, ipadx=16, pady=8)

        # =====================================================================
        # 2. FILA DE 4 TARJETAS KPI DE ALTO IMPACTO
        # =====================================================================
        kpi_grid = tk.Frame(self, bg="#FFF5F5")
        kpi_grid.pack(fill="x", pady=(0, 20))

        self.kpi_post_val, self.kpi_post_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=0,
            titulo="POSTULANTES PENDIENTES",
            color="#D97706",
            texto_accion="Evaluar solicitudes →",
            destino_menu="✅  Admisión Voluntarios"
        )

        self.kpi_vol_val, self.kpi_vol_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=1,
            titulo="VOLUNTARIOS ACTIVOS",
            color="#B91C1C",
            texto_accion="Ver control asistencia →",
            destino_menu="📋  Control Asistencia"
        )

        self.kpi_act_val, self.kpi_act_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=2,
            titulo="ACTIVIDADES OPERATIVAS",
            color="#991B1B",
            texto_accion="Gestionar calendario →",
            destino_menu="📅  Gestión Actividades"
        )

        self.kpi_don_val, self.kpi_don_sub = self._crear_tarjeta_kpi(
            kpi_grid,
            col=3,
            titulo="RECAUDACIÓN MONETARIA",
            color="#15803D",
            texto_accion="Ver reportes y gráficos →",
            destino_menu="📈  Reportes y Rendimiento"
        )

        # =====================================================================
        # 3. CUERPO CENTRAL EXPANDIDO (OCUPA TODO EL ESPACIO RESTANTE)
        # =====================================================================
        cuerpo = tk.Frame(self, bg="#FFF5F5")
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=3, uniform="dash_body")
        cuerpo.columnconfigure(1, weight=2, uniform="dash_body")
        cuerpo.rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: PRÓXIMAS ACTIVIDADES ---
        card_act = tk.Frame(cuerpo, bg="#FFFFFF", padx=20, pady=18)
        card_act.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        hdr_act = tk.Frame(card_act, bg="#FFFFFF")
        hdr_act.pack(fill="x", pady=(0, 12))

        tk.Label(
            hdr_act,
            text="📅  Próximas Actividades y Ocupación de Cupos",
            font=("Segoe UI", 13, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(side="left")

        tb.Button(
            hdr_act,
            text="Asignar Voluntarios →",
            bootstyle="danger-outline",
            command=lambda: self.on_navegar("👥  Asignar Voluntarios")
        ).pack(side="right", ipady=3)

        cols_act = ("actividad", "fecha", "horario", "lugar", "cupos", "estado")
        self.tabla_act = tb.Treeview(
            card_act,
            columns=cols_act,
            show="headings",
            height=10,
            bootstyle="danger"
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
        self.tabla_act.pack(fill=BOTH, expand=True)

        # --- PANEL DERECHO: ÚLTIMAS DONACIONES RECIBIDAS ---
        card_don = tk.Frame(cuerpo, bg="#FFFFFF", padx=20, pady=18)
        card_don.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        hdr_don = tk.Frame(card_don, bg="#FFFFFF")
        hdr_don.pack(fill="x", pady=(0, 12))

        tk.Label(
            hdr_don,
            text="🎁  Últimas Donaciones",
            font=("Segoe UI", 13, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(side="left")

        tb.Button(
            hdr_don,
            text="+ Nueva Donación",
            bootstyle="danger-outline",
            command=lambda: self.on_navegar("🎁  Gestión Donaciones")
        ).pack(side="right", ipady=3)

        cols_don = ("fecha", "donante", "tipo", "aporte")
        self.tabla_don = tb.Treeview(
            card_don,
            columns=cols_don,
            show="headings",
            height=10,
            bootstyle="danger"
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
        self.tabla_don.pack(fill=BOTH, expand=True)

    def _crear_tarjeta_kpi(
        self,
        parent,
        col: int,
        titulo: str,
        color: str,
        texto_accion: str,
        destino_menu: str
    ):
        parent.columnconfigure(col, weight=1, uniform="kpi_exec")
        padx = (0, 8) if col == 0 else ((8, 0) if col == 3 else 8)

        card = tk.Frame(parent, bg="#FFFFFF", padx=20, pady=20)
        card.grid(row=0, column=col, sticky="nsew", padx=padx)

        tk.Frame(card, bg=color, height=5).pack(fill="x", pady=(0, 14))

        tk.Label(
            card,
            text=titulo,
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#475569",
            anchor="w"
        ).pack(fill="x")

        lbl_val = tk.Label(
            card,
            text="0",
            font=("Segoe UI", 28, "bold"),
            bg="#FFFFFF",
            fg=color,
            anchor="w"
        )
        lbl_val.pack(fill="x", pady=(6, 6))

        lbl_sub = tk.Label(
            card,
            text="Cargando...",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#64748B",
            anchor="w"
        )
        lbl_sub.pack(fill="x", pady=(0, 12))

        btn_link = tk.Button(
            card,
            text=texto_accion,
            font=("Segoe UI", 9, "bold"),
            bg="#FFF5F5",
            fg=color,
            activebackground="#FEE2E2",
            activeforeground=color,
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            anchor="w",
            command=lambda: self.on_navegar(destino_menu)
        )
        btn_link.pack(fill="x")

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
            self.tabla_act.insert("", tk.END, values=("Sin actividades próximas", "-", "-", "-", "-", "-"))
        else:
            for act in proximas:
                self.tabla_act.insert("", tk.END, values=(
                    act["nombre"],
                    str(act["fecha"]),
                    act["horario"],
                    act["lugar"],
                    act["cupos_str"],
                    act["estado"]
                ))

        for w in self.tabla_don.get_children():
            self.tabla_don.delete(w)

        ultimas = datos["ultimas_donaciones"]
        if not ultimas:
            self.tabla_don.insert("", tk.END, values=("-", "Sin donaciones registradas", "-", "-"))
        else:
            for don in ultimas:
                self.tabla_don.insert("", tk.END, values=(
                    str(don["fecha_donacion"]),
                    don["donante"],
                    don["tipo"],
                    don["detalle_str"]
                ))