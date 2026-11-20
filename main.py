import ttkbootstrap as tb
from views.login_view import LoginView
from views.main_window import MainWindow


class BoliviaKindnessApp:
    def __init__(self):
        self.root = tb.Window(
            title="Save the Childre Bolivia — Gestión de Voluntariado",
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
            on_login_success=self.mostrar_principal
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