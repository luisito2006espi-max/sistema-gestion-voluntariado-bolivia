import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.auth_controller import AuthController
from views.ui_components import PALETTE, RoundedCard, SaveTheChildrenLogo


class LoginView(tb.Frame):
    """Pantalla de acceso institucional minimalista con paleta Rojo, Blanco, Negro y Plomo."""

    def __init__(self, master, on_login_success, on_abrir_donacion=None):
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success
        self.on_abrir_donacion = on_abrir_donacion
        self.auth_controller = AuthController()
        self.mostrar_pass = False
        self.info_visible = False
        self.voluntario_info_visible = False

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()

    def _construir_ui(self):
        # Lienzo principal en rojo institucional con ondas geométricas sutiles
        self.bg_canvas = tk.Canvas(
            self,
            bg=PALETTE["rojo_oscuro"],
            highlightthickness=0,
            bd=0
        )
        self.bg_canvas.pack(fill=BOTH, expand=True)
        self.bg_canvas.bind("<Configure>", self._dibujar_fondo)

        # =====================================================================
        # TARJETA CENTRAL CURVA DE INICIO DE SESIÓN
        # =====================================================================
        self.login_card = RoundedCard(
            self.bg_canvas,
            radius=24,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=34,
            pady=26,
            canvas_bg=PALETTE["rojo_oscuro"],
            width=430
        )
        self.login_card.place(relx=0.5, rely=0.5, anchor="center")

        body = self.login_card.body

        # Logo institucional
        logo_wrap = tk.Frame(body, bg=PALETTE["blanco"])
        logo_wrap.pack(pady=(0, 8))
        SaveTheChildrenLogo(logo_wrap, size=58, bg=PALETTE["blanco"]).pack()

        # Título principal en Negro
        tk.Label(
            body,
            text="Save the Children Bolivia",
            font=("Segoe UI", 19, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"]
        ).pack()

        # Descripción breve visible
        tk.Label(
            body,
            text="Sistema de gestión de voluntariado, actividades comunitarias y donaciones.",
            font=("Segoe UI", 10),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            wraplength=350,
            justify="center"
        ).pack(pady=(4, 14))

        # Separador en plomo claro
        tk.Frame(body, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(0, 14))

        # Campo: Usuario
        tk.Label(
            body,
            text="Usuario",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.entry_usuario = tb.Entry(body, font=("Segoe UI", 11))
        self.entry_usuario.pack(fill="x", ipady=5, pady=(0, 12))
        self.entry_usuario.focus_set()
        self.entry_usuario.bind("<Return>", lambda _e: self.entry_password.focus_set())

        # Campo: Contraseña + botón ver/ocultar
        tk.Label(
            body,
            text="Contraseña",
            font=("Segoe UI", 10, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        pass_row = tk.Frame(body, bg=PALETTE["blanco"])
        pass_row.pack(fill="x", pady=(0, 6))

        self.entry_password = tb.Entry(pass_row, font=("Segoe UI", 11), show="•")
        self.entry_password.pack(side="left", fill="x", expand=True, ipady=5)
        self.entry_password.bind("<Return>", lambda _e: self._iniciar_sesion())

        self.btn_ver = tk.Button(
            pass_row,
            text="👁",
            font=("Segoe UI", 10),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            activebackground=PALETTE["plomo_borde"],
            bd=0,
            padx=10,
            cursor="hand2",
            command=self._alternar_password
        )
        self.btn_ver.pack(side="right", fill="y", padx=(6, 0))

        # Mensaje de error discreto
        self.lbl_error = tk.Label(
            body,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["rojo"],
            wraplength=350,
            justify="center"
        )
        self.lbl_error.pack(fill="x", pady=(2, 8))

        # Botón principal en Rojo Institucional
        self.btn_ingresar = tk.Button(
            body,
            text="Iniciar Sesión",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=10,
            cursor="hand2",
            command=self._iniciar_sesion
        )
        self.btn_ingresar.pack(fill="x")
        self.btn_ingresar.bind("<Enter>", lambda _e: self.btn_ingresar.config(bg=PALETTE["rojo_hover"]))
        self.btn_ingresar.bind("<Leave>", lambda _e: self.btn_ingresar.config(bg=PALETTE["rojo"]))

        # =====================================================================
        # ACCESOS PÚBLICOS DISCRETOS (DONAR / SER VOLUNTARIO)
        # =====================================================================
        tk.Frame(body, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(14, 10))

        enlaces_row = tk.Frame(body, bg=PALETTE["blanco"])
        enlaces_row.pack(fill="x")

        self.btn_donar = tk.Button(
            enlaces_row,
            text="❤ ¿Deseas donar?",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["rojo"],
            activebackground=PALETTE["rojo_suave"],
            activeforeground=PALETTE["rojo_oscuro"],
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._abrir_donacion
        )
        self.btn_donar.pack(side="left")
        self.btn_donar.bind(
            "<Enter>",
            lambda _e: self.btn_donar.config(bg=PALETTE["rojo_suave"], fg=PALETTE["rojo_oscuro"])
        )
        self.btn_donar.bind(
            "<Leave>",
            lambda _e: self.btn_donar.config(bg=PALETTE["blanco"], fg=PALETTE["rojo"])
        )

        self.btn_ser_voluntario = tk.Button(
            enlaces_row,
            text="¿Quieres ser voluntario?",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            activebackground=PALETTE["plomo_fondo"],
            activeforeground=PALETTE["negro"],
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._alternar_panel_voluntario
        )
        self.btn_ser_voluntario.pack(side="right")
        self.btn_ser_voluntario.bind(
            "<Enter>",
            lambda _e: self.btn_ser_voluntario.config(bg=PALETTE["plomo_fondo"], fg=PALETTE["negro"])
        )
        self.btn_ser_voluntario.bind(
            "<Leave>",
            lambda _e: self.btn_ser_voluntario.config(bg=PALETTE["blanco"], fg=PALETTE["plomo_texto"])
        )

        # =====================================================================
        # ÍCONO CIRCULAR "i" EN LA ESQUINA INFERIOR DERECHA
        # =====================================================================
        self.btn_info = tk.Canvas(
            self.bg_canvas,
            width=46,
            height=46,
            bg=PALETTE["rojo_oscuro"],
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        self.btn_info.place(relx=1.0, rely=1.0, x=-24, y=-24, anchor="se")
        self._dibujar_boton_info(hover=False)
        self.btn_info.bind("<Button-1>", lambda _e: self._alternar_panel_info())
        self.btn_info.bind("<Enter>", lambda _e: self._dibujar_boton_info(hover=True))
        self.btn_info.bind("<Leave>", lambda _e: self._dibujar_boton_info(hover=False))

        # Panel flotante curvo de información del sistema ("i")
        self.info_card = RoundedCard(
            self.bg_canvas,
            radius=20,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=22,
            pady=20,
            canvas_bg=PALETTE["rojo_oscuro"],
            width=360
        )
        self._construir_contenido_info()

        # Panel informativo curvo para "¿Quieres ser voluntario?"
        self.voluntario_card = RoundedCard(
            self.bg_canvas,
            radius=22,
            bg_color=PALETTE["blanco"],
            border_color=PALETTE["plomo_borde"],
            padx=26,
            pady=22,
            canvas_bg=PALETTE["rojo_oscuro"],
            width=640
        )
        self._construir_contenido_voluntario()

    def _dibujar_fondo(self, event):
        w, h = event.width, event.height
        self.bg_canvas.delete("bg_decor")
        self.bg_canvas.create_polygon(
            0, 0,
            w, 0,
            w, h * 0.42,
            0, h * 0.68,
            fill=PALETTE["rojo"],
            outline="",
            tags="bg_decor"
        )
        self.bg_canvas.create_oval(
            -140, -140, 260, 260,
            fill=PALETTE["rojo_oscuro"],
            outline="",
            tags="bg_decor"
        )
        self.bg_canvas.tag_lower("bg_decor")

    def _dibujar_boton_info(self, hover: bool):
        self.btn_info.delete("all")
        fill_c = PALETTE["plomo_fondo"] if hover else PALETTE["blanco"]
        self.btn_info.create_oval(3, 3, 43, 43, fill=fill_c, outline=PALETTE["plomo_borde"], width=1)
        self.btn_info.create_text(
            23, 23,
            text="i",
            font=("Georgia", 16, "bold italic"),
            fill=PALETTE["rojo"]
        )

    def _construir_contenido_info(self):
        b = self.info_card.body

        top = tk.Frame(b, bg=PALETTE["blanco"])
        top.pack(fill="x", pady=(0, 8))

        SaveTheChildrenLogo(top, size=34, bg=PALETTE["blanco"]).pack(side="left", padx=(0, 10))

        tit_box = tk.Frame(top, bg=PALETTE["blanco"])
        tit_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            tit_box,
            text="Save the Children Bolivia",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            tit_box,
            text="Acerca del Sistema  •  Versión 1.3",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["rojo"],
            anchor="w"
        ).pack(fill="x")

        tk.Button(
            top,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            bd=0,
            padx=7,
            pady=2,
            cursor="hand2",
            command=self._alternar_panel_info
        ).pack(side="right", anchor="n")

        tk.Frame(b, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(4, 10))

        tk.Label(
            b,
            text=(
                "Plataforma institucional diseñada para coordinar el ciclo completo de "
                "voluntariado en Bolivia: evaluación y admisión de postulantes, planificación "
                "de jornadas comunitarias, control de asistencia y trazabilidad de donaciones."
            ),
            font=("Segoe UI", 9),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            wraplength=310,
            justify="left"
        ).pack(fill="x", pady=(0, 10))

        badge = tk.Frame(b, bg=PALETTE["plomo_fondo"], padx=10, pady=7)
        badge.pack(fill="x")

        tk.Label(
            badge,
            text="Acceso exclusivo para Administradores y Voluntarios habilitados.",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            wraplength=290,
            justify="left"
        ).pack(anchor="w")

    def _construir_contenido_voluntario(self):
        """Panel informativo textual con la estética institucional de la plantilla."""
        b = self.voluntario_card.body

        # Encabezado idéntico al estilo de info_card
        top = tk.Frame(b, bg=PALETTE["blanco"])
        top.pack(fill="x", pady=(0, 8))

        SaveTheChildrenLogo(top, size=38, bg=PALETTE["blanco"]).pack(side="left", padx=(0, 12))

        tit_box = tk.Frame(top, bg=PALETTE["blanco"])
        tit_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            tit_box,
            text="Programa de Voluntariado — Save the Children Bolivia",
            font=("Segoe UI", 12, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            tit_box,
            text="Guía de Postulación, Requisitos Documentales y Compromiso",
            font=("Segoe UI", 8, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["rojo"],
            anchor="w"
        ).pack(fill="x")

        tk.Button(
            top,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["plomo_fondo"],
            fg=PALETTE["negro"],
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self._alternar_panel_voluntario
        ).pack(side="right", anchor="n")

        tk.Frame(b, bg=PALETTE["plomo_borde"], height=1).pack(fill="x", pady=(4, 10))

        # Paso 1: Cómo iniciar la postulación
        tk.Label(
            b,
            text="1. ¿Cómo postular?",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            b,
            text=(
                "Acércate a nuestras oficinas de Save the Children Bolivia o comunícate por vía "
                "telefónica. Un administrador registrará tus datos personales en el sistema y "
                "verificará de forma presencial la entrega de tus respaldos físicos (no se suben "
                "archivos digitales al sistema)."
            ),
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            wraplength=580,
            justify="left"
        ).pack(fill="x", pady=(2, 8))

        # Paso 2: Los 5 requisitos obligatorios
        tk.Label(
            b,
            text="2. Documentación física requerida para la admisión:",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x", pady=(0, 3))

        requisitos = [
            "• Fotocopia de Cédula de Identidad (CI): Documento vigente y legible.",
            "• Formulario de Solicitud: Validación de datos personales y declaración de disponibilidad horaria (Mañanas, Tardes, Fines de Semana o Tiempo Completo).",
            "• Acuerdo de Voluntario: Aceptación expresa del código de conducta y políticas de protección infantil de Save the Children.",
            "• Certificado de Antecedentes: Presentación obligatoria del certificado vigente y verificación de no contar con antecedentes.",
            "• Currículum Vitae (CV): Respaldo de formación académica (colegio, estudiante universitario/técnico o título profesional) y situación laboral actual."
        ]

        req_box = tk.Frame(b, bg=PALETTE["plomo_fondo"], padx=12, pady=8)
        req_box.pack(fill="x", pady=(0, 8))

        for item in requisitos:
            tk.Label(
                req_box,
                text=item,
                font=("Segoe UI", 8),
                bg=PALETTE["plomo_fondo"],
                fg=PALETTE["negro"],
                wraplength=555,
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=1)

        # Paso 3: Reglas de compromiso y sistema de strikes
        tk.Label(
            b,
            text="3. Participación en actividades y sistema de compromiso (5 Strikes):",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["blanco"],
            fg=PALETTE["negro"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            b,
            text=(
                "Una vez admitido, recibirás tus credenciales para ingresar al Portal del Voluntario, "
                "donde deberás confirmar o rechazar las actividades asignadas. Rechazar una actividad "
                "teniendo disponibilidad declarada acumula 1 strike; confirmar asistencia y faltar "
                "acumula 2 strikes. Al llegar a 5 strikes, la cuenta se inactiva de forma irreversible."
            ),
            font=("Segoe UI", 8),
            bg=PALETTE["blanco"],
            fg=PALETTE["plomo_texto"],
            wraplength=580,
            justify="left"
        ).pack(fill="x", pady=(2, 10))

        # Botón de cierre al pie
        btn_cerrar_vol = tk.Button(
            b,
            text="Entendido, volver al inicio de sesión",
            font=("Segoe UI", 9, "bold"),
            bg=PALETTE["rojo"],
            fg=PALETTE["blanco"],
            activebackground=PALETTE["rojo_hover"],
            activeforeground=PALETTE["blanco"],
            bd=0,
            pady=7,
            cursor="hand2",
            command=self._alternar_panel_voluntario
        )
        btn_cerrar_vol.pack(fill="x")

    def _alternar_panel_info(self):
        if self.voluntario_info_visible:
            self.voluntario_info_visible = False
            self.voluntario_card.place_forget()

        self.info_visible = not self.info_visible
        if self.info_visible:
            self.info_card.place(relx=1.0, rely=1.0, x=-24, y=-80, anchor="se")
            tk.Misc.lift(self.info_card)
        else:
            self.info_card.place_forget()

    def _alternar_panel_voluntario(self):
        if self.info_visible:
            self.info_visible = False
            self.info_card.place_forget()

        self.voluntario_info_visible = not self.voluntario_info_visible
        if self.voluntario_info_visible:
            self.voluntario_card.place(relx=0.5, rely=0.5, anchor="center")
            tk.Misc.lift(self.voluntario_card)
        else:
            self.voluntario_card.place_forget()

    def _abrir_donacion(self):
        if callable(self.on_abrir_donacion):
            self.on_abrir_donacion()

    def _alternar_password(self):
        self.mostrar_pass = not self.mostrar_pass
        self.entry_password.config(show="" if self.mostrar_pass else "•")

    def _iniciar_sesion(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        if not usuario or not password:
            self.lbl_error.config(text="Ingresa tu usuario y contraseña para continuar.")
            return

        self.lbl_error.config(text="")
        try:
            if hasattr(self.auth_controller, "iniciar_sesion"):
                resp = self.auth_controller.iniciar_sesion(usuario, password)
            else:
                resp = self.auth_controller.login(usuario, password)

            if isinstance(resp, tuple):
                if len(resp) == 3:
                    exito, mensaje, sesion = resp
                    if exito:
                        self.on_login_success(sesion)
                    else:
                        self.lbl_error.config(text=str(mensaje))
                elif len(resp) == 2:
                    exito, data = resp
                    if exito:
                        self.on_login_success(data)
                    else:
                        self.lbl_error.config(text=str(data))
            elif isinstance(resp, dict):
                self.on_login_success(resp)
            else:
                self.lbl_error.config(text="Credenciales incorrectas.")
        except Exception as e:
            self.lbl_error.config(text=str(e))