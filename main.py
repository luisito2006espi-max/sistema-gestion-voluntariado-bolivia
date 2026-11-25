import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from views.login_view import LoginView
from views.main_window import MainWindow


class BoliviaKindnessApp:
    def __init__(self):
        self.root = tb.Window(
            title="Save the Children Bolivia — Gestión de Voluntariado",
            themename="litera",
            size=(980, 620),
            resizable=(False, False)
        )
        self.root.place_window_center()
        self.vista_actual = None
        self.mostrar_login()

    def _limpiar_ventana(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
            self.vista_actual = None

    def mostrar_login(self):
        self._limpiar_ventana()
        self.root.geometry("980x620")
        self.root.resizable(False, False)
        self.root.place_window_center()
        self.vista_actual = LoginView(
            master=self.root,
            on_login_success=self.mostrar_principal,
            on_abrir_donacion=self.mostrar_autodonacion
        )

    def mostrar_autodonacion(self):
        """Abre el portal público de autodonación (se implementa en la Etapa 3)."""
        try:
            from views.autodonacion_view import AutoDonacionView
        except ImportError:
            Messagebox.show_info(
                "El portal público de autodonación se habilitará en la Etapa 3 de la migración.",
                title="Save the Children Bolivia",
                parent=self.root
            )
            return

        self._limpiar_ventana()
        self.root.geometry("980x660")
        self.root.resizable(False, False)
        self.root.place_window_center()
        self.vista_actual = AutoDonacionView(
            master=self.root,
            on_volver_login=self.mostrar_login
        )

    def mostrar_principal(self, sesion: dict):
        self._limpiar_ventana()
        self.root.geometry("1150x700")
        self.root.resizable(True, True)
        self.root.place_window_center()
        self.vista_actual = MainWindow(
            master=self.root,
            sesion=sesion,
            on_logout=self.mostrar_login
        )

    def ejecutar(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BoliviaKindnessApp()
    app.ejecutar()