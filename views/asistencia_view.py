import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.actividad_controller import ActividadController
from views.ui_components import PALETTE, RoundedCard


class ControlAsistenciaView(tk.Frame):
    """
    Vista para Administrador: Control de asistencia por Hora de Llegada y Partida.
    Solo permite registrar/modificar cuando la actividad está en estado 'Finalizada'.
    """

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = ActividadController()
        self.actividades_map = {}
        self.actividad_actual = None
        self.asignados_cache = {}
        self.asignacion_seleccionada = None

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._cargar_actividades()

    def _configurar_estilos_tabla(self):
        style = tb.Style()
        style.configure(
            "Asis.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=31,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Asis.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 7)
        )
        style.map(
            "Asis.Treeview.Heading",
            background=[("active", PALETTE["plomo_borde"])]
        )
        style.map(
            "Asis.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO (20 pt)
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 14))

        izq = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        izq.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq,
            text="SAVE THE CHILDREN BOLIVIA  •  CERTIFICACIÓN DE HORAS",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["rojo"]
        ).pack(anchor="w")

        tk.Label(
            izq,
            text="Control de Asistencia y Horas Cumplidas",
            font=("Segoe UI", 20, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq,
            text="Registra la hora de llegada y partida una vez finalizada la actividad (acotado al horario programado).",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_ref = tk.Button(
            header,
            text="↻  Sincronizar Estados",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._cargar_actividades
        )
        btn_ref.pack(side="right", pady=6)

        # =====================================================================
        # 2. BARRA SUPERIOR CURVA DE SELECCIÓN DE ACTIVIDAD
        # =====================================================================
        top_card = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=12,
            expand_body=False
        )
        top_card.pack(fill="x", pady=(0, 12))

        tb_body = top_card.body

        tk.Label(
            tb_body,
            text="Actividad a Evaluar:",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 10))

        self.combo_actividad = tb.Combobox(
            tb_body,
            state="readonly",
            width=48,
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_actividad.pack(side="left", padx=(0, 14))
        self.combo_actividad.bind("<<ComboboxSelected>>", lambda _e: self._al_cambiar_actividad())

        self.lbl_duracion = tk.Label(
            tb_body,
            text="Horario programado: -",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            padx=12,
            pady=5
        )
        self.lbl_duracion.pack(side="right")

        # Banner de bloqueo cuando la actividad NO está Finalizada
        self.lbl_aviso_estado = tk.Label(
            self,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo_suave"],
            fg=PALETTE["rojo"],
            padx=14,
            pady=8,
            anchor="w"
        )

        # =====================================================================
        # 3. CUERPO DIVIDIDO: PLANILLA IZQUIERDA + REGISTRO INDIVIDUAL DERECHA
        # =====================================================================
        cuerpo = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=62)
        cuerpo.columnconfigure(1, weight=38)
        cuerpo.rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: PLANILLA ---
        tabla_card = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=16,
            expand_body=True
        )
        tabla_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        bt = tabla_card.body

        tk.Label(
            bt,
            text="📋  Planilla de Voluntarios Asignados",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 10))

        columnas = ("ci", "nombre", "estado_asis", "rango", "horas", "obs")
        self.tabla = tb.Treeview(
            bt,
            columns=columnas,
            show="headings",
            style="Asis.Treeview"
        )
        cols_cfg = {
            "ci": ("CI", 85),
            "nombre": ("Voluntario", 175),
            "estado_asis": ("Asistencia", 90),
            "rango": ("Llegada - Partida", 115),
            "horas": ("Horas", 65),
            "obs": ("Observaciones", 145)
        }
        for col, (titulo, ancho) in cols_cfg.items():
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="center" if col not in ("nombre", "obs") else "w")

        self.tabla.tag_configure("par", background=PALETTE["blanco"])
        self.tabla.tag_configure("impar", background="#F9FAFB")
        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar_voluntario)

        # --- PANEL DERECHO: REGISTRO INDIVIDUAL ---
        form_card = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=18,
            expand_body=True
        )
        form_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        bf = form_card.body

        tk.Label(
            bf,
            text="⏱  Registro Individual de Participación",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 10))

        self.lbl_voluntario = tk.Label(
            bf,
            text="Selecciona un voluntario de la planilla izquierda.",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            padx=12,
            pady=10,
            wraplength=300,
            justify="left"
        )
        self.lbl_voluntario.pack(fill="x", pady=(0, 12))

        # Switch Asistió / Faltó
        self.var_asistio = tk.BooleanVar(value=True)
        self.chk_asistio = tb.Checkbutton(
            bf,
            text="El voluntario ASISTIÓ a la actividad",
            variable=self.var_asistio,
            bootstyle="success-round-toggle",
            command=self._al_cambiar_check_asistio
        )
        self.chk_asistio.pack(anchor="w", pady=(0, 12))

        # Fila de Hora de Llegada y Hora de Partida
        horas_grid = tk.Frame(bf, bg=PALETTE["blanco"])
        horas_grid.pack(fill="x", pady=(0, 8))
        horas_grid.columnconfigure(0, weight=1, uniform="h_cols")
        horas_grid.columnconfigure(1, weight=1, uniform="h_cols")

        tk.Label(
            horas_grid,
            text="Hora de Llegada *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.combo_llegada = tb.Combobox(
            horas_grid,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_llegada.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(3, 0))
        self.combo_llegada.bind("<<ComboboxSelected>>", lambda _e: self._al_cambiar_hora_llegada())

        tk.Label(
            horas_grid,
            text="Hora de Partida *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.combo_partida = tb.Combobox(
            horas_grid,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_partida.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(3, 0))
        self.combo_partida.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_preview_horas())

        # Indicador calculado automáticamente
        self.lbl_horas_calc = tk.Label(
            bf,
            text="Horas efectivas calculadas: 0.00 hrs",
            font=("Segoe UI", 9, "bold"),
            bg="#DCFCE7",
            fg="#15803D",
            padx=12,
            pady=7,
            anchor="w"
        )
        self.lbl_horas_calc.pack(fill="x", pady=(4, 12))

        # Observaciones
        tk.Label(
            bf,
            text="Observaciones de desempeño (Opcional):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 4))

        self.txt_obs = tk.Text(
            bf,
            height=4,
            font=("Segoe UI", 9),
            bd=1,
            relief="solid"
        )
        self.txt_obs.pack(fill="x", pady=(0, 14))

        self.btn_guardar = tk.Button(
            bf,
            text="✓  Guardar Asistencia",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=10,
            cursor="hand2",
            command=self._guardar_asistencia
        )
        self.btn_guardar.pack(fill="x")

    def _cargar_actividades(self):
        try:
            todas = self.controller.obtener_actividades("Todas")
            validas = [a for a in todas if a["estado"] != "Cancelada"]

            self.actividades_map.clear()
            etiquetas = []
            for a in validas:
                etiqueta = f"[{a['estado']}] {a['nombre']} — {a['fecha']}"
                self.actividades_map[etiqueta] = a
                etiquetas.append(etiqueta)

            self.combo_actividad["values"] = etiquetas
            if etiquetas:
                # Priorizar seleccionar una actividad 'Finalizada' si existe
                finalizadas = [e for e in etiquetas if e.startswith("[Finalizada]")]
                self.combo_actividad.set(finalizadas[0] if finalizadas else etiquetas[0])
                self._al_cambiar_actividad()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_cambiar_actividad(self):
        etiqueta = self.combo_actividad.get()
        act = self.actividades_map.get(etiqueta)
        if not act:
            return

        self.actividad_actual = act
        self.asignacion_seleccionada = None
        duracion_max = float(act["duracion_horas"])

        self.lbl_duracion.config(
            text=f"Horario: {act['hora_inicio_str']} a {act['hora_fin_str']}  (Máx: {duracion_max:.2f} hrs)"
        )

        # Inicializar opciones de llegada y partida acotadas al horario de la actividad
        llegadas = self.controller.generar_horas_llegada(act["hora_inicio_str"], act["hora_fin_str"])
        self.combo_llegada["values"] = llegadas
        if llegadas:
            self.combo_llegada.set(llegadas[0])
            self._al_cambiar_hora_llegada(preferida_partida=act["hora_fin_str"])

        self._aplicar_bloqueo_por_estado()
        self._cargar_planilla()

    def _aplicar_bloqueo_por_estado(self):
        """Bloquea toda edición si la actividad no está en estado 'Finalizada'."""
        if not self.actividad_actual:
            return

        es_finalizada = self.actividad_actual.get("estado") == "Finalizada"

        if es_finalizada:
            self.lbl_aviso_estado.pack_forget()
            self.chk_asistio.config(state="normal")
            self.txt_obs.config(state="normal")
            self.btn_guardar.config(
                state="normal",
                text="✓  Guardar Asistencia",
                bg=PALETTE["rojo"],
                cursor="hand2"
            )
            self._al_cambiar_check_asistio()
        else:
            estado_act = self.actividad_actual.get("estado", "Pendiente")
            self.lbl_aviso_estado.config(
                text=(
                    f"🔒  Actividad '{estado_act}': No se permite marcar asistencia ni modificar horas "
                    f"mientras la jornada no haya finalizado ({self.actividad_actual['hora_fin_str']})."
                )
            )
            self.lbl_aviso_estado.pack(fill="x", pady=(0, 10), before=self.master.winfo_children()[-1] if False else None)
            self.chk_asistio.config(state="disabled")
            self.combo_llegada.config(state="disabled")
            self.combo_partida.config(state="disabled")
            self.txt_obs.config(state="disabled")
            self.btn_guardar.config(
                state="disabled",
                text=f"🔒  Bloqueado ({estado_act})",
                bg=PALETTE["plomo_claro"],
                cursor="arrow"
            )

    def _al_cambiar_hora_llegada(self, preferida_partida: str = None):
        if not self.actividad_actual:
            return
        llegada = self.combo_llegada.get()
        partidas = self.controller.generar_horas_partida(llegada, self.actividad_actual["hora_fin_str"])
        self.combo_partida["values"] = partidas
        if not partidas:
            self.combo_partida.set("")
        elif preferida_partida and preferida_partida in partidas:
            self.combo_partida.set(preferida_partida)
        elif self.combo_partida.get() not in partidas:
            self.combo_partida.set(partidas[-1])
        self._actualizar_preview_horas()

    def _actualizar_preview_horas(self):
        if not self.actividad_actual:
            return
        duracion_max = float(self.actividad_actual["duracion_horas"])
        if not self.var_asistio.get():
            self.lbl_horas_calc.config(
                text="Inasistencia seleccionada: 0.00 hrs",
                bg=PALETTE["rojo_suave"],
                fg=PALETTE["rojo"]
            )
            return

        horas = self.controller.calcular_horas_rango(
            self.combo_llegada.get(),
            self.combo_partida.get()
        )
        self.lbl_horas_calc.config(
            text=f"✓ Horas efectivas calculadas: {horas:.2f} hrs  (Tope actividad: {duracion_max:.2f} hrs)",
            bg="#DCFCE7",
            fg="#15803D"
        )

    def _cargar_planilla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.asignados_cache.clear()

        if not self.actividad_actual:
            return

        try:
            lista = self.controller.obtener_asignados(self.actividad_actual["id_actividad"])
            for idx, row in enumerate(lista):
                iid = str(row["id_asignacion"])
                self.asignados_cache[iid] = row
                tag = "par" if idx % 2 == 0 else "impar"

                llegada_saved, partida_saved, obs_limpia = self.controller.extraer_horario_observaciones(
                    row["observaciones"]
                )

                if row["id_asistencia"] is None:
                    estado_txt = "Pendiente"
                    rango_txt = "-"
                    horas_txt = "-"
                elif bool(row["asistio"]):
                    estado_txt = "Asistió"
                    rango_txt = (
                        f"{llegada_saved} - {partida_saved}"
                        if llegada_saved and partida_saved
                        else f"{self.actividad_actual['hora_inicio_str']} - {self.actividad_actual['hora_fin_str']}"
                    )
                    horas_txt = f"{float(row['horas_cumplidas']):.2f}"
                else:
                    estado_txt = "Faltó"
                    rango_txt = "-"
                    horas_txt = "0.00"

                self.tabla.insert("", tk.END, iid=iid, values=(
                    row["ci"],
                    row["nombre_completo"],
                    estado_txt,
                    rango_txt,
                    horas_txt,
                    obs_limpia
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar_voluntario(self, _event):
        sel = self.tabla.selection()
        if not sel:
            return
        row = self.asignados_cache.get(sel[0])
        if not row or not self.actividad_actual:
            return

        self.asignacion_seleccionada = row
        self.lbl_voluntario.config(
            text=f"Voluntario: {row['nombre_completo']}\nCI: {row['ci']}  |  Tel: {row['telefono'] or 'N/A'}"
        )

        es_finalizada = self.actividad_actual.get("estado") == "Finalizada"
        llegada_saved, partida_saved, obs_limpia = self.controller.extraer_horario_observaciones(
            row["observaciones"]
        )

        if row["id_asistencia"] is not None:
            asistio = bool(row["asistio"])
            self.var_asistio.set(asistio)
            if asistio and llegada_saved and llegada_saved in self.combo_llegada["values"]:
                self.combo_llegada.set(llegada_saved)
                self._al_cambiar_hora_llegada(preferida_partida=partida_saved)
            else:
                self.combo_llegada.set(self.actividad_actual["hora_inicio_str"])
                self._al_cambiar_hora_llegada(preferida_partida=self.actividad_actual["hora_fin_str"])
        else:
            self.var_asistio.set(True)
            self.combo_llegada.set(self.actividad_actual["hora_inicio_str"])
            self._al_cambiar_hora_llegada(preferida_partida=self.actividad_actual["hora_fin_str"])

        self.txt_obs.config(state="normal")
        self.txt_obs.delete("1.0", tk.END)
        if obs_limpia:
            self.txt_obs.insert("1.0", obs_limpia)

        if es_finalizada:
            self._al_cambiar_check_asistio()
        else:
            self.txt_obs.config(state="disabled")

    def _al_cambiar_check_asistio(self):
        if not self.actividad_actual or self.actividad_actual.get("estado") != "Finalizada":
            return

        if self.var_asistio.get():
            self.combo_llegada.config(state="readonly")
            self.combo_partida.config(state="readonly")
        else:
            self.combo_llegada.config(state="disabled")
            self.combo_partida.config(state="disabled")

        self._actualizar_preview_horas()

    def _guardar_asistencia(self):
        exito, mensaje = self.controller.guardar_asistencia(
            actividad=self.actividad_actual,
            asignacion=self.asignacion_seleccionada,
            asistio=self.var_asistio.get(),
            hora_llegada=self.combo_llegada.get(),
            hora_partida=self.combo_partida.get(),
            observaciones=self.txt_obs.get("1.0", tk.END)
        )
        if not exito:
            messagebox.showwarning("Control de Asistencia", mensaje)
            return

        messagebox.showinfo("Asistencia Registrada", mensaje)
        self._cargar_planilla()