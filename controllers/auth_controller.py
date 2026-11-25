from models.auth_model import AuthModel


class AuthController:
    sesion_activa: dict | None = None

    def __init__(self):
        self.model = AuthModel()

    def iniciar_sesion(self, usuario: str, password: str) -> tuple[bool, str, dict | None]:
        if not usuario.strip() or not password.strip():
            return False, "Ingresa tu usuario y contraseña.", None

        try:
            datos_sesion = self.model.autenticar_usuario(usuario, password)
            if not datos_sesion:
                return False, "Usuario o contraseña incorrectos.", None

            self.model.registrar_auditoria_acceso(datos_sesion["id_usuario"])
            AuthController.sesion_activa = datos_sesion
            return True, f"Bienvenido, {datos_sesion['nombre_mostrar']}.", datos_sesion
        except Exception as e:
            return False, str(e), None

    def obtener_historial_accesos(self, limite: int = 200) -> list[dict]:
        return self.model.listar_auditoria_accesos(limite)

    @staticmethod
    def obtener_sesion() -> dict | None:
        return AuthController.sesion_activa

    @staticmethod
    def obtener_id_usuario_activo() -> int:
        if not AuthController.sesion_activa:
            raise RuntimeError("No hay una sesión de usuario activa.")
        return int(AuthController.sesion_activa["id_usuario"])

    @staticmethod
    def cerrar_sesion():
        AuthController.sesion_activa = None