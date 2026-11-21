import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.donacion_controller import DonacionController
from views.ui_components import PALETTE, RoundedCard, InputValidators


class GestionDonacionesView(tk.Frame):
    """Vista para Administrador: Registro y control de donaciones monetarias y materiales."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = DonacionController()

        self.tipos_map = {}
        self.metodos_map = {}
        self.insumos_map = {}
        self.carrito_insumos = []
        self.donaciones_cache = {}

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._inicializar_datos()

    def _configurar_estilos_tabla(self):
        """Aplica el estilo limpio en plomo y negro igual al Panel General."""
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
        # 1. ENCABEZADO (20 pt)
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="SAVE THE CHILDREN BOLIVIA  •  RECURSOS Y APORTES",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["rojo"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Gestión de Donaciones (Monetarias y en Especie)",
            font=("Segoe UI", 20, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            header,
            text="Registra aportes económicos o entrega de insumos con trazabilidad completa del donante.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        # =====================================================================
        # 2. CUERPO DIVIDIDO EN DOS TARJETAS CURVAS
        # =====================================================================
        cuerpo = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=48, uniform="don_cols")
        cuerpo.columnconfigure(1, weight=52, uniform="don_cols")
        cuerpo.rowconfigure(0, weight=1)

        # =====================================================================
        # PANEL IZQUIERDO: FORMULARIO DE REGISTRO
        # =====================================================================
        card_reg = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=22,
            pady=18,
            expand_body=True
        )
        card_reg.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        br = card_reg.body

        tk.Label(
            br,
            text="1. Datos del Donante",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(0, 8))

        # Fila CI/NIT (Solo números) + Botón Buscar
        doc_row = tk.Frame(br, bg=PALETTE["blanco"])
        doc_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            doc_row,
            text="CI / NIT [Solo números]:",
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

        # Nombre / Razón Social (Solo letras)
        tk.Label(
            br,
            text="Nombre Completo o Razón Social *  [Solo letras]",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_nombre = tb.Entry(br, font=("Segoe UI", 10))
        self.entry_nombre.pack(fill="x", ipady=3, pady=(3, 10))
        InputValidators.aplicar(self.entry_nombre, "letras")

        # Teléfono (Solo números) y Correo Electrónico en 2 columnas
        tel_mail_frame = tk.Frame(br, bg=PALETTE["blanco"])
        tel_mail_frame.pack(fill="x", pady=(0, 12))
        tel_mail_frame.columnconfigure(0, weight=1, uniform="tm_cols")
        tel_mail_frame.columnconfigure(1, weight=1, uniform="tm_cols")

        tk.Label(
            tel_mail_frame,
            text="Teléfono  [Solo números]",
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

        # Separador en plomo claro
        tk.Frame(br, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(2, 12))

        # Sección 2: Tipo de Donación
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
            state="readonly",
            width=18,
            font=("Segoe UI", 10, "bold"),
            bootstyle="danger"
        )
        self.combo_tipo.pack(side="right")
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda _e: self._alternar_panel_tipo())

        # Contenedor dinámico en plomo neutro (cambia según DINERO o MATERIAL)
        self.contenedor_dinamico = tk.Frame(br, bg=PALETTE["plomo_fondo"], padx=14, pady=12)
        self.contenedor_dinamico.pack(fill=BOTH, expand=True, pady=(0, 10))

        # --- Sub-panel A: DINERO ---
        self.frame_dinero = tk.Frame(self.contenedor_dinamico, bg=PALETTE["plomo_fondo"])

        tk.Label(
            self.frame_dinero,
            text="Monto Donado (Bs.) *  [Solo números / decimales]",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_monto = tb.Entry(self.frame_dinero, font=("Segoe UI", 11, "bold"))
        self.entry_monto.pack(fill="x", ipady=4, pady=(3, 12))
        InputValidators.aplicar(self.entry_monto, "decimales")

        tk.Label(
            self.frame_dinero,
            text="Método de Pago *  (QR, Efectivo o Transferencia)",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.combo_metodo = tb.Combobox(
            self.frame_dinero,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
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
            width=21,
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
        self.tabla_carrito.pack(fill=BOTH, expand=True, pady=(0, 6))

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

        # Observaciones y Botones Inferiores
        tk.Label(
            br,
            text="Observaciones (Opcional)",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(anchor="w")

        self.entry_obs = tb.Entry(br, font=("Segoe UI", 9))
        self.entry_obs.pack(fill="x", ipady=3, pady=(3, 12))

        btns_bottom = tk.Frame(br, bg=PALETTE["blanco"])
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

        # =====================================================================
        # PANEL DERECHO: HISTORIAL Y DESGLOSE DE DONACIONES
        # =====================================================================
        card_hist = RoundedCard(
            cuerpo,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=18,
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
            text="Selecciona un registro para ver el desglose completo",
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

        cols = ("fecha", "donante", "tipo", "detalle")
        self.tabla_hist = tb.Treeview(
            bh,
            columns=cols,
            show="headings",
            style="Don.Treeview"
        )
        self.tabla_hist.heading("fecha", text="Fecha")
        self.tabla_hist.heading("donante", text="Donante")
        self.tabla_hist.heading("tipo", text="Tipo")
        self.tabla_hist.heading("detalle", text="Monto / Resumen")

        self.tabla_hist.column("fecha", width=90, anchor="center")
        self.tabla_hist.column("donante", width=180, anchor="w")
        self.tabla_hist.column("tipo", width=85, anchor="center")
        self.tabla_hist.column("detalle", width=165, anchor="w")

        self.tabla_hist.tag_configure("par", background=PALETTE["blanco"])
        self.tabla_hist.tag_configure("impar", background="#F9FAFB")
        self.tabla_hist.pack(fill=BOTH, expand=True, pady=(0, 12))
        self.tabla_hist.bind("<<TreeviewSelect>>", self._al_seleccionar_donacion)

        # Caja inferior de detalle de la donación seleccionada
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

    @staticmethod
    def _asignar_texto_seguro(entry_widget, texto: str):
        """Inserta texto cargado desde BD sin bloquearse si el registro antiguo tenía símbolos."""
        modo_anterior = entry_widget.cget("validate")
        entry_widget.configure(validate="none")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, texto or "")
        entry_widget.configure(validate=modo_anterior)

    def _inicializar_datos(self):
        try:
            cats = self.controller.cargar_catalogos()

            self.tipos_map = {t["nombre"]: t for t in cats["tipos"]}
            tipos_nombres = list(self.tipos_map.keys())
            self.combo_tipo["values"] = tipos_nombres
            if tipos_nombres:
                self.combo_tipo.set(tipos_nombres[0])

            self.metodos_map = {m["nombre"]: m for m in cats["metodos"]}
            metodos_nombres = list(self.metodos_map.keys())
            self.combo_metodo["values"] = metodos_nombres
            if metodos_nombres:
                self.combo_metodo.set(metodos_nombres[0])

            self.insumos_map = {
                f"{i['nombre']} ({i['unidad_medida']})": i for i in cats["insumos"]
            }
            insumos_labels = list(self.insumos_map.keys())
            self.combo_insumo["values"] = insumos_labels
            if insumos_labels:
                self.combo_insumo.set(insumos_labels[0])

            self._alternar_panel_tipo()
            self._cargar_historial()
        except Exception as e:
            messagebox.showerror("Error de Catálogos", str(e))

    def _alternar_panel_tipo(self):
        tipo = self.combo_tipo.get().strip().upper()
        self.frame_dinero.pack_forget()
        self.frame_material.pack_forget()

        if tipo == "DINERO":
            self.frame_dinero.pack(fill=BOTH, expand=True)
        elif tipo == "MATERIAL":
            self.frame_material.pack(fill=BOTH, expand=True)

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

    def _guardar_donacion(self):
        datos_donante = {
            "documento": self.entry_doc.get(),
            "nombre": self.entry_nombre.get(),
            "telefono": self.entry_tel.get(),
            "correo": self.entry_correo.get()
        }
        tipo_obj = self.tipos_map.get(self.combo_tipo.get())
        metodo_obj = self.metodos_map.get(self.combo_metodo.get())

        exito, mensaje = self.controller.registrar_donacion(
            datos_donante=datos_donante,
            tipo_obj=tipo_obj,
            monto_str=self.entry_monto.get(),
            metodo_obj=metodo_obj,
            lista_insumos=self.carrito_insumos,
            observaciones=self.entry_obs.get(),
            id_usuario_registra=self.sesion["id_usuario"]
        )

        if not exito:
            messagebox.showwarning("Validación de Donación", mensaje)
            return

        messagebox.showinfo("Donación Registrada", mensaje)
        self._limpiar_todo()
        self._cargar_historial()

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
                    str(r["fecha"]),
                    r["donante"],
                    r["tipo_donacion"],
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

        if don["tipo_donacion"].upper() == "DINERO":
            texto = (
                f"👤 Donante: {don['donante']}  |  CI/NIT: {don['documento'] or 'N/A'}\n"
                f"💵 Tipo: DINERO  |  Método de Pago: {don['metodo_pago']}  |  Monto: Bs. {float(don['monto'] or 0):,.2f}"
            )
            self.lbl_detalle_don.config(text=texto)
        else:
            try:
                items = self.controller.obtener_desglose_material(don["id_donacion"])
                lineas = [f"👤 Donante: {don['donante']}  |  CI/NIT: {don['documento'] or 'N/A'}  |  📦 Tipo: MATERIAL"]
                for it in items:
                    lineas.append(f"  • {it['insumo']}: {float(it['cantidad']):g} {it['unidad_medida']}")
                self.lbl_detalle_don.config(text="\n".join(lineas))
            except Exception as e:
                self.lbl_detalle_don.config(text=f"Error al cargar insumos: {e}")