import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.auth_controller import AuthController
from views.ui_components import PALETTE, RoundedCard


class AuditoriaAccesosView(tk.Frame):
    """Vista de Auditoría de Inicios de Sesión con búsqueda y filtros múltiples."""

    def __init__(self, master, sesion: dict):
        super().__init__(master, bg=PALETTE["plomo_fondo"])
        self.sesion = sesion
        self.controller = AuthController()
        self.logs_cache = []

        self.pack(fill=BOTH, expand=True)
        self._configurar_estilos_tabla()
        self._construir_ui()
        self._cargar_logs()

    def _configurar_estilos_tabla(self):
        style = tb.Style()
        style.configure(
            "Aud.Treeview",
            background=PALETTE["blanco"],
            foreground=PALETTE["negro"],
            fieldbackground=PALETTE["blanco"],
            rowheight=31,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Aud.Treeview.Heading",
            background=PALETTE["plomo_fondo"],
            foreground=PALETTE["negro"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 8)
        )
        style.map(
            "Aud.Treeview.Heading",
            background=[("active", PALETTE["plomo_borde"])]
        )
        style.map(
            "Aud.Treeview",
            background=[("selected", PALETTE["rojo_suave"])],
            foreground=[("selected", PALETTE["negro"])]
        )

    def _construir_ui(self):
        # =====================================================================
        # 1. ENCABEZADO (20 pt)
        # =====================================================================
        header = tk.Frame(self, bg=PALETTE["plomo_fondo"])
        header.pack(fill="x", pady=(0, 8))

        titulos = tk.Frame(header, bg=PALETTE["plomo_fondo"])
        titulos.pack(side="left", fill="x", expand=True)

        tk.Label(
            titulos,
            text="Auditoría y Trazabilidad de Accesos",
            font=("Segoe UI", 16, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"]
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            titulos,
            text="Registro histórico de inicios de sesión capturado automáticamente por MySQL.",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"]
        ).pack(anchor="w")

        btn_ref = tk.Button(
            header,
            text="↻  Actualizar Registro",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._cargar_logs
        )
        btn_ref.pack(side="right", pady=6)
        btn_ref.bind("<Enter>", lambda _e: btn_ref.config(bg=PALETTE["rojo_hover"]))
        btn_ref.bind("<Leave>", lambda _e: btn_ref.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # 2. BARRA CURVA DE BÚSQUEDA Y FILTROS (PERSONA, ROL, FECHA, HORA)
        # =====================================================================
        filtro_card = RoundedCard(
            self,
            radius=18,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=18,
            pady=12,
            expand_body=False
        )
        filtro_card.pack(fill="x", pady=(0, 8))

        fb = filtro_card.body

        # Buscador general (Nombre, Cuenta, Fecha u Hora)
        tk.Label(
            fb,
            text="🔍 Buscar (Nombre, Usuario, Fecha u Hora):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 8))

        self.entry_buscar = tb.Entry(fb, width=28, font=("Segoe UI", 9))
        self.entry_buscar.pack(side="left", ipady=3, padx=(0, 14))
        self.entry_buscar.bind("<KeyRelease>", lambda _e: self._aplicar_filtros())

        # Filtro por Rol
        tk.Label(
            fb,
            text="Rol:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.combo_rol = tb.Combobox(
            fb,
            values=["Todos", "Administrador", "Voluntario"],
            state="readonly",
            width=15,
            bootstyle="danger"
        )
        self.combo_rol.set("Todos")
        self.combo_rol.pack(side="left", padx=(0, 14))
        self.combo_rol.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_filtros())

        # Filtro rápido por Fecha (AAAA-MM-DD)
        tk.Label(
            fb,
            text="Fecha (AAAA-MM-DD):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack(side="left", padx=(0, 6))

        self.entry_fecha = tb.Entry(fb, width=13, font=("Segoe UI", 9))
        self.entry_fecha.pack(side="left", ipady=3, padx=(0, 10))
        self.entry_fecha.bind("<KeyRelease>", lambda _e: self._aplicar_filtros())

        btn_limpiar = tk.Button(
            fb,
            text="Limpiar Filtros",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._limpiar_filtros
        )
        btn_limpiar.pack(side="left")

        self.lbl_contador = tk.Label(
            fb,
            text="0 registros",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["plomo_texto"],
            padx=10,
            pady=4
        )
        self.lbl_contador.pack(side="right")

        # =====================================================================
        # 3. TARJETA CURVA CON TABLA UNIFICADA
        # =====================================================================
        card = RoundedCard(
            self,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=20,
            pady=16,
            expand_body=True
        )
        card.pack(fill=BOTH, expand=True)

        cols = ("fecha_hora", "usuario", "rol", "persona")
        self.tabla = tb.Treeview(card.body, columns=cols, show="headings", style="Aud.Treeview")
        self.tabla.heading("fecha_hora", text="Fecha y Hora de Acceso")
        self.tabla.heading("usuario", text="Cuenta de Usuario")
        self.tabla.heading("rol", text="Rol del Sistema")
        self.tabla.heading("persona", text="Usuario / Voluntario")

        self.tabla.column("fecha_hora", width=180, anchor="center")
        self.tabla.column("usuario", width=160, anchor="center")
        self.tabla.column("rol", width=140, anchor="center")
        self.tabla.column("persona", width=260, anchor="w")

        self.tabla.tag_configure("par", background=PALETTE["blanco"])
        self.tabla.tag_configure("impar", background="#F9FAFB")
        self.tabla.pack(fill=BOTH, expand=True)

    def _cargar_logs(self):
        try:
            raw_logs = self.controller.obtener_historial_accesos(500)
            self.logs_cache.clear()
            roles_encontrados = {"Administrador", "Voluntario"}

            for item in raw_logs:
                fh = item["fecha_hora_acceso"]
                fh_str = fh.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fh, "strftime") else str(fh)
                rol_str = str(item.get("rol") or "")
                if rol_str:
                    roles_encontrados.add(rol_str)

                self.logs_cache.append({
                    "fecha_hora": fh_str,
                    "usuario": str(item.get("usuario") or ""),
                    "rol": rol_str,
                    "persona": str(item.get("persona") or "")
                })

            rol_actual = self.combo_rol.get()
            self.combo_rol["values"] = ["Todos"] + sorted(roles_encontrados)
            if rol_actual in self.combo_rol["values"]:
                self.combo_rol.set(rol_actual)
            else:
                self.combo_rol.set("Todos")

            self._aplicar_filtros()
        except Exception as e:
            messagebox.showerror("Error de Auditoría", str(e))

    def _aplicar_filtros(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)

        texto_q = self.entry_buscar.get().strip().lower()
        rol_q = self.combo_rol.get().strip()
        fecha_q = self.entry_fecha.get().strip().lower()

        filtrados = []
        for reg in self.logs_cache:
            if rol_q != "Todos" and reg["rol"].lower() != rol_q.lower():
                continue

            if fecha_q and fecha_q not in reg["fecha_hora"].lower():
                continue

            if texto_q:
                combinado = f"{reg['persona']} {reg['usuario']} {reg['rol']} {reg['fecha_hora']}".lower()
                if texto_q not in combinado:
                    continue

            filtrados.append(reg)

        for idx, reg in enumerate(filtrados):
            tag = "par" if idx % 2 == 0 else "impar"
            self.tabla.insert("", tk.END, values=(
                reg["fecha_hora"],
                reg["usuario"],
                reg["rol"],
                reg["persona"]
            ), tags=(tag,))

        self.lbl_contador.config(text=f"Mostrando {len(filtrados)} de {len(self.logs_cache)}")

    def _limpiar_filtros(self):
        self.entry_buscar.delete(0, tk.END)
        self.entry_fecha.delete(0, tk.END)
        self.combo_rol.set("Todos")
        self._aplicar_filtros()