import calendar
from datetime import date
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.voluntario_controller import VoluntarioController


class InscripcionVoluntarioView(tb.Frame):
    """Vista limpia y profesional para la inscripción de postulantes (Recepcionista y Admin)."""

    MESES = [
        ("01 - Enero", 1),
        ("02 - Febrero", 2),
        ("03 - Marzo", 3),
        ("04 - Abril", 4),
        ("05 - Mayo", 5),
        ("06 - Junio", 6),
        ("07 - Julio", 7),
        ("08 - Agosto", 8),
        ("09 - Septiembre", 9),
        ("10 - Octubre", 10),
        ("11 - Noviembre", 11),
        ("12 - Diciembre", 12),
    ]

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = VoluntarioController()
        self.meses_map = dict(self.MESES)
        self.cols_vol = self.controller.model.obtener_columnas_voluntario()
        self.tiene_direccion = "direccion" in self.cols_vol

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()

    def _construir_ui(self):
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 16))

        tk.Label(
            header,
            text="Inscripción de Postulante a Voluntariado",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Completa la ficha de postulación. Requisitos: edad entre 18 y 60 años y Carnet de Identidad vigente.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w", pady=(3, 0))

        card = tk.Frame(self, bg="#FFFFFF", padx=28, pady=24)
        card.pack(fill="x")

        # --- SECCIÓN 1: DATOS DE IDENTIFICACIÓN ---
        self._titulo_seccion(card, "1. Datos de Identificación Personal")

        grid_id = tk.Frame(card, bg="#FFFFFF")
        grid_id.pack(fill="x", pady=(0, 16))
        for c in range(2):
            grid_id.columnconfigure(c, weight=1, uniform="sec1")

        tk.Label(grid_id, text="Carnet de Identidad (CI) *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=0, column=0, sticky="w", padx=6)
        self.entry_ci = tb.Entry(grid_id, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_ci.grid(row=1, column=0, sticky="ew", padx=6, ipady=4, pady=(2, 10))

        tk.Label(grid_id, text="Nombres *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=0, column=1, sticky="w", padx=6)
        self.entry_nombres = tb.Entry(grid_id, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_nombres.grid(row=1, column=1, sticky="ew", padx=6, ipady=4, pady=(2, 10))

        tk.Label(grid_id, text="Apellido Paterno *", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=2, column=0, sticky="w", padx=6)
        self.entry_ap_pat = tb.Entry(grid_id, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_ap_pat.grid(row=3, column=0, sticky="ew", padx=6, ipady=4)

        tk.Label(grid_id, text="Apellido Materno (Opcional)", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=2, column=1, sticky="w", padx=6)
        self.entry_ap_mat = tb.Entry(grid_id, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_ap_mat.grid(row=3, column=1, sticky="ew", padx=6, ipady=4)

        # --- SECCIÓN 2: FECHA DE NACIMIENTO (3 LISTAS: DÍA / MES / AÑO) ---
        self._titulo_seccion(card, "2. Fecha de Nacimiento (Edad permitida: 18 a 60 años) *")

        fecha_box = tk.Frame(card, bg="#FFF5F5", padx=14, pady=12)
        fecha_box.pack(fill="x", padx=6, pady=(0, 18))

        hoy = date.today()
        anios_validos = [str(y) for y in range(hoy.year - 18, hoy.year - 62, -1)]
        meses_labels = [m[0] for m in self.MESES]
        dias_iniciales = [f"{d:02d}" for d in range(1, 32)]

        tk.Label(fecha_box, text="Día:", font=("Segoe UI", 9, "bold"), bg="#FFF5F5", fg="#7F1D1D").pack(side="left", padx=(0, 6))
        self.combo_dia = tb.Combobox(fecha_box, values=dias_iniciales, state="readonly", width=6, font=("Segoe UI", 10), bootstyle="danger")
        self.combo_dia.pack(side="left", padx=(0, 16))
        self.combo_dia.bind("<<ComboboxSelected>>", lambda e: self._actualizar_preview_edad())

        tk.Label(fecha_box, text="Mes:", font=("Segoe UI", 9, "bold"), bg="#FFF5F5", fg="#7F1D1D").pack(side="left", padx=(0, 6))
        self.combo_mes = tb.Combobox(fecha_box, values=meses_labels, state="readonly", width=16, font=("Segoe UI", 10), bootstyle="danger")
        self.combo_mes.pack(side="left", padx=(0, 16))
        self.combo_mes.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_mes_anio())

        tk.Label(fecha_box, text="Año:", font=("Segoe UI", 9, "bold"), bg="#FFF5F5", fg="#7F1D1D").pack(side="left", padx=(0, 6))
        self.combo_anio = tb.Combobox(fecha_box, values=anios_validos, state="readonly", width=8, font=("Segoe UI", 10), bootstyle="danger")
        self.combo_anio.pack(side="left", padx=(0, 18))
        self.combo_anio.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_mes_anio())

        self.lbl_edad_preview = tk.Label(
            fecha_box,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#FFF5F5",
            fg="#15803D"
        )
        self.lbl_edad_preview.pack(side="right")

        self._restablecer_fecha_defecto()

        # --- SECCIÓN 3: INFORMACIÓN DE CONTACTO ---
        self._titulo_seccion(card, "3. Información de Contacto")

        grid_con = tk.Frame(card, bg="#FFFFFF")
        grid_con.pack(fill="x", pady=(0, 18))
        grid_con.columnconfigure(0, weight=1, uniform="sec3")
        grid_con.columnconfigure(1, weight=1, uniform="sec3")

        tk.Label(grid_con, text="Teléfono / Celular", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=0, column=0, sticky="w", padx=6)
        self.entry_tel = tb.Entry(grid_con, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_tel.grid(row=1, column=0, sticky="ew", padx=6, ipady=4, pady=(2, 10))

        tk.Label(grid_con, text="Correo Electrónico", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=0, column=1, sticky="w", padx=6)
        self.entry_correo = tb.Entry(grid_con, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_correo.grid(row=1, column=1, sticky="ew", padx=6, ipady=4, pady=(2, 10))

        self.entry_dir = None
        if self.tiene_direccion:
            tk.Label(grid_con, text="Dirección / Zona de Residencia", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").grid(row=2, column=0, columnspan=2, sticky="w", padx=6)
            self.entry_dir = tb.Entry(grid_con, font=("Segoe UI", 10), bootstyle="danger")
            self.entry_dir.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6, ipady=4)

        # Barra de botones
        tk.Frame(card, bg="#E2E8F0", height=1).pack(fill="x", padx=6, pady=(4, 14))
        btns = tk.Frame(card, bg="#FFFFFF")
        btns.pack(fill="x", padx=6)

        tb.Button(
            btns,
            text="Limpiar Formulario",
            bootstyle="secondary-outline",
            command=self._limpiar
        ).pack(side="left", ipady=5, ipadx=10)

        tb.Button(
            btns,
            text="✓ Registrar Postulante",
            bootstyle="danger",
            command=self._guardar
        ).pack(side="right", ipady=6, ipadx=20)

    def _titulo_seccion(self, parent, texto: str):
        frame_sec = tk.Frame(parent, bg="#FFFFFF")
        frame_sec.pack(fill="x", padx=6, pady=(4, 8))
        tk.Label(
            frame_sec,
            text=texto,
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#991B1B"
        ).pack(anchor="w")

    def _restablecer_fecha_defecto(self):
        hoy = date.today()
        anio_def = str(hoy.year - 22)
        self.combo_anio.set(anio_def)
        self.combo_mes.set(self.MESES[0][0])
        self._al_cambiar_mes_anio()
        self.combo_dia.set("15")
        self._actualizar_preview_edad()

    def _al_cambiar_mes_anio(self):
        try:
            anio = int(self.combo_anio.get())
            mes_num = self.meses_map.get(self.combo_mes.get(), 1)
            max_dias = calendar.monthrange(anio, mes_num)[1]
        except Exception:
            max_dias = 31

        nuevos_dias = [f"{d:02d}" for d in range(1, max_dias + 1)]
        self.combo_dia["values"] = nuevos_dias

        dia_actual = self.combo_dia.get()
        if not dia_actual or int(dia_actual) > max_dias:
            self.combo_dia.set(f"{max_dias:02d}")

        self._actualizar_preview_edad()

    def _actualizar_preview_edad(self):
        anio = self.combo_anio.get()
        mes_num = self.meses_map.get(self.combo_mes.get(), 0)
        dia = self.combo_dia.get()

        ok, _msg, _fecha, edad = self.controller.validar_fecha_nacimiento_partes(anio, mes_num, dia)
        if edad is None:
            self.lbl_edad_preview.config(text="", fg="#64748B")
        elif ok:
            self.lbl_edad_preview.config(text=f"Edad: {edad} años  ✓  (Apto para voluntariado)", fg="#15803D")
        else:
            self.lbl_edad_preview.config(text=f"Edad: {edad} años  ✕  (Fuera de rango: 18 a 60 años)", fg="#DC2626")

    def _limpiar(self):
        campos = [self.entry_ci, self.entry_nombres, self.entry_ap_pat, self.entry_ap_mat, self.entry_tel, self.entry_correo]
        if self.entry_dir is not None:
            campos.append(self.entry_dir)
        for w in campos:
            w.delete(0, tk.END)
        self._restablecer_fecha_defecto()

    def _guardar(self):
        datos = {
            "ci": self.entry_ci.get(),
            "nombres": self.entry_nombres.get(),
            "apellido_paterno": self.entry_ap_pat.get(),
            "apellido_materno": self.entry_ap_mat.get(),
            "anio": self.combo_anio.get(),
            "mes_num": self.meses_map.get(self.combo_mes.get(), 0),
            "dia": self.combo_dia.get(),
            "telefono": self.entry_tel.get(),
            "correo": self.entry_correo.get(),
            "direccion": self.entry_dir.get() if self.entry_dir is not None else ""
        }
        exito, msg = self.controller.inscribir_postulante(datos, self.sesion["id_usuario"])
        if not exito:
            messagebox.showwarning("Validación de Postulante", msg)
            return

        messagebox.showinfo("Postulante Registrado", msg)
        self._limpiar()


class AdmisionVoluntariosView(tb.Frame):
    """Vista profesional y organizada para evaluación, admisión y trazabilidad de voluntarios."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = VoluntarioController()
        self.voluntarios_cache = {}
        self.seleccionado = None
        self.tiene_direccion = "direccion" in self.controller.model.obtener_columnas_voluntario()

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_tabla()

    def _construir_ui(self):
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 12))

        tk.Label(
            header,
            text="Admisión y Control de Voluntarios",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Selecciona un postulante o voluntario para revisar su ficha completa, aprobar su ingreso o gestionar su estado.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w", pady=(2, 0))

        # Barra superior de filtros y búsqueda
        barra_filtro = tk.Frame(self, bg="#FFFFFF", padx=16, pady=10)
        barra_filtro.pack(fill="x", pady=(0, 10))

        tk.Label(barra_filtro, text="Filtrar por Estado:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side="left", padx=(0, 6))
        self.combo_estado = tb.Combobox(
            barra_filtro,
            values=["Todos", "Postulante", "Admitido", "Rechazado", "Inactivo"],
            state="readonly",
            width=15,
            bootstyle="danger"
        )
        self.combo_estado.set("Todos")
        self.combo_estado.pack(side="left", padx=(0, 16))
        self.combo_estado.bind("<<ComboboxSelected>>", lambda e: self._cargar_tabla())

        tk.Label(barra_filtro, text="Buscar (CI o Nombre):", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side="left", padx=(0, 6))
        self.entry_busq = tb.Entry(barra_filtro, width=25, bootstyle="danger")
        self.entry_busq.pack(side="left", padx=(0, 8))
        self.entry_busq.bind("<Return>", lambda e: self._cargar_tabla())

        tb.Button(barra_filtro, text="🔍 Buscar", bootstyle="danger", command=self._cargar_tabla).pack(side="left", padx=(0, 6))
        tb.Button(barra_filtro, text="↻ Limpiar", bootstyle="secondary-outline", command=self._limpiar_filtros).pack(side="left")

        # Tabla principal (SIN IDs visibles, incluye Edad)
        card_tbl = tk.Frame(self, bg="#FFFFFF", padx=16, pady=12)
        card_tbl.pack(fill=BOTH, expand=True, pady=(0, 12))

        cols = ("ci", "nombre", "edad", "telefono", "estado", "usuario", "creado")
        self.tabla = tb.Treeview(card_tbl, columns=cols, show="headings", height=7, bootstyle="danger")
        cfg = {
            "ci": ("CI", 95),
            "nombre": ("Nombre Completo", 220),
            "edad": ("Edad", 65),
            "telefono": ("Teléfono", 95),
            "estado": ("Estado", 95),
            "usuario": ("Cuenta Usuario", 125),
            "creado": ("Fecha Registro", 130)
        }
        for c, (tit, w) in cfg.items():
            self.tabla.heading(c, text=tit)
            self.tabla.column(c, width=w, anchor="center" if c != "nombre" else "w")

        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        # Ficha Inferior Estructurada (Detalle del Voluntario + Auditoría + Acciones)
        card_ficha = tk.Frame(self, bg="#FFFFFF", padx=20, pady=16)
        card_ficha.pack(fill="x")

        top_ficha = tk.Frame(card_ficha, bg="#FFFFFF")
        top_ficha.pack(fill="x", pady=(0, 10))

        self.lbl_ficha_titulo = tk.Label(
            top_ficha,
            text="Ficha del Postulante / Voluntario (Selecciona una fila arriba)",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        )
        self.lbl_ficha_titulo.pack(side="left")

        self.lbl_ficha_badge = tk.Label(
            top_ficha,
            text="SIN SELECCIÓN",
            font=("Segoe UI", 8, "bold"),
            bg="#F1F5F9",
            fg="#475569",
            padx=10,
            pady=3
        )
        self.lbl_ficha_badge.pack(side="right")

        det_grid = tk.Frame(card_ficha, bg="#FFF5F5", padx=14, pady=12)
        det_grid.pack(fill="x", pady=(0, 12))
        det_grid.columnconfigure(0, weight=1, uniform="ficha_cols")
        det_grid.columnconfigure(1, weight=1, uniform="ficha_cols")

        self.lbl_col_izq = tk.Label(
            det_grid,
            text=self._texto_izq_vacio(),
            font=("Segoe UI", 9),
            bg="#FFF5F5",
            fg="#1E293B",
            justify="left",
            anchor="nw"
        )
        self.lbl_col_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.lbl_col_der = tk.Label(
            det_grid,
            text="• Usuario Asignado: -\n• Fecha Inscripción: -\n• Fecha Admisión: -\n• Registro en BD (Creado): -\n• Última Modificación BD: -",
            font=("Segoe UI", 9),
            bg="#FFF5F5",
            fg="#1E293B",
            justify="left",
            anchor="nw"
        )
        self.lbl_col_der.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Barra de acciones de evaluación
        acciones_bar = tk.Frame(card_ficha, bg="#FFFFFF")
        acciones_bar.pack(fill="x")

        tk.Label(
            acciones_bar,
            text="Acciones de Evaluación:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#475569"
        ).pack(side="left")

        tb.Button(
            acciones_bar,
            text="🚫 Desactivar Cuenta",
            bootstyle="secondary-outline",
            command=self._desactivar
        ).pack(side="right", padx=(8, 0), ipady=4)

        tb.Button(
            acciones_bar,
            text="✕ Rechazar Postulación",
            bootstyle="warning-outline",
            command=self._rechazar
        ).pack(side="right", padx=(8, 0), ipady=4)

        tb.Button(
            acciones_bar,
            text="✅ Admitir y Generar Credenciales",
            bootstyle="danger",
            command=self._admitir
        ).pack(side="right", ipady=4, ipadx=12)

    def _texto_izq_vacio(self) -> str:
        base = "• CI: -\n• Fecha Nacimiento: -\n• Teléfono: -\n• Correo: -"
        if self.tiene_direccion:
            base += "\n• Dirección: -"
        return base

    def _limpiar_filtros(self):
        self.combo_estado.set("Todos")
        self.entry_busq.delete(0, tk.END)
        self._cargar_tabla()

    def _resetear_ficha(self):
        self.seleccionado = None
        self.lbl_ficha_titulo.config(text="Ficha del Postulante / Voluntario (Selecciona una fila arriba)")
        self.lbl_ficha_badge.config(text="SIN SELECCIÓN", bg="#F1F5F9", fg="#475569")
        self.lbl_col_izq.config(text=self._texto_izq_vacio())
        self.lbl_col_der.config(text="• Usuario Asignado: -\n• Fecha Inscripción: -\n• Fecha Admisión: -\n• Registro en BD (Creado): -\n• Última Modificación BD: -")

    def _cargar_tabla(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)
        self.voluntarios_cache.clear()
        self._resetear_ficha()

        try:
            lista = self.controller.obtener_voluntarios(self.combo_estado.get(), self.entry_busq.get())
            for v in lista:
                iid = str(v["id_voluntario"])
                self.voluntarios_cache[iid] = v
                edad_txt = f"{v['edad']} años" if v["edad"] is not None else "-"
                self.tabla.insert("", tk.END, iid=iid, values=(
                    v["ci"],
                    v["nombre_completo"],
                    edad_txt,
                    v["telefono"] or "-",
                    v["estado"],
                    v["cuenta_usuario"] or "Sin cuenta",
                    v["fecha_creacion_str"]
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar(self, _event):
        sel = self.tabla.selection()
        if not sel:
            return
        v = self.voluntarios_cache.get(sel[0])
        if not v:
            return
        self.seleccionado = v

        est = v["estado"]
        colores_badge = {
            "Postulante": ("#FEF3C7", "#B45309"),
            "Admitido": ("#DCFCE7", "#15803D"),
            "Rechazado": ("#FEE2E2", "#B91C1C"),
            "Inactivo": ("#E2E8F0", "#475569")
        }
        bg_b, fg_b = colores_badge.get(est, ("#F1F5F9", "#475569"))

        self.lbl_ficha_titulo.config(text=f"Ficha: {v['nombre_completo']}")
        self.lbl_ficha_badge.config(text=est.upper(), bg=bg_b, fg=fg_b)

        edad_info = f" ({v['edad']} años)" if v["edad"] is not None else ""
        texto_izq = (
            f"• Carnet de Identidad: {v['ci']}\n"
            f"• Fecha de Nacimiento: {v['fecha_nacimiento_str']}{edad_info}\n"
            f"• Teléfono / Celular: {v['telefono'] or 'No registrado'}\n"
            f"• Correo Electrónico: {v['correo'] or 'No registrado'}"
        )
        if self.tiene_direccion:
            texto_izq += f"\n• Dirección: {v['direccion'] or 'No registrada'}"

        self.lbl_col_izq.config(text=texto_izq)

        self.lbl_col_der.config(
            text=(
                f"• Cuenta de Acceso: {v['cuenta_usuario'] or 'Pendiente de admisión'}\n"
                f"• Fecha de Inscripción: {v['fecha_inscripcion'] or '-'}\n"
                f"• Fecha de Admisión: {v['fecha_admision'] or 'Pendiente'}\n"
                f"• Auditoría Creación BD: {v['fecha_creacion_str']}\n"
                f"• Auditoría Modificación BD: {v['fecha_actualizacion_str']}"
            )
        )

    def _admitir(self):
        exito, msg = self.controller.aprobar_postulante(self.seleccionado)
        if not exito:
            messagebox.showwarning("Atención", msg)
            return
        messagebox.showinfo("Admisión Completada", msg)
        self._cargar_tabla()

    def _rechazar(self):
        if not self.seleccionado:
            messagebox.showwarning("Atención", "Selecciona primero un postulante de la tabla.")
            return
        if not messagebox.askyesno("Confirmar Rechazo", f"¿Rechazar la postulación de {self.seleccionado['nombre_completo']}?"):
            return
        exito, msg = self.controller.rechazar_postulante(self.seleccionado)
        if not exito:
            messagebox.showwarning("Atención", msg)
            return
        messagebox.showinfo("Postulación Rechazada", msg)
        self._cargar_tabla()

    def _desactivar(self):
        if not self.seleccionado:
            messagebox.showwarning("Atención", "Selecciona un voluntario admitido de la tabla.")
            return
        if not messagebox.askyesno("Confirmar Desactivación", f"¿Desactivar la cuenta de {self.seleccionado['nombre_completo']}?"):
            return
        exito, msg = self.controller.desactivar_voluntario(self.seleccionado)
        if not exito:
            messagebox.showwarning("Atención", msg)
            return
        messagebox.showinfo("Cuenta Desactivada", msg)
        self._cargar_tabla()