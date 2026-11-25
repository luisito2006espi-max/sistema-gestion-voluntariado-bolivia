import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.donacion_controller import DonacionController
from views.ui_components import PALETTE, RoundedCard, InputValidators


class GestionDonacionesView(tk.Frame):
    """
    Vista para Administrador:
    - Sub-pestaña 1: Registro e Historial de Donaciones (Monetarias y en Especie).
    - Sub-pestaña 2: Inventario Disponible y Despacho de Insumos (ENTREGA_INSUMO).
    """

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = DonacionController()

        self.insumos_map = {}
        self.insumos_inv_map = {}
        self.actividades_map = {}
        self.carrito_insumos = []
        self.donaciones_cache = {}

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._inicializar_datos()

    def _configurar_estilos_tabla(self):
        style = tb.Style()
        style.configure(
            "Don.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Don.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 7)
        )
        style.map(
            "Don.Treeview.Heading",
            background=[("active", PALETTE["plomo_borde"])]
        )
        style.map(
            "Don.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Gestión de Donaciones e Inventario de Insumos",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Registra aportes económicos o en especie (incluyendo autodonaciones públicas) y controla las entregas de almacén.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w", pady=(2, 0))

        # =====================================================================
        # 2. NOTEBOOK DE SUB-MÓDULOS (DONACIONES VS. INVENTARIO/ENTREGAS)
        # =====================================================================
        self.notebook = tb.Notebook(self, bootstyle="danger")
        self.notebook.pack(fill=BOTH, expand=True)

        self.tab_donaciones = tk.Frame(self.notebook, bg=PALETTE["plomo_fondo"], pady=8)
        self.tab_inventario = tk.Frame(self.notebook, bg=PALETTE["plomo_fondo"], pady=8)

        self.notebook.add(self.tab_donaciones, text="  🎁  Registro e Historial de Donaciones  ")
        self.notebook.add(self.tab_inventario, text="  📦  Inventario y Despacho de Insumos  ")

        self._construir_tab_donaciones(self.tab_donaciones)
        self._construir_tab_inventario(self.tab_inventario)

    # =========================================================================
    # SUB-PESTAÑA 1: REGISTRO E HISTORIAL DE DONACIONES
    # =========================================================================
    def _construir_tab_donaciones(self, parent):
        cuerpo = tk.Frame(parent, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=48, uniform="don_cols")
        cuerpo.columnconfigure(1, weight=52, uniform="don_cols")
        cuerpo.rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: FORMULARIO DESPLAZABLE + BOTONES FIJOS ---
        card_reg = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=14,
            expand_body=True
        )
        card_reg.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        footer_reg = tk.Frame(card_reg.body, bg=PALETTE["blanco"])
        footer_reg.pack(side="bottom", fill="x", pady=(8, 0))

        tk.Frame(footer_reg, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(0, 10))

        btns_bottom = tk.Frame(footer_reg, bg=PALETTE["blanco"])
        btns_bottom.pack(fill="x")

        btn_limpiar = tk.Button(
            btns_bottom,
            text="Limpiar",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
            command=self._limpiar_todo
        )
        btn_limpiar.pack(side="left", padx=(0, 10))

        btn_guardar = tk.Button(
            btns_bottom,
            text="✓  Registrar Donación",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=9,
            cursor="hand2",
            command=self._guardar_donacion
        )
        btn_guardar.pack(side="right", fill="x", expand=True)
        btn_guardar.bind("<Enter>", lambda _e: btn_guardar.config(bg=PALETTE["rojo_hover"]))
        btn_guardar.bind("<Leave>", lambda _e: btn_guardar.config(bg=PALETTE["rojo"]))

        scroll_wrap = tk.Frame(card_reg.body, bg=PALETTE["blanco"])
        scroll_wrap.pack(side="top", fill=BOTH, expand=True)

        self.canvas_reg = tk.Canvas(
            scroll_wrap,
            bg=PALETTE["blanco"],
            highlightthickness=0,
            bd=0
        )
        scrollbar_reg = tb.Scrollbar(
            scroll_wrap,
            orient="vertical",
            command=self.canvas_reg.yview,
            bootstyle="danger-round"
        )
        self.canvas_reg.configure(yscrollcommand=scrollbar_reg.set)

        scrollbar_reg.pack(side="right", fill="y", padx=(6, 0))
        self.canvas_reg.pack(side="left", fill=BOTH, expand=True)

        br = tk.Frame(self.canvas_reg, bg=PALETTE["blanco"], padx=2)
        self._reg_win_id = self.canvas_reg.create_window((0, 0), window=br, anchor="nw")

        br.bind(
            "<Configure>",
            lambda _e: self.canvas_reg.configure(scrollregion=self.canvas_reg.bbox("all"))
        )
        self.canvas_reg.bind(
            "<Configure>",
            lambda e: self.canvas_reg.itemconfigure(self._reg_win_id, width=e.width)
        )

        scroll_wrap.bind("<Enter>", lambda _e: self.canvas_reg.bind_all("<MouseWheel>", self._on_mousewheel_reg))
        scroll_wrap.bind("<Leave>", lambda _e: self.canvas_reg.unbind_all("<MouseWheel>"))
        self.bind("<Destroy>", lambda _e: self._desvincular_rueda())

        tk.Label(
            br,
            text="1. Datos del Donante",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 8))

        doc_row = tk.Frame(br, bg=PALETTE["blanco"])
        doc_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            doc_row,
            text="CI / NIT:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 8))

        self.entry_doc = tb.Entry(doc_row, width=18, font=("Segoe UI", 10))
        self.entry_doc.pack(side="left", padx=(0, 8), ipady=3)
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

        tk.Label(
            br,
            text="Nombre Completo o Razón Social *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_nombre = tb.Entry(br, font=("Segoe UI", 10))
        self.entry_nombre.pack(fill="x", ipady=3, pady=(3, 10))
        InputValidators.aplicar(self.entry_nombre, "letras")

        tel_mail_frame = tk.Frame(br, bg=PALETTE["blanco"])
        tel_mail_frame.pack(fill="x", pady=(0, 12))
        tel_mail_frame.columnconfigure(0, weight=1, uniform="tm_cols")
        tel_mail_frame.columnconfigure(1, weight=1, uniform="tm_cols")

        tk.Label(
            tel_mail_frame,
            text="Teléfono",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.entry_tel = tb.Entry(tel_mail_frame, font=("Segoe UI", 10))
        self.entry_tel.grid(row=1, column=0, sticky="ew", padx=(0, 6), ipady=3, pady=(3, 0))
        InputValidators.aplicar(self.entry_tel, "enteros")

        tk.Label(
            tel_mail_frame,
            text="Correo Electrónico",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.entry_correo = tb.Entry(tel_mail_frame, font=("Segoe UI", 10))
        self.entry_correo.grid(row=1, column=1, sticky="ew", padx=(6, 0), ipady=3, pady=(3, 0))

        tk.Frame(br, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(2, 12))

        tipo_row = tk.Frame(br, bg=PALETTE["blanco"])
        tipo_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            tipo_row,
            text="2. Tipo de Donación *",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left")

        self.combo_tipo = tb.Combobox(
            tipo_row,
            values=list(self.controller.TIPOS_DONACION),
            state="readonly",
            width=18,
            font=("Segoe UI", 10, "bold"),
            bootstyle="danger"
        )
        self.combo_tipo.set("DINERO")
        self.combo_tipo.pack(side="right")
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda _e: self._alternar_panel_tipo())

        self.contenedor_dinamico = tk.Frame(br, bg=PALETTE["plomo_fondo"], padx=14, pady=12)
        self.contenedor_dinamico.pack(fill="x", pady=(0, 10))

        # --- Sub-panel A: DINERO ---
        self.frame_dinero = tk.Frame(self.contenedor_dinamico, bg=PALETTE["plomo_fondo"])

        tk.Label(
            self.frame_dinero,
            text="Monto Donado (Bs.) *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_monto = tb.Entry(self.frame_dinero, font=("Segoe UI", 11, "bold"))
        self.entry_monto.pack(fill="x", ipady=4, pady=(3, 12))
        InputValidators.aplicar(self.entry_monto, "decimales")

        tk.Label(
            self.frame_dinero,
            text="Método de Pago *",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.combo_metodo = tb.Combobox(
            self.frame_dinero,
            values=list(self.controller.METODOS_PAGO),
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_metodo.set("QR")
        self.combo_metodo.pack(fill="x", ipady=3, pady=(3, 6))

        # --- Sub-panel B: MATERIAL ---
        self.frame_material = tk.Frame(self.contenedor_dinamico, bg=PALETTE["plomo_fondo"])

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
            width=20,
            font=("Segoe UI", 9),
            bootstyle="danger"
        )
        self.combo_insumo.pack(side="left", padx=(0, 6))

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

        btn_add_item = tk.Button(
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
            command=self._agregar_insumo_lista
        )
        btn_add_item.pack(side="right")

        self.tabla_carrito = tb.Treeview(
            self.frame_material,
            columns=("insumo", "cantidad", "unidad"),
            show="headings",
            height=4,
            style="Don.Treeview"
        )
        self.tabla_carrito.heading("insumo", text="Insumo")
        self.tabla_carrito.heading("cantidad", text="Cantidad")
        self.tabla_carrito.heading("unidad", text="Unidad")
        self.tabla_carrito.column("insumo", width=150, anchor="w")
        self.tabla_carrito.column("cantidad", width=70, anchor="center")
        self.tabla_carrito.column("unidad", width=110, anchor="center")
        self.tabla_carrito.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_carrito.tag_configure("impar", background="#F9FAFB")
        self.tabla_carrito.pack(fill="x", pady=(0, 6))

        btn_quitar_item = tk.Button(
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
            command=self._quitar_insumo_lista
        )
        btn_quitar_item.pack(anchor="e")

        tk.Label(
            br,
            text="Observaciones",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_obs = tb.Entry(br, font=("Segoe UI", 9))
        self.entry_obs.pack(fill="x", ipady=3, pady=(3, 10))

        # --- PANEL DERECHO: HISTORIAL Y DESGLOSE DE DONACIONES ---
        card_hist = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=14,
            expand_body=True
        )
        card_hist.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        bh = card_hist.body

        top_hist = tk.Frame(bh, bg=PALETTE["blanco"])
        top_hist.pack(fill="x", pady=(0, 10))

        tit_hist_box = tk.Frame(top_hist, bg=PALETTE["blanco"])
        tit_hist_box.pack(side="left")

        tk.Label(
            tit_hist_box,
            text="🎁  Historial de Donaciones",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        tk.Label(
            tit_hist_box,
            text="Incluye registros administrativos y autodonaciones del portal público",
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        self.combo_filtro = tb.Combobox(
            top_hist,
            values=["Todos", "DINERO", "MATERIAL"],
            state="readonly",
            width=14,
            bootstyle="danger"
        )
        self.combo_filtro.set("Todos")
        self.combo_filtro.pack(side="right", pady=2)
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda _e: self._cargar_historial())

        cols = ("fecha", "donante", "tipo", "origen", "detalle")
        self.tabla_hist = tb.Treeview(
            bh,
            columns=cols,
            show="headings",
            height=8,
            style="Don.Treeview"
        )
        self.tabla_hist.heading("fecha", text="Fecha / Hora")
        self.tabla_hist.heading("donante", text="Donante")
        self.tabla_hist.heading("tipo", text="Tipo")
        self.tabla_hist.heading("origen", text="Canal")
        self.tabla_hist.heading("detalle", text="Monto / Resumen")

        self.tabla_hist.column("fecha", width=110, anchor="center")
        self.tabla_hist.column("donante", width=165, anchor="w")
        self.tabla_hist.column("tipo", width=75, anchor="center")
        self.tabla_hist.column("origen", width=95, anchor="center")
        self.tabla_hist.column("detalle", width=155, anchor="w")

        self.tabla_hist.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_hist.tag_configure("impar", background="#F9FAFB")
        self.tabla_hist.pack(fill=BOTH, expand=True, pady=(0, 12))
        self.tabla_hist.bind("<<TreeviewSelect>>", self._al_seleccionar_donacion)

        self.lbl_detalle_don = tk.Label(
            bh,
            text="Selecciona una donación de la tabla para ver su desglose completo.",
            font=("Segoe UI", 9),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            padx=14,
            pady=10,
            justify="left",
            anchor="w"
        )
        self.lbl_detalle_don.pack(fill="x")

    # =========================================================================
    # SUB-PESTAÑA 2: INVENTARIO DISPONIBLE Y DESPACHO DE INSUMOS
    # =========================================================================
    def _construir_tab_inventario(self, parent):
        cuerpo = tk.Frame(parent, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=48, uniform="inv_cols")
        cuerpo.columnconfigure(1, weight=52, uniform="inv_cols")
        cuerpo.rowconfigure(0, weight=1)

        # --- IZQUIERDA: SOLO INSUMOS REGISTRADOS CON CANTIDAD DISPONIBLE ---
        card_stock = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=14,
            expand_body=True
        )
        card_stock.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        bs = card_stock.body

        top_st = tk.Frame(bs, bg=PALETTE["blanco"])
        top_st.pack(fill="x", pady=(0, 10))

        tit_st_box = tk.Frame(top_st, bg=PALETTE["blanco"])
        tit_st_box.pack(side="left")

        tk.Label(
            tit_st_box,
            text="📊  Existencias Disponibles en Almacén",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        tk.Label(
            tit_st_box,
            text="Muestra únicamente insumos registrados con stock disponible",
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_ref_inv = tk.Button(
            top_st,
            text="↻ Actualizar",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._refrescar_inventario_y_entregas
        )
        btn_ref_inv.pack(side="right")

        cols_st = ("insumo", "unidad", "disponible")
        self.tabla_stock = tb.Treeview(
            bs,
            columns=cols_st,
            show="headings",
            style="Don.Treeview"
        )
        self.tabla_stock.heading("insumo", text="Insumo Registrado")
        self.tabla_stock.heading("unidad", text="Unidad")
        self.tabla_stock.heading("disponible", text="Cantidad Disponible")

        self.tabla_stock.column("insumo", width=230, anchor="w")
        self.tabla_stock.column("unidad", width=120, anchor="center")
        self.tabla_stock.column("disponible", width=130, anchor="center")

        self.tabla_stock.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_stock.tag_configure("impar", background="#F9FAFB")
        self.tabla_stock.pack(fill=BOTH, expand=True)

        # --- DERECHA: FORMULARIO DE ENTREGA + HISTORIAL DE SALIDAS ---
        card_desp = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=14,
            expand_body=True
        )
        card_desp.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        bd = card_desp.body

        tk.Label(
            bd,
            text="🚚  Registrar Entrega / Despacho de Insumos",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 8))

        form_box = tk.Frame(bd, bg=PALETTE["plomo_fondo"], padx=14, pady=12)
        form_box.pack(fill="x", pady=(0, 12))

        # Paso 1: Tipo de destino (Fundación vs Otras Organizaciones)
        r_dest_tipo = tk.Frame(form_box, bg=PALETTE["plomo_fondo"])
        r_dest_tipo.pack(fill="x", pady=(0, 8))

        tk.Label(
            r_dest_tipo,
            text="1. ¿Cuál es el destino de la entrega? *:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.combo_tipo_destino = tb.Combobox(
            r_dest_tipo,
            values=list(self.controller.TIPOS_DESTINO_DESPACHO),
            state="readonly",
            font=("Segoe UI", 9, "bold"),
            bootstyle="danger"
        )
        self.combo_tipo_destino.set(self.controller.TIPOS_DESTINO_DESPACHO[0])
        self.combo_tipo_destino.pack(fill="x", pady=(2, 0))
        self.combo_tipo_destino.bind("<<ComboboxSelected>>", lambda _e: self._alternar_destino_despacho())

        # Paso 2: Insumo disponible y cantidad
        r1 = tk.Frame(form_box, bg=PALETTE["plomo_fondo"])
        r1.pack(fill="x", pady=(0, 8))

        tk.Label(
            r1,
            text="2. Insumo disponible *:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.combo_insumo_desp = tb.Combobox(
            r1,
            state="readonly",
            width=28,
            font=("Segoe UI", 9),
            bootstyle="danger"
        )
        self.combo_insumo_desp.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(
            r1,
            text="Cantidad *:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.entry_cant_desp = tb.Entry(r1, width=9, font=("Segoe UI", 9, "bold"))
        self.entry_cant_desp.pack(side="left")
        InputValidators.aplicar(self.entry_cant_desp, "decimales")

        # Contenedor dinámico según el destino seleccionado
        self.box_destino_dinamico = tk.Frame(form_box, bg=PALETTE["plomo_fondo"])
        self.box_destino_dinamico.pack(fill="x", pady=(0, 8))

        # Sub-bloque A: Actividad de la Fundación
        self.frame_dest_actividad = tk.Frame(self.box_destino_dinamico, bg=PALETTE["plomo_fondo"])

        tk.Label(
            self.frame_dest_actividad,
            text="3. Actividad vinculada de la Fundación *:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.combo_actividad_desp = tb.Combobox(
            self.frame_dest_actividad,
            state="readonly",
            font=("Segoe UI", 9),
            bootstyle="danger"
        )
        self.combo_actividad_desp.pack(fill="x", pady=(2, 6))

        tk.Label(
            self.frame_dest_actividad,
            text="Nota o detalle adicional de entrega (Opcional):",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        self.entry_nota_actividad = tb.Entry(self.frame_dest_actividad, font=("Segoe UI", 9))
        self.entry_nota_actividad.pack(fill="x", ipady=2, pady=(2, 0))

        # Sub-bloque B: Otras Organizaciones (Hospitales, Escuelas, etc.)
        self.frame_dest_externo = tk.Frame(self.box_destino_dinamico, bg=PALETTE["plomo_fondo"])

        tk.Label(
            self.frame_dest_externo,
            text="3. Nombre de la Organización, Hospital, Escuela o Beneficiario *:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_destino_desp = tb.Entry(self.frame_dest_externo, font=("Segoe UI", 9))
        self.entry_destino_desp.pack(fill="x", ipady=3, pady=(2, 0))

        btn_despachar = tk.Button(
            form_box,
            text="✓  Confirmar Salida de Inventario",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=8,
            cursor="hand2",
            command=self._registrar_despacho
        )
        btn_despachar.pack(fill="x")
        btn_despachar.bind("<Enter>", lambda _e: btn_despachar.config(bg=PALETTE["rojo_hover"]))
        btn_despachar.bind("<Leave>", lambda _e: btn_despachar.config(bg=PALETTE["rojo"]))

        tk.Label(
            bd,
            text="Historial Reciente de Entregas (ENTREGA_INSUMO)",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 6))

        cols_ent = ("fecha", "insumo", "cantidad", "destino")
        self.tabla_entregas = tb.Treeview(
            bd,
            columns=cols_ent,
            show="headings",
            height=6,
            style="Don.Treeview"
        )
        self.tabla_entregas.heading("fecha", text="Fecha / Hora")
        self.tabla_entregas.heading("insumo", text="Insumo")
        self.tabla_entregas.heading("cantidad", text="Cantidad")
        self.tabla_entregas.heading("destino", text="Actividad / Destino")

        self.tabla_entregas.column("fecha", width=110, anchor="center")
        self.tabla_entregas.column("insumo", width=140, anchor="w")
        self.tabla_entregas.column("cantidad", width=85, anchor="center")
        self.tabla_entregas.column("destino", width=180, anchor="w")

        self.tabla_entregas.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_entregas.tag_configure("impar", background="#F9FAFB")
        self.tabla_entregas.pack(fill=BOTH, expand=True)

        self._alternar_destino_despacho()

    # =========================================================================
    # EVENTOS Y LÓGICA DE INTERFAZ
    # =========================================================================
    def _on_mousewheel_reg(self, event):
        if hasattr(self, "canvas_reg") and self.canvas_reg.winfo_exists():
            self.canvas_reg.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _desvincular_rueda(self):
        try:
            if hasattr(self, "canvas_reg") and self.canvas_reg.winfo_exists():
                self.canvas_reg.unbind_all("<MouseWheel>")
        except Exception:
            pass

    @staticmethod
    def _asignar_texto_seguro(entry_widget, texto: str):
        modo_anterior = entry_widget.cget("validate")
        entry_widget.configure(validate="none")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, texto or "")
        entry_widget.configure(validate=modo_anterior)

    def _inicializar_datos(self):
        try:
            cats = self.controller.cargar_catalogos()

            self.insumos_map = {
                f"{i['nombre']} ({i['unidad_medida']})": i for i in cats["insumos"]
            }
            insumos_labels = list(self.insumos_map.keys())
            self.combo_insumo["values"] = insumos_labels
            if insumos_labels:
                self.combo_insumo.set(insumos_labels[0])

            self.actividades_map = {}
            for act in cats["actividades"]:
                etiqueta = f"{act['nombre']} ({act['fecha']} - {act['estado']})"
                self.actividades_map[etiqueta] = act
            act_labels = list(self.actividades_map.keys())
            self.combo_actividad_desp["values"] = act_labels
            if act_labels:
                self.combo_actividad_desp.set(act_labels[0])
            else:
                self.combo_actividad_desp.set("")

            self._alternar_panel_tipo()
            self._cargar_historial()
            self._refrescar_inventario_y_entregas()
        except Exception as e:
            messagebox.showerror("Error de Catálogos", str(e))

    def _alternar_destino_despacho(self):
        tipo_dest = self.combo_tipo_destino.get()
        self.frame_dest_actividad.pack_forget()
        self.frame_dest_externo.pack_forget()

        if tipo_dest == "Actividad de la Fundación":
            self.frame_dest_actividad.pack(fill="x")
        else:
            self.frame_dest_externo.pack(fill="x")

    def _alternar_panel_tipo(self):
        tipo = self.combo_tipo.get().strip().upper()
        self.frame_dinero.pack_forget()
        self.frame_material.pack_forget()

        if tipo == "DINERO":
            self.frame_dinero.pack(fill="x")
        elif tipo == "MATERIAL":
            self.frame_material.pack(fill="x")

        if hasattr(self, "canvas_reg") and self.canvas_reg.winfo_exists():
            self.canvas_reg.update_idletasks()
            self.canvas_reg.configure(scrollregion=self.canvas_reg.bbox("all"))
            self.canvas_reg.yview_moveto(0)

    def _buscar_donante(self):
        doc = self.entry_doc.get().strip()
        if not doc:
            messagebox.showwarning("Búsqueda", "Ingresa el CI o NIT del donante para buscarlo.")
            return

        encontrado = self.controller.buscar_donante(doc)
        if not encontrado:
            messagebox.showinfo(
                "Nuevo Donante",
                "No se encontró un donante previo con ese documento. Completa sus datos para registrarlo."
            )
            self.entry_nombre.focus_set()
            return

        self._asignar_texto_seguro(self.entry_nombre, encontrado.get("nombre", ""))
        self._asignar_texto_seguro(self.entry_tel, encontrado.get("telefono", ""))
        self.entry_correo.delete(0, tk.END)
        self.entry_correo.insert(0, encontrado.get("correo") or "")
        messagebox.showinfo("Donante Encontrado", f"Datos cargados de: {encontrado['nombre']}")

    def _agregar_insumo_lista(self):
        insumo_obj = self.insumos_map.get(self.combo_insumo.get())
        ok, msg, item = self.controller.validar_item_insumo(insumo_obj, self.entry_cant.get())
        if not ok:
            messagebox.showwarning("Validación de Insumo", msg)
            return

        actualizado = False
        for existente in self.carrito_insumos:
            if existente["id_insumo"] == item["id_insumo"]:
                existente["cantidad"] = round(existente["cantidad"] + item["cantidad"], 2)
                actualizado = True
                break

        if not actualizado:
            self.carrito_insumos.append(item)

        self.entry_cant.delete(0, tk.END)
        self._refrescar_tabla_carrito()

    def _quitar_insumo_lista(self):
        sel = self.tabla_carrito.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona un ítem de la lista para quitarlo.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.carrito_insumos):
            self.carrito_insumos.pop(idx)
            self._refrescar_tabla_carrito()

    def _refrescar_tabla_carrito(self):
        for w in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(w)
        for idx, item in enumerate(self.carrito_insumos):
            tag = "par" if idx % 2 == 0 else "impar"
            self.tabla_carrito.insert("", tk.END, iid=str(idx), values=(
                item["nombre"],
                f"{item['cantidad']:g}",
                item["unidad_medida"]
            ), tags=(tag,))

    def _limpiar_todo(self):
        for entry in (
            self.entry_doc,
            self.entry_nombre,
            self.entry_tel,
            self.entry_correo,
            self.entry_monto,
            self.entry_cant,
            self.entry_obs
        ):
            entry.delete(0, tk.END)
        self.carrito_insumos.clear()
        self._refrescar_tabla_carrito()
        if hasattr(self, "canvas_reg") and self.canvas_reg.winfo_exists():
            self.canvas_reg.yview_moveto(0)

    def _guardar_donacion(self):
        datos_donante = {
            "documento": self.entry_doc.get(),
            "nombre": self.entry_nombre.get(),
            "telefono": self.entry_tel.get(),
            "correo": self.entry_correo.get()
        }

        exito, resultado = self.controller.registrar_donacion(
            datos_donante=datos_donante,
            tipo_nombre=self.combo_tipo.get(),
            monto_str=self.entry_monto.get(),
            metodo_pago=self.combo_metodo.get(),
            lista_insumos=self.carrito_insumos,
            observaciones=self.entry_obs.get(),
            id_usuario_registra=self.sesion["id_usuario"]
        )

        if not exito:
            messagebox.showwarning("Validación de Donación", str(resultado))
            return

        msg = resultado["mensaje"] if isinstance(resultado, dict) else str(resultado)
        messagebox.showinfo("Donación Registrada", msg)
        self._limpiar_todo()
        self._cargar_historial()
        self._refrescar_inventario_y_entregas()

    def _cargar_historial(self):
        for w in self.tabla_hist.get_children():
            self.tabla_hist.delete(w)
        self.donaciones_cache.clear()

        try:
            registros = self.controller.obtener_historial(self.combo_filtro.get())
            for idx, r in enumerate(registros):
                iid = str(r["id_donacion"])
                self.donaciones_cache[iid] = r
                tag = "par" if idx % 2 == 0 else "impar"

                if r["tipo_donacion"].upper() == "DINERO":
                    resumen = f"Bs. {float(r['monto'] or 0):,.2f} ({r['metodo_pago'] or '-'})"
                else:
                    resumen = f"{r['cantidad_items']} insumo(s) entregado(s)"

                self.tabla_hist.insert("", tk.END, iid=iid, values=(
                    r.get("fecha_hora_str", str(r["fecha"])),
                    r["donante"],
                    r["tipo_donacion"],
                    r.get("origen", "Sistema"),
                    resumen
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar_donacion(self, _event):
        sel = self.tabla_hist.selection()
        if not sel:
            return
        don = self.donaciones_cache.get(sel[0])
        if not don:
            return

        obs_txt = f"  |  Obs: {don['observaciones']}" if don.get("observaciones") else ""

        if don["tipo_donacion"].upper() == "DINERO":
            texto = (
                f"👤 Donante: {don['donante']}  |  CI/NIT: {don['documento'] or 'N/A'}  |  Canal: {don.get('origen', '-')}\n"
                f"💵 Tipo: DINERO  |  Método: {don['metodo_pago']}  |  Monto: Bs. {float(don['monto'] or 0):,.2f}{obs_txt}"
            )
            self.lbl_detalle_don.config(text=texto)
        else:
            try:
                items = self.controller.obtener_desglose_material(don["id_donacion"])
                lineas = [
                    f"👤 Donante: {don['donante']}  |  CI/NIT: {don['documento'] or 'N/A'}  |  "
                    f"📦 Tipo: MATERIAL ({don.get('origen', '-')}){obs_txt}"
                ]
                for it in items:
                    lineas.append(f"  • {it['insumo']}: {float(it['cantidad']):g} {it['unidad_medida']}")
                self.lbl_detalle_don.config(text="\n".join(lineas))
            except Exception as e:
                self.lbl_detalle_don.config(text=f"Error al cargar insumos: {e}")

    def _refrescar_inventario_y_entregas(self):
        try:
            inventario = self.controller.obtener_inventario()
            for w in self.tabla_stock.get_children():
                self.tabla_stock.delete(w)

            self.insumos_inv_map.clear()
            labels_inv = []

            # Solo reconocer y mostrar insumos registrados con cantidad disponible > 0
            disponibles = [
                item for item in inventario
                if round(float(item.get("stock_disponible") or 0), 2) > 0
            ]

            for idx, item in enumerate(disponibles):
                disp = round(float(item["stock_disponible"]), 2)
                tag = "par" if idx % 2 == 0 else "impar"
                self.tabla_stock.insert("", tk.END, values=(
                    item["nombre"],
                    item["unidad_medida"],
                    f"{disp:g}"
                ), tags=(tag,))

                etiqueta = f"{item['nombre']} [Disp: {disp:g} {item['unidad_medida']}]"
                self.insumos_inv_map[etiqueta] = item
                labels_inv.append(etiqueta)

            self.combo_insumo_desp["values"] = labels_inv
            if labels_inv:
                self.combo_insumo_desp.set(labels_inv[0])
            else:
                self.combo_insumo_desp.set("Sin insumos disponibles en almacén")

            entregas = self.controller.obtener_historial_entregas()
            for w in self.tabla_entregas.get_children():
                self.tabla_entregas.delete(w)

            for idx, ent in enumerate(entregas):
                tag = "par" if idx % 2 == 0 else "impar"
                dest = ent.get("destino") or ent.get("actividad") or "-"
                self.tabla_entregas.insert("", tk.END, values=(
                    ent["fecha_str"],
                    ent["insumo"],
                    f"{float(ent['cantidad']):g} {ent['unidad_medida']}",
                    dest
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Error de Inventario", str(e))

    def _registrar_despacho(self):
        tipo_destino = self.combo_tipo_destino.get()
        insumo_obj = self.insumos_inv_map.get(self.combo_insumo_desp.get())

        if tipo_destino == "Actividad de la Fundación":
            actividad_obj = self.actividades_map.get(self.combo_actividad_desp.get())
            destino_texto = self.entry_nota_actividad.get()
        else:
            actividad_obj = None
            destino_texto = self.entry_destino_desp.get()

        exito, mensaje = self.controller.registrar_entrega_insumo(
            insumo_obj=insumo_obj,
            cantidad_str=self.entry_cant_desp.get(),
            tipo_destino=tipo_destino,
            actividad_obj=actividad_obj,
            destino=destino_texto,
            id_usuario_entrega=self.sesion["id_usuario"]
        )
        if not exito:
            messagebox.showwarning("Validación de Despacho", mensaje)
            return

        messagebox.showinfo("Entrega Registrada", mensaje)
        self.entry_cant_desp.delete(0, tk.END)
        self.entry_destino_desp.delete(0, tk.END)
        self.entry_nota_actividad.delete(0, tk.END)
        self._refrescar_inventario_y_entregas()