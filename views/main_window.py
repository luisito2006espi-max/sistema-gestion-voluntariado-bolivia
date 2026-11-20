import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.auth_controller import AuthController
from views.dashboard_view import DashboardView
from views.voluntarios_view import InscripcionVoluntarioView, AdmisionVoluntariosView
from views.actividades_view import GestionActividadesView, AsignarVoluntariosView
from views.asistencia_view import ControlAsistenciaView
from views.donaciones_view import GestionDonacionesView
from views.reportes_view import ReportesRendimientoView
from views.portal_voluntario_view import MisActividadesView, MiHistorialHorasView
from views.auditoria_view import AuditoriaAccesosView


class MainWindow(tb.Frame):
    def __init__(self, master, sesion: dict, on_logout):
        super().__init__(master)
        self.master = master
        self.sesion = sesion
        self.on_logout = on_logout
        self.botones_menu = {}

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()

    def _construir_ui(self):
        sidebar = tk.Frame(self, bg="#7F1D1D", width=245, padx=16, pady=24)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Save the Children\nBolivia",
            font=("Segoe UI", 15, "bold"),
            bg="#7F1D1D",
            fg="#FFFFFF",
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        user_card = tk.Frame(sidebar, bg="#991B1B", padx=12, pady=10)
        user_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            user_card,
            text=self.sesion["nombre_mostrar"],
            font=("Segoe UI", 10, "bold"),
            bg="#991B1B",
            fg="#FFFFFF",
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            user_card,
            text=f"Rol: {self.sesion['rol']}",
            font=("Segoe UI", 9),
            bg="#991B1B",
            fg="#FECACA",
            anchor="w"
        ).pack(fill="x")

        rol = self.sesion["rol"]
        opciones_menu = self._obtener_opciones_por_rol(rol)

        for texto_btn in opciones_menu:
            btn = tk.Button(
                sidebar,
                text=texto_btn,
                font=("Segoe UI", 10),
                bg="#7F1D1D",
                fg="#FEF2F2",
                activebackground="#B91C1C",
                activeforeground="#FFFFFF",
                bd=0,
                anchor="w",
                padx=10,
                pady=8,
                cursor="hand2",
                command=lambda t=texto_btn: self._navegar(t)
            )
            btn.pack(fill="x", pady=1)
            self.botones_menu[texto_btn] = btn

        tb.Button(
            sidebar,
            text="Cerrar Sesión",
            bootstyle="light-outline",
            command=self._cerrar_sesion
        ).pack(side="bottom", fill="x")

        self.area_contenido = tk.Frame(self, bg="#FFF5F5", padx=28, pady=22)
        self.area_contenido.pack(side="right", fill=BOTH, expand=True)

        primera_opcion = opciones_menu[0]
        self._navegar(primera_opcion)

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

    def _resaltar_boton_activo(self, opcion_activa: str):
        for texto, btn in self.botones_menu.items():
            if texto == opcion_activa:
                btn.config(bg="#B91C1C", font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg="#7F1D1D", font=("Segoe UI", 10))

    def _navegar(self, opcion: str):
        self._resaltar_boton_activo(opcion)

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