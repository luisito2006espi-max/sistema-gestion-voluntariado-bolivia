from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.donacion_controller import DonacionController
from views.ui_components import PALETTE, RoundedCard, InputValidators, SaveTheChildrenLogo


class ComprobanteAutodonacionModal(tk.Toplevel):
    """Comprobante visual emitido al donante tras registrar su aporte público."""

    def __init__(self, master, comprobante: dict):
        super().__init__(master)
        self.comprobante = comprobante

        self.title("Comprobante de Donación — Save the Children Bolivia")
        self.configure(bg=PALETTE["plomo_fondo"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._construir_ui()
        self._centrar_ventana()

    def _centrar_ventana(self):
        self.update_idletasks()
        w = max(460, self.winfo_reqwidth())
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(20, (sw - w) // 2)
        y = max(20, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_ui(self):
        wrap = tk.Frame(self, bg=PALETTE["plomo_fondo"], padx=20, pady=18)
        wrap.pack(fill=BOTH, expand=True)

        card = tk.Frame(
            wrap,
            bg=PALETTE["blanco"],
            highlightbackground=PALETTE["plomo_borde"],
            highlightthickness=1,
            padx=22,
            pady=18
        )
        card.pack(fill="x")

        hdr = tk.Frame(card, bg=PALETTE["blanco"])
        hdr.pack(fill="x", pady=(0, 10))

        SaveTheChildrenLogo(hdr, size=40, bg=PALETTE["blanco"]).pack(side="left", padx=(0, 12))

        tit_box = tk.Frame(hdr, bg=PALETTE["blanco"])
        tit_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            tit_box,
            text="¡Gracias por tu Solidaridad!",
            font=("Segoe UI", 13, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["rojo"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            tit_box,
            text="Save the Children Bolivia • Constancia de Autodonación",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            anchor="w"
        ).pack(fill="x")

        tk.Frame(card, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(4, 12))

        # Código de comprobante destacado
        cod_box = tk.Frame(card, bg="#DCFCE7", padx=14, pady=10)
        cod_box.pack(fill="x", pady=(0, 12))

        tk.Label(
            cod_box,
            text=f"Código de Registro: {self.comprobante.get('codigo_comprobante', 'SCB-DON')}",
            font=("Segoe UI", 11, "bold"),
            bg="#DCFCE7",
            fg="#15803D",
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            cod_box,
            text=f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            font=("Segoe UI", 8),
            bg="#DCFCE7",
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # Detalle del aporte
        det_box = tk.Frame(card, bg=PALETTE["plomo_fondo"], padx=14, pady=10)
        det_box.pack(fill="x", pady=(0, 14))

        filas = [
            ("Donante:", self.comprobante.get("donante", "-")),
            ("Modalidad:", self.comprobante.get("tipo", "-")),
            ("Aporte registrado:", self.comprobante.get("resumen", "-")),
            ("Canal:", "Portal Público (Autodonación)")
        ]
        for etiqueta, valor in filas:
            row = tk.Frame(det_box, bg=PALETTE["plomo_fondo"])
            row.pack(fill="x", pady=2)
            tk.Label(
                row,
                text=etiqueta,
                font=("Segoe UI", 9, "bold"),
                bg=PALETTE["plomo_fondo"],
                fg=PALETTE["plomo_texto"],
                width=16,
                anchor="w"
            ).pack(side="left")
            tk.Label(
                row,
                text=valor,
                font=("Segoe UI", 9, "bold"),
                bg=PALETTE["plomo_fondo"],
                fg=PALETTE["negro"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

        btn_ok = tk.Button(
            card,
            text="Aceptar y Finalizar",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=9,
            cursor="hand2",
            command=self.destroy
        )
        btn_ok.pack(fill="x")
        btn_ok.bind("<Enter>", lambda _e: btn_ok.config(bg=PALETTE["rojo_hover"]))
        btn_ok.bind("<Leave>", lambda _e: btn_ok.config(bg=PALETTE["rojo"]))


class AutoDonacionView(tk.Frame):
    """
    Portal Público de Autodonación (accesible desde la pantalla de inicio de sesión).
    Registra donantes con origen 'Autoregistro' y donaciones con canal 'Autodonacion'
    (id_admin_registra = NULL).
    """

    def __init__(self, master, on_volver_login):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.on_volver_login = on_volver_login
        self.controller = DonacionController()

        self.insumos_map = {}
        self.carrito_insumos = []
        self.tipo_actual = "DINERO"

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._cargar_catalogo_insumos()
        self._seleccionar_tipo("DINERO")

    def _configurar_estilos_tabla(self):
        style = tb.Style()
        style.configure(
            "AutoDon.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "AutoDon.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(6, 6)
        )
        style.map(
            "AutoDon.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. BARRA SUPERIOR INSTITUCIONAL
        # =====================================================================
        topbar = tk.Frame(self, bg=PALETTE["negro"], padx=24, pady=12)
        topbar.pack(fill="x")

        SaveTheChildrenLogo(topbar, size=40, bg=PALETTE["negro"]).pack(side="left", padx=(0, 12))

        tit_box = tk.Frame(topbar, bg=PALETTE["negro"])
        tit_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            tit_box,
            text="Portal Público de Donaciones — Save the Children Bolivia",
            font=("Segoe UI", 13, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            tit_box,
            text="Tu aporte directo impulsa programas de educación, salud y protección infantil en Bolivia.",
            font=("Segoe UI", 9),
            bg=PALETTE["negro"],
            fg=PALETTE["plomo_claro"],
            anchor="w"
        ).pack(fill="x")

        btn_volver = tk.Button(
            topbar,
            text="←  Volver al Inicio de Sesión",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["negro_suave"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.on_volver_login
        )
        btn_volver.pack(side="right")
        btn_volver.bind("<Enter>", lambda _e: btn_volver.config(bg=PALETTE["rojo"]))
        btn_volver.bind("<Leave>", lambda _e: btn_volver.config(bg=PALETTE["negro_suave"]))

        # =====================================================================
        # 2. CONTENEDOR PRINCIPAL DE DOS COLUMNAS (980x660)
        # =====================================================================
        cuerpo = tk.Frame(self, bg=PALETTE["plomo_fondo"], padx=22, pady=16)
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=48, uniform="pub_cols")
        cuerpo.columnconfigure(1, weight=52, uniform="pub_cols")
        cuerpo.rowconfigure(0, weight=1)

        # --- COLUMNA IZQUIERDA: DATOS DEL DONANTE ---
        card_izq = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=22,
            pady=16,
            expand_body=True
        )
        card_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        bi = card_izq.body

        tk.Label(
            bi,
            text="1. Identificación del Donante",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            bi,
            text="Si ya donaste antes, ingresa tu CI o NIT para recuperar tus datos.",
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            anchor="w"
        ).pack(fill="x", pady=(2, 10))

        # CI / NIT + Botón Buscar
        doc_row = tk.Frame(bi, bg=PALETTE["blanco"])
        doc_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            doc_row,
            text="CI / NIT:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 8))

        self.entry_doc = tb.Entry(doc_row, width=18, font=("Segoe UI", 10))
        self.entry_doc.pack(side="left", ipady=3, padx=(0, 8))
        InputValidators.aplicar(self.entry_doc, "enteros")
        self.entry_doc.bind("<Return>", lambda _e: self._buscar_donante())

        btn_buscar = tk.Button(
            doc_row,
            text="🔍 Buscar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._buscar_donante
        )
        btn_buscar.pack(side="left")
        btn_buscar.bind("<Enter>", lambda _e: btn_buscar.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"]))
        btn_buscar.bind("<Leave>", lambda _e: btn_buscar.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"]))

        # Nombre completo
        tk.Label(
            bi,
            text="Nombre Completo o Razón Social *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        self.entry_nombre = tb.Entry(bi, font=("Segoe UI", 10))
        self.entry_nombre.pack(fill="x", ipady=4, pady=(3, 10))
        InputValidators.aplicar(self.entry_nombre, "letras")

        # Teléfono y Correo en 2 columnas
        tm_grid = tk.Frame(bi, bg=PALETTE["blanco"])
        tm_grid.pack(fill="x", pady=(0, 10))
        tm_grid.columnconfigure(0, weight=1, uniform="pub_tm")
        tm_grid.columnconfigure(1, weight=1, uniform="pub_tm")

        tk.Label(
            tm_grid,
            text="Teléfono / Celular",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.entry_tel = tb.Entry(tm_grid, font=("Segoe UI", 10))
        self.entry_tel.grid(row=1, column=0, sticky="ew", padx=(0, 6), ipady=3, pady=(3, 0))
        InputValidators.aplicar(self.entry_tel, "enteros")

        tk.Label(
            tm_grid,
            text="Correo Electrónico",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.entry_correo = tb.Entry(tm_grid, font=("Segoe UI", 10))
        self.entry_correo.grid(row=1, column=1, sticky="ew", padx=(6, 0), ipady=3, pady=(3, 0))

        # Observaciones / Mensaje
        tk.Label(
            bi,
            text="Mensaje u Observaciones (Opcional)",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        self.entry_obs = tb.Entry(bi, font=("Segoe UI", 9))
        self.entry_obs.pack(fill="x", ipady=3, pady=(3, 14))

        # Nota de seguridad institucional al pie
        info_seg = tk.Frame(bi, bg=PALETTE["plomo_fondo"], padx=12, pady=10)
        info_seg.pack(side="bottom", fill="x")

        tk.Label(
            info_seg,
            text="Compromiso de Transparencia y Seguridad",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            info_seg,
            text=(
                "Save the Children Bolivia nunca solicita números de tarjeta ni claves bancarias. "
                "Tu donación ingresa directamente al inventario o fondo operativo institucional."
            ),
            font=("Segoe UI", 8),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            wraplength=370,
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # --- COLUMNA DERECHA: DETALLES DEL APORTE ---
        card_der = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=22,
            pady=16,
            expand_body=True
        )
        card_der.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        bd = card_der.body

        tk.Label(
            bd,
            text="2. Detalles de tu Donación",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # Selector visual de modalidad (DINERO / MATERIAL)
        selector_frame = tk.Frame(bd, bg=PALETTE["blanco"])
        selector_frame.pack(fill="x", pady=(0, 12))
        selector_frame.columnconfigure(0, weight=1, uniform="sel_tipo")
        selector_frame.columnconfigure(1, weight=1, uniform="sel_tipo")

        self.btn_tipo_dinero = tk.Button(
            selector_frame,
            text="💵  Aporte Económico (DINERO)",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            pady=9,
            cursor="hand2",
            command=lambda: self._seleccionar_tipo("DINERO")
        )
        self.btn_tipo_dinero.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_tipo_material = tk.Button(
            selector_frame,
            text="📦  En Especie (MATERIAL)",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            pady=9,
            cursor="hand2",
            command=lambda: self._seleccionar_tipo("MATERIAL")
        )
        self.btn_tipo_material.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Contenedor dinámico según tipo elegido
        self.contenedor_tipo = tk.Frame(bd, bg=PALETTE["plomo_fondo"], padx=14, pady=12)
        self.contenedor_tipo.pack(fill=BOTH, expand=True, pady=(0, 12))

        # --- Sub-panel A: DINERO ---
        self.frame_dinero = tk.Frame(self.contenedor_tipo, bg=PALETTE["plomo_fondo"])

        tk.Label(
            self.frame_dinero,
            text="Montos sugeridos (Bs.):",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        presets_row = tk.Frame(self.frame_dinero, bg=PALETTE["plomo_fondo"])
        presets_row.pack(fill="x", pady=(0, 10))
        for idx_p, monto_p in enumerate(("50", "100", "200", "500")):
            presets_row.columnconfigure(idx_p, weight=1, uniform="presets")
            b_pre = tk.Button(
                presets_row,
                text=f"Bs. {monto_p}",
                font=("Segoe UI", 9, "bold"),
                bg=PALETTE["blanco"],
                fg=PALETTE["negro"],
                activebackground=PALETTE["rojo_suave"],
                bd=0,
                pady=6,
                cursor="hand2",
                command=lambda m=monto_p: self._aplicar_monto_sugerido(m)
            )
            b_pre.grid(row=0, column=idx_p, sticky="ew", padx=3)

        tk.Label(
            self.frame_dinero,
            text="Monto a Donar (Bs.) *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        self.entry_monto = tb.Entry(self.frame_dinero, font=("Segoe UI", 12, "bold"))
        self.entry_monto.pack(fill="x", ipady=4, pady=(3, 10))
        InputValidators.aplicar(self.entry_monto, "decimales")

        tk.Label(
            self.frame_dinero,
            text="Método de Pago *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        self.combo_metodo = tb.Combobox(
            self.frame_dinero,
            values=list(self.controller.METODOS_PAGO),
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_metodo.set("QR")
        self.combo_metodo.pack(fill="x", ipady=3, pady=(3, 8))

        tk.Label(
            self.frame_dinero,
            text="• QR / Transferencia: Cuenta institucional Save the Children Bolivia.\n• Efectivo: Recepción en oficina central con entrega de recibo.",
            font=("Segoe UI", 8),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=(4, 0))

        # --- Sub-panel B: MATERIAL ---
        self.frame_material = tk.Frame(self.contenedor_tipo, bg=PALETTE["plomo_fondo"])

        add_bar = tk.Frame(self.frame_material, bg=PALETTE["plomo_fondo"])
        add_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            add_bar,
            text="Insumo:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 4))

        self.combo_insumo = tb.Combobox(
            add_bar,
            state="readonly",
            width=22,
            font=("Segoe UI", 9),
            bootstyle="danger"
        )
        self.combo_insumo.pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Label(
            add_bar,
            text="Cant:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 4))

        self.entry_cant = tb.Entry(add_bar, width=7, font=("Segoe UI", 9))
        self.entry_cant.pack(side="left", padx=(0, 6))
        InputValidators.aplicar(self.entry_cant, "decimales")

        btn_add = tk.Button(
            add_bar,
            text="+ Agregar",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._agregar_insumo
        )
        btn_add.pack(side="right")

        self.tabla_carrito = tb.Treeview(
            self.frame_material,
            columns=("insumo", "cantidad", "unidad"),
            show="headings",
            height=4,
            style="AutoDon.Treeview"
        )
        self.tabla_carrito.heading("insumo", text="Insumo")
        self.tabla_carrito.heading("cantidad", text="Cantidad")
        self.tabla_carrito.heading("unidad", text="Unidad")
        self.tabla_carrito.column("insumo", width=180, anchor="w")
        self.tabla_carrito.column("cantidad", width=70, anchor="center")
        self.tabla_carrito.column("unidad", width=115, anchor="center")
        self.tabla_carrito.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_carrito.tag_configure("impar", background="#F9FAFB")
        self.tabla_carrito.pack(fill=BOTH, expand=True, pady=(0, 6))

        btn_quitar = tk.Button(
            self.frame_material,
            text="✕ Quitar Ítem Seleccionado",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["rojo_suave"],
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._quitar_insumo
        )
        btn_quitar.pack(anchor="e")

        # --- BARRA DE ACCIÓN INFERIOR ---
        btn_bar = tk.Frame(bd, bg=PALETTE["blanco"])
        btn_bar.pack(side="bottom", fill="x")

        btn_limpiar = tk.Button(
            btn_bar,
            text="Limpiar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            command=self._limpiar_formulario
        )
        btn_limpiar.pack(side="left", padx=(0, 10))

        btn_donar = tk.Button(
            btn_bar,
            text="❤  Confirmar y Registrar Donación",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=10,
            cursor="hand2",
            command=self._confirmar_donacion
        )
        btn_donar.pack(side="right", fill="x", expand=True)
        btn_donar.bind("<Enter>", lambda _e: btn_donar.config(bg=PALETTE["rojo_hover"]))
        btn_donar.bind("<Leave>", lambda _e: btn_donar.config(bg=PALETTE["rojo"]))

    # =========================================================================
    # LÓGICA DE INTERACCIÓN Y REGISTRO PÚBLICO
    # =========================================================================
    @staticmethod
    def _asignar_texto_seguro(entry_widget, texto: str):
        modo_anterior = entry_widget.cget("validate")
        entry_widget.configure(validate="none")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, texto or "")
        entry_widget.configure(validate=modo_anterior)

    def _cargar_catalogo_insumos(self):
        try:
            cats = self.controller.cargar_catalogos()
            self.insumos_map = {
                f"{i['nombre']} ({i['unidad_medida']})": i for i in cats["insumos"]
            }
            etiquetas = list(self.insumos_map.keys())
            self.combo_insumo["values"] = etiquetas
            if etiquetas:
                self.combo_insumo.set(etiquetas[0])
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo cargar el catálogo de insumos: {e}")

    def _seleccionar_tipo(self, tipo: str):
        self.tipo_actual = tipo
        self.frame_dinero.pack_forget()
        self.frame_material.pack_forget()

        if tipo == "DINERO":
            self.btn_tipo_dinero.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"])
            self.btn_tipo_material.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"])
            self.frame_dinero.pack(fill=BOTH, expand=True)
        else:
            self.btn_tipo_material.config(bg=PALETTE["rojo"], fg=PALETTE["blanco"])
            self.btn_tipo_dinero.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"])
            self.frame_material.pack(fill=BOTH, expand=True)

    def _aplicar_monto_sugerido(self, monto_str: str):
        self._asignar_texto_seguro(self.entry_monto, monto_str)

    def _buscar_donante(self):
        doc = self.entry_doc.get().strip()
        if not doc:
            messagebox.showwarning("Búsqueda", "Ingresa tu CI o NIT para buscar tus datos registrados.")
            return

        encontrado = self.controller.buscar_donante(doc)
        if not encontrado:
            messagebox.showinfo(
                "Nuevo Donante",
                "No encontramos un registro previo con ese documento. Completa tu nombre para continuar."
            )
            self.entry_nombre.focus_set()
            return

        self._asignar_texto_seguro(self.entry_nombre, encontrado.get("nombre", ""))
        self._asignar_texto_seguro(self.entry_tel, encontrado.get("telefono", ""))
        self.entry_correo.delete(0, tk.END)
        self.entry_correo.insert(0, encontrado.get("correo") or "")
        messagebox.showinfo("Donante Identificado", f"¡Bienvenido de nuevo, {encontrado['nombre']}!")

    def _agregar_insumo(self):
        insumo_obj = self.insumos_map.get(self.combo_insumo.get())
        ok, msg, item = self.controller.validar_item_insumo(insumo_obj, self.entry_cant.get())
        if not ok:
            messagebox.showwarning("Validación de Insumo", msg)
            return

        for existente in self.carrito_insumos:
            if existente["id_insumo"] == item["id_insumo"]:
                existente["cantidad"] = round(existente["cantidad"] + item["cantidad"], 2)
                break
        else:
            self.carrito_insumos.append(item)

        self.entry_cant.delete(0, tk.END)
        self._refrescar_carrito()

    def _quitar_insumo(self):
        sel = self.tabla_carrito.selection()
        if not sel:
            messagebox.showwarning("Selección", "Selecciona un ítem de la lista para quitarlo.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.carrito_insumos):
            self.carrito_insumos.pop(idx)
            self._refrescar_carrito()

    def _refrescar_carrito(self):
        for w in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(w)
        for idx, item in enumerate(self.carrito_insumos):
            tag = "par" if idx % 2 == 0 else "impar"
            self.tabla_carrito.insert("", tk.END, iid=str(idx), values=(
                item["nombre"],
                f"{item['cantidad']:g}",
                item["unidad_medida"]
            ), tags=(tag,))

    def _limpiar_formulario(self):
        for entry in (
            self.entry_doc,
            self.entry_nombre,
            self.entry_tel,
            self.entry_correo,
            self.entry_obs,
            self.entry_monto,
            self.entry_cant
        ):
            entry.delete(0, tk.END)
        self.carrito_insumos.clear()
        self._refrescar_carrito()
        self.entry_doc.focus_set()

    def _confirmar_donacion(self):
        datos_donante = {
            "documento": self.entry_doc.get(),
            "nombre": self.entry_nombre.get(),
            "telefono": self.entry_tel.get(),
            "correo": self.entry_correo.get()
        }

        exito, resultado = self.controller.registrar_donacion(
            datos_donante=datos_donante,
            tipo_nombre=self.tipo_actual,
            monto_str=self.entry_monto.get(),
            metodo_pago=self.combo_metodo.get(),
            lista_insumos=self.carrito_insumos,
            observaciones=self.entry_obs.get(),
            id_usuario_registra=None
        )

        if not exito:
            messagebox.showwarning("Verifica tus datos", str(resultado))
            return

        self._limpiar_formulario()
        if isinstance(resultado, dict):
            ComprobanteAutodonacionModal(self, resultado)
        else:
            messagebox.showinfo("Donación Registrada", str(resultado))