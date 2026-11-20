import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from models.actividad_model import ActividadModel


class MisActividadesView(tb.Frame):
    """Pestaña 1 del Voluntario: Agenda formal de actividades asignadas y ficha de detalles."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.model = ActividadModel()
        self.perfil = None
        self.actividades_cache = {}

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO INSTITUCIONAL (20 pt)
        # =====================================================================
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 14))

        izq_hdr = tk.Frame(header, bg="#FFF5F5")
        izq_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq_hdr,
            text="SAVE THE CHILDREN BOLIVIA  •  PORTAL DEL VOLUNTARIO",
            font=("Segoe UI", 9, "bold"),
            bg="#FFF5F5",
            fg="#B91C1C"
        ).pack(anchor="w")

        tk.Label(
            izq_hdr,
            text="Mis Actividades Asignadas",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq_hdr,
            text="Consulta tus próximas jornadas comunitarias, horarios, lugares de encuentro y estado de participación.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#475569"
        ).pack(anchor="w")

        tb.Button(
            header,
            text="↻  Actualizar Agenda",
            bootstyle="danger",
            command=self._cargar_datos
        ).pack(side="right", ipady=6, ipadx=14, pady=6)

        # =====================================================================
        # 2. TARJETAS DE RESUMEN DEL VOLUNTARIO
        # =====================================================================
        kpi_row = tk.Frame(self, bg="#FFF5F5")
        kpi_row.pack(fill="x", pady=(0, 14))

        self.lbl_kpi_pend, self.lbl_kpi_pend_sub = self._crear_kpi(
            kpi_row, 0, "ACTIVIDADES PRÓXIMAS", "#D97706"
        )
        self.lbl_kpi_comp, self.lbl_kpi_comp_sub = self._crear_kpi(
            kpi_row, 1, "JORNADAS COMPLETADAS", "#15803D"
        )
        self.lbl_kpi_est, self.lbl_kpi_est_sub = self._crear_kpi(
            kpi_row, 2, "ESTADO DE VOLUNTARIADO", "#B91C1C"
        )

        # =====================================================================
        # 3. BARRA DE FILTRO
        # =====================================================================
        filtro_bar = tk.Frame(self, bg="#FFFFFF", padx=16, pady=10)
        filtro_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            filtro_bar,
            text="Mostrar actividades:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(side="left", padx=(0, 8))

        self.combo_estado = tb.Combobox(
            filtro_bar,
            values=["Todas", "Programada", "En Curso", "Finalizada", "Cancelada"],
            state="readonly",
            width=18,
            bootstyle="danger"
        )
        self.combo_estado.set("Todas")
        self.combo_estado.pack(side="left")
        self.combo_estado.bind("<<ComboboxSelected>>", lambda e: self._cargar_datos())

        tk.Label(
            filtro_bar,
            text="Haz clic en una fila para ver la descripción completa e instrucciones",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#64748B"
        ).pack(side="right")

        # =====================================================================
        # 4. TABLA DE ACTIVIDADES (SIN IDs VISIBLES)
        # =====================================================================
        card_tbl = tk.Frame(self, bg="#FFFFFF", padx=16, pady=14)
        card_tbl.pack(fill=BOTH, expand=True, pady=(0, 12))

        cols = ("actividad", "fecha", "horario", "lugar", "estado_act", "asistencia")
        self.tabla = tb.Treeview(card_tbl, columns=cols, show="headings", height=7, bootstyle="danger")
        cfg = {
            "actividad": ("Actividad Comunitaria", 220),
            "fecha": ("Fecha", 95),
            "horario": ("Horario", 115),
            "lugar": ("Punto de Encuentro / Lugar", 180),
            "estado_act": ("Estado Actividad", 110),
            "asistencia": ("Mi Asistencia", 115)
        }
        for c, (tit, w) in cfg.items():
            self.tabla.heading(c, text=tit)
            self.tabla.column(c, width=w, anchor="center" if c not in ("actividad", "lugar") else "w")

        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        # =====================================================================
        # 5. FICHA INFERIOR DE DETALLE DE LA ACTIVIDAD SELECCIONADA
        # =====================================================================
        card_det = tk.Frame(self, bg="#FFFFFF", padx=20, pady=14)
        card_det.pack(fill="x")

        top_det = tk.Frame(card_det, bg="#FFFFFF")
        top_det.pack(fill="x", pady=(0, 8))

        self.lbl_det_titulo = tk.Label(
            top_det,
            text="Detalle de la Actividad (Selecciona una actividad de la lista superior)",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        )
        self.lbl_det_titulo.pack(side="left")

        self.lbl_det_badge = tk.Label(
            top_det,
            text="SIN SELECCIÓN",
            font=("Segoe UI", 8, "bold"),
            bg="#F1F5F9",
            fg="#475569",
            padx=10,
            pady=3
        )
        self.lbl_det_badge.pack(side="right")

        box_det = tk.Frame(card_det, bg="#FFF5F5", padx=14, pady=10)
        box_det.pack(fill="x")

        self.lbl_det_info = tk.Label(
            box_det,
            text="• Lugar y Horario: -\n• Descripción de la Actividad: -\n• Observaciones del Coordinador: -",
            font=("Segoe UI", 9),
            bg="#FFF5F5",
            fg="#1E293B",
            justify="left",
            anchor="w"
        )
        self.lbl_det_info.pack(fill="x")

    def _crear_kpi(self, parent, col: int, titulo: str, color: str):
        parent.columnconfigure(col, weight=1, uniform="vol_kpi1")
        padx = (0, 8) if col == 0 else ((8, 0) if col == 2 else 8)

        card = tk.Frame(parent, bg="#FFFFFF", padx=18, pady=14)
        card.grid(row=0, column=col, sticky="nsew", padx=padx)

        tk.Frame(card, bg=color, height=4).pack(fill="x", pady=(0, 10))
        tk.Label(card, text=titulo, font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#475569", anchor="w").pack(fill="x")
        lbl_v = tk.Label(card, text="0", font=("Segoe UI", 22, "bold"), bg="#FFFFFF", fg=color, anchor="w")
        lbl_v.pack(fill="x", pady=(2, 2))
        lbl_s = tk.Label(card, text="-", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B", anchor="w")
        lbl_s.pack(fill="x")
        return lbl_v, lbl_s

    def _cargar_datos(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)
        self.actividades_cache.clear()
        self.lbl_det_titulo.config(text="Detalle de la Actividad (Selecciona una actividad de la lista superior)")
        self.lbl_det_badge.config(text="SIN SELECCIÓN", bg="#F1F5F9", fg="#475569")
        self.lbl_det_info.config(text="• Lugar y Horario: -\n• Descripción de la Actividad: -\n• Observaciones del Coordinador: -")

        try:
            self.perfil = self.model.obtener_perfil_voluntario_por_usuario(self.sesion["id_usuario"])
            if not self.perfil:
                messagebox.showwarning("Perfil no vinculado", "No se encontró un perfil de voluntario asociado a esta cuenta.")
                return

            todas = self.model.listar_actividades_voluntario(self.perfil["id_voluntario"], "Todas")
            pendientes = sum(1 for a in todas if a["estado_actividad"] in ("Programada", "En Curso"))
            completadas = sum(1 for a in todas if a["id_asistencia"] is not None and int(a["asistio"] or 0) == 1)

            self.lbl_kpi_pend.config(text=str(pendientes))
            self.lbl_kpi_pend_sub.config(text="Programadas o en curso")

            self.lbl_kpi_comp.config(text=str(completadas))
            self.lbl_kpi_comp_sub.config(text=f"De {len(todas)} actividades asignadas")

            self.lbl_kpi_est.config(text=self.perfil["estado"])
            self.lbl_kpi_est_sub.config(text=f"CI: {self.perfil['ci']}")

            filtradas = self.model.listar_actividades_voluntario(
                self.perfil["id_voluntario"],
                self.combo_estado.get()
            )

            for act in filtradas:
                iid = str(act["id_asignacion"])
                self.actividades_cache[iid] = act

                if act["id_asistencia"] is None:
                    asist_txt = "Pendiente"
                elif int(act["asistio"] or 0) == 1:
                    asist_txt = f"✓ Asistió ({act['horas_cumplidas']:.1f}h)"
                else:
                    asist_txt = "✕ Inasistencia"

                self.tabla.insert("", tk.END, iid=iid, values=(
                    act["actividad"],
                    str(act["fecha"]),
                    f"{act['hora_inicio_str']} - {act['hora_fin_str']}",
                    act["lugar"],
                    act["estado_actividad"],
                    asist_txt
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar(self, _event):
        sel = self.tabla.selection()
        if not sel:
            return
        act = self.actividades_cache.get(sel[0])
        if not act:
            return

        est = act["estado_actividad"]
        colores = {
            "Programada": ("#FEF3C7", "#B45309"),
            "En Curso": ("#DBEAFE", "#1D4ED8"),
            "Finalizada": ("#DCFCE7", "#15803D"),
            "Cancelada": ("#FEE2E2", "#B91C1C")
        }
        bg_b, fg_b = colores.get(est, ("#F1F5F9", "#475569"))

        self.lbl_det_titulo.config(text=f"Actividad: {act['actividad']}")
        self.lbl_det_badge.config(text=est.upper(), bg=bg_b, fg=fg_b)

        desc = act["descripcion"] or "Sin descripción adicional registrada."
        obs = act["observaciones"] or "Sin observaciones registradas."
        self.lbl_det_info.config(
            text=(
                f"• Fecha y Horario: {act['fecha']} de {act['hora_inicio_str']} a {act['hora_fin_str']} ({act['duracion_horas']:.1f} hrs estimadas)  |  Lugar: {act['lugar']}\n"
                f"• Descripción: {desc}\n"
                f"• Observaciones del Coordinador: {obs}"
            )
        )


class MiHistorialHorasView(tb.Frame):
    """Pestaña 2 del Voluntario: Constancia oficial de horas acumuladas e historial de participación."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.model = ActividadModel()

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_historial()

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO INSTITUCIONAL (20 pt)
        # =====================================================================
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 14))

        izq_hdr = tk.Frame(header, bg="#FFF5F5")
        izq_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq_hdr,
            text="SAVE THE CHILDREN BOLIVIA  •  CONSTANCIA DE SERVICIO",
            font=("Segoe UI", 9, "bold"),
            bg="#FFF5F5",
            fg="#B91C1C"
        ).pack(anchor="w")

        tk.Label(
            izq_hdr,
            text="Mi Historial de Horas y Participación",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq_hdr,
            text="Resumen oficial de tus horas de voluntariado validadas y registro de asistencia por actividad.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#475569"
        ).pack(anchor="w")

        tb.Button(
            header,
            text="↻  Actualizar Constancia",
            bootstyle="danger",
            command=self._cargar_historial
        ).pack(side="right", ipady=6, ipadx=14, pady=6)

        # =====================================================================
        # 2. CREDENCIAL DIGITAL DEL VOLUNTARIO
        # =====================================================================
        cred_card = tk.Frame(self, bg="#FFFFFF", padx=20, pady=14)
        cred_card.pack(fill="x", pady=(0, 14))

        self.lbl_credencial = tk.Label(
            cred_card,
            text="Cargando datos oficiales del voluntario...",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D",
            anchor="w",
            justify="left"
        )
        self.lbl_credencial.pack(fill="x")

        # =====================================================================
        # 3. 3 TARJETAS KPI DE RENDIMIENTO PERSONAL
        # =====================================================================
        kpi_grid = tk.Frame(self, bg="#FFF5F5")
        kpi_grid.pack(fill="x", pady=(0, 14))

        self.lbl_horas_val, self.lbl_horas_sub = self._crear_kpi(
            kpi_grid, 0, "TOTAL HORAS CUMPLIDAS", "#B91C1C"
        )
        self.lbl_asist_val, self.lbl_asist_sub = self._crear_kpi(
            kpi_grid, 1, "ASISTENCIAS CONFIRMADAS", "#15803D"
        )
        self.lbl_cump_val, self.lbl_cump_sub = self._crear_kpi(
            kpi_grid, 2, "ÍNDICE DE CUMPLIMIENTO", "#1D4ED8"
        )

        # =====================================================================
        # 4. TABLA DETALLADA DE HORAS VALIDADAS
        # =====================================================================
        card_tbl = tk.Frame(self, bg="#FFFFFF", padx=18, pady=16)
        card_tbl.pack(fill=BOTH, expand=True)

        tk.Label(
            card_tbl,
            text="Detalle Cronológico de Participación",
            font=("Segoe UI", 12, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(0, 10))

        cols = ("fecha", "actividad", "lugar", "estado_asist", "horas", "observaciones")
        self.tabla = tb.Treeview(card_tbl, columns=cols, show="headings", height=9, bootstyle="danger")
        cfg = {
            "fecha": ("Fecha", 95),
            "actividad": ("Actividad", 200),
            "lugar": ("Lugar", 160),
            "estado_asist": ("Asistencia", 115),
            "horas": ("Horas Validadas", 110),
            "observaciones": ("Observaciones", 210)
        }
        for c, (tit, w) in cfg.items():
            self.tabla.heading(c, text=tit)
            self.tabla.column(c, width=w, anchor="center" if c in ("fecha", "estado_asist", "horas") else "w")

        self.tabla.pack(fill=BOTH, expand=True)

    def _crear_kpi(self, parent, col: int, titulo: str, color: str):
        parent.columnconfigure(col, weight=1, uniform="vol_kpi2")
        padx = (0, 8) if col == 0 else ((8, 0) if col == 2 else 8)

        card = tk.Frame(parent, bg="#FFFFFF", padx=18, pady=16)
        card.grid(row=0, column=col, sticky="nsew", padx=padx)

        tk.Frame(card, bg=color, height=4).pack(fill="x", pady=(0, 10))
        tk.Label(card, text=titulo, font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#475569", anchor="w").pack(fill="x")
        lbl_v = tk.Label(card, text="0", font=("Segoe UI", 24, "bold"), bg="#FFFFFF", fg=color, anchor="w")
        lbl_v.pack(fill="x", pady=(4, 2))
        lbl_s = tk.Label(card, text="-", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B", anchor="w")
        lbl_s.pack(fill="x")
        return lbl_v, lbl_s

    def _cargar_historial(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)

        try:
            perfil = self.model.obtener_perfil_voluntario_por_usuario(self.sesion["id_usuario"])
            if not perfil:
                self.lbl_credencial.config(text="No se encontró perfil de voluntario asociado a esta cuenta.")
                return

            f_adm = perfil["fecha_admision"] if perfil["fecha_admision"] else "No registrada"
            self.lbl_credencial.config(
                text=(
                    f"👤 Voluntario(a): {perfil['nombre_completo']}    |    "
                    f"🪪 CI: {perfil['ci']}    |    "
                    f"📅 Fecha de Admisión: {f_adm}    |    "
                    f"✅ Estado: {perfil['estado']}"
                )
            )

            actividades = self.model.listar_actividades_voluntario(perfil["id_voluntario"], "Todas")

            total_horas = sum(float(a["horas_cumplidas"] or 0.0) for a in actividades)
            evaluadas = [a for a in actividades if a["id_asistencia"] is not None]
            asistencias = sum(1 for a in evaluadas if int(a["asistio"] or 0) == 1)
            inasistencias = len(evaluadas) - asistencias
            porcentaje = round((asistencias / len(evaluadas)) * 100, 1) if evaluadas else 0.0

            self.lbl_horas_val.config(text=f"{total_horas:,.2f} hrs")
            self.lbl_horas_sub.config(text="Horas acumuladas certificadas")

            self.lbl_asist_val.config(text=str(asistencias))
            self.lbl_asist_sub.config(text=f"{inasistencias} inasistencia(s) registrada(s)")

            self.lbl_cump_val.config(text=f"{porcentaje:.1f}%")
            self.lbl_cump_sub.config(text=f"Sobre {len(evaluadas)} jornada(s) evaluada(s)")

            for act in actividades:
                if act["id_asistencia"] is None:
                    est_asist = "Pendiente"
                    hrs_txt = "0.00 hrs"
                elif int(act["asistio"] or 0) == 1:
                    est_asist = "✓ Asistió"
                    hrs_txt = f"{act['horas_cumplidas']:.2f} hrs"
                else:
                    est_asist = "✕ No asistió"
                    hrs_txt = "0.00 hrs"

                self.tabla.insert("", tk.END, values=(
                    str(act["fecha"]),
                    act["actividad"],
                    act["lugar"],
                    est_asist,
                    hrs_txt,
                    act["observaciones"] or "-"
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))