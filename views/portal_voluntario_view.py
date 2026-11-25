from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.actividad_controller import ActividadController
from views.ui_components import PALETTE, RoundedCard


def _configurar_estilo_tabla_portal():
    """Aplica la misma configuración limpia en plomo y negro que el Panel General."""
    style = tb.Style()
    style.configure(
        "Port.Treeview",
        background=PALETTE["blanco"],
        foreground=PALETTE["negro"],
        fieldbackground=PALETTE["blanco"],
        rowheight=31,
        borderwidth=0,
        font=("Segoe UI", 9)
    )
    style.configure(
        "Port.Treeview.Heading",
        background=PALETTE["plomo_fondo"],
        foreground=PALETTE["negro"],
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 9, "bold"),
        padding=(8, 7)
    )
    style.map(
        "Port.Treeview.Heading",
        background=[("active", PALETTE["plomo_borde"])]
    )
    style.map(
        "Port.Treeview",
        background=[("selected", PALETTE["rojo_suave"])],
        foreground=[("selected", PALETTE["negro"])]
    )


class ModalAutocancelarParticipacion(tk.Toplevel):
    """Modal para que el voluntario cancele una actividad programada con advertencia de strikes."""

    def __init__(
        self,
        master,
        actividad_item: dict,
        strikes_actuales: int,
        sesion: dict,
        controller: ActividadController,
        on_confirmado
    ):
        super().__init__(master)
        self.actividad_item = actividad_item
        self.strikes_actuales = int(strikes_actuales or 0)
        self.sesion = sesion
        self.controller = controller
        self.on_confirmado = on_confirmado

        self.title("Cancelar Mi Participación")
        self.configure(bg=PALETTE["plomo_fondo"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self.strikes_previstos, self.horas_restantes = self._calcular_penalidad_prevista()
        self._construir_ui()
        self._centrar()

    def _calcular_penalidad_prevista(self) -> tuple[int, float]:
        dt_inicio = datetime.combine(self.actividad_item["fecha"], datetime.min.time())
        try:
            h, m = map(int, self.actividad_item["hora_inicio_str"].split(":"))
            dt_inicio = dt_inicio.replace(hour=h, minute=m)
        except Exception:
            pass
        horas_rest = (dt_inicio - datetime.now()).total_seconds() / 3600.0
        strikes = 2 if horas_rest < 24 else 1
        return strikes, max(horas_rest, 0.0)

    def _centrar(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = max(20, (self.winfo_screenwidth() - w) // 2)
        y = max(20, (self.winfo_screenheight() - h) // 2)
        self.geometry(f"+{x}+{y}")

    def _construir_ui(self):
        wrap = tk.Frame(self, bg=PALETTE["plomo_fondo"], padx=18, pady=16)
        wrap.pack(fill=BOTH, expand=True)

        hdr = tk.Frame(wrap, bg=PALETTE["negro"], padx=14, pady=10)
        hdr.pack(fill="x", pady=(0, 10))

        tk.Label(
            hdr,
            text="Confirmar Cancelación de Participación",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            hdr,
            text=f"Actividad: {self.actividad_item['actividad']}  •  {self.actividad_item['fecha']} ({self.actividad_item['hora_inicio_str']})",
            font=("Segoe UI", 8),
            bg=PALETTE["negro"],
            fg=PALETTE["plomo_claro"],
            anchor="w"
        ).pack(fill="x")

        card = tk.Frame(
            wrap,
            bg=PALETTE["blanco"],
            highlightbackground=PALETTE["plomo_borde"],
            highlightthickness=1,
            padx=16,
            pady=14
        )
        card.pack(fill="x")

        nuevo_total = self.strikes_actuales + self.strikes_previstos
        aviso_box = tk.Frame(card, bg=PALETTE["rojo_suave"], padx=12, pady=10)
        aviso_box.pack(fill="x", pady=(0, 10))

        detalle_tiempo = (
            f"Faltan menos de 24 horas ({self.horas_restantes:.1f} hrs) para el inicio."
            if self.strikes_previstos == 2
            else f"Anticipación mayor a 24 horas ({self.horas_restantes:.1f} hrs restantes)."
        )
        texto_alerta = (
            f"⚠️ Penalización aplicable: +{self.strikes_previstos} Strike(s) ({detalle_tiempo})\n"
            f"• Tu acumulado pasará de {self.strikes_actuales}/5 a {nuevo_total}/5 strikes."
        )
        if nuevo_total >= 5:
            texto_alerta += "\n🚨 ATENCIÓN: Al llegar a 5 strikes tu cuenta pasará a 'Inactivo_Definitivo' y se cerrará."

        tk.Label(
            aviso_box,
            text=texto_alerta,
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["rojo_suave"],
            fg=PALETTE["rojo"],
            justify="left",
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            card,
            text="Motivo o justificación de la cancelación (obligatorio):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.entry_motivo = tb.Entry(card, font=("Segoe UI", 10), width=52)
        self.entry_motivo.pack(fill="x", ipady=4, pady=(0, 4))
        self.entry_motivo.focus_set()

        btn_row = tk.Frame(wrap, bg=PALETTE["plomo_fondo"])
        btn_row.pack(fill="x", pady=(10, 0))

        tk.Button(
            btn_row,
            text="Volver",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            bd=1,
            relief="solid",
            padx=14,
            pady=7,
            cursor="hand2",
            command=self.destroy
        ).pack(side="left")

        tk.Button(
            btn_row,
            text=f"Confirmar Cancelación (+{self.strikes_previstos} Strike)",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._confirmar
        ).pack(side="right")

    def _confirmar(self):
        exito, resultado = self.controller.cancelar_participacion_desde_portal(
            id_usuario=self.sesion["id_usuario"],
            actividad_item=self.actividad_item,
            motivo=self.entry_motivo.get()
        )
        if not exito:
            messagebox.showwarning("Validación", str(resultado), parent=self)
            return

        inactivado = False
        if isinstance(resultado, dict):
            inactivado = bool(resultado.get("inactivado_definitivo"))
            msg = (
                f"Se canceló tu participación en '{resultado['actividad']}'.\n"
                f"• Strikes aplicados: +{resultado['strikes_aplicados']}\n"
                f"• Acumulado actual: {resultado['total_strikes']}/5 strikes"
            )
            if inactivado:
                msg += (
                    "\n\n🚨 Has alcanzado el límite de 5 strikes. Tu cuenta pasó a estado "
                    "'Inactivo_Definitivo' y se ha cerrado tu acceso al sistema."
                )
            messagebox.showinfo("Participación Cancelada", msg, parent=self)

        self.destroy()
        if callable(self.on_confirmado):
            self.on_confirmado(inactivado)


class MisActividadesView(tk.Frame):
    """Pestaña 1 del Voluntario: Agenda formal de actividades asignadas y ficha de detalles."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = ActividadController()
        self.paquete_actual = None
        self.actividades_cache = {}
        self.actividad_seleccionada = None

        self.pack(fill=BOTH, expand=True)
        _configurar_estilo_tabla_portal()
        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO INSTITUCIONAL
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 12))

        izq_hdr = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        izq_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq_hdr,
            text="SAVE THE CHILDREN BOLIVIA  •  PORTAL DEL VOLUNTARIO",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["rojo"]
        ).pack(anchor="w")

        tk.Label(
            izq_hdr,
            text="Mis Actividades Asignadas",
            font=("Segoe UI", 20, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq_hdr,
            text="Consulta tus próximas jornadas comunitarias, horarios, lugares de encuentro y estado de participación.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_ref = tk.Button(
            header,
            text="↻  Actualizar Agenda",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._cargar_datos
        )
        btn_ref.pack(side="right", pady=6)
        btn_ref.bind("<Enter>", lambda _e: btn_ref.config(bg=PALETTE["rojo_hover"]))
        btn_ref.bind("<Leave>", lambda _e: btn_ref.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # 2. TARJETAS CURVAS DE RESUMEN DEL VOLUNTARIO (4 KPIs)
        # =====================================================================
        kpi_row = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        kpi_row.pack(fill="x", pady=(0, 8))

        self.lbl_kpi_pend, self.lbl_kpi_pend_sub = self._crear_kpi(
            kpi_row, 0, "ACTIVIDADES PRÓXIMAS", PALETTE["rojo"]
        )
        self.lbl_kpi_comp, self.lbl_kpi_comp_sub = self._crear_kpi(
            kpi_row, 1, "JORNADAS COMPLETADAS", PALETTE["negro"]
        )
        self.lbl_kpi_est, self.lbl_kpi_est_sub = self._crear_kpi(
            kpi_row, 2, "ESTADO DE VOLUNTARIADO", PALETTE["rojo_oscuro"]
        )
        self.lbl_kpi_stk, self.lbl_kpi_stk_sub = self._crear_kpi(
            kpi_row, 3, "STRIKES ACUMULADOS", PALETTE["negro"]
        )

        # =====================================================================
        # 3. BARRA CURVA DE FILTRO Y CANCELACIÓN VOLUNTARIA
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
        filtro_card.pack(fill="x", pady=(0, 10))

        fb = filtro_card.body

        tk.Label(
            fb,
            text="Mostrar actividades:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 8))

        self.combo_estado = tb.Combobox(
            fb,
            values=["Todas", "Programada", "En Curso", "Finalizada", "Cancelada"],
            state="readonly",
            width=18,
            bootstyle="danger"
        )
        self.combo_estado.set("Todas")
        self.combo_estado.pack(side="left")
        self.combo_estado.bind("<<ComboboxSelected>>", lambda _e: self._cargar_datos())

        self.btn_cancelar_part = tk.Button(
            fb,
            text="✕  Cancelar Mi Participación",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["rojo_suave"],
            fg=PALETTE["rojo"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._abrir_autocancelacion
        )
        self.btn_cancelar_part.pack(side="right")
        self.btn_cancelar_part.bind(
            "<Enter>",
            lambda _e: self.btn_cancelar_part.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"])
        )
        self.btn_cancelar_part.bind(
            "<Leave>",
            lambda _e: self.btn_cancelar_part.config(bg=PALETTE["rojo_suave"], fg=PALETTE["rojo"])
        )

        tk.Label(
            fb,
            text="Selecciona una fila para ver detalles o cancelar una actividad programada",
            font=("Segoe UI", 9),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"]
        ).pack(side="right", padx=(0, 14))

        # =====================================================================
        # 4. TARJETA CURVA CON TABLA UNIFICADA
        # =====================================================================
        card_tbl = RoundedCard(
            self,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=14,
            expand_body=True
        )
        card_tbl.pack(fill=BOTH, expand=True, pady=(0, 10))

        cols = ("actividad", "fecha", "horario", "lugar", "estado_act", "asistencia")
        self.tabla = tb.Treeview(
            card_tbl.body,
            columns=cols,
            show="headings",
            height=5,
            style="Port.Treeview"
        )
        cfg = {
            "actividad": ("Actividad Comunitaria", 220),
            "fecha": ("Fecha", 95),
            "horario": ("Horario", 115),
            "lugar": ("Punto de Encuentro / Lugar", 180),
            "estado_act": ("Estado Actividad", 110),
            "asistencia": ("Mi Participación", 125)
        }
        for c, (tit, w) in cfg.items():
            self.tabla.heading(c, text=tit)
            self.tabla.column(c, width=w, anchor="center" if c not in ("actividad", "lugar") else "w")

        self.tabla.tag_configure("par", background=PALETTE["blanco"])
        self.tabla.tag_configure("impar", background="#F9FAFB")
        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        # =====================================================================
        # 5. FICHA INFERIOR CURVA DE DETALLE
        # =====================================================================
        card_det = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=14,
            expand_body=False
        )
        card_det.pack(fill="x")

        bd = card_det.body

        top_det = tk.Frame(bd, bg=PALETTE["blanco"])
        top_det.pack(fill="x", pady=(0, 8))

        self.lbl_det_titulo = tk.Label(
            top_det,
            text="Detalle de la Actividad (Selecciona una actividad de la lista superior)",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        )
        self.lbl_det_titulo.pack(side="left")

        self.lbl_det_badge = tk.Label(
            top_det,
            text="SIN SELECCIÓN",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            padx=10,
            pady=3
        )
        self.lbl_det_badge.pack(side="right")

        box_det = tk.Frame(bd, bg=PALETTE["plomo_fondo"], padx=14, pady=10)
        box_det.pack(fill="x")

        self.lbl_det_info = tk.Label(
            box_det,
            text="• Lugar y Horario: -\n• Descripción de la Actividad: -\n• Observaciones del Coordinador: -",
            font=("Segoe UI", 9),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            justify="left",
            anchor="w"
        )
        self.lbl_det_info.pack(fill="x")

    def _crear_kpi(self, parent, col: int, titulo: str, color: str):
        parent.columnconfigure(col, weight=1, uniform="vol_kpi1")
        padx = (0, 6) if col == 0 else ((6, 0) if col == 3 else 6)

        card = RoundedCard(
            parent,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=16,
            pady=13,
            expand_body=False
        )
        card.grid(row=0, column=col, sticky="nsew", padx=padx)

        b = card.body
        tk.Frame(b, bg=color, height=4).pack(fill="x", pady=(0, 8))
        tk.Label(b, text=titulo, font=("Segoe UI", 8, "bold"), bg=PALETTE["blanco"], fg=PALETTE["plomo_texto"], anchor="w").pack(fill="x")
        lbl_v = tk.Label(b, text="0", font=("Segoe UI", 21, "bold"), bg=PALETTE["blanco"], fg=color, anchor="w")
        lbl_v.pack(fill="x", pady=(2, 2))
        lbl_s = tk.Label(b, text="-", font=("Segoe UI", 8), bg=PALETTE["blanco"], fg=PALETTE["plomo_texto"], anchor="w")
        lbl_s.pack(fill="x")
        return lbl_v, lbl_s

    def _cargar_datos(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)
        self.actividades_cache.clear()
        self.actividad_seleccionada = None
        self.lbl_det_titulo.config(text="Detalle de la Actividad (Selecciona una actividad de la lista superior)")
        self.lbl_det_badge.config(text="SIN SELECCIÓN", bg=PALETTE["plomo_fondo"], fg=PALETTE["plomo_texto"])
        self.lbl_det_info.config(text="• Lugar y Horario: -\n• Descripción de la Actividad: -\n• Observaciones del Coordinador: -")

        try:
            paquete = self.controller.obtener_datos_portal_voluntario(
                self.sesion["id_usuario"],
                self.combo_estado.get()
            )
            self.paquete_actual = paquete
            perfil = paquete["perfil"]
            resumen = paquete["resumen"]
            todas = paquete["todas"]

            pendientes = resumen["programadas"] + resumen["en_curso"]
            self.lbl_kpi_pend.config(text=str(pendientes))
            self.lbl_kpi_pend_sub.config(text="Programadas o en curso")

            self.lbl_kpi_comp.config(text=str(resumen["asistencias"]))
            self.lbl_kpi_comp_sub.config(text=f"De {len(todas)} actividades asignadas")

            self.lbl_kpi_est.config(text=perfil["estado"])
            self.lbl_kpi_est_sub.config(text=f"CI: {perfil['ci']}")

            strikes_act = int(resumen.get("strikes_actuales", 0))
            color_stk = PALETTE["rojo"] if strikes_act >= 3 else PALETTE["negro"]
            self.lbl_kpi_stk.config(text=f"{strikes_act} / 5", fg=color_stk)
            self.lbl_kpi_stk_sub.config(
                text="5 strikes = baja definitiva" if strikes_act < 5 else "Límite alcanzado"
            )

            for idx, act in enumerate(paquete["actividades"]):
                iid = str(act["id_asignacion"])
                self.actividades_cache[iid] = act
                tag = "par" if idx % 2 == 0 else "impar"

                if act.get("estado_asignacion") == "Cancelada":
                    asist_txt = "🚫 Cancelada"
                elif act["id_asistencia"] is None:
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
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar(self, _event):
        sel = self.tabla.selection()
        if not sel:
            return
        act = self.actividades_cache.get(sel[0])
        if not act:
            return
        self.actividad_seleccionada = act

        est = act["estado_actividad"]
        colores = {
            "Programada": ("#FEF3C7", "#B45309"),
            "En Curso": ("#DBEAFE", "#1D4ED8"),
            "Finalizada": ("#DCFCE7", "#15803D"),
            "Cancelada": (PALETTE["rojo_suave"], PALETTE["rojo"])
        }
        bg_b, fg_b = colores.get(est, (PALETTE["plomo_fondo"], PALETTE["plomo_texto"]))

        titulo_extra = " [ASIGNACIÓN CANCELADA]" if act.get("estado_asignacion") == "Cancelada" else ""
        self.lbl_det_titulo.config(text=f"Actividad: {act['actividad']}{titulo_extra}")
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

    def _abrir_autocancelacion(self):
        act = self.actividad_seleccionada
        if not act:
            messagebox.showwarning("Atención", "Selecciona primero una actividad 'Programada' de la tabla.")
            return
        if act.get("estado_asignacion") == "Cancelada":
            messagebox.showwarning("Atención", "Esta asignación ya fue cancelada previamente.")
            return
        if act.get("estado_actividad") != "Programada":
            messagebox.showwarning(
                "No permitido",
                "Solo puedes cancelar tu participación en actividades que aún estén en estado 'Programada'."
            )
            return

        strikes_act = (
            self.paquete_actual["perfil"]["total_strikes"]
            if self.paquete_actual else 0
        )

        def _post_cancelacion(inactivado_definitivo: bool):
            if inactivado_definitivo:
                top = self.winfo_toplevel()
                if hasattr(top, "cerrar_sesion"):
                    top.cerrar_sesion()
                else:
                    top.destroy()
                return
            self._cargar_datos()

        ModalAutocancelarParticipacion(
            master=self,
            actividad_item=act,
            strikes_actuales=strikes_act,
            sesion=self.sesion,
            controller=self.controller,
            on_confirmado=_post_cancelacion
        )


class MiHistorialHorasView(tk.Frame):
    """Pestaña 2 del Voluntario: Constancia oficial de horas acumuladas, strikes e historial."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = ActividadController()
        self.paquete_actual = None

        self.pack(fill=BOTH, expand=True)
        _configurar_estilo_tabla_portal()
        self._construir_ui()
        self._cargar_historial()

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO INSTITUCIONAL
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        izq_hdr = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        izq_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq_hdr,
            text="Mi Historial de Horas y Participación",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq_hdr,
            text="Resumen oficial de tus horas de voluntariado validadas, asistencia y control disciplinario.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_ref = tk.Button(
            header,
            text="↻  Actualizar Constancia",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._cargar_historial
        )
        btn_ref.pack(side="right", pady=6)
        btn_ref.bind("<Enter>", lambda _e: btn_ref.config(bg=PALETTE["rojo_hover"]))
        btn_ref.bind("<Leave>", lambda _e: btn_ref.config(bg=PALETTE["rojo"]))

        btn_excel = tk.Button(
            header,
            text="📊  Exportar Excel",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._exportar_excel
        )
        btn_excel.pack(side="right", pady=6, padx=(0, 8))

        # =====================================================================
        # 2. CREDENCIAL DIGITAL CURVA DEL VOLUNTARIO
        # =====================================================================
        cred_card = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=12,
            expand_body=False
        )
        cred_card.pack(fill="x", pady=(0, 10))

        self.lbl_credencial = tk.Label(
            cred_card.body,
            text="Cargando datos oficiales del voluntario...",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w",
            justify="left"
        )
        self.lbl_credencial.pack(fill="x")

        # =====================================================================
        # 3. 4 TARJETAS KPI CURVAS DE RENDIMIENTO Y STRIKES
        # =====================================================================
        kpi_grid = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        kpi_grid.pack(fill="x", pady=(0, 10))

        self.lbl_horas_val, self.lbl_horas_sub = self._crear_kpi(
            kpi_grid, 0, "TOTAL HORAS CUMPLIDAS", PALETTE["rojo"]
        )
        self.lbl_asist_val, self.lbl_asist_sub = self._crear_kpi(
            kpi_grid, 1, "ASISTENCIAS CONFIRMADAS", PALETTE["negro"]
        )
        self.lbl_cump_val, self.lbl_cump_sub = self._crear_kpi(
            kpi_grid, 2, "ÍNDICE DE CUMPLIMIENTO", PALETTE["rojo_oscuro"]
        )
        self.lbl_stk_val, self.lbl_stk_sub = self._crear_kpi(
            kpi_grid, 3, "STRIKES ACUMULADOS", PALETTE["negro"]
        )

        # =====================================================================
        # 4. TARJETA CURVA CON TABLA DETALLADA DE PARTICIPACIÓN
        # =====================================================================
        card_tbl = RoundedCard(
            self,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=14,
            expand_body=True
        )
        card_tbl.pack(fill=BOTH, expand=True, pady=(0, 10))

        tk.Label(
            card_tbl.body,
            text="📋  Detalle Cronológico de Participación",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 8))

        cols = ("fecha", "actividad", "lugar", "estado_asist", "horas", "observaciones")
        self.tabla = tb.Treeview(
            card_tbl.body,
            columns=cols,
            show="headings",
            height=5,
            style="Port.Treeview"
        )
        cfg = {
            "fecha": ("Fecha", 95),
            "actividad": ("Actividad", 200),
            "lugar": ("Lugar", 160),
            "estado_asist": ("Asistencia", 125),
            "horas": ("Horas Validadas", 110),
            "observaciones": ("Observaciones", 210)
        }
        for c, (tit, w) in cfg.items():
            self.tabla.heading(c, text=tit)
            self.tabla.column(c, width=w, anchor="center" if c in ("fecha", "estado_asist", "horas") else "w")

        self.tabla.tag_configure("par", background=PALETTE["blanco"])
        self.tabla.tag_configure("impar", background="#F9FAFB")
        self.tabla.pack(fill=BOTH, expand=True)

        # =====================================================================
        # 5. TARJETA INFERIOR DE AUDITORÍA DE STRIKES
        # =====================================================================
        card_stk = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=12,
            expand_body=False
        )
        card_stk.pack(fill="x")

        tk.Label(
            card_stk.body,
            text="⚠️  Historial de Strikes Disciplinarios (Límite máximo: 5 strikes)",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 6))

        cols_stk = ("fecha", "actividad", "cantidad", "motivo")
        self.tabla_strikes = tb.Treeview(
            card_stk.body,
            columns=cols_stk,
            show="headings",
            height=3,
            style="Port.Treeview"
        )
        cfg_stk = {
            "fecha": ("Fecha Registro", 130),
            "actividad": ("Actividad Asociada", 220),
            "cantidad": ("Penalización", 100),
            "motivo": ("Motivo / Justificación", 420)
        }
        for c, (tit, w) in cfg_stk.items():
            self.tabla_strikes.heading(c, text=tit)
            self.tabla_strikes.column(c, width=w, anchor="center" if c in ("fecha", "cantidad") else "w")

        self.tabla_strikes.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_strikes.tag_configure("impar", background="#F9FAFB")
        self.tabla_strikes.pack(fill="x")

    def _crear_kpi(self, parent, col: int, titulo: str, color: str):
        parent.columnconfigure(col, weight=1, uniform="vol_kpi2")
        padx = (0, 6) if col == 0 else ((6, 0) if col == 3 else 6)

        card = RoundedCard(
            parent,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=16,
            pady=13,
            expand_body=False
        )
        card.grid(row=0, column=col, sticky="nsew", padx=padx)

        b = card.body
        tk.Frame(b, bg=color, height=4).pack(fill="x", pady=(0, 8))
        tk.Label(b, text=titulo, font=("Segoe UI", 8, "bold"), bg=PALETTE["blanco"], fg=PALETTE["plomo_texto"], anchor="w").pack(fill="x")
        lbl_v = tk.Label(b, text="0", font=("Segoe UI", 21, "bold"), bg=PALETTE["blanco"], fg=color, anchor="w")
        lbl_v.pack(fill="x", pady=(2, 2))
        lbl_s = tk.Label(b, text="-", font=("Segoe UI", 8), bg=PALETTE["blanco"], fg=PALETTE["plomo_texto"], anchor="w")
        lbl_s.pack(fill="x")
        return lbl_v, lbl_s

    def _cargar_historial(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)
        for w in self.tabla_strikes.get_children():
            self.tabla_strikes.delete(w)

        try:
            paquete = self.controller.obtener_datos_portal_voluntario(self.sesion["id_usuario"], "Todas")
            self.paquete_actual = paquete
            perfil = paquete["perfil"]
            resumen = paquete["resumen"]
            actividades = paquete["todas"]
            strikes_lista = paquete.get("strikes", [])

            f_adm = perfil["fecha_admision"] if perfil["fecha_admision"] else "No registrada"
            strikes_act = int(resumen.get("strikes_actuales", 0))
            self.lbl_credencial.config(
                text=(
                    f"👤 Voluntario(a): {perfil['nombre_completo']}    |    "
                    f"🪪 CI: {perfil['ci']}    |    "
                    f"📅 Admisión: {f_adm}    |    "
                    f"✅ Estado: {perfil['estado']}    |    "
                    f"⚠️ Strikes: {strikes_act}/5"
                )
            )

            evaluadas = resumen["asistencias"] + resumen["inasistencias"]
            porcentaje = resumen["cumplimiento"] if evaluadas > 0 else 0.0

            self.lbl_horas_val.config(text=f"{resumen['total_horas']:,.2f} hrs")
            self.lbl_horas_sub.config(text="Horas acumuladas certificadas")

            self.lbl_asist_val.config(text=str(resumen["asistencias"]))
            self.lbl_asist_sub.config(text=f"{resumen['inasistencias']} inasistencia(s) registrada(s)")

            self.lbl_cump_val.config(text=f"{porcentaje:.1f}%")
            self.lbl_cump_sub.config(text=f"Sobre {evaluadas} jornada(s) evaluada(s)")

            color_stk = PALETTE["rojo"] if strikes_act >= 3 else PALETTE["negro"]
            self.lbl_stk_val.config(text=f"{strikes_act} / 5", fg=color_stk)
            self.lbl_stk_sub.config(
                text="Sin infracciones registradas" if strikes_act == 0 else f"{len(strikes_lista)} registro(s) en historial"
            )

            for idx, act in enumerate(actividades):
                tag = "par" if idx % 2 == 0 else "impar"
                if act.get("estado_asignacion") == "Cancelada":
                    est_asist = "🚫 Cancelada"
                    hrs_txt = "0.00 hrs"
                elif act["id_asistencia"] is None:
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
                ), tags=(tag,))

            for idx, st in enumerate(strikes_lista):
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla_strikes.insert("", tk.END, values=(
                    st["fecha_str"],
                    st["actividad"] or "General / Administrativa",
                    f"+{st['cantidad_strikes']} Strike(s)",
                    st["motivo"] or "-"
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _exportar_excel(self):
        if not self.paquete_actual:
            messagebox.showwarning("Atención", "No hay datos cargados para exportar.")
            return

        ci = self.paquete_actual["perfil"]["ci"]
        ruta = filedialog.asksaveasfilename(
            title="Guardar Constancia de Voluntariado en Excel",
            defaultextension=".xlsx",
            initialfile=f"Historial_Voluntariado_{ci}.xlsx",
            filetypes=[("Archivo Excel", "*.xlsx")]
        )
        if not ruta:
            return

        exito, mensaje = self.controller.exportar_historial_voluntario_excel(ruta, self.paquete_actual)
        if exito:
            messagebox.showinfo("Exportación Exitosa", mensaje)
        else:
            messagebox.showerror("Error al Exportar", mensaje)