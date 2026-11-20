import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.auth_controller import AuthController


class LoginView(tb.Frame):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success
        self.auth_controller = AuthController()
        self.mostrar_pass = False

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()

    def _construir_ui(self):
        self.columnconfigure(0, weight=46, uniform="grupo")
        self.columnconfigure(1, weight=54, uniform="grupo")
        self.rowconfigure(0, weight=1)

        self._construir_panel_izquierdo()
        self._construir_panel_derecho()

    def _construir_panel_izquierdo(self):
        """Panel de marca Bolivia Kindness Bridge en paleta Rojo Solidario."""
        panel_izq = tk.Frame(self, bg="#7F1D1D", padx=36, pady=36)
        panel_izq.grid(row=0, column=0, sticky="nsew")

        canvas = tk.Canvas(
            panel_izq, width=96, height=96,
            bg="#7F1D1D", highlightthickness=0
        )
        canvas.pack(anchor="w", pady=(8, 16))
        self._dibujar_emblema_puente(canvas)

        tk.Label(
            panel_izq,
            text="Save the Children\nBolivia",
            font=("Segoe UI", 24, "bold"),
            fg="#FFFFFF",
            bg="#7F1D1D",
            justify="left"
        ).pack(anchor="w")

        tk.Label(
            panel_izq,
            text="Conectando solidaridad, voluntarios y ayuda\ncomunitaria con transparencia y trazabilidad.",
            font=("Segoe UI", 10),
            fg="#FECACA",
            bg="#7F1D1D",
            justify="left"
        ).pack(anchor="w", pady=(10, 26))

        modulos = [
            ("👥", "Gestión de Voluntariado", "Inscripción, evaluación y admisión de postulantes."),
            ("📅", "Actividades y Asistencia", "Asignación por cupos y control de horas cumplidas."),
            ("🎁", "Donaciones Trazables", "Registro monetario y de insumos en especie.")
        ]

        for icono, titulo, desc in modulos:
            card = tk.Frame(panel_izq, bg="#991B1B", padx=14, pady=10)
            card.pack(fill="x", pady=6)

            tk.Label(
                card, text=icono, font=("Segoe UI", 14),
                bg="#991B1B", fg="#FBBF24"
            ).pack(side="left", padx=(0, 12))

            texto_frame = tk.Frame(card, bg="#991B1B")
            texto_frame.pack(side="left", fill="x", expand=True)

            tk.Label(
                texto_frame, text=titulo, font=("Segoe UI", 10, "bold"),
                bg="#991B1B", fg="#FFFFFF", anchor="w"
            ).pack(fill="x")

            tk.Label(
                texto_frame, text=desc, font=("Segoe UI", 9),
                bg="#991B1B", fg="#FEE2E2", anchor="w"
            ).pack(fill="x")

        tk.Label(
            panel_izq,
            text="◆ Sistema Integral de Gestión • Arquitectura 3FN",
            font=("Segoe UI", 9),
            fg="#FCA5A5",
            bg="#7F1D1D"
        ).pack(side="bottom", anchor="w", pady=(16, 0))

    def _dibujar_emblema_puente(self, canvas: tk.Canvas):
        """Dibuja un ícono geométrico limpio (círculo, arco de puente y sol)."""
        canvas.create_oval(4, 4, 92, 92, fill="#991B1B", outline="#F87171", width=2)
        canvas.create_oval(38, 20, 58, 40, fill="#FBBF24", outline="")
        canvas.create_arc(
            18, 38, 78, 88, start=0, extent=180,
            style="arc", outline="#FFFFFF", width=3.5
        )
        canvas.create_line(14, 62, 82, 62, fill="#FCA5A5", width=3)
        canvas.create_line(28, 52, 28, 72, fill="#FFFFFF", width=2.5)
        canvas.create_line(68, 52, 68, 72, fill="#FFFFFF", width=2.5)

    def _construir_panel_derecho(self):
        """Panel derecho con el formulario de inicio de sesión."""
        panel_der = tk.Frame(self, bg="#FFFFFF", padx=48, pady=40)
        panel_der.grid(row=0, column=1, sticky="nsew")

        contenedor = tk.Frame(panel_der, bg="#FFFFFF")
        contenedor.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92)

        badge = tk.Label(
            contenedor,
            text="  PORTAL DE ACCESO  ",
            font=("Segoe UI", 8, "bold"),
            bg="#FEF2F2",
            fg="#B91C1C",
            pady=4
        )
        badge.pack(anchor="w", pady=(0, 10))

        tk.Label(
            contenedor,
            text="Iniciar Sesión",
            font=("Segoe UI", 22, "bold"),
            bg="#FFFFFF",
            fg="#0F172A"
        ).pack(anchor="w")

        tk.Label(
            contenedor,
            text="Ingresa tus credenciales asignadas para acceder a tu panel.",
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#64748B"
        ).pack(anchor="w", pady=(4, 18))

        roles_frame = tk.Frame(contenedor, bg="#FFF5F5", padx=10, pady=8)
        roles_frame.pack(fill="x", pady=(0, 20))
        tk.Label(
            roles_frame,
            text="Perfiles:  ● Administrador   ● Voluntario",
            font=("Segoe UI", 9),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            contenedor,
            text="Usuario",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(anchor="w", pady=(0, 4))

        self.entry_usuario = tb.Entry(
            contenedor,
            font=("Segoe UI", 11),
            bootstyle="danger"
        )
        self.entry_usuario.pack(fill="x", ipady=5, pady=(0, 14))
        self.entry_usuario.focus_set()

        tk.Label(
            contenedor,
            text="Contraseña",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(anchor="w", pady=(0, 4))

        pass_frame = tk.Frame(contenedor, bg="#FFFFFF")
        pass_frame.pack(fill="x", pady=(0, 14))

        self.entry_password = tb.Entry(
            pass_frame,
            font=("Segoe UI", 11),
            show="•",
            bootstyle="danger"
        )
        self.entry_password.pack(side="left", fill="x", expand=True, ipady=5)

        self.btn_ver_pass = tb.Button(
            pass_frame,
            text="👁",
            width=3,
            bootstyle="secondary-outline",
            command=self._alternar_visibilidad_password
        )
        self.btn_ver_pass.pack(side="right", padx=(6, 0), ipady=4)

        self.lbl_mensaje = tk.Label(
            contenedor,
            text="",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#DC2626",
            wraplength=360,
            justify="left"
        )
        self.lbl_mensaje.pack(fill="x", pady=(2, 12))

        self.btn_ingresar = tb.Button(
            contenedor,
            text="Ingresar al Sistema  →",
            bootstyle="danger",
            command=self._procesar_login
        )
        self.btn_ingresar.pack(fill="x", ipady=7)

        self.entry_usuario.bind("<Return>", lambda e: self.entry_password.focus_set())
        self.entry_password.bind("<Return>", lambda e: self._procesar_login())

    def _alternar_visibilidad_password(self):
        self.mostrar_pass = not self.mostrar_pass
        if self.mostrar_pass:
            self.entry_password.config(show="")
            self.btn_ver_pass.config(text="🙈")
        else:
            self.entry_password.config(show="•")
            self.btn_ver_pass.config(text="👁")

    def _procesar_login(self):
        usuario = self.entry_usuario.get()
        password = self.entry_password.get()

        self.btn_ingresar.config(state="disabled", text="Verificando...")
        self.update_idletasks()

        exito, mensaje, sesion = self.auth_controller.iniciar_sesion(usuario, password)

        self.btn_ingresar.config(state="normal", text="Ingresar al Sistema  →")

        if not exito:
            self.lbl_mensaje.config(text=f"⚠ {mensaje}", fg="#DC2626")
            self.entry_password.delete(0, tk.END)
            self.entry_password.focus_set()
            return

        self.lbl_mensaje.config(text=f"✓ {mensaje}", fg="#B91C1C")
        self.after(250, lambda: self.on_login_success(sesion))