import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from controllers.reporte_controller import ReporteController


class ReportesRendimientoView(tb.Frame):
    """Vista de Analítica, Gráficos de 2 Variables, Rendimiento y Exportación Excel."""

    PALETA_ROJA = ["#991B1B", "#DC2626", "#F87171", "#FBBF24", "#7F1D1D", "#FCA5A5"]

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = ReporteController()
        self.paquete_actual = None

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_reportes(usar_todo=True)

    def _construir_ui(self):
        # Encabezado + Botón Exportar Excel
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 10))

        titulos_frame = tk.Frame(header, bg="#FFF5F5")
        titulos_frame.pack(side="left")

        tk.Label(
            titulos_frame,
            text="Reportes Estadísticos y Rendimiento",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            titulos_frame,
            text="Análisis cuantitativo, cualitativo, evolución temporal y desempeño de voluntarios.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w")

        tb.Button(
            header,
            text="📥 Exportar a Excel (.xlsx)",
            bootstyle="success",
            command=self._exportar_excel
        ).pack(side="right", ipady=6, ipadx=10)

        # Barra de Filtros por Fecha
        filtro_bar = tk.Frame(self, bg="#FFFFFF", padx=16, pady=10)
        filtro_bar.pack(fill="x", pady=(0, 10))

        tk.Label(filtro_bar, text="Desde:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side="left", padx=(0, 6))
        self.date_desde = tb.DateEntry(filtro_bar, bootstyle="danger", dateformat="%Y-%m-%d", width=13)
        self.date_desde.pack(side="left", padx=(0, 14))

        tk.Label(filtro_bar, text="Hasta:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side="left", padx=(0, 6))
        self.date_hasta = tb.DateEntry(filtro_bar, bootstyle="danger", dateformat="%Y-%m-%d", width=13)
        self.date_hasta.pack(side="left", padx=(0, 14))

        tb.Button(
            filtro_bar, text="🔍 Filtrar Rango", bootstyle="danger",
            command=lambda: self._cargar_reportes(usar_todo=False)
        ).pack(side="left", padx=(0, 8))

        tb.Button(
            filtro_bar, text="Ver Todo el Historial", bootstyle="danger-outline",
            command=lambda: self._cargar_reportes(usar_todo=True)
        ).pack(side="left")

        self.lbl_periodo = tk.Label(
            filtro_bar,
            text="Mostrando: Todo el historial",
            font=("Segoe UI", 9, "bold"),
            bg="#FEF2F2",
            fg="#7F1D1D",
            padx=10,
            pady=4
        )
        self.lbl_periodo.pack(side="right")

        # Notebook con 4 sub-pestañas analíticas
        self.notebook = tb.Notebook(self, bootstyle="danger")
        self.notebook.pack(fill=BOTH, expand=True)

        self.tab_rendimiento = tk.Frame(self.notebook, bg="#FFF5F5", padx=10, pady=10)
        self.tab_voluntarios = tk.Frame(self.notebook, bg="#FFF5F5", padx=10, pady=10)
        self.tab_actividades = tk.Frame(self.notebook, bg="#FFF5F5", padx=10, pady=10)
        self.tab_donaciones = tk.Frame(self.notebook, bg="#FFF5F5", padx=10, pady=10)

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
        ax.set_title(titulo, fontsize=10, fontweight="bold", color="#7F1D1D", pad=10)
        ax.text(0.5, 0.5, "Sin datos registrados en este período", ha="center", va="center", fontsize=9, color="#64748B")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    def _grafico_pastel(self, parent, etiquetas: list[str], valores: list[float], titulo: str):
        fig = Figure(figsize=(4.4, 3.1), dpi=95, facecolor="#FFFFFF")
        ax = fig.add_subplot(111)

        pares = [(e, v) for e, v in zip(etiquetas, valores) if v > 0]
        if not pares:
            self._dibujar_sin_datos(ax, titulo)
        else:
            labs, vals = zip(*pares)
            colores = [self.PALETA_ROJA[i % len(self.PALETA_ROJA)] for i in range(len(vals))]
            ax.pie(
                vals,
                labels=labs,
                autopct="%1.1f%%",
                startangle=140,
                colors=colores,
                textprops={"fontsize": 8, "color": "#1E293B"}
            )
            ax.set_title(titulo, fontsize=10, fontweight="bold", color="#7F1D1D", pad=8)

        fig.tight_layout()
        self._incrustar_figura(parent, fig)

    def _grafico_linea_tiempo(self, parent, periodos: list[str], valores: list[float], titulo: str, ylabel: str):
        fig = Figure(figsize=(4.8, 3.1), dpi=95, facecolor="#FFFFFF")
        ax = fig.add_subplot(111)

        if not periodos:
            self._dibujar_sin_datos(ax, titulo)
        else:
            ax.plot(periodos, valores, marker="o", color="#B91C1C", linewidth=2.2, markersize=6)
            ax.fill_between(periodos, valores, color="#FECACA", alpha=0.35)
            ax.set_title(titulo, fontsize=10, fontweight="bold", color="#7F1D1D", pad=8)
            ax.set_ylabel(ylabel, fontsize=8, color="#475569")
            ax.tick_params(axis="x", labelsize=8, rotation=20)
            ax.tick_params(axis="y", labelsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        fig.tight_layout()
        self._incrustar_figura(parent, fig)

    def _grafico_barras_horizontales(self, parent, etiquetas: list[str], valores: list[float], titulo: str, xlabel: str):
        fig = Figure(figsize=(4.8, 3.1), dpi=95, facecolor="#FFFFFF")
        ax = fig.add_subplot(111)

        if not etiquetas:
            self._dibujar_sin_datos(ax, titulo)
        else:
            etiquetas_cortas = [(e[:22] + "...") if len(e) > 25 else e for e in etiquetas]
            y_pos = range(len(etiquetas_cortas))
            ax.barh(y_pos, valores, color="#B91C1C", height=0.55)
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(etiquetas_cortas, fontsize=8)
            ax.invert_yaxis()
            ax.set_xlabel(xlabel, fontsize=8, color="#475569")
            ax.set_title(titulo, fontsize=10, fontweight="bold", color="#7F1D1D", pad=8)
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

        # Parte superior: 2 gráficos lado a lado
        top_charts = tk.Frame(self.tab_rendimiento, bg="#FFF5F5")
        top_charts.pack(fill="x", pady=(0, 10))
        top_charts.columnconfigure(0, weight=55)
        top_charts.columnconfigure(1, weight=45)

        card_g1 = tk.Frame(top_charts, bg="#FFFFFF", padx=8, pady=8)
        card_g1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        top_8 = [r for r in rend if r["total_horas"] > 0][:8]
        self._grafico_barras_horizontales(
            card_g1,
            [r["voluntario"] for r in top_8],
            [r["total_horas"] for r in top_8],
            "Top Voluntarios por Horas Cumplidas",
            "Horas Totales"
        )

        card_g2 = tk.Frame(top_charts, bg="#FFFFFF", padx=8, pady=8)
        card_g2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._grafico_pastel(
            card_g2,
            ["Asistencias", "Inasistencias"],
            [kpis["total_asistencias"], kpis["total_inasistencias"]],
            "Cumplimiento de Asistencia (Cualitativa)"
        )

        # Parte inferior: Tabla completa de rendimiento (SIN ID)
        card_tbl = tk.Frame(self.tab_rendimiento, bg="#FFFFFF", padx=12, pady=10)
        card_tbl.pack(fill=BOTH, expand=True)

        cols = ("ci", "voluntario", "estado", "asignadas", "asist", "faltas", "horas", "cumpl")
        tbl = tb.Treeview(card_tbl, columns=cols, show="headings", height=6, bootstyle="danger")
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

        for r in rend:
            tbl.insert("", tk.END, values=(
                r["ci"],
                r["voluntario"],
                r["estado_voluntario"],
                r["actividades_asignadas"],
                r["asistencias"],
                r["inasistencias"],
                f"{r['total_horas']:.2f}",
                f"{r['porcentaje_cumplimiento']}%"
            ))
        tbl.pack(fill=BOTH, expand=True)

    # =========================================================================
    # PESTAÑA 2: VOLUNTARIOS (POR TIEMPO, ESTADO Y REGISTRADOR)
    # =========================================================================

    def _render_tab_voluntarios(self):
        self._limpiar_frame(self.tab_voluntarios)
        vol_tiempo = self.paquete_actual["vol_tiempo"]
        vol_estado = self.paquete_actual["vol_estado"]
        vol_reg = self.paquete_actual["vol_registrador"]

        top_charts = tk.Frame(self.tab_voluntarios, bg="#FFF5F5")
        top_charts.pack(fill="x", pady=(0, 10))
        top_charts.columnconfigure(0, weight=52)
        top_charts.columnconfigure(1, weight=48)

        card_g1 = tk.Frame(top_charts, bg="#FFFFFF", padx=8, pady=8)
        card_g1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._grafico_linea_tiempo(
            card_g1,
            [x["periodo"] for x in vol_tiempo],
            [x["cantidad"] for x in vol_tiempo],
            "Cantidad de Voluntarios Inscritos por Tiempo",
            "Postulantes"
        )

        card_g2 = tk.Frame(top_charts, bg="#FFFFFF", padx=8, pady=8)
        card_g2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._grafico_pastel(
            card_g2,
            [x["estado"] for x in vol_estado],
            [x["cantidad"] for x in vol_estado],
            "Distribución de Voluntarios por Estado"
        )

        # Tabla inferior: Inscripciones por Usuario (Recepcionista/Admin)
        card_tbl = tk.Frame(self.tab_voluntarios, bg="#FFFFFF", padx=12, pady=10)
        card_tbl.pack(fill=BOTH, expand=True)

        tk.Label(
            card_tbl,
            text="Relación: Personal que Registra vs. Cantidad de Postulantes Inscritos",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(0, 6))

        tbl = tb.Treeview(card_tbl, columns=("usuario", "cantidad"), show="headings", height=5, bootstyle="danger")
        tbl.heading("usuario", text="Usuario (Recepcionista / Administrador)")
        tbl.heading("cantidad", text="Postulantes Registrados")
        tbl.column("usuario", width=350, anchor="w")
        tbl.column("cantidad", width=180, anchor="center")

        for item in vol_reg:
            tbl.insert("", tk.END, values=(item["registrador"], item["cantidad"]))
        tbl.pack(fill=BOTH, expand=True)

    # =========================================================================
    # PESTAÑA 3: ACTIVIDADES (POR TIEMPO, ESTADO Y OCUPACIÓN DE CUPOS)
    # =========================================================================

    def _render_tab_actividades(self):
        self._limpiar_frame(self.tab_actividades)
        act_tiempo = self.paquete_actual["act_tiempo"]
        act_estado = self.paquete_actual["act_estado"]
        act_ocup = self.paquete_actual["act_ocupacion"]

        top_charts = tk.Frame(self.tab_actividades, bg="#FFF5F5")
        top_charts.pack(fill="x", pady=(0, 10))
        top_charts.columnconfigure(0, weight=52)
        top_charts.columnconfigure(1, weight=48)

        card_g1 = tk.Frame(top_charts, bg="#FFFFFF", padx=8, pady=8)
        card_g1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._grafico_linea_tiempo(
            card_g1,
            [x["periodo"] for x in act_tiempo],
            [x["cantidad"] for x in act_tiempo],
            "Cantidad de Actividades por Tiempo",
            "Actividades"
        )

        card_g2 = tk.Frame(top_charts, bg="#FFFFFF", padx=8, pady=8)
        card_g2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._grafico_pastel(
            card_g2,
            [x["estado"] for x in act_estado],
            [x["cantidad"] for x in act_estado],
            "Actividades por Estado (Cualitativa)"
        )

        # Tabla inferior: Cupo Máximo vs. Voluntarios Asignados
        card_tbl = tk.Frame(self.tab_actividades, bg="#FFFFFF", padx=12, pady=10)
        card_tbl.pack(fill=BOTH, expand=True)

        cols = ("actividad", "fecha", "lugar", "estado", "cupo", "asignados", "ocupacion")
        tbl = tb.Treeview(card_tbl, columns=cols, show="headings", height=5, bootstyle="danger")
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

        for a in act_ocup:
            tbl.insert("", tk.END, values=(
                a["actividad"],
                str(a["fecha"]),
                a["lugar"],
                a["estado"],
                a["cupo_maximo"],
                a["inscritos"],
                f"{a['porcentaje_ocupacion']}%"
            ))
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

        # Rejilla 2x2 de gráficos para cubrir todas las relaciones de donaciones
        grid_charts = tk.Frame(self.tab_donaciones, bg="#FFF5F5")
        grid_charts.pack(fill=BOTH, expand=True)
        grid_charts.columnconfigure(0, weight=50)
        grid_charts.columnconfigure(1, weight=50)
        grid_charts.rowconfigure(0, weight=50)
        grid_charts.rowconfigure(1, weight=50)

        # Gráfico 1: Donaciones Monetarias por Tiempo
        c1 = tk.Frame(grid_charts, bg="#FFFFFF", padx=6, pady=6)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        self._grafico_linea_tiempo(
            c1,
            [x["periodo"] for x in don_tiempo],
            [x["total_monto"] for x in don_tiempo],
            "Recaudación Monetaria por Tiempo (Bs.)",
            "Monto (Bs.)"
        )

        # Gráfico 2: Recaudación por Método de Pago (Pastel)
        c2 = tk.Frame(grid_charts, bg="#FFFFFF", padx=6, pady=6)
        c2.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        self._grafico_pastel(
            c2,
            [x["metodo"] for x in don_metodo],
            [x["total_monto"] for x in don_metodo],
            "Recaudación por Método de Pago (Bs.)"
        )

        # Gráfico 3: Proporción DINERO vs. MATERIAL (Pastel)
        c3 = tk.Frame(grid_charts, bg="#FFFFFF", padx=6, pady=6)
        c3.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(5, 0))
        self._grafico_pastel(
            c3,
            [x["tipo"] for x in don_tipo],
            [x["cantidad"] for x in don_tipo],
            "Proporción de Donaciones: Dinero vs. Material"
        )

        # Gráfico 4: Cantidad de Insumos Donados en Especie (Barras)
        c4 = tk.Frame(grid_charts, bg="#FFFFFF", padx=6, pady=6)
        c4.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(5, 0))
        self._grafico_barras_horizontales(
            c4,
            [f"{x['insumo']} ({x['unidad_medida']})" for x in don_insumos],
            [x["total_cantidad"] for x in don_insumos],
            "Insumos Recibidos por Categoría",
            "Cantidad Total"
        )