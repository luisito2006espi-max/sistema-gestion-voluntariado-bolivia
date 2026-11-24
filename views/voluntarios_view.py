from datetime import date
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.voluntario_controller import VoluntarioController
from views.ui_components import PALETTE, RoundedCard, InputValidators


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
        # 1. ENCABEZADO (20 pt)
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
            text="Registra nuevos aspirantes validando identidad, edad reglamentaria (18 a 60 años) y datos de contacto.",
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

        # Fila 0: CI (Solo Números) | Nombres (Solo Letras)
        self.entry_ci = self._crear_campo(
            grid, row=0, col=0,
            etiqueta="Carnet de Identidad (CI) *  ",
            validacion="enteros"
        )
        self.entry_nombres = self._crear_campo(
            grid, row=0, col=1,
            etiqueta="Nombres *  ",
            validacion="letras"
        )

        # Fila 1: Apellido Paterno (Solo Letras) | Apellido Materno (Solo Letras)
        self.entry_ap_paterno = self._crear_campo(
            grid, row=1, col=0,
            etiqueta="Apellido Paterno *  ",
            validacion="letras"
        )
        self.entry_ap_materno = self._crear_campo(
            grid, row=1, col=1,
            etiqueta="Apellido Materno ",
            validacion="letras"
        )

        # Fila 2: Fecha de Nacimiento + Edad Calculada en Vivo | Teléfono (Solo Números)
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

        # Eventos para recalcular la edad automáticamente al escribir o elegir fecha
        self.date_nac.entry.bind("<KeyRelease>", self._actualizar_edad_preview)
        self.date_nac.entry.bind("<FocusOut>", self._actualizar_edad_preview)
        self.date_nac.bind("<<DateEntrySelected>>", self._actualizar_edad_preview)

        self.entry_telefono = self._crear_campo(
            grid, row=2, col=1,
            etiqueta="Teléfono / Celular  ",
            validacion="enteros"
        )

        # Fila 3: Correo Electrónico | Dirección / Zona
        self.entry_correo = self._crear_campo(
            grid, row=3, col=0,
            etiqueta="Correo Electrónico ",
            validacion=None
        )
        self.entry_direccion = self._crear_campo(
            grid, row=3, col=1,
            etiqueta="Dirección / Zona de Residencia ",
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
            text="Requisitos de Inscripción",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        reglas = [
            ("Rango de Edad", "El postulante debe tener entre 18 y 60 años cumplidos a la fecha."),
            ("Carnet Único", "No se permiten dos registros con el mismo número de CI."),
            ("Validación de Campos", "Nombres y apellidos aceptan solo letras; CI y teléfono aceptan solo números."),
            ("Siguiente Paso", "Tras inscribirlo, pasará a 'Admisión Voluntarios' para habilitar su cuenta.")
        ]

        for titulo_r, desc_r in reglas:
            box = tk.Frame(bi, bg=PALETTE["plomo_fondo"], padx=12, pady=9)
            box.pack(fill="x", pady=(0, 8))

            tk.Label(
                box,
                text=f"• {titulo_r}",
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
            "id_usuario_registra": self.sesion.get("id_usuario")
        }

        exito, mensaje = self.controller.registrar_postulante(datos)
        if exito:
            messagebox.showinfo("Inscripción Exitosa", mensaje)
            self._limpiar_formulario()
        else:
            messagebox.showwarning("Validación de Inscripción", mensaje)


class AdmisionVoluntariosView(tk.Frame):
    """Pestaña de Admisión y Control de Voluntarios con tabla resaltada y curvas."""

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
        # 1. ENCABEZADO (20 pt)
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
            text="Evalúa postulantes, genera credenciales de acceso al portal y administra el estado de los voluntarios.",
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

        # Filtros izquierdos
        tk.Label(
            bar,
            text="Estado:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.combo_estado = tb.Combobox(
            bar,
            values=["Todos", "Postulante", "Admitido", "Rechazado", "Inactivo"],
            state="readonly",
            width=14,
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

        self.entry_buscar = tb.Entry(bar, width=24, font=("Segoe UI", 9))
        self.entry_buscar.pack(side="left", ipady=2)
        self.entry_buscar.bind("<KeyRelease>", lambda _e: self._cargar_voluntarios())

        # Botones de acción derechos
        btn_baja = tk.Button(
            bar,
            text="Desactivar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self._cambiar_estado_seleccionado("Inactivo")
        )
        btn_baja.pack(side="right", padx=(6, 0))

        btn_rechazar = tk.Button(
            bar,
            text="✕ Rechazar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo_suave"],
            fg=PALETTE["rojo"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self._cambiar_estado_seleccionado("Rechazado")
        )
        btn_rechazar.pack(side="right", padx=(6, 0))

        btn_admitir = tk.Button(
            bar,
            text="✓ Admitir y Crear Cuenta",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._admitir_seleccionado
        )
        btn_admitir.pack(side="right")
        btn_admitir.bind("<Enter>", lambda _e: btn_admitir.config(bg=PALETTE["rojo_hover"]))
        btn_admitir.bind("<Leave>", lambda _e: btn_admitir.config(bg=PALETTE["rojo"]))

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

        cols = ("ci", "nombre", "edad", "fecha_nac", "telefono", "inscripcion", "estado", "usuario")
        self.tabla = tb.Treeview(
            bt,
            columns=cols,
            show="headings",
            height=8,
            style="Vol.Treeview"
        )
        cfg = {
            "ci": ("CI", 95),
            "nombre": ("Nombre Completo", 220),
            "edad": ("Edad", 70),
            "fecha_nac": ("F. Nacimiento", 105),
            "telefono": ("Teléfono", 95),
            "inscripcion": ("F. Inscripción", 100),
            "estado": ("Estado", 100),
            "usuario": ("Cuenta Usuario", 130)
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
            text="Selecciona un registro de la tabla para ver su información completa de contacto y admisión.",
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
            text="Selecciona un registro de la tabla para ver su información completa de contacto y admisión.",
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
                usuario_txt = v.get("cuenta_usuario") or "Sin cuenta"

                self.tabla.insert("", tk.END, iid=iid, values=(
                    v["ci"],
                    v["nombre_completo"],
                    edad_txt,
                    v.get("fecha_nacimiento_str", "-"),
                    v.get("telefono") or "-",
                    str(v.get("fecha_inscripcion") or "-"),
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
        correo = v.get("correo") or "No registrado"
        f_adm = str(v.get("fecha_admision")) if v.get("fecha_admision") else "Pendiente"
        usr = v.get("cuenta_usuario") or "Sin cuenta generada"
        self.lbl_detalle.config(
            text=(
                f"👤 {v['nombre_completo']}  |  CI: {v['ci']}  |  Edad: {v.get('edad', '-')} años ({v.get('fecha_nacimiento_str', '-')})  |  "
                f"✉️ Correo: {correo}  |  ✅ Fecha Admisión: {f_adm}  |  🔑 Usuario: {usr}"
            ),
            fg=PALETTE["negro"]
        )

    def _admitir_seleccionado(self):
        v = self._obtener_seleccionado()
        if not v:
            messagebox.showwarning("Selección requerida", "Selecciona un postulante de la tabla.")
            return

        if v["estado"] != "Postulante":
            messagebox.showinfo("Aviso", f"Este registro ya tiene estado '{v['estado']}'.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar Admisión",
            f"¿Admitir a {v['nombre_completo']} (CI: {v['ci']}) como Voluntario activo y generar su cuenta de acceso?"
        )
        if not confirmar:
            return

        exito, resultado = self.controller.admitir_voluntario(v)
        if exito and isinstance(resultado, dict):
            messagebox.showinfo(
                "Voluntario Admitido",
                f"Se habilitó la cuenta para {resultado['nombre']}:\n\n"
                f"• Usuario: {resultado['usuario']}\n"
                f"• Contraseña temporal: {resultado['password']}\n\n"
                "Entrega estas credenciales al voluntario para su primer ingreso."
            )
            self._cargar_voluntarios()
        else:
            messagebox.showerror("Error al Admitir", str(resultado))

    def _cambiar_estado_seleccionado(self, nuevo_estado: str):
        v = self._obtener_seleccionado()
        if not v:
            messagebox.showwarning("Selección requerida", "Selecciona un registro de la tabla.")
            return

        if v["estado"] == nuevo_estado:
            messagebox.showinfo("Aviso", f"El registro ya se encuentra en estado '{nuevo_estado}'.")
            return

        if nuevo_estado == "Rechazado" and v["estado"] != "Postulante":
            messagebox.showwarning("Acción no permitida", "Solo se pueden rechazar postulantes pendientes.")
            return

        if nuevo_estado == "Inactivo" and v["estado"] != "Admitido":
            messagebox.showwarning("Acción no permitida", "Solo se pueden desactivar voluntarios admitidos.")
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