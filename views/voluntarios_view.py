from datetime import date
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.voluntario_controller import VoluntarioController
from views.ui_components import PALETTE, RoundedCard, InputValidators, SaveTheChildrenLogo


class InscripcionVoluntarioView(tk.Frame):
    """Pestaña de Inscripción de Postulantes con filtros de teclado y cálculo automático de edad."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = VoluntarioController()

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._actualizar_edad_preview()

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Inscripción de Postulante a Voluntariado",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            header,
            text="Registra los datos personales del aspirante antes de realizar la verificación documental de admisión.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        # =====================================================================
        # 2. CONTENEDOR PRINCIPAL: FORMULARIO CURVO + PANEL LATERAL DE REGLAS
        # =====================================================================
        cuerpo = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        # --- TARJETA IZQUIERDA: FORMULARIO DE INSCRIPCIÓN ---
        card_form = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=26,
            pady=14,
            expand_body=True
        )
        card_form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        b = card_form.body

        tk.Label(
            b,
            text="Datos Personales y de Contacto del Postulante",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            b,
            text="Los campos marcados con (*) son obligatorios. Cada casilla restringe el tipo de carácter permitido.",
            font=("Segoe UI", 9),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w", pady=(0, 14))

        tk.Frame(b, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(0, 16))

        grid = tk.Frame(b, bg=PALETTE["blanco"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="form_col")
        grid.columnconfigure(1, weight=1, uniform="form_col")

        # Fila 0: CI | Nombres
        self.entry_ci = self._crear_campo(
            grid, row=0, col=0,
            etiqueta="Carnet de Identidad (CI) *",
            validacion="enteros"
        )
        self.entry_nombres = self._crear_campo(
            grid, row=0, col=1,
            etiqueta="Nombres *",
            validacion="letras"
        )

        # Fila 1: Apellido Paterno | Apellido Materno
        self.entry_ap_paterno = self._crear_campo(
            grid, row=1, col=0,
            etiqueta="Apellido Paterno *",
            validacion="letras"
        )
        self.entry_ap_materno = self._crear_campo(
            grid, row=1, col=1,
            etiqueta="Apellido Materno",
            validacion="letras"
        )

        # Fila 2: Fecha de Nacimiento + Edad Calculada | Teléfono *
        celda_fecha = tk.Frame(grid, bg=PALETTE["blanco"])
        celda_fecha.grid(row=2, column=0, sticky="ew", padx=(0, 12), pady=(0, 8))

        tk.Label(
            celda_fecha,
            text="Fecha de Nacimiento *  (AAAA-MM-DD)",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        fecha_row = tk.Frame(celda_fecha, bg=PALETTE["blanco"])
        fecha_row.pack(fill="x")

        fecha_defecto = date.today().replace(year=date.today().year - 22)
        self.date_nac = tb.DateEntry(
            fecha_row,
            dateformat="%Y-%m-%d",
            startdate=fecha_defecto,
            bootstyle="danger",
            width=15
        )
        self.date_nac.pack(side="left", ipady=2)

        self.lbl_edad_calc = tk.Label(
            fecha_row,
            text="Edad: -- años",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            padx=12,
            pady=6
        )
        self.lbl_edad_calc.pack(side="left", padx=(10, 0), fill="x", expand=True)

        self.date_nac.entry.bind("<KeyRelease>", self._actualizar_edad_preview)
        self.date_nac.entry.bind("<FocusOut>", self._actualizar_edad_preview)
        self.date_nac.bind("<<DateEntrySelected>>", self._actualizar_edad_preview)

        self.entry_telefono = self._crear_campo(
            grid, row=2, col=1,
            etiqueta="Teléfono / Celular *",
            validacion="enteros"
        )

        # Fila 3: Correo Electrónico | Dirección / Zona
        self.entry_correo = self._crear_campo(
            grid, row=3, col=0,
            etiqueta="Correo Electrónico",
            validacion=None
        )
        self.entry_direccion = self._crear_campo(
            grid, row=3, col=1,
            etiqueta="Dirección / Zona de Residencia",
            validacion=None
        )

        # Barra inferior de botones
        tk.Frame(b, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(6, 10))

        btn_bar = tk.Frame(b, bg=PALETTE["blanco"])
        btn_bar.pack(fill="x")

        btn_limpiar = tk.Button(
            btn_bar,
            text="Limpiar Campos",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
            command=self._limpiar_formulario
        )
        btn_limpiar.pack(side="left")

        btn_guardar = tk.Button(
            btn_bar,
            text="✓  Registrar Postulante",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=24,
            pady=10,
            cursor="hand2",
            command=self._guardar_postulante
        )
        btn_guardar.pack(side="right")
        btn_guardar.bind("<Enter>", lambda _e: btn_guardar.config(bg=PALETTE["rojo_hover"]))
        btn_guardar.bind("<Leave>", lambda _e: btn_guardar.config(bg=PALETTE["rojo"]))

        # --- TARJETA DERECHA: REQUISITOS Y FLUJO DE ADMISIÓN ---
        card_info = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=14,
            expand_body=True
        )
        card_info.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        bi = card_info.body

        tk.Frame(bi, bg=PALETTE["rojo"], height=4).pack(fill="x", pady=(0, 12))

        tk.Label(
            bi,
            text="Flujo de Inscripción y Admisión",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        reglas = [
            ("1. Edad Reglamentaria", "El postulante debe tener entre 18 y 60 años cumplidos a la fecha."),
            ("2. Identidad y Contacto", "CI único (5 a 12 dígitos) y teléfono obligatorio (7 a 10 dígitos)."),
            ("3. Verificación Documental", "En 'Admisión Voluntarios' se validan los 5 respaldos físicos (CI, Solicitud, Acuerdo, Antecedentes y CV)."),
            ("4. Dictamen y Credenciales", "Al aprobar la evaluación se genera automáticamente su usuario y contraseña.")
        ]

        for titulo_r, desc_r in reglas:
            box = tk.Frame(bi, bg=PALETTE["plomo_fondo"], padx=12, pady=9)
            box.pack(fill="x", pady=(0, 8))

            tk.Label(
                box,
                text=titulo_r,
                font=("Segoe UI", 9, "bold"),
                bg=PALETTE["plomo_fondo"],
                fg=PALETTE["negro"],
                anchor="w"
            ).pack(fill="x")

            tk.Label(
                box,
                text=desc_r,
                font=("Segoe UI", 8),
                bg=PALETTE["plomo_fondo"],
                fg=PALETTE["plomo_texto"],
                wraplength=230,
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=(2, 0))

    def _crear_campo(self, parent, row: int, col: int, etiqueta: str, validacion: str | None):
        padx = (0, 12) if col == 0 else (12, 0)
        celda = tk.Frame(parent, bg=PALETTE["blanco"])
        celda.grid(row=row, column=col, sticky="ew", padx=padx, pady=(0, 8))

        tk.Label(
            celda,
            text=etiqueta,
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        entry = tb.Entry(celda, font=("Segoe UI", 10))
        entry.pack(fill="x", ipady=4)

        if validacion:
            InputValidators.aplicar(entry, validacion)

        return entry

    def _actualizar_edad_preview(self, _event=None):
        texto_fecha = self.date_nac.entry.get().strip()
        try:
            fecha_nac = self.controller.parsear_fecha(texto_fecha)
            edad = self.controller.calcular_edad(fecha_nac)
            if 18 <= edad <= 60:
                self.lbl_edad_calc.config(
                    text=f"✓ {edad} años (Apto)",
                    bg="#DCFCE7",
                    fg="#15803D"
                )
            else:
                self.lbl_edad_calc.config(
                    text=f"✕ {edad} años (Fuera de rango)",
                    bg=PALETTE["rojo_suave"],
                    fg=PALETTE["rojo"]
                )
        except Exception:
            self.lbl_edad_calc.config(
                text="Fecha incompleta",
                bg=PALETTE["plomo_fondo"],
                fg=PALETTE["plomo_texto"]
            )

    def _limpiar_formulario(self):
        for entry in (
            self.entry_ci,
            self.entry_nombres,
            self.entry_ap_paterno,
            self.entry_ap_materno,
            self.entry_telefono,
            self.entry_correo,
            self.entry_direccion
        ):
            entry.delete(0, tk.END)

        fecha_defecto = date.today().replace(year=date.today().year - 22)
        self.date_nac.entry.delete(0, tk.END)
        self.date_nac.entry.insert(0, fecha_defecto.strftime("%Y-%m-%d"))
        self._actualizar_edad_preview()
        self.entry_ci.focus_set()

    def _guardar_postulante(self):
        datos = {
            "ci": self.entry_ci.get(),
            "nombres": self.entry_nombres.get(),
            "apellido_paterno": self.entry_ap_paterno.get(),
            "apellido_materno": self.entry_ap_materno.get(),
            "fecha_nacimiento": self.date_nac.entry.get(),
            "telefono": self.entry_telefono.get(),
            "correo": self.entry_correo.get(),
            "direccion": self.entry_direccion.get(),
            "id_admin_registra": self.sesion.get("id_usuario")
        }

        exito, mensaje = self.controller.registrar_postulante(datos)
        if exito:
            messagebox.showinfo("Inscripción Exitosa", mensaje)
            self._limpiar_formulario()
        else:
            messagebox.showwarning("Validación de Inscripción", mensaje)


class ModalEvaluacionAdmision(tk.Toplevel):
    """
    Ventana modal desplazable de verificación física de los 5 requisitos de admisión.
    Mantiene fija la cabecera y los botones inferiores mientras permite hacer scroll
    en el cuerpo cuando se despliega la justificación manual.
    """

    def __init__(self, master, voluntario: dict, sesion: dict, controller: VoluntarioController, on_guardado):
        super().__init__(master)
        self.voluntario = voluntario
        self.sesion = sesion
        self.controller = controller
        self.on_guardado = on_guardado

        self.title(f"Evaluación Documental — {voluntario['nombre_completo']}")
        self.configure(bg=PALETTE["plomo_fondo"])
        self.resizable(False, True)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        # Variables del formulario
        self.var_ci = tk.BooleanVar(value=bool(voluntario.get("ci_presentado")))
        self.var_datos = tk.BooleanVar(value=bool(voluntario.get("datos_verificados")))
        self.var_disponibilidad = tk.StringVar(
            value=voluntario.get("disponibilidad") or "Fines de Semana"
        )
        self.var_acuerdo = tk.BooleanVar(value=bool(voluntario.get("acepta_reglas")))
        self.var_ant_pres = tk.BooleanVar(value=bool(voluntario.get("antecedentes_presentado")))
        self.var_tiene_ant = tk.BooleanVar(value=bool(voluntario.get("tiene_antecedentes")))
        self.var_cv_pres = tk.BooleanVar(value=bool(voluntario.get("cv_presentado")))
        self.var_educacion = tk.StringVar(
            value=voluntario.get("nivel_educativo") or "Bachiller"
        )
        self.var_laboral = tk.StringVar(
            value=voluntario.get("situacion_laboral") or "No Trabaja"
        )
        self.var_anular_manual = tk.BooleanVar(value=False)
        self.var_decision_manual = tk.StringVar(value="Admitido")

        self._construir_ui()
        self._recalcular_veredicto()
        self._centrar_ventana()

    def _centrar_ventana(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(max(690, self.winfo_reqwidth() + 24), sw - 40)
        h = min(self.winfo_reqheight(), sh - 90)
        x = max(20, (sw - w) // 2)
        y = max(20, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _al_destruir(self, event):
        if event.widget is self:
            self.unbind_all("<MouseWheel>")

    def _construir_ui(self):
        # =====================================================================
        # 1. CABECERA INSTITUCIONAL FIJA ARRIBA
        # =====================================================================
        hdr_wrap = tk.Frame(self, bg=PALETTE["plomo_fondo"], padx=18, pady=12)
        hdr_wrap.pack(side="top", fill="x")

        hdr = tk.Frame(hdr_wrap, bg=PALETTE["negro"], padx=16, pady=10)
        hdr.pack(fill="x")

        SaveTheChildrenLogo(hdr, size=32, bg=PALETTE["negro"]).pack(side="left", padx=(0, 10))

        info_hdr = tk.Frame(hdr, bg=PALETTE["negro"])
        info_hdr.pack(side="left", fill="x", expand=True)

        tk.Label(
            info_hdr,
            text=f"Evaluación de Admisión: {self.voluntario['nombre_completo']}",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            info_hdr,
            text=(
                f"CI: {self.voluntario['ci']}  •  Edad: {self.voluntario.get('edad', '-')} años  •  "
                f"Tel: {self.voluntario.get('telefono') or '-'}"
            ),
            font=("Segoe UI", 8),
            bg=PALETTE["negro"],
            fg=PALETTE["plomo_claro"],
            anchor="w"
        ).pack(fill="x")

        # =====================================================================
        # 2. BARRA INFERIOR FIJA DE BOTONES (SIEMPRE VISIBLE)
        # =====================================================================
        footer = tk.Frame(self, bg=PALETTE["blanco"], padx=18, pady=12)
        footer.pack(side="bottom", fill="x")

        tk.Frame(self, bg=PALETTE["plomo_borde"], height=1).pack(side="bottom", fill="x")

        tk.Button(
            footer,
            text="Cancelar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            bd=1,
            relief="solid",
            padx=16,
            pady=7,
            cursor="hand2",
            command=self.destroy
        ).pack(side="left")

        btn_confirmar = tk.Button(
            footer,
            text="✓  Guardar Evaluación y Aplicar Decisión",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._guardar
        )
        btn_confirmar.pack(side="right")
        btn_confirmar.bind("<Enter>", lambda _e: btn_confirmar.config(bg=PALETTE["rojo_hover"]))
        btn_confirmar.bind("<Leave>", lambda _e: btn_confirmar.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # 3. CONTENEDOR CENTRAL DESPLAZABLE (CANVAS + SCROLLBAR)
        # =====================================================================
        scroll_container = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        scroll_container.pack(side="top", fill=BOTH, expand=True)

        self.canvas = tk.Canvas(
            scroll_container,
            bg=PALETTE["plomo_fondo"],
            highlightthickness=0,
            bd=0
        )
        scrollbar = tb.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self.canvas.yview,
            bootstyle="danger-round"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=(0, 10))
        self.canvas.pack(side="left", fill=BOTH, expand=True)

        wrap = tk.Frame(self.canvas, bg=PALETTE["plomo_fondo"], padx=18, pady=4)
        self._win_id = self.canvas.create_window((0, 0), window=wrap, anchor="nw")

        wrap.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self._win_id, width=e.width)
        )

        def _on_mousewheel(event):
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", self._al_destruir)

        # Tarjeta blanca de checklist dentro del área desplazable
        card = tk.Frame(
            wrap,
            bg=PALETTE["blanco"],
            highlightbackground=PALETTE["plomo_borde"],
            highlightthickness=1,
            padx=18,
            pady=14
        )
        card.pack(fill="x", pady=(0, 10))

        # 1. Cédula de Identidad
        self._bloque_requisito(
            card,
            titulo="1. Cédula de Identidad (Fotocopia física)",
            texto_check="El postulante presentó fotocopia legible de su Cédula de Identidad vigente.",
            variable=self.var_ci
        )

        # 2. Formulario de Solicitud + Disponibilidad
        b2 = self._bloque_requisito(
            card,
            titulo="2. Formulario de Solicitud y Disponibilidad Horaria",
            texto_check="Se comprobó que los datos registrados en el sistema coinciden con su solicitud.",
            variable=self.var_datos
        )
        row_disp = tk.Frame(b2, bg=PALETTE["plomo_fondo"])
        row_disp.pack(fill="x", pady=(6, 0))
        tk.Label(
            row_disp,
            text="Disponibilidad declarada:",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 8))
        cb_disp = tb.Combobox(
            row_disp,
            textvariable=self.var_disponibilidad,
            values=list(self.controller.DISPONIBILIDADES),
            state="readonly",
            width=24,
            bootstyle="danger"
        )
        cb_disp.pack(side="left")

        # 3. Acuerdo de Voluntario
        self._bloque_requisito(
            card,
            titulo="3. Acuerdo de Voluntario y Código de Conducta",
            texto_check="El postulante declara estar de acuerdo con las reglas y políticas de Save the Children.",
            variable=self.var_acuerdo
        )

        # 4. Certificado de Antecedentes
        b4 = self._bloque_requisito(
            card,
            titulo="4. Certificado de Antecedentes (Filtro de Seguridad)",
            texto_check="Presentó su Certificado de Antecedentes vigente.",
            variable=self.var_ant_pres,
            comando_extra=self._toggle_antecedentes
        )
        self.chk_tiene_ant = tb.Checkbutton(
            b4,
            text="⚠ El certificado registra antecedentes (Inhabilita admisión automática)",
            variable=self.var_tiene_ant,
            bootstyle="danger-round-toggle",
            command=self._recalcular_veredicto
        )
        self.chk_tiene_ant.pack(anchor="w", pady=(6, 0))

        # 5. Currículum Vitae
        b5 = self._bloque_requisito(
            card,
            titulo="5. Currículum Vitae (Formación Académica y Situación Laboral)",
            texto_check="Presentó su Currículum Vitae documentado.",
            variable=self.var_cv_pres
        )
        row_cv = tk.Frame(b5, bg=PALETTE["plomo_fondo"])
        row_cv.pack(fill="x", pady=(6, 0))

        tk.Label(
            row_cv,
            text="Nivel educativo:",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))
        tb.Combobox(
            row_cv,
            textvariable=self.var_educacion,
            values=list(self.controller.NIVELES_EDUCATIVOS),
            state="readonly",
            width=28,
            bootstyle="secondary"
        ).pack(side="left", padx=(0, 14))

        tk.Label(
            row_cv,
            text="Situación laboral:",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))
        tb.Combobox(
            row_cv,
            textvariable=self.var_laboral,
            values=list(self.controller.SITUACIONES_LABORALES),
            state="readonly",
            width=22,
            bootstyle="secondary"
        ).pack(side="left")

        # =====================================================================
        # PANEL DE VEREDICTO AUTOMÁTICO Y ANULACIÓN MANUAL AUDITADA
        # =====================================================================
        self.veredicto_box = tk.Frame(card, bg="#DCFCE7", padx=14, pady=10)
        self.veredicto_box.pack(fill="x", pady=(8, 8))

        self.lbl_veredicto = tk.Label(
            self.veredicto_box,
            text="DICTAMEN AUTOMÁTICO DEL SISTEMA: ADMITIDO",
            font=("Segoe UI", 10, "bold"),
            bg="#DCFCE7",
            fg="#15803D",
            anchor="w"
        )
        self.lbl_veredicto.pack(fill="x")

        self.lbl_veredicto_desc = tk.Label(
            self.veredicto_box,
            text="Cumple con los 5 requisitos documentales y no registra antecedentes.",
            font=("Segoe UI", 8),
            bg="#DCFCE7",
            fg=PALETTE["negro"],
            anchor="w"
        )
        self.lbl_veredicto_desc.pack(fill="x")

        # Opción de cambio manual por el administrador
        override_row = tk.Frame(card, bg=PALETTE["blanco"])
        override_row.pack(fill="x", pady=(2, 4))

        tb.Checkbutton(
            override_row,
            text="Modificar dictamen automáticamente calculado (Requiere justificación obligatoria)",
            variable=self.var_anular_manual,
            bootstyle="warning-round-toggle",
            command=self._toggle_override
        ).pack(side="left")

        self.frame_override = tk.Frame(card, bg=PALETTE["plomo_fondo"], padx=12, pady=10)

        ov_top = tk.Frame(self.frame_override, bg=PALETTE["plomo_fondo"])
        ov_top.pack(fill="x", pady=(0, 6))

        tk.Label(
            ov_top,
            text="Decisión final del Administrador:",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 8))

        self.cb_decision_manual = tb.Combobox(
            ov_top,
            textvariable=self.var_decision_manual,
            values=["Admitido", "Rechazado"],
            state="readonly",
            width=15,
            bootstyle="danger"
        )
        self.cb_decision_manual.pack(side="left")

        tk.Label(
            self.frame_override,
            text="Motivo del cambio (obligatorio):",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        self.entry_motivo = tb.Entry(self.frame_override, font=("Segoe UI", 9))
        self.entry_motivo.pack(fill="x", ipady=3, pady=(2, 0))

        self._toggle_antecedentes()

    def _bloque_requisito(self, parent, titulo: str, texto_check: str, variable: tk.BooleanVar, comando_extra=None):
        box = tk.Frame(parent, bg=PALETTE["plomo_fondo"], padx=12, pady=8)
        box.pack(fill="x", pady=(0, 7))

        tk.Label(
            box,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 3))

        def _al_marcar():
            if callable(comando_extra):
                comando_extra()
            self._recalcular_veredicto()

        tb.Checkbutton(
            box,
            text=texto_check,
            variable=variable,
            bootstyle="success-round-toggle",
            command=_al_marcar
        ).pack(anchor="w")

        return box

    def _toggle_antecedentes(self):
        if self.var_ant_pres.get():
            self.chk_tiene_ant.configure(state="normal")
        else:
            self.var_tiene_ant.set(False)
            self.chk_tiene_ant.configure(state="disabled")

    def _toggle_override(self):
        if self.var_anular_manual.get():
            self.frame_override.pack(fill="x", pady=(2, 6))
            auto = self._obtener_dictamen_actual()
            self.var_decision_manual.set("Rechazado" if auto == "Admitido" else "Admitido")
            self.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.yview_moveto(1.0)
            self.entry_motivo.focus_set()
        else:
            self.frame_override.pack_forget()
            self.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _obtener_dictamen_actual(self) -> str:
        return self.controller.calcular_dictamen_automatico(
            ci_presentado=self.var_ci.get(),
            datos_verificados=self.var_datos.get(),
            acepta_reglas=self.var_acuerdo.get(),
            antecedentes_presentado=self.var_ant_pres.get(),
            tiene_antecedentes=self.var_tiene_ant.get(),
            cv_presentado=self.var_cv_pres.get()
        )

    def _recalcular_veredicto(self):
        dictamen = self._obtener_dictamen_actual()
        if dictamen == "Admitido":
            self.veredicto_box.config(bg="#DCFCE7")
            self.lbl_veredicto.config(
                text="DICTAMEN AUTOMÁTICO DEL SISTEMA: ADMITIDO",
                bg="#DCFCE7",
                fg="#15803D"
            )
            self.lbl_veredicto_desc.config(
                text="Cumple con los 5 requisitos documentales y no registra antecedentes.",
                bg="#DCFCE7"
            )
        else:
            self.veredicto_box.config(bg=PALETTE["rojo_suave"])
            self.lbl_veredicto.config(
                text="DICTAMEN AUTOMÁTICO DEL SISTEMA: RECHAZADO",
                bg=PALETTE["rojo_suave"],
                fg=PALETTE["rojo"]
            )
            razon = (
                "El certificado reporta antecedentes penales/policiales."
                if self.var_tiene_ant.get()
                else "Falta presentar o verificar uno o más requisitos documentales."
            )
            self.lbl_veredicto_desc.config(text=razon, bg=PALETTE["rojo_suave"])

    def _guardar(self):
        auto = self._obtener_dictamen_actual()
        decision = self.var_decision_manual.get() if self.var_anular_manual.get() else auto

        form_eval = {
            "ci_presentado": self.var_ci.get(),
            "datos_verificados": self.var_datos.get(),
            "disponibilidad": self.var_disponibilidad.get(),
            "acepta_reglas": self.var_acuerdo.get(),
            "antecedentes_presentado": self.var_ant_pres.get(),
            "tiene_antecedentes": self.var_tiene_ant.get(),
            "cv_presentado": self.var_cv_pres.get(),
            "nivel_educativo": self.var_educacion.get(),
            "situacion_laboral": self.var_laboral.get(),
            "decision_final": decision,
            "motivo_cambio": self.entry_motivo.get() if self.var_anular_manual.get() else ""
        }

        exito, resultado = self.controller.evaluar_admision(
            voluntario=self.voluntario,
            form_eval=form_eval,
            id_admin_evalua=self.sesion["id_usuario"]
        )
        if not exito:
            messagebox.showwarning("Validación de Admisión", str(resultado), parent=self)
            return

        if isinstance(resultado, dict) and resultado.get("decision_final") == "Admitido":
            msg = f"Se admitió a {resultado['nombre']} como Voluntario activo.\n\n"
            if resultado.get("cuenta_creada"):
                msg += (
                    f"• Usuario asignado: {resultado['usuario']}\n"
                    f"• Contraseña temporal: {resultado['password']}\n\n"
                    "Entrega estas credenciales al voluntario para su ingreso al portal."
                )
            else:
                msg += f"• Cuenta vinculada: {resultado.get('usuario')}"
            messagebox.showinfo("Voluntario Admitido", msg, parent=self)
        else:
            messagebox.showinfo(
                "Postulante Rechazado",
                f"La evaluación de {self.voluntario['nombre_completo']} quedó registrada con dictamen: RECHAZADO.",
                parent=self
            )

        self.destroy()
        if callable(self.on_guardado):
            self.on_guardado()


class AdmisionVoluntariosView(tk.Frame):
    """Pestaña de Admisión y Control de Voluntarios con evaluación documental y control de strikes."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = VoluntarioController()
        self.voluntarios_cache = {}

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._cargar_voluntarios()

    def _configurar_estilos_tabla(self):
        style = tb.Style()
        style.configure(
            "Vol.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=32,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Vol.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 8)
        )
        style.map(
            "Vol.Treeview.Heading",
            background=[("active", PALETTE["plomo_borde"])]
        )
        style.map(
            "Vol.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        izq = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        izq.pack(side="left", fill="x", expand=True)

        tk.Label(
            izq,
            text="Admisión y Control de Voluntarios",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            izq,
            text="Evalúa requisitos físicos, genera credenciales de acceso y administra el estado y strikes.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_ref = tk.Button(
            header,
            text="↻  Actualizar Lista",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._cargar_voluntarios
        )
        btn_ref.pack(side="right", pady=6)
        btn_ref.bind("<Enter>", lambda _e: btn_ref.config(bg=PALETTE["rojo_hover"]))
        btn_ref.bind("<Leave>", lambda _e: btn_ref.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # 2. BARRA CURVA DE FILTROS Y ACCIONES DE ADMISIÓN
        # =====================================================================
        card_top = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=12,
            expand_body=False
        )
        card_top.pack(fill="x", pady=(0, 12))

        bar = card_top.body

        tk.Label(
            bar,
            text="Estado:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.combo_estado = tb.Combobox(
            bar,
            values=["Todos", "Postulante", "Admitido", "Rechazado", "Inactivo", "Inactivo_Definitivo"],
            state="readonly",
            width=18,
            bootstyle="danger"
        )
        self.combo_estado.set("Todos")
        self.combo_estado.pack(side="left", padx=(0, 14))
        self.combo_estado.bind("<<ComboboxSelected>>", lambda _e: self._cargar_voluntarios())

        tk.Label(
            bar,
            text="Buscar (CI o Nombre):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.entry_buscar = tb.Entry(bar, width=22, font=("Segoe UI", 9))
        self.entry_buscar.pack(side="left", ipady=2)
        self.entry_buscar.bind("<KeyRelease>", lambda _e: self._cargar_voluntarios())

        # Botones de acción derechos
        btn_reactivar = tk.Button(
            bar,
            text="Reactivar",
            font=("Segoe UI", 9, "bold"),
            bg="#DCFCE7",
            fg="#15803D",
            activebackground="#15803D",
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=11,
            pady=6,
            cursor="hand2",
            command=lambda: self._cambiar_estado_seleccionado("Admitido")
        )
        btn_reactivar.pack(side="right", padx=(6, 0))

        btn_baja = tk.Button(
            bar,
            text="Desactivar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=11,
            pady=6,
            cursor="hand2",
            command=lambda: self._cambiar_estado_seleccionado("Inactivo")
        )
        btn_baja.pack(side="right", padx=(6, 0))

        btn_evaluar = tk.Button(
            bar,
            text="📋 Evaluar Requisitos y Admitir",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._abrir_evaluacion_seleccionado
        )
        btn_evaluar.pack(side="right")
        btn_evaluar.bind("<Enter>", lambda _e: btn_evaluar.config(bg=PALETTE["rojo_hover"]))
        btn_evaluar.bind("<Leave>", lambda _e: btn_evaluar.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # 3. TARJETA CURVA PRINCIPAL CON TABLA RESALTANTE
        # =====================================================================
        card_tbl = RoundedCard(
            self,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=16,
            expand_body=True
        )
        card_tbl.pack(fill=BOTH, expand=True, pady=(0, 12))

        bt = card_tbl.body

        tbl_hdr = tk.Frame(bt, bg=PALETTE["blanco"])
        tbl_hdr.pack(fill="x", pady=(0, 10))

        tk.Label(
            tbl_hdr,
            text="📋  Listado General de Postulantes y Voluntarios",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left")

        self.lbl_contador = tk.Label(
            tbl_hdr,
            text="0 registros",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            padx=10,
            pady=3
        )
        self.lbl_contador.pack(side="right")

        cols = ("ci", "nombre", "edad", "telefono", "inscripcion", "disponibilidad", "strikes", "estado", "usuario")
        self.tabla = tb.Treeview(
            bt,
            columns=cols,
            show="headings",
            height=8,
            style="Vol.Treeview"
        )
        cfg = {
            "ci": ("CI", 90),
            "nombre": ("Nombre Completo", 210),
            "edad": ("Edad", 65),
            "telefono": ("Teléfono", 90),
            "inscripcion": ("F. Inscripción", 135),
            "disponibilidad": ("Disponibilidad", 120),
            "strikes": ("Strikes", 65),
            "estado": ("Estado", 115),
            "usuario": ("Cuenta Usuario", 125)
        }
        for c, (tit, w) in cfg.items():
            self.tabla.heading(c, text=tit)
            self.tabla.column(c, width=w, anchor="center" if c not in ("nombre", "usuario") else "w")

        self.tabla.tag_configure("par", background=PALETTE["blanco"])
        self.tabla.tag_configure("impar", background="#F9FAFB")
        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        # =====================================================================
        # 4. FICHA INFERIOR CURVA DE DETALLE DEL VOLUNTARIO SELECCIONADO
        # =====================================================================
        card_det = RoundedCard(
            self,
            radius=16,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=10,
            expand_body=False
        )
        card_det.pack(fill="x")

        self.lbl_detalle = tk.Label(
            card_det.body,
            text="Selecciona un registro de la tabla para ver su evaluación documental, disponibilidad, strikes y cuenta.",
            font=("Segoe UI", 9),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            anchor="w",
            justify="left"
        )
        self.lbl_detalle.pack(fill="x")

    def _cargar_voluntarios(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)
        self.voluntarios_cache.clear()
        self.lbl_detalle.config(
            text="Selecciona un registro de la tabla para ver su evaluación documental, disponibilidad, strikes y cuenta.",
            fg=PALETTE["plomo_texto"]
        )

        try:
            filas = self.controller.listar_voluntarios(
                filtro_estado=self.combo_estado.get(),
                busqueda=self.entry_buscar.get()
            )
            self.lbl_contador.config(text=f"{len(filas)} registro(s)")

            for idx, v in enumerate(filas):
                iid = str(v["id_voluntario"])
                self.voluntarios_cache[iid] = v
                tag = "par" if idx % 2 == 0 else "impar"
                edad_txt = f"{v['edad']} años" if v.get("edad") is not None else "-"
                disp_txt = v.get("disponibilidad") or "Sin evaluar"
                strikes_txt = f"{v['total_strikes']}/5"
                usuario_txt = v.get("cuenta_usuario") or "Sin cuenta"

                self.tabla.insert("", tk.END, iid=iid, values=(
                    v["ci"],
                    v["nombre_completo"],
                    edad_txt,
                    v.get("telefono") or "-",
                    v.get("fecha_inscripcion_str", "-"),
                    disp_txt,
                    strikes_txt,
                    v["estado"],
                    usuario_txt
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _obtener_seleccionado(self) -> dict | None:
        sel = self.tabla.selection()
        if not sel:
            return None
        return self.voluntarios_cache.get(sel[0])

    def _al_seleccionar(self, _event):
        v = self._obtener_seleccionado()
        if not v:
            return

        usr = v.get("cuenta_usuario") or "Sin cuenta"
        if v.get("resultado_automatico"):
            eval_info = (
                f"Educación: {v.get('nivel_educativo')} ({v.get('situacion_laboral')})  |  "
                f"Dictamen Auto: {v.get('resultado_automatico')} → Final: {v.get('decision_final')}"
            )
            if v.get("motivo_cambio"):
                eval_info += f" (Cambio manual: {v['motivo_cambio']})"
        else:
            eval_info = "Evaluación documental: Pendiente de revisión física"

        self.lbl_detalle.config(
            text=(
                f"👤 {v['nombre_completo']}  |  CI: {v['ci']}  |  Strikes: {v['total_strikes']}/5  |  "
                f"🔑 Usuario: {usr}  |  {eval_info}"
            ),
            fg=PALETTE["negro"]
        )

    def _abrir_evaluacion_seleccionado(self):
        v = self._obtener_seleccionado()
        if not v:
            messagebox.showwarning("Selección requerida", "Selecciona un postulante de la tabla.")
            return

        if v["estado"] not in ("Postulante", "Rechazado"):
            messagebox.showinfo(
                "Evaluación ya completada",
                f"Este registro tiene estado '{v['estado']}' y ya pasó el proceso de admisión."
            )
            return

        ModalEvaluacionAdmision(
            master=self,
            voluntario=v,
            sesion=self.sesion,
            controller=self.controller,
            on_guardado=self._cargar_voluntarios
        )

    def _cambiar_estado_seleccionado(self, nuevo_estado: str):
        v = self._obtener_seleccionado()
        if not v:
            messagebox.showwarning("Selección requerida", "Selecciona un registro de la tabla.")
            return

        if v["estado"] == "Inactivo_Definitivo":
            messagebox.showerror(
                "Cuenta Bloqueada Irreversiblemente",
                "Este voluntario acumuló 5 strikes y quedó en estado 'Inactivo_Definitivo'. No puede reactivarse."
            )
            return

        if v["estado"] == nuevo_estado:
            messagebox.showinfo("Aviso", f"El registro ya se encuentra en estado '{nuevo_estado}'.")
            return

        if nuevo_estado == "Inactivo" and v["estado"] != "Admitido":
            messagebox.showwarning("Acción no permitida", "Solo se pueden desactivar voluntarios admitidos.")
            return

        if nuevo_estado == "Admitido" and v["estado"] != "Inactivo":
            messagebox.showwarning(
                "Acción no permitida",
                "Usa el botón 'Evaluar Requisitos y Admitir' para admitir postulantes nuevos."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar Cambio de Estado",
            f"¿Cambiar el estado de {v['nombre_completo']} a '{nuevo_estado}'?"
        )
        if not confirmar:
            return

        exito, mensaje = self.controller.cambiar_estado(v, nuevo_estado)
        if exito:
            messagebox.showinfo("Estado Actualizado", mensaje)
            self._cargar_voluntarios()
        else:
            messagebox.showerror("Error", mensaje)