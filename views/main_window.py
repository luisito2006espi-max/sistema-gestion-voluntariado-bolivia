import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.auth_controller import AuthController
from views.ui_components import PALETTE, SaveTheChildrenLogo
from views.dashboard_view import DashboardView
from views.voluntarios_view import InscripcionVoluntarioView, AdmisionVoluntariosView
from views.actividades_view import GestionActividadesView, AsignarVoluntariosView
from views.asistencia_view import ControlAsistenciaView
from views.donaciones_view import GestionDonacionesView
from views.reportes_view import ReportesRendimientoView
from views.portal_voluntario_view import MisActividadesView, MiHistorialHorasView
from views.auditoria_view import AuditoriaAccesosView


class MainWindow(tb.Frame):
    """Ventana principal con barra de navegación superior y paleta institucional."""

    def __init__(self, master, sesion: dict, on_logout):
        super().__init__(master)
        self.master = master
        self.sesion = sesion
        self.on_logout = on_logout
        self.botones_menu = {}
        self.opcion_actual = ""
        self.lbl_strikes = None

        try:
            self.master.state("zoomed")
        except Exception:
            pass

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()

    def _construir_ui(self):
        # =====================================================================
        # 1. FRANJA SUPERIOR INSTITUCIONAL (NEGRO + ACENTO ROJO)
        # =====================================================================
        tk.Frame(self, bg=PALETTE["rojo"], height=4).pack(fill="x")

        top_header = tk.Frame(self, bg=PALETTE["negro"], padx=20, pady=6)
        top_header.pack(fill="x")

        # Marca izquierda: Logo + Título
        brand_box = tk.Frame(top_header, bg=PALETTE["negro"])
        brand_box.pack(side="left")

        SaveTheChildrenLogo(brand_box, size=38, bg=PALETTE["negro"]).pack(side="left", padx=(0, 12))

        title_stack = tk.Frame(brand_box, bg=PALETTE["negro"])
        title_stack.pack(side="left")

        tk.Label(
            title_stack,
            text="Save the Children Bolivia",
            font=("Segoe UI", 13, "bold"),
            bg=PALETTE["negro"],
            fg=PALETTE["blanco"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            title_stack,
            text="Sistema de Gestión de Voluntariado y Operaciones",
            font=("Segoe UI", 8),
            bg=PALETTE["negro"],
            fg=PALETTE["plomo_claro"],
            anchor="w"
        ).pack(fill="x")

        # Controles derechos: Tarjeta de Usuario + Cerrar Sesión
        right_box = tk.Frame(top_header, bg=PALETTE["negro"])
        right_box.pack(side="right")

        user_pill = tk.Frame(right_box, bg=PALETTE["negro_suave"], padx=12, pady=6)
        user_pill.pack(side="left", padx=(0, 12))

        tk.Label(
            user_pill,
            text=f"👤  {self.sesion['nombre_mostrar']}",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["negro_suave"],
            fg=PALETTE["blanco"]
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            user_pill,
            text=self.sesion["rol"].upper(),
            font=("Segoe UI", 7, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            padx=8,
            pady=2
        ).pack(side="left")

        if self.sesion.get("rol") == "Voluntario":
            strikes = int(self.sesion.get("strikes_actuales", 0))
            bg_strike = PALETTE["rojo_oscuro"] if strikes >= 3 else PALETTE["plomo_texto"]
            self.lbl_strikes = tk.Label(
                user_pill,
                text=f"⚡ {strikes}/5 STRIKES",
                font=("Segoe UI", 7, "bold"),
                bg=bg_strike,
                fg=PALETTE["blanco"],
                padx=8,
                pady=2
            )
            self.lbl_strikes.pack(side="left", padx=(6, 0))

        btn_salir = tk.Button(
            right_box,
            text="Cerrar Sesión",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["negro_suave"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            command=self._cerrar_sesion
        )
        btn_salir.pack(side="left")
        btn_salir.bind("<Enter>", lambda _e: btn_salir.config(bg=PALETTE["rojo"]))
        btn_salir.bind("<Leave>", lambda _e: btn_salir.config(bg=PALETTE["negro_suave"]))

        # =====================================================================
        # 2. BARRA HORIZONTAL DE PESTAÑAS
        # =====================================================================
        nav_bar = tk.Frame(self, bg=PALETTE["blanco"], padx=16, pady=4)
        nav_bar.pack(fill="x")

        tk.Frame(self, bg=PALETTE["plomo_borde"], height=1).pack(fill="x")

        opciones_menu = self._obtener_opciones_por_rol(self.sesion["rol"])

        for texto_btn in opciones_menu:
            btn = tk.Button(
                nav_bar,
                text=texto_btn,
                font=("Segoe UI", 9),
                bg=PALETTE["blanco"],
                fg=PALETTE["negro"],
                activebackground=PALETTE["rojo_hover"],
                activeforeground=PALETTE["blanco"],
                bd=0,
                padx=9,
                pady=6,
                cursor="hand2",
                command=lambda t=texto_btn: self._navegar(t)
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Enter>", lambda _e, t=texto_btn: self._on_tab_hover(t, True))
            btn.bind("<Leave>", lambda _e, t=texto_btn: self._on_tab_hover(t, False))
            self.botones_menu[texto_btn] = btn

        # =====================================================================
        # 3. ÁREA CENTRAL DE CONTENIDO
        # =====================================================================
        self.area_contenido = tk.Frame(self, bg=PALETTE["plomo_fondo"], padx=18, pady=10)
        self.area_contenido.pack(fill=BOTH, expand=True)

        self._navegar(opciones_menu[0])

    def _refrescar_badge_strikes(self):
        if self.lbl_strikes is not None:
            strikes = int(self.sesion.get("strikes_actuales", 0))
            bg_strike = PALETTE["rojo_oscuro"] if strikes >= 3 else PALETTE["plomo_texto"]
            self.lbl_strikes.config(text=f"⚡ {strikes}/5 STRIKES", bg=bg_strike)

    def _obtener_opciones_por_rol(self, rol: str) -> list[str]:
        if rol == "Administrador":
            return [
                "📊  Panel General",
                "📝  Inscribir Postulante",
                "✅  Admisión Voluntarios",
                "📅  Gestión Actividades",
                "👥  Asignar Voluntarios",
                "📋  Control Asistencia",
                "🎁  Gestión Donaciones",
                "📈  Reportes y Rendimiento",
                "🛡️  Auditoría Accesos"
            ]
        return [
            "📅  Mis Actividades Asignadas",
            "⏱  Mi Historial de Horas"
        ]

    def _on_tab_hover(self, opcion: str, entrando: bool):
        if opcion == self.opcion_actual:
            return
        btn = self.botones_menu.get(opcion)
        if btn:
            btn.config(bg=PALETTE["plomo_fondo"] if entrando else PALETTE["blanco"])

    def _resaltar_boton_activo(self, opcion_activa: str):
        self.opcion_actual = opcion_activa
        for texto, btn in self.botones_menu.items():
            if texto == opcion_activa:
                btn.config(
                    bg=PALETTE["rojo"],
                    fg=PALETTE["blanco"],
                    font=("Segoe UI", 9, "bold")
                )
            else:
                btn.config(
                    bg=PALETTE["blanco"],
                    fg=PALETTE["negro"],
                    font=("Segoe UI", 9)
                )

    def _navegar(self, opcion: str):
        self._resaltar_boton_activo(opcion)
        self._refrescar_badge_strikes()

        for w in self.area_contenido.winfo_children():
            w.destroy()

        if "Panel General" in opcion:
            DashboardView(self.area_contenido, self.sesion, on_navegar=self._navegar)
        elif "Inscribir Postulante" in opcion:
            InscripcionVoluntarioView(self.area_contenido, self.sesion)
        elif "Admisión Voluntarios" in opcion:
            AdmisionVoluntariosView(self.area_contenido, self.sesion)
        elif "Gestión Actividades" in opcion:
            GestionActividadesView(self.area_contenido, self.sesion)
        elif "Asignar Voluntarios" in opcion:
            AsignarVoluntariosView(self.area_contenido, self.sesion)
        elif "Control Asistencia" in opcion:
            ControlAsistenciaView(self.area_contenido, self.sesion)
        elif "Gestión Donaciones" in opcion:
            GestionDonacionesView(self.area_contenido, self.sesion)
        elif "Reportes y Rendimiento" in opcion:
            ReportesRendimientoView(self.area_contenido, self.sesion)
        elif "Auditoría Accesos" in opcion:
            AuditoriaAccesosView(self.area_contenido, self.sesion)
        elif "Mis Actividades Asignadas" in opcion:
            MisActividadesView(self.area_contenido, self.sesion)
        elif "Mi Historial de Horas" in opcion:
            MiHistorialHorasView(self.area_contenido, self.sesion)

    def _cerrar_sesion(self):
        AuthController.cerrar_sesion()
        self.on_logout()