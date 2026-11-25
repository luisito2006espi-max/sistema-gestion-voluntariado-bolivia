import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.actividad_controller import ActividadController
from views.ui_components import PALETTE, RoundedCard


def _configurar_estilo_tabla_operaciones():
    """Configura el estilo limpio en plomo y negro igual al Panel General."""
    style = tb.Style()
    style.configure(
        "Op.Treeview",
        background=PALETTE["blanco"],
        foreground=PALETTE["negro"],
        fieldbackground=PALETTE["blanco"],
        rowheight=31,
        borderwidth=0,
        font=("Segoe UI", 9)
    )
    style.configure(
        "Op.Treeview.Heading",
        background=PALETTE["plomo_fondo"],
        foreground=PALETTE["negro"],
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 9, "bold"),
        padding=(8, 7)
    )
    style.map(
        "Op.Treeview.Heading",
        background=[("active", PALETTE["plomo_borde"])]
    )
    style.map(
        "Op.Treeview",
        background=[("selected", PALETTE["rojo_suave"])],
        foreground=[("selected", PALETTE["negro"])]
    )


class GestionActividadesView(tk.Frame):
    """Vista para Administrador: Programación, edición, cancelación y restablecimiento de actividades."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = ActividadController()
        self.actividades_cache = {}
        self.actividad_seleccionada = None
        self.actividad_en_edicion = None

        self.pack(fill=BOTH, expand=True)
        _configurar_estilo_tabla_operaciones()
        self._construir_ui()
        self._cargar_actividades()

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Gestión de Actividades Comunitarias",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            header,
            text="Las actividades pasan automáticamente a 'En Curso' y 'Finalizada' según su horario (duración permitida: 1 a 5 horas).",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        # =====================================================================
        # 2. TARJETA CURVA DE FORMULARIO (CREAR / EDITAR)
        # =====================================================================
        card_form = RoundedCard(
            self,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=22,
            pady=10,
            expand_body=False
        )
        card_form.pack(fill="x", pady=(0, 8))

        bf = card_form.body

        self.lbl_titulo_form = tk.Label(
            bf,
            text="Nueva Actividad (* Campos obligatorios)",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        )
        self.lbl_titulo_form.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        for c in range(4):
            bf.columnconfigure(c, weight=1, uniform="act_cols")

        # Fila 1: Nombre + Lugar
        tk.Label(bf, text="Nombre de la Actividad *", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=1, column=0, columnspan=2, sticky="w", padx=6)
        self.entry_nombre = tb.Entry(bf, font=("Segoe UI", 10))
        self.entry_nombre.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, ipady=4, pady=(2, 4))

        tk.Label(bf, text="Lugar / Punto de Encuentro *", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=1, column=2, columnspan=2, sticky="w", padx=6)
        self.entry_lugar = tb.Entry(bf, font=("Segoe UI", 10))
        self.entry_lugar.grid(row=2, column=2, columnspan=2, sticky="ew", padx=6, ipady=4, pady=(2, 4))

        # Fila 2: Fecha, Hora Inicio, Hora Fin, Cupo Máximo
        tk.Label(bf, text="Fecha *", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=3, column=0, sticky="w", padx=6)
        self.date_fecha = tb.DateEntry(bf, bootstyle="danger", dateformat="%Y-%m-%d")
        self.date_fecha.grid(row=4, column=0, sticky="ew", padx=6, pady=(2, 4))

        tk.Label(bf, text="Hora Inicio *", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=3, column=1, sticky="w", padx=6)
        horas_inicio = self.controller.generar_horas_inicio()
        self.combo_hora_ini = tb.Combobox(
            bf,
            values=horas_inicio,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_hora_ini.set("08:30")
        self.combo_hora_ini.grid(row=4, column=1, sticky="ew", padx=6, pady=(2, 4))
        self.combo_hora_ini.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_horas_fin())

        tk.Label(bf, text="Hora Fin (1h - 5h) *", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=3, column=2, sticky="w", padx=6)
        self.combo_hora_fin = tb.Combobox(
            bf,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_hora_fin.grid(row=4, column=2, sticky="ew", padx=6, pady=(2, 4))
        self._actualizar_horas_fin("11:30")

        tk.Label(bf, text="Cupo Máximo (3 - 15) *", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=3, column=3, sticky="w", padx=6)
        self.combo_cupo = tb.Combobox(
            bf,
            values=self.controller.generar_cupos_validos(),
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_cupo.set("10")
        self.combo_cupo.grid(row=4, column=3, sticky="ew", padx=6, pady=(2, 4))

        # Fila 3: Descripción + Botones
        tk.Label(bf, text="Descripción / Tareas a realizar", font=("Segoe UI", 9, "bold"), bg=PALETTE["blanco"], fg=PALETTE["negro"]).grid(row=5, column=0, columnspan=3, sticky="w", padx=6)
        self.entry_desc = tb.Entry(bf, font=("Segoe UI", 10))
        self.entry_desc.grid(row=6, column=0, columnspan=3, sticky="ew", padx=6, ipady=4)

        acciones_form = tk.Frame(bf, bg=PALETTE["blanco"])
        acciones_form.grid(row=6, column=3, sticky="ew", padx=6)

        self.btn_guardar = tk.Button(
            acciones_form,
            text="+ Programar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self._guardar_formulario
        )
        self.btn_guardar.pack(side="right", fill="x", expand=True)

        self.btn_cancelar_edicion = tk.Button(
            acciones_form,
            text="Cancelar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
            command=self._salir_modo_edicion
        )

        # =====================================================================
        # 3. TARJETA CURVA INFERIOR CON TABLA SUAVIZADA
        # =====================================================================
        card_lista = RoundedCard(
            self,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=16,
            expand_body=True
        )
        card_lista.pack(fill=BOTH, expand=True)

        bl = card_lista.body

        top_tabla = tk.Frame(bl, bg=PALETTE["blanco"])
        top_tabla.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_tabla,
            text="📅  Actividades Registradas",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 14))

        self.combo_filtro = tb.Combobox(
            top_tabla,
            values=["Todas", "Programada", "En Curso", "Finalizada", "Cancelada"],
            state="readonly",
            width=14,
            bootstyle="danger"
        )
        self.combo_filtro.set("Todas")
        self.combo_filtro.pack(side="left")
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda _e: self._cargar_actividades())

        self._crear_btn_tabla(
            top_tabla, "✕ Cancelar Actividad", self._cancelar_actividad, primario=True
        ).pack(side="right", padx=(6, 0))

        self._crear_btn_tabla(
            top_tabla, "🔄 Restablecer", self._restablecer_actividad
        ).pack(side="right", padx=(6, 0))

        self._crear_btn_tabla(
            top_tabla, "✏️ Editar Seleccionada", self._cargar_para_editar
        ).pack(side="right", padx=(6, 0))

        self._crear_btn_tabla(
            top_tabla, "↻ Actualizar", self._cargar_actividades
        ).pack(side="right", padx=(6, 0))

        columnas = ("nombre", "fecha", "horario", "lugar", "cupos", "estado")
        self.tabla = tb.Treeview(
            bl,
            columns=columnas,
            show="headings",
            height=6,
            style="Op.Treeview"
        )
        cols_cfg = {
            "nombre": ("Actividad", 220),
            "fecha": ("Fecha", 105),
            "horario": ("Horario", 115),
            "lugar": ("Lugar", 180),
            "cupos": ("Cupos (Asig/Max)", 120),
            "estado": ("Estado", 105)
        }
        for col, (titulo, ancho) in cols_cfg.items():
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="center" if col in ("fecha", "horario", "cupos", "estado") else "w")

        self.tabla.tag_configure("par", background=PALETTE["blanco"])
        self.tabla.tag_configure("impar", background="#F9FAFB")
        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

    def _crear_btn_tabla(self, parent, texto: str, comando, primario: bool = False):
        bg_base = PALETTE["rojo"] if primario else PALETTE["plomo_fondo"]
        fg_base = PALETTE["blanco"] if primario else PALETTE["negro"]
        btn = tk.Button(
            parent,
            text=texto,
            font=("Segoe UI", 8, "bold"),
            bg=bg_base,
            fg=fg_base,
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=comando
        )
        if not primario:
            btn.bind("<Enter>", lambda _e: btn.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"]))
            btn.bind("<Leave>", lambda _e: btn.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"]))
        else:
            btn.bind("<Enter>", lambda _e: btn.config(bg=PALETTE["rojo_hover"]))
            btn.bind("<Leave>", lambda _e: btn.config(bg=PALETTE["rojo"]))
        return btn

    def _actualizar_horas_fin(self, hora_preferida: str = None):
        hora_ini = self.combo_hora_ini.get()
        opciones_fin = self.controller.generar_horas_fin_validas(hora_ini)
        self.combo_hora_fin["values"] = opciones_fin

        if not opciones_fin:
            self.combo_hora_fin.set("")
            return

        if hora_preferida and hora_preferida in opciones_fin:
            self.combo_hora_fin.set(hora_preferida)
        elif self.combo_hora_fin.get() not in opciones_fin:
            sugerida = opciones_fin[min(4, len(opciones_fin) - 1)]
            self.combo_hora_fin.set(sugerida)

    def _guardar_formulario(self):
        datos = {
            "nombre": self.entry_nombre.get(),
            "lugar": self.entry_lugar.get(),
            "fecha": self.date_fecha.entry.get(),
            "hora_inicio": self.combo_hora_ini.get(),
            "hora_fin": self.combo_hora_fin.get(),
            "cupo_maximo": self.combo_cupo.get(),
            "descripcion": self.entry_desc.get(),
            "id_admin_crea": self.sesion.get("id_usuario")
        }

        if self.actividad_en_edicion is not None:
            exito, mensaje = self.controller.editar_actividad(self.actividad_en_edicion, datos)
            if not exito:
                messagebox.showwarning("Error al Editar", mensaje)
                return
            messagebox.showinfo("Actividad Actualizada", mensaje)
            self._salir_modo_edicion()
        else:
            exito, mensaje = self.controller.registrar_actividad(datos)
            if not exito:
                messagebox.showwarning("Validación de Actividad", mensaje)
                return
            messagebox.showinfo("Actividad Creada", mensaje)
            self._limpiar_campos()

        self._cargar_actividades()

    def _limpiar_campos(self):
        self.entry_nombre.delete(0, tk.END)
        self.entry_lugar.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.combo_hora_ini.set("08:30")
        self._actualizar_horas_fin("11:30")
        self.combo_cupo.set("10")

    def _cargar_para_editar(self):
        act = self.actividad_seleccionada
        if not act:
            messagebox.showwarning("Atención", "Selecciona una actividad de la tabla para editarla.")
            return
        if act["estado"] == "Finalizada":
            messagebox.showwarning("No permitido", "No se puede editar una actividad que ya finalizó.")
            return

        self.actividad_en_edicion = act
        self.lbl_titulo_form.config(text=f"✏️ Editando Actividad: {act['nombre']}", fg=PALETTE["rojo"])

        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, act["nombre"])

        self.entry_lugar.delete(0, tk.END)
        self.entry_lugar.insert(0, act["lugar"])

        self.date_fecha.entry.delete(0, tk.END)
        self.date_fecha.entry.insert(0, str(act["fecha"]))

        if act["hora_inicio_str"] in self.combo_hora_ini["values"]:
            self.combo_hora_ini.set(act["hora_inicio_str"])
        self._actualizar_horas_fin(act["hora_fin_str"])

        cupo_str = str(act["cupo_maximo"])
        if cupo_str in self.combo_cupo["values"]:
            self.combo_cupo.set(cupo_str)

        self.entry_desc.delete(0, tk.END)
        if act["descripcion"]:
            self.entry_desc.insert(0, act["descripcion"])

        self.btn_guardar.config(text="💾 Guardar", bg=PALETTE["negro"])
        self.btn_cancelar_edicion.pack(side="left", padx=(0, 6))

    def _salir_modo_edicion(self):
        self.actividad_en_edicion = None
        self.lbl_titulo_form.config(text="Nueva Actividad (* Campos obligatorios)", fg=PALETTE["negro"])
        self.btn_guardar.config(text="+ Programar", bg=PALETTE["rojo"])
        self.btn_cancelar_edicion.pack_forget()
        self._limpiar_campos()

    def _cargar_actividades(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.actividades_cache.clear()
        self.actividad_seleccionada = None

        try:
            filtro = self.combo_filtro.get() if hasattr(self, "combo_filtro") else "Todas"
            lista = self.controller.obtener_actividades(filtro)
            for idx, act in enumerate(lista):
                iid = str(act["id_actividad"])
                self.actividades_cache[iid] = act
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla.insert("", tk.END, iid=iid, values=(
                    act["nombre"],
                    str(act["fecha"]),
                    f"{act['hora_inicio_str']} - {act['hora_fin_str']}",
                    act["lugar"],
                    f"{act['inscritos']} / {act['cupo_maximo']}",
                    act["estado"]
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar(self, _event):
        sel = self.tabla.selection()
        if sel:
            self.actividad_seleccionada = self.actividades_cache.get(sel[0])

    def _cancelar_actividad(self):
        act = self.actividad_seleccionada
        if not act:
            messagebox.showwarning("Atención", "Selecciona primero una actividad de la tabla.")
            return

        confirmar = messagebox.askyesno(
            "Advertencia de Cancelación",
            f"¿Estás seguro de que deseas CANCELAR la actividad '{act['nombre']}'?\n\n"
            "• La actividad quedará suspendida.\n"
            "• No se podrán asignar nuevos voluntarios mientras esté cancelada.",
            icon="warning"
        )
        if not confirmar:
            return

        exito, mensaje = self.controller.cancelar_actividad(act)
        if not exito:
            messagebox.showwarning("Atención", mensaje)
            return

        if self.actividad_en_edicion and self.actividad_en_edicion["id_actividad"] == act["id_actividad"]:
            self._salir_modo_edicion()

        messagebox.showinfo("Actividad Cancelada", mensaje)
        self._cargar_actividades()

    def _restablecer_actividad(self):
        act = self.actividad_seleccionada
        if not act:
            messagebox.showwarning("Atención", "Selecciona una actividad cancelada de la tabla.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar Restablecimiento",
            f"¿Deseas restablecer la actividad '{act['nombre']}'?\n"
            "Volverá a estar activa según su fecha y horario."
        )
        if not confirmar:
            return

        exito, mensaje = self.controller.restablecer_actividad(act)
        if not exito:
            messagebox.showwarning("Atención", mensaje)
            return

        messagebox.showinfo("Actividad Restablecida", mensaje)
        self._cargar_actividades()


class ModalCancelarAsignacionStrike(tk.Toplevel):
    """Modal para cancelar la asignación de un voluntario aplicando strikes en STRIKE_VOLUNTARIO."""

    OPCIONES_PENALIDAD = {
        "1 Strike — Cancelación o inasistencia sin aviso previo": 1,
        "2 Strikes — Cancelación crítica de última hora": 2,
        "0 Strikes — Cancelación justificada (sin penalización)": 0
    }

    def __init__(self, master, asignacion: dict, sesion: dict, controller: ActividadController, on_confirmado):
        super().__init__(master)
        self.asignacion = asignacion
        self.sesion = sesion
        self.controller = controller
        self.on_confirmado = on_confirmado

        self.title("Cancelar Asignación y Evaluar Strike")
        self.configure(bg=PALETTE["plomo_fondo"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._construir_ui()
        self._centrar()

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
            text="Cancelación de Participación y Control de Strikes",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            anchor="w"
        ).pack(fill="x")

        strikes_act = int(self.asignacion.get("total_strikes", 0))
        tk.Label(
            hdr,
            text=f"Voluntario: {self.asignacion['nombre_completo']}  •  Strikes acumulados: {strikes_act}/5",
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

        tk.Label(
            card,
            text="Penalización a aplicar (Al llegar a 5 strikes pasa a Inactivo_Definitivo):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.combo_penalidad = tb.Combobox(
            card,
            values=list(self.OPCIONES_PENALIDAD.keys()),
            state="readonly",
            width=52,
            font=("Segoe UI", 9),
            bootstyle="danger"
        )
        self.combo_penalidad.set("1 Strike — Cancelación o inasistencia sin aviso previo")
        self.combo_penalidad.pack(fill="x", pady=(0, 10))

        tk.Label(
            card,
            text="Motivo de la cancelación (obligatorio):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.entry_motivo = tb.Entry(card, font=("Segoe UI", 10))
        self.entry_motivo.pack(fill="x", ipady=4, pady=(0, 6))
        self.entry_motivo.focus_set()

        btn_row = tk.Frame(wrap, bg=PALETTE["plomo_fondo"])
        btn_row.pack(fill="x", pady=(10, 0))

        tk.Button(
            btn_row,
            text="Cerrar",
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
            text="⚠️ Confirmar Cancelación",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._confirmar
        ).pack(side="right")

    def _confirmar(self):
        strikes = self.OPCIONES_PENALIDAD.get(self.combo_penalidad.get(), 1)
        motivo = self.entry_motivo.get()

        exito, resultado = self.controller.cancelar_asignacion_voluntario(
            asignacion=self.asignacion,
            cantidad_strikes=strikes,
            motivo=motivo,
            id_admin_registra=self.sesion["id_usuario"]
        )
        if not exito:
            messagebox.showwarning("Validación", str(resultado), parent=self)
            return

        if isinstance(resultado, dict):
            msg = (
                f"Asignación cancelada para {resultado['voluntario']}.\n"
                f"• Strikes aplicados: +{resultado['strikes_aplicados']}\n"
                f"• Acumulado actual: {resultado['total_strikes']}/5 strikes"
            )
            if resultado.get("inactivado_definitivo"):
                msg += (
                    "\n\n🚨 ALERTA: El voluntario alcanzó 5 strikes y fue marcado "
                    "automáticamente como 'Inactivo_Definitivo' (cuenta bloqueada)."
                )
            messagebox.showinfo("Asignación Cancelada", msg, parent=self)

        self.destroy()
        if callable(self.on_confirmado):
            self.on_confirmado()


class AsignarVoluntariosView(tk.Frame):
    """Vista para Administrador: Asignación de voluntarios admitidos (máximo 1 actividad por día)."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = ActividadController()
        self.actividades_map = {}
        self.actividad_actual = None
        self.voluntarios_cache = {}
        self.asignados_cache = {}

        self.pack(fill=BOTH, expand=True)
        _configurar_estilo_tabla_operaciones()
        self._construir_ui()
        self._cargar_combo_actividades()

    def _construir_ui(self):
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Asignación de Voluntarios a Actividades",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            header,
            text="Solo voluntarios con estado 'Admitido' pueden ser asignados (máximo 1 actividad por día).",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        # Selector superior curvo
        selector_card = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=12,
            expand_body=False
        )
        selector_card.pack(fill="x", pady=(0, 8))

        sb = selector_card.body

        tk.Label(
            sb,
            text="Actividad:",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 10))

        self.combo_actividad = tb.Combobox(
            sb,
            state="readonly",
            width=50,
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_actividad.pack(side="left", padx=(0, 16))
        self.combo_actividad.bind("<<ComboboxSelected>>", lambda _e: self._al_cambiar_actividad())

        self.lbl_cupos = tk.Label(
            sb,
            text="Cupos: -",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo_suave"],
            fg=PALETTE["rojo"],
            padx=12,
            pady=5
        )
        self.lbl_cupos.pack(side="right")

        # Cuerpo dividido en dos tarjetas curvas
        cuerpo = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=50, uniform="asig_cols")
        cuerpo.columnconfigure(1, weight=50, uniform="asig_cols")
        cuerpo.rowconfigure(0, weight=1)

        # Panel Izquierdo: Voluntarios Admitidos
        izq_card = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=16,
            expand_body=True
        )
        izq_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))

        bi = izq_card.body

        tk.Label(
            bi,
            text="👥  Voluntarios Admitidos Disponibles",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 8))

        busq_frame = tk.Frame(bi, bg=PALETTE["blanco"])
        busq_frame.pack(fill="x", pady=(0, 10))

        self.entry_buscar = tb.Entry(busq_frame, font=("Segoe UI", 9))
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=2)
        self.entry_buscar.bind("<KeyRelease>", lambda _e: self._cargar_voluntarios_admitidos())

        btn_busq = tk.Button(
            busq_frame,
            text="Buscar",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._cargar_voluntarios_admitidos
        )
        btn_busq.pack(side="right")

        self.tabla_admitidos = tb.Treeview(
            bi,
            columns=("ci", "nombre", "telefono", "strikes"),
            show="headings",
            height=8,
            style="Op.Treeview"
        )
        self.tabla_admitidos.heading("ci", text="CI")
        self.tabla_admitidos.heading("nombre", text="Voluntario")
        self.tabla_admitidos.heading("telefono", text="Teléfono")
        self.tabla_admitidos.heading("strikes", text="Strikes")
        self.tabla_admitidos.column("ci", width=85, anchor="center")
        self.tabla_admitidos.column("nombre", width=185, anchor="w")
        self.tabla_admitidos.column("telefono", width=85, anchor="center")
        self.tabla_admitidos.column("strikes", width=65, anchor="center")
        self.tabla_admitidos.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_admitidos.tag_configure("impar", background="#F9FAFB")
        self.tabla_admitidos.pack(fill=BOTH, expand=True, pady=(0, 10))

        btn_asig = tk.Button(
            bi,
            text="Asignar Voluntario Seleccionado  →",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=9,
            cursor="hand2",
            command=self._asignar
        )
        btn_asig.pack(fill="x")
        btn_asig.bind("<Enter>", lambda _e: btn_asig.config(bg=PALETTE["rojo_hover"]))
        btn_asig.bind("<Leave>", lambda _e: btn_asig.config(bg=PALETTE["rojo"]))

        # Panel Derecho: Voluntarios Asignados
        der_card = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=16,
            expand_body=True
        )
        der_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))

        bd = der_card.body

        tk.Label(
            bd,
            text="✅  Voluntarios Asignados (Confirmados)",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 8))

        self.lbl_info_act = tk.Label(
            bd,
            text="Lugar y horario de la actividad seleccionada",
            font=("Segoe UI", 9),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            padx=10,
            pady=6,
            anchor="w"
        )
        self.lbl_info_act.pack(fill="x", pady=(0, 10))

        self.tabla_asignados = tb.Treeview(
            bd,
            columns=("ci", "nombre", "strikes", "estado"),
            show="headings",
            height=8,
            style="Op.Treeview"
        )
        self.tabla_asignados.heading("ci", text="CI")
        self.tabla_asignados.heading("nombre", text="Voluntario Asignado")
        self.tabla_asignados.heading("strikes", text="Strikes")
        self.tabla_asignados.heading("estado", text="Estado")
        self.tabla_asignados.column("ci", width=85, anchor="center")
        self.tabla_asignados.column("nombre", width=185, anchor="w")
        self.tabla_asignados.column("strikes", width=65, anchor="center")
        self.tabla_asignados.column("estado", width=90, anchor="center")
        self.tabla_asignados.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_asignados.tag_configure("impar", background="#F9FAFB")
        self.tabla_asignados.pack(fill=BOTH, expand=True, pady=(0, 10))

        acciones_der = tk.Frame(bd, bg=PALETTE["blanco"])
        acciones_der.pack(fill="x")

        btn_quitar = tk.Button(
            acciones_der,
            text="✕ Quitar Sin Strike",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
            command=self._quitar_asignacion
        )
        btn_quitar.pack(side="left", padx=(0, 8))

        btn_cancelar_asig = tk.Button(
            acciones_der,
            text="⚠️ Cancelar Participación (Aplicar Strike)",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo_suave"],
            fg=PALETTE["rojo"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=9,
            cursor="hand2",
            command=self._abrir_cancelacion_strike
        )
        btn_cancelar_asig.pack(side="right", fill="x", expand=True)
        btn_cancelar_asig.bind(
            "<Enter>",
            lambda _e: btn_cancelar_asig.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"])
        )
        btn_cancelar_asig.bind(
            "<Leave>",
            lambda _e: btn_cancelar_asig.config(bg=PALETTE["rojo_suave"], fg=PALETTE["rojo"])
        )

    def _cargar_combo_actividades(self):
        try:
            todas = self.controller.obtener_actividades("Todas")
            activas = [a for a in todas if a["estado"] in ("Programada", "En Curso")]

            self.actividades_map.clear()
            etiquetas = []
            for a in activas:
                etiqueta = f"{a['nombre']}  ({a['fecha']} | {a['hora_inicio_str']}-{a['hora_fin_str']})"
                self.actividades_map[etiqueta] = a
                etiquetas.append(etiqueta)

            self.combo_actividad["values"] = etiquetas
            if etiquetas:
                self.combo_actividad.set(etiquetas[0])
                self._al_cambiar_actividad()
            else:
                self.combo_actividad.set("No hay actividades programadas o en curso")
                self.actividad_actual = None

            self._cargar_voluntarios_admitidos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_cambiar_actividad(self):
        etiqueta = self.combo_actividad.get()
        act = self.actividades_map.get(etiqueta)
        if not act:
            return

        todas = self.controller.obtener_actividades("Todas")
        for item in todas:
            if item["id_actividad"] == act["id_actividad"]:
                act = item
                self.actividades_map[etiqueta] = item
                break

        self.actividad_actual = act
        self.lbl_cupos.config(
            text=f"Cupos ocupados: {act['inscritos']} / {act['cupo_maximo']}  (Disponibles: {act['cupos_disponibles']})"
        )
        self.lbl_info_act.config(
            text=f"📍 {act['lugar']}   |   🕒 {act['hora_inicio_str']} a {act['hora_fin_str']}   |   Estado: {act['estado']}"
        )
        self._cargar_asignados()

    def _cargar_voluntarios_admitidos(self):
        for item in self.tabla_admitidos.get_children():
            self.tabla_admitidos.delete(item)
        self.voluntarios_cache.clear()

        try:
            lista = self.controller.obtener_voluntarios_admitidos(self.entry_buscar.get())
            for idx, v in enumerate(lista):
                iid = str(v["id_voluntario"])
                self.voluntarios_cache[iid] = v
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla_admitidos.insert("", tk.END, iid=iid, values=(
                    v["ci"],
                    v["nombre_completo"],
                    v["telefono"] or "-",
                    f"{v['total_strikes']}/5"
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cargar_asignados(self):
        for item in self.tabla_asignados.get_children():
            self.tabla_asignados.delete(item)
        self.asignados_cache.clear()

        if not self.actividad_actual:
            return

        try:
            lista = self.controller.obtener_asignados(self.actividad_actual["id_actividad"])
            for idx, a in enumerate(lista):
                iid = str(a["id_asignacion"])
                self.asignados_cache[iid] = a
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla_asignados.insert("", tk.END, iid=iid, values=(
                    a["ci"],
                    a["nombre_completo"],
                    f"{a['total_strikes']}/5",
                    a["estado_asignacion"]
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _asignar(self):
        sel = self.tabla_admitidos.selection()
        vol = self.voluntarios_cache.get(sel[0]) if sel else None

        exito, mensaje = self.controller.asignar_voluntario(
            actividad=self.actividad_actual,
            voluntario=vol,
            id_admin=self.sesion["id_usuario"]
        )
        if not exito:
            messagebox.showwarning("No se pudo asignar", mensaje)
            return

        messagebox.showinfo("Asignación Confirmada", mensaje)
        self._al_cambiar_actividad()

    def _quitar_asignacion(self):
        sel = self.tabla_asignados.selection()
        asig = self.asignados_cache.get(sel[0]) if sel else None

        exito, mensaje = self.controller.remover_asignacion(asig)
        if not exito:
            messagebox.showwarning("Atención", mensaje)
            return

        messagebox.showinfo("Asignación Eliminada", mensaje)
        self._al_cambiar_actividad()

    def _abrir_cancelacion_strike(self):
        sel = self.tabla_asignados.selection()
        asig = self.asignados_cache.get(sel[0]) if sel else None
        if not asig:
            messagebox.showwarning("Atención", "Selecciona un voluntario de la lista de asignados.")
            return

        def _post_cancelacion():
            self._al_cambiar_actividad()
            self._cargar_voluntarios_admitidos()

        ModalCancelarAsignacionStrike(
            master=self,
            asignacion=asig,
            sesion=self.sesion,
            controller=self.controller,
            on_confirmado=_post_cancelacion
        )