import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from controllers.reporte_controller import ReporteController
from views.ui_components import PALETTE, RoundedCard


class ReportesRendimientoView(tk.Frame):
    """Vista de Analítica, Gráficos de 2 Variables, Rendimiento y Exportación Excel."""

    PALETA_GRAFICOS = [
        PALETTE["rojo"],
        PALETTE["negro"],
        PALETTE["rojo_oscuro"],
        PALETTE["plomo_texto"],
        "#EF4444",
        PALETTE["plomo_claro"]
    ]

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = ReporteController()
        self.paquete_actual = None

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._cargar_reportes(usar_todo=True)

    def _configurar_estilos_tabla(self):
        """Aplica la misma configuración limpia de tablas que el Panel General."""
        style = tb.Style()
        style.configure(
            "Rep.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=29,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Rep.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 7)
        )
        style.map(
            "Rep.Treeview.Heading",
            background=[("active", PALETTE["plomo_borde"])]
        )
        style.map(
            "Rep.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO + BOTÓN EXPORTAR EXCEL
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 12))

        titulos_frame = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        titulos_frame.pack(side="left")

        tk.Label(
            titulos_frame,
            text="SAVE THE CHILDREN BOLIVIA  •  INTELIGENCIA OPERATIVA",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["rojo"]
        ).pack(anchor="w")

        tk.Label(
            titulos_frame,
            text="Reportes Estadísticos y Rendimiento",
            font=("Segoe UI", 20, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            titulos_frame,
            text="Análisis cuantitativo, cualitativo, evolución temporal y desempeño de voluntarios.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_excel = tk.Button(
            header,
            text="📥  Exportar a Excel (.xlsx)",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
            command=self._exportar_excel
        )
        btn_excel.pack(side="right", pady=8)
        btn_excel.bind("<Enter>", lambda _e: btn_excel.config(bg=PALETTE["rojo"]))
        btn_excel.bind("<Leave>", lambda _e: btn_excel.config(bg=PALETTE["negro"]))

        # =====================================================================
        # 2. BARRA CURVA DE FILTROS POR FECHA
        # =====================================================================
        filtro_card = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=11,
            expand_body=False
        )
        filtro_card.pack(fill="x", pady=(0, 12))

        fb = filtro_card.body

        tk.Label(fb, text="Desde:", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).pack(side="left", padx=(0, 6))
        self.date_desde = tb.DateEntry(fb, bootstyle="danger", dateformat="%Y-%m-%d", width=13)
        self.date_desde.pack(side="left", padx=(0, 14))

        tk.Label(fb, text="Hasta:", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).pack(side="left", padx=(0, 6))
        self.date_hasta = tb.DateEntry(fb, bootstyle="danger", dateformat="%Y-%m-%d", width=13)
        self.date_hasta.pack(side="left", padx=(0, 14))

        btn_filtrar = tk.Button(
            fb,
            text="🔍 Filtrar Rango",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self._cargar_reportes(usar_todo=False)
        )
        btn_filtrar.pack(side="left", padx=(0, 8))

        btn_todo = tk.Button(
            fb,
            text="Ver Todo el Historial",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self._cargar_reportes(usar_todo=True)
        )
        btn_todo.pack(side="left")

        self.lbl_periodo = tk.Label(
            fb,
            text="Mostrando: Todo el historial",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            padx=12,
            pady=5
        )
        self.lbl_periodo.pack(side="right")

        # =====================================================================
        # 3. NOTEBOOK CON 4 SUB-PESTAÑAS ANALÍTICAS
        # =====================================================================
        self.notebook = tb.Notebook(self, bootstyle="danger")
        self.notebook.pack(fill=BOTH, expand=True)

        self.tab_rendimiento = tk.Frame(self.notebook, bg=PALETTE["plomo_fondo"], padx=8, pady=10)
        self.tab_voluntarios = tk.Frame(self.notebook, bg=PALETTE["plomo_fondo"], padx=8, pady=10)
        self.tab_actividades = tk.Frame(self.notebook, bg=PALETTE["plomo_fondo"], padx=8, pady=10)
        self.tab_donaciones = tk.Frame(self.notebook, bg=PALETTE["plomo_fondo"], padx=8, pady=10)

        self.notebook.add(self.tab_rendimiento, text="  🏆 Rendimiento y Asistencia  ")
        self.notebook.add(self.tab_voluntarios, text="  👥 Voluntarios (Tiempo y Estado)  ")
        self.notebook.add(self.tab_actividades, text="  📅 Actividades y Cupos  ")
        self.notebook.add(self.tab_donaciones, text="  🎁 Donaciones (Dinero y Especie)  ")

    def _cargar_reportes(self, usar_todo: bool):
        if usar_todo:
            f_ini, f_fin = None, None
        else:
            ok, msg, f_ini, f_fin = self.controller.validar_fechas(
                self.date_desde.entry.get(),
                self.date_hasta.entry.get()
            )
            if not ok:
                messagebox.showwarning("Filtro de Fechas", msg)
                return

        try:
            self.paquete_actual = self.controller.generar_paquete_analitico(f_ini, f_fin)
            self.lbl_periodo.config(text=f"Mostrando: {self.paquete_actual['periodo']}")

            self._render_tab_rendimiento()
            self._render_tab_voluntarios()
            self._render_tab_actividades()
            self._render_tab_donaciones()
        except Exception as e:
            messagebox.showerror("Error al Generar Reportes", str(e))

    def _exportar_excel(self):
        if not self.paquete_actual:
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar Reporte en Excel",
            defaultextension=".xlsx",
            filetypes=[("Libro de Excel", "*.xlsx")],
            initialfile="Reporte_Voluntariado_SaveTheChildren.xlsx"
        )
        if not ruta:
            return

        exito, mensaje = self.controller.exportar_a_excel(ruta, self.paquete_actual)
        if exito:
            messagebox.showinfo("Exportación Exitosa", mensaje)
        else:
            messagebox.showerror("Error de Exportación", mensaje)

    # =========================================================================
    # HELPERS DE GRÁFICOS MATPLOTLIB
    # =========================================================================

    def _limpiar_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _incrustar_figura(self, parent, fig: Figure):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    def _dibujar_sin_datos(self, ax, titulo: str):
        ax.set_title(titulo, fontsize=10, fontweight="bold", color=PALETTE["negro"], pad=10)
        ax.text(
            0.5, 0.5,
            "Sin datos registrados en este período",
            ha="center", va="center",
            fontsize=9, color=PALETTE["plomo_texto"]
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    def _grafico_pastel(self, parent, etiquetas: list[str], valores: list[float], titulo: str):
        fig = Figure(figsize=(4.4, 2.8), dpi=95, facecolor=PALETTE["blanco"])
        ax = fig.add_subplot(111)

        pares = [(e, v) for e, v in zip(etiquetas, valores) if v > 0]
        if not pares:
            self._dibujar_sin_datos(ax, titulo)
        else:
            labs, vals = zip(*pares)
            colores = [self.PALETA_GRAFICOS[i % len(self.PALETA_GRAFICOS)] for i in range(len(vals))]
            ax.pie(
                vals,
                labels=labs,
                autopct="%1.1f%%",
                startangle=140,
                colors=colores,
                textprops={"fontsize": 8, "color": PALETTE["negro"]}
            )
            ax.set_title(titulo, fontsize=10, fontweight="bold", color=PALETTE["negro"], pad=8)

        fig.tight_layout()
        self._incrustar_figura(parent, fig)

    def _grafico_linea_tiempo(self, parent, periodos: list[str], valores: list[float], titulo: str, ylabel: str):
        fig = Figure(figsize=(4.8, 2.8), dpi=95, facecolor=PALETTE["blanco"])
        ax = fig.add_subplot(111)

        if not periodos:
            self._dibujar_sin_datos(ax, titulo)
        else:
            ax.plot(periodos, valores, marker="o", color=PALETTE["rojo"], linewidth=2.2, markersize=6)
            ax.fill_between(periodos, valores, color=PALETTE["rojo_suave"], alpha=0.55)
            ax.set_title(titulo, fontsize=10, fontweight="bold", color=PALETTE["negro"], pad=8)
            ax.set_ylabel(ylabel, fontsize=8, color=PALETTE["plomo_texto"])
            ax.tick_params(axis="x", labelsize=8, rotation=20)
            ax.tick_params(axis="y", labelsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        fig.tight_layout()
        self._incrustar_figura(parent, fig)

    def _grafico_barras_horizontales(self, parent, etiquetas: list[str], valores: list[float], titulo: str, xlabel: str):
        fig = Figure(figsize=(4.8, 2.8), dpi=95, facecolor=PALETTE["blanco"])
        ax = fig.add_subplot(111)

        if not etiquetas:
            self._dibujar_sin_datos(ax, titulo)
        else:
            etiquetas_cortas = [(e[:22] + "...") if len(e) > 25 else e for e in etiquetas]
            y_pos = range(len(etiquetas_cortas))
            ax.barh(y_pos, valores, color=PALETTE["rojo"], height=0.55)
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(etiquetas_cortas, fontsize=8)
            ax.invert_yaxis()
            ax.set_xlabel(xlabel, fontsize=8, color=PALETTE["plomo_texto"])
            ax.set_title(titulo, fontsize=10, fontweight="bold", color=PALETTE["negro"], pad=8)
            ax.tick_params(axis="x", labelsize=8)
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        fig.tight_layout()
        self._incrustar_figura(parent, fig)

    # =========================================================================
    # PESTAÑA 1: RENDIMIENTO Y ASISTENCIA
    # =========================================================================

    def _render_tab_rendimiento(self):
        self._limpiar_frame(self.tab_rendimiento)
        rend = self.paquete_actual["rendimiento"]
        kpis = self.paquete_actual["kpis"]

        top_charts = tk.Frame(self.tab_rendimiento, bg=PALETTE["plomo_fondo"])
        top_charts.pack(fill="x", pady=(0, 10))
        top_charts.columnconfigure(0, weight=55)
        top_charts.columnconfigure(1, weight=45)

        card_g1 = RoundedCard(
            top_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=10, pady=10,
            expand_body=True, height=245
        )
        card_g1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        top_8 = [r for r in rend if r["total_horas"] > 0][:8]
        self._grafico_barras_horizontales(
            card_g1.body,
            [r["voluntario"] for r in top_8],
            [r["total_horas"] for r in top_8],
            "Top Voluntarios por Horas Cumplidas",
            "Horas Totales"
        )

        card_g2 = RoundedCard(
            top_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=10, pady=10,
            expand_body=True, height=245
        )
        card_g2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._grafico_pastel(
            card_g2.body,
            ["Asistencias", "Inasistencias"],
            [kpis["total_asistencias"], kpis["total_inasistencias"]],
            "Cumplimiento de Asistencia (Cualitativa)"
        )

        # Tabla inferior unificada
        card_tbl = RoundedCard(
            self.tab_rendimiento, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=16, pady=12,
            expand_body=True
        )
        card_tbl.pack(fill=BOTH, expand=True)

        cols = ("ci", "voluntario", "estado", "asignadas", "asist", "faltas", "horas", "cumpl")
        tbl = tb.Treeview(card_tbl.body, columns=cols, show="headings", height=6, style="Rep.Treeview")
        headers = {
            "ci": ("CI", 90),
            "voluntario": ("Voluntario", 210),
            "estado": ("Estado", 85),
            "asignadas": ("Asignadas", 80),
            "asist": ("Asistió", 70),
            "faltas": ("Faltó", 70),
            "horas": ("Horas Totales", 95),
            "cumpl": ("% Cumpl.", 80)
        }
        for c, (txt, w) in headers.items():
            tbl.heading(c, text=txt)
            tbl.column(c, width=w, anchor="center" if c != "voluntario" else "w")

        tbl.tag_configure("par", background=PALETTE["blanco"])
        tbl.tag_configure("impar", background="#F9FAFB")

        for idx, r in enumerate(rend):
            tag = "par" if idx % 2 == 0 else "impar"
            tbl.insert("", tk.END, values=(
                r["ci"],
                r["voluntario"],
                r["estado_voluntario"],
                r["actividades_asignadas"],
                r["asistencias"],
                r["inasistencias"],
                f"{r['total_horas']:.2f}",
                f"{r['porcentaje_cumplimiento']}%"
            ), tags=(tag,))
        tbl.pack(fill=BOTH, expand=True)

    # =========================================================================
    # PESTAÑA 2: VOLUNTARIOS (POR TIEMPO, ESTADO Y REGISTRADOR)
    # =========================================================================

    def _render_tab_voluntarios(self):
        self._limpiar_frame(self.tab_voluntarios)
        vol_tiempo = self.paquete_actual["vol_tiempo"]
        vol_estado = self.paquete_actual["vol_estado"]
        vol_reg = self.paquete_actual["vol_registrador"]

        top_charts = tk.Frame(self.tab_voluntarios, bg=PALETTE["plomo_fondo"])
        top_charts.pack(fill="x", pady=(0, 10))
        top_charts.columnconfigure(0, weight=52)
        top_charts.columnconfigure(1, weight=48)

        card_g1 = RoundedCard(
            top_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=10, pady=10,
            expand_body=True, height=245
        )
        card_g1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._grafico_linea_tiempo(
            card_g1.body,
            [x["periodo"] for x in vol_tiempo],
            [x["cantidad"] for x in vol_tiempo],
            "Cantidad de Voluntarios Inscritos por Tiempo",
            "Postulantes"
        )

        card_g2 = RoundedCard(
            top_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=10, pady=10,
            expand_body=True, height=245
        )
        card_g2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._grafico_pastel(
            card_g2.body,
            [x["estado"] for x in vol_estado],
            [x["cantidad"] for x in vol_estado],
            "Distribución de Voluntarios por Estado"
        )

        card_tbl = RoundedCard(
            self.tab_voluntarios, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=16, pady=12,
            expand_body=True
        )
        card_tbl.pack(fill=BOTH, expand=True)

        tk.Label(
            card_tbl.body,
            text="Relación: Personal que Registra vs. Cantidad de Postulantes Inscritos",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 6))

        tbl = tb.Treeview(card_tbl.body, columns=("usuario", "cantidad"), show="headings", height=5, style="Rep.Treeview")
        tbl.heading("usuario", text="Usuario (Administrador / Registrador)")
        tbl.heading("cantidad", text="Postulantes Registrados")
        tbl.column("usuario", width=350, anchor="w")
        tbl.column("cantidad", width=180, anchor="center")
        tbl.tag_configure("par", background=PALETTE["blanco"])
        tbl.tag_configure("impar", background="#F9FAFB")

        for idx, item in enumerate(vol_reg):
            tag = "par" if idx % 2 == 0 else "impar"
            tbl.insert("", tk.END, values=(item["registrador"], item["cantidad"]), tags=(tag,))
        tbl.pack(fill=BOTH, expand=True)

    # =========================================================================
    # PESTAÑA 3: ACTIVIDADES (POR TIEMPO, ESTADO Y OCUPACIÓN DE CUPOS)
    # =========================================================================

    def _render_tab_actividades(self):
        self._limpiar_frame(self.tab_actividades)
        act_tiempo = self.paquete_actual["act_tiempo"]
        act_estado = self.paquete_actual["act_estado"]
        act_ocup = self.paquete_actual["act_ocupacion"]

        top_charts = tk.Frame(self.tab_actividades, bg=PALETTE["plomo_fondo"])
        top_charts.pack(fill="x", pady=(0, 10))
        top_charts.columnconfigure(0, weight=52)
        top_charts.columnconfigure(1, weight=48)

        card_g1 = RoundedCard(
            top_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=10, pady=10,
            expand_body=True, height=245
        )
        card_g1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._grafico_linea_tiempo(
            card_g1.body,
            [x["periodo"] for x in act_tiempo],
            [x["cantidad"] for x in act_tiempo],
            "Cantidad de Actividades por Tiempo",
            "Actividades"
        )

        card_g2 = RoundedCard(
            top_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=10, pady=10,
            expand_body=True, height=245
        )
        card_g2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._grafico_pastel(
            card_g2.body,
            [x["estado"] for x in act_estado],
            [x["cantidad"] for x in act_estado],
            "Actividades por Estado (Cualitativa)"
        )

        card_tbl = RoundedCard(
            self.tab_actividades, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=16, pady=12,
            expand_body=True
        )
        card_tbl.pack(fill=BOTH, expand=True)

        cols = ("actividad", "fecha", "lugar", "estado", "cupo", "asignados", "ocupacion")
        tbl = tb.Treeview(card_tbl.body, columns=cols, show="headings", height=5, style="Rep.Treeview")
        headers = {
            "actividad": ("Actividad", 200),
            "fecha": ("Fecha", 95),
            "lugar": ("Lugar", 150),
            "estado": ("Estado", 95),
            "cupo": ("Cupo Máx.", 85),
            "asignados": ("Asignados", 85),
            "ocupacion": ("% Ocupación", 90)
        }
        for c, (txt, w) in headers.items():
            tbl.heading(c, text=txt)
            tbl.column(c, width=w, anchor="center" if c not in ("actividad", "lugar") else "w")

        tbl.tag_configure("par", background=PALETTE["blanco"])
        tbl.tag_configure("impar", background="#F9FAFB")

        for idx, a in enumerate(act_ocup):
            tag = "par" if idx % 2 == 0 else "impar"
            tbl.insert("", tk.END, values=(
                a["actividad"],
                str(a["fecha"]),
                a["lugar"],
                a["estado"],
                a["cupo_maximo"],
                a["inscritos"],
                f"{a['porcentaje_ocupacion']}%"
            ), tags=(tag,))
        tbl.pack(fill=BOTH, expand=True)

    # =========================================================================
    # PESTAÑA 4: DONACIONES (TIEMPO, MÉTODO PAGO, TIPO E INSUMOS)
    # =========================================================================

    def _render_tab_donaciones(self):
        self._limpiar_frame(self.tab_donaciones)
        don_tiempo = self.paquete_actual["don_tiempo"]
        don_metodo = self.paquete_actual["don_metodo"]
        don_tipo = self.paquete_actual["don_tipo"]
        don_insumos = self.paquete_actual["don_insumos"]

        grid_charts = tk.Frame(self.tab_donaciones, bg=PALETTE["plomo_fondo"])
        grid_charts.pack(fill=BOTH, expand=True)
        grid_charts.columnconfigure(0, weight=50)
        grid_charts.columnconfigure(1, weight=50)
        grid_charts.rowconfigure(0, weight=50)
        grid_charts.rowconfigure(1, weight=50)

        c1 = RoundedCard(
            grid_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=8, pady=8, expand_body=True
        )
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self._grafico_linea_tiempo(
            c1.body,
            [x["periodo"] for x in don_tiempo],
            [x["total_monto"] for x in don_tiempo],
            "Recaudación Monetaria por Tiempo (Bs.)",
            "Monto (Bs.)"
        )

        c2 = RoundedCard(
            grid_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=8, pady=8, expand_body=True
        )
        c2.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        self._grafico_pastel(
            c2.body,
            [x["metodo"] for x in don_metodo],
            [x["total_monto"] for x in don_metodo],
            "Recaudación por Método de Pago (Bs.)"
        )

        c3 = RoundedCard(
            grid_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=8, pady=8, expand_body=True
        )
        c3.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(6, 0))
        self._grafico_pastel(
            c3.body,
            [x["tipo"] for x in don_tipo],
            [x["cantidad"] for x in don_tipo],
            "Proporción de Donaciones: Dinero vs. Material"
        )

        c4 = RoundedCard(
            grid_charts, radius=18, bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"], padx=8, pady=8, expand_body=True
        )
        c4.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(6, 0))
        self._grafico_barras_horizontales(
            c4.body,
            [f"{x['insumo']} ({x['unidad_medida']})" for x in don_insumos],
            [x["total_cantidad"] for x in don_insumos],
            "Insumos Recibidos por Categoría",
            "Cantidad Total"
        )