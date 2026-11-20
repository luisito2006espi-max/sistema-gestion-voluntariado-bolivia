import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.actividad_controller import ActividadController


class GestionActividadesView(tb.Frame):
    """Vista para Administrador: Programación, edición, cancelación y restablecimiento de actividades."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = ActividadController()
        self.actividades_cache = {}
        self.actividad_seleccionada = None
        self.actividad_en_edicion = None

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_actividades()

    def _construir_ui(self):
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="Gestión de Actividades Comunitarias",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Las actividades pasan automáticamente a 'En Curso' al llegar su hora de inicio (duración permitida: 1 a 5 horas).",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w", pady=(2, 0))

        # Tarjeta Formulario (sirve tanto para Crear como para Editar)
        card_form = tk.Frame(self, bg="#FFFFFF", padx=20, pady=16)
        card_form.pack(fill="x", pady=(0, 14))

        self.lbl_titulo_form = tk.Label(
            card_form,
            text="Nueva Actividad (* Campos obligatorios)",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#991B1B"
        )
        self.lbl_titulo_form.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        for c in range(4):
            card_form.columnconfigure(c, weight=1, uniform="act_cols")

        # Fila 1: Nombre + Lugar
        tk.Label(card_form, text="Nombre de la Actividad *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=1, column=0, columnspan=2, sticky="w", padx=6)
        self.entry_nombre = tb.Entry(card_form, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_nombre.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, ipady=4, pady=(2, 8))

        tk.Label(card_form, text="Lugar / Punto de Encuentro *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=1, column=2, columnspan=2, sticky="w", padx=6)
        self.entry_lugar = tb.Entry(card_form, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_lugar.grid(row=2, column=2, columnspan=2, sticky="ew", padx=6, ipady=4, pady=(2, 8))

        # Fila 2: Fecha, Hora Inicio (Combobox), Hora Fin (Combobox), Cupo Máximo (Combobox 3-15)
        tk.Label(card_form, text="Fecha *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=3, column=0, sticky="w", padx=6)
        self.date_fecha = tb.DateEntry(card_form, bootstyle="danger", dateformat="%Y-%m-%d")
        self.date_fecha.grid(row=4, column=0, sticky="ew", padx=6, pady=(2, 8))

        tk.Label(card_form, text="Hora Inicio *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=3, column=1, sticky="w", padx=6)
        horas_inicio = self.controller.generar_horas_inicio()
        self.combo_hora_ini = tb.Combobox(
            card_form,
            values=horas_inicio,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_hora_ini.set("08:30")
        self.combo_hora_ini.grid(row=4, column=1, sticky="ew", padx=6, pady=(2, 8))
        self.combo_hora_ini.bind("<<ComboboxSelected>>", lambda e: self._actualizar_horas_fin())

        tk.Label(card_form, text="Hora Fin (1h - 5h) *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=3, column=2, sticky="w", padx=6)
        self.combo_hora_fin = tb.Combobox(
            card_form,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_hora_fin.grid(row=4, column=2, sticky="ew", padx=6, pady=(2, 8))
        self._actualizar_horas_fin("11:30")

        tk.Label(card_form, text="Cupo Máximo (3 - 15) *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=3, column=3, sticky="w", padx=6)
        self.combo_cupo = tb.Combobox(
            card_form,
            values=self.controller.generar_cupos_validos(),
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_cupo.set("10")
        self.combo_cupo.grid(row=4, column=3, sticky="ew", padx=6, pady=(2, 8))

        # Fila 3: Descripción + Botones de Guardar / Cancelar Edición
        tk.Label(card_form, text="Descripción / Tareas a realizar", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=5, column=0, columnspan=3, sticky="w", padx=6)
        self.entry_desc = tb.Entry(card_form, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_desc.grid(row=6, column=0, columnspan=3, sticky="ew", padx=6, ipady=4)

        acciones_form = tk.Frame(card_form, bg="#FFFFFF")
        acciones_form.grid(row=6, column=3, sticky="ew", padx=6)

        self.btn_guardar = tb.Button(
            acciones_form,
            text="+ Programar",
            bootstyle="danger",
            command=self._guardar_formulario
        )
        self.btn_guardar.pack(side="right", fill="x", expand=True, ipady=4)

        self.btn_cancelar_edicion = tb.Button(
            acciones_form,
            text="Cancelar",
            bootstyle="secondary-outline",
            command=self._salir_modo_edicion
        )

        # Tabla inferior de actividades + botones de Editar, Restablecer y Cancelar
        card_lista = tk.Frame(self, bg="#FFFFFF", padx=18, pady=14)
        card_lista.pack(fill=BOTH, expand=True)

        top_tabla = tk.Frame(card_lista, bg="#FFFFFF")
        top_tabla.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_tabla,
            text="Actividades Registradas",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(side="left")

        tb.Button(
            top_tabla,
            text="✕ Cancelar Actividad",
            bootstyle="danger",
            command=self._cancelar_actividad
        ).pack(side="right", padx=(6, 0))

        tb.Button(
            top_tabla,
            text="🔄 Restablecer",
            bootstyle="warning-outline",
            command=self._restablecer_actividad
        ).pack(side="right", padx=(6, 0))

        tb.Button(
            top_tabla,
            text="✏️ Editar Seleccionada",
            bootstyle="danger-outline",
            command=self._cargar_para_editar
        ).pack(side="right", padx=(6, 0))

        tb.Button(
            top_tabla,
            text="↻ Actualizar",
            bootstyle="secondary-outline",
            command=self._cargar_actividades
        ).pack(side="right", padx=(6, 0))

        # Tabla SIN ID visible
        columnas = ("nombre", "fecha", "horario", "lugar", "cupos", "estado")
        self.tabla = tb.Treeview(
            card_lista,
            columns=columnas,
            show="headings",
            bootstyle="danger"
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

        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

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
            # Por defecto sugiere 3 horas de duración si existe, o la primera opción válida
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
            "descripcion": self.entry_desc.get()
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
        self.lbl_titulo_form.config(text=f"✏️ Editando Actividad: {act['nombre']}", fg="#B91C1C")

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

        self.btn_guardar.config(text="💾 Guardar", bootstyle="success")
        self.btn_cancelar_edicion.pack(side="left", padx=(0, 6), ipady=4)

    def _salir_modo_edicion(self):
        self.actividad_en_edicion = None
        self.lbl_titulo_form.config(text="Nueva Actividad (* Campos obligatorios)", fg="#991B1B")
        self.btn_guardar.config(text="+ Programar", bootstyle="danger")
        self.btn_cancelar_edicion.pack_forget()
        self._limpiar_campos()

    def _cargar_actividades(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.actividades_cache.clear()
        self.actividad_seleccionada = None

        try:
            lista = self.controller.obtener_actividades("Todas")
            for act in lista:
                iid = str(act["id_actividad"])
                self.actividades_cache[iid] = act
                self.tabla.insert("", tk.END, iid=iid, values=(
                    act["nombre"],
                    str(act["fecha"]),
                    f"{act['hora_inicio_str']} - {act['hora_fin_str']}",
                    act["lugar"],
                    f"{act['inscritos']} / {act['cupo_maximo']}",
                    act["estado"]
                ))
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


class AsignarVoluntariosView(tb.Frame):
    """Vista para Administrador: Asignación de voluntarios admitidos (máximo 1 actividad por día)."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = ActividadController()
        self.actividades_map = {}
        self.actividad_actual = None
        self.voluntarios_cache = {}
        self.asignados_cache = {}

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_combo_actividades()

    def _construir_ui(self):
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="Asignación de Voluntarios a Actividades",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Cada voluntario admitido puede participar como máximo en 1 actividad por día.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w", pady=(2, 0))

        selector_card = tk.Frame(self, bg="#FFFFFF", padx=18, pady=14)
        selector_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            selector_card,
            text="Actividad:",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(side="left", padx=(0, 10))

        self.combo_actividad = tb.Combobox(
            selector_card,
            state="readonly",
            width=48,
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_actividad.pack(side="left", padx=(0, 16))
        self.combo_actividad.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_actividad())

        self.lbl_cupos = tk.Label(
            selector_card,
            text="Cupos: -",
            font=("Segoe UI", 10, "bold"),
            bg="#FEF2F2",
            fg="#B91C1C",
            padx=12,
            pady=5
        )
        self.lbl_cupos.pack(side="right")

        cuerpo = tk.Frame(self, bg="#FFF5F5")
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=50)
        cuerpo.columnconfigure(1, weight=50)
        cuerpo.rowconfigure(0, weight=1)

        # Panel Izquierdo: Voluntarios Admitidos
        izq_card = tk.Frame(cuerpo, bg="#FFFFFF", padx=16, pady=14)
        izq_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            izq_card,
            text="Voluntarios Admitidos Disponibles",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(0, 8))

        busq_frame = tk.Frame(izq_card, bg="#FFFFFF")
        busq_frame.pack(fill="x", pady=(0, 8))

        self.entry_buscar = tb.Entry(busq_frame, bootstyle="danger")
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_buscar.bind("<Return>", lambda e: self._cargar_voluntarios_admitidos())

        tb.Button(
            busq_frame, text="Buscar", bootstyle="danger-outline",
            command=self._cargar_voluntarios_admitidos
        ).pack(side="right")

        self.tabla_admitidos = tb.Treeview(
            izq_card,
            columns=("ci", "nombre", "telefono"),
            show="headings",
            bootstyle="danger"
        )
        self.tabla_admitidos.heading("ci", text="CI")
        self.tabla_admitidos.heading("nombre", text="Voluntario")
        self.tabla_admitidos.heading("telefono", text="Teléfono")
        self.tabla_admitidos.column("ci", width=95, anchor="center")
        self.tabla_admitidos.column("nombre", width=190, anchor="w")
        self.tabla_admitidos.column("telefono", width=95, anchor="center")
        self.tabla_admitidos.pack(fill=BOTH, expand=True, pady=(0, 10))

        tb.Button(
            izq_card,
            text="Asignar Voluntario Seleccionado  →",
            bootstyle="danger",
            command=self._asignar
        ).pack(fill="x", ipady=5)

        # Panel Derecho: Voluntarios Asignados
        der_card = tk.Frame(cuerpo, bg="#FFFFFF", padx=16, pady=14)
        der_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            der_card,
            text="Voluntarios Asignados (Confirmados)",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(0, 8))

        self.lbl_info_act = tk.Label(
            der_card,
            text="Lugar y horario de la actividad seleccionada",
            font=("Segoe UI", 9),
            bg="#FFF5F5",
            fg="#475569",
            padx=10,
            pady=6,
            anchor="w"
        )
        self.lbl_info_act.pack(fill="x", pady=(0, 8))

        self.tabla_asignados = tb.Treeview(
            der_card,
            columns=("ci", "nombre", "estado"),
            show="headings",
            bootstyle="danger"
        )
        self.tabla_asignados.heading("ci", text="CI")
        self.tabla_asignados.heading("nombre", text="Voluntario Asignado")
        self.tabla_asignados.heading("estado", text="Estado")
        self.tabla_asignados.column("ci", width=95, anchor="center")
        self.tabla_asignados.column("nombre", width=200, anchor="w")
        self.tabla_asignados.column("estado", width=90, anchor="center")
        self.tabla_asignados.pack(fill=BOTH, expand=True, pady=(0, 10))

        tb.Button(
            der_card,
            text="✕ Quitar Asignación Seleccionada",
            bootstyle="secondary-outline",
            command=self._quitar_asignacion
        ).pack(fill="x", ipady=5)

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
            for v in lista:
                iid = str(v["id_voluntario"])
                self.voluntarios_cache[iid] = v
                self.tabla_admitidos.insert("", tk.END, iid=iid, values=(
                    v["ci"],
                    v["nombre_completo"],
                    v["telefono"] or "-"
                ))
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
            for a in lista:
                iid = str(a["id_asignacion"])
                self.asignados_cache[iid] = a
                self.tabla_asignados.insert("", tk.END, iid=iid, values=(
                    a["ci"],
                    a["nombre_completo"],
                    a["estado_asignacion"]
                ))
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