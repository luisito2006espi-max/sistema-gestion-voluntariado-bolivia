import hashlib
from mysql.connector import Error
from config.database import Database


class AuthModel:
    def __init__(self):
        self.db = Database()

    @staticmethod
    def hashear_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _columnas_tabla(self, cursor, tabla: str) -> set[str]:
        cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        return {
            (f["Field"] if isinstance(f, dict) else f[0])
            for f in cursor.fetchall()
        }

    def autenticar_usuario(self, usuario: str, password: str) -> dict | None:
        """
        Valida credenciales en USUARIO + ROL.
        Si el rol es Voluntario, verifica que su estado en VOLUNTARIO no sea 'Inactivo'.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_usr = self._columnas_tabla(cursor, "USUARIO")
            col_pass = "password_hash" if "password_hash" in cols_usr else (
                "contrasena" if "contrasena" in cols_usr else "password"
            )
            select_activo = "u.activo," if "activo" in cols_usr else "1 AS activo,"

            cursor.execute(
                f"""
                SELECT 
                    u.id_usuario,
                    u.usuario,
                    u.{col_pass} AS hash_guardado,
                    {select_activo}
                    r.nombre AS rol
                FROM USUARIO u
                INNER JOIN ROL r ON u.id_rol = r.id_rol
                WHERE u.usuario = %s
                LIMIT 1
                """,
                (usuario.strip(),)
            )
            fila = cursor.fetchone()
            if not fila:
                return None

            if int(fila["activo"]) == 0:
                raise ValueError("Esta cuenta de usuario se encuentra desactivada.")

            hash_ingresado = self.hashear_password(password)
            if fila["hash_guardado"] not in (hash_ingresado, password):
                return None

            nombre_mostrar = fila["usuario"]

            # Si es Voluntario, validar estado activo y obtener nombre real
            if fila["rol"] == "Voluntario":
                cursor.execute(
                    """
                    SELECT 
                        CONCAT_WS(' ', v.nombres, v.apellido_paterno) AS nombre_corto,
                        ev.nombre AS estado_vol
                    FROM VOLUNTARIO v
                    INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                    WHERE v.id_usuario = %s
                    LIMIT 1
                    """,
                    (fila["id_usuario"],)
                )
                vol = cursor.fetchone()
                if vol:
                    if vol["estado_vol"] == "Inactivo":
                        raise ValueError("Tu cuenta de voluntario ha sido desactivada por el Administrador.")
                    nombre_mostrar = vol["nombre_corto"]

            return {
                "id_usuario": fila["id_usuario"],
                "usuario": fila["usuario"],
                "rol": fila["rol"],
                "nombre_mostrar": nombre_mostrar
            }
        except Error as e:
            raise RuntimeError(f"Error de conexión al validar usuario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def registrar_auditoria_acceso(self, id_usuario: int):
        """Flujo 1: Registra el acceso en AUDITORIA_ACCESO dejando que MySQL ponga fecha_hora_acceso."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO AUDITORIA_ACCESO (id_usuario) VALUES (%s)",
                (id_usuario,)
            )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"Error al registrar auditoría de acceso: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_auditoria_accesos(self, limite: int = 200) -> list[dict]:
        """Consulta el historial de inicios de sesión para el panel del Administrador."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT 
                    aa.fecha_hora_acceso,
                    u.usuario,
                    r.nombre AS rol,
                    COALESCE(
                        CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno),
                        u.usuario
                    ) AS persona
                FROM AUDITORIA_ACCESO aa
                INNER JOIN USUARIO u ON aa.id_usuario = u.id_usuario
                INNER JOIN ROL r ON u.id_rol = r.id_rol
                LEFT JOIN VOLUNTARIO v ON v.id_usuario = u.id_usuario
                ORDER BY aa.fecha_hora_acceso DESC
                LIMIT %s
                """,
                (limite,)
            )
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar auditoría de accesos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()