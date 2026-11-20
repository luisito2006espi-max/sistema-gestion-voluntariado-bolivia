import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.auth_controller import AuthController


class AuditoriaAccesosView(tb.Frame):
    """Vista de Auditoría de Inicios de Sesión para el Administrador."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = AuthController()

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_logs()

    def _construir_ui(self):
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 14))

        titulos = tk.Frame(header, bg="#FFF5F5")
        titulos.pack(side="left")

        tk.Label(
            titulos,
            text="Auditoría y Trazabilidad de Accesos",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            titulos,
            text="Registro histórico de inicios de sesión capturado automáticamente por MySQL.",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w", pady=(2, 0))

        tb.Button(
            header,
            text="↻ Actualizar Registro",
            bootstyle="danger-outline",
            command=self._cargar_logs
        ).pack(side="right", ipady=5)

        card = tk.Frame(self, bg="#FFFFFF", padx=18, pady=16)
        card.pack(fill=BOTH, expand=True)

        cols = ("fecha_hora", "usuario", "rol", "persona")
        self.tabla = tb.Treeview(card, columns=cols, show="headings", bootstyle="danger")
        self.tabla.heading("fecha_hora", text="Fecha y Hora de Acceso")
        self.tabla.heading("usuario", text="Cuenta de Usuario")
        self.tabla.heading("rol", text="Rol del Sistema")
        self.tabla.heading("persona", text="Usuario / Voluntario")

        self.tabla.column("fecha_hora", width=180, anchor="center")
        self.tabla.column("usuario", width=160, anchor="center")
        self.tabla.column("rol", width=140, anchor="center")
        self.tabla.column("persona", width=250, anchor="w")

        self.tabla.pack(fill=BOTH, expand=True)

    def _cargar_logs(self):
        for w in self.tabla.get_children():
            self.tabla.delete(w)

        try:
            logs = self.controller.obtener_historial_accesos(200)
            for item in logs:
                fh = item["fecha_hora_acceso"]
                fh_str = fh.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fh, "strftime") else str(fh)
                self.tabla.insert("", tk.END, values=(
                    fh_str,
                    item["usuario"],
                    item["rol"],
                    item["persona"]
                ))
        except Exception as e:
            messagebox.showerror("Error de Auditoría", str(e))