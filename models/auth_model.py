import hashlib
from mysql.connector import Error
from config.database import Database
from utils.security import encriptar_password, verificar_password


class AuthModel:
    def __init__(self):
        self.db = Database()

    @staticmethod
    def hashear_password(password: str) -> str:
        """Delega el cifrado PBKDF2-HMAC-SHA256 a utils/security.py."""
        return encriptar_password(password)

    def autenticar_usuario(self, usuario: str, password: str) -> dict | None:
        """
        Valida credenciales en USUARIO (esquema v1.3 FNBC).
        Si el rol es Voluntario, verifica su estado (Admitido vs Inactivo / Inactivo_Definitivo)
        y recupera su id_voluntario y strikes acumulados para la sesión.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT 
                    id_usuario,
                    usuario,
                    password_hash,
                    rol,
                    activo
                FROM USUARIO
                WHERE usuario = %s
                LIMIT 1
                """,
                (usuario.strip(),)
            )
            fila = cursor.fetchone()
            if not fila:
                return None

            if int(fila["activo"]) == 0:
                raise ValueError("Esta cuenta de usuario se encuentra desactivada.")

            hash_guardado = fila["password_hash"]
            es_valida = verificar_password(password, hash_guardado)
            if not es_valida:
                sha256_legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
                es_valida = (hash_guardado == sha256_legacy)

            if not es_valida:
                return None

            nombre_mostrar = fila["usuario"]
            id_voluntario = None
            strikes_actuales = 0

            if fila["rol"] == "Voluntario":
                cursor.execute(
                    """
                    SELECT 
                        v.id_voluntario,
                        CONCAT_WS(' ', v.nombres, v.apellido_paterno) AS nombre_corto,
                        v.estado AS estado_vol,
                        COALESCE(
                            (SELECT SUM(s.cantidad_strikes)
                             FROM STRIKE_VOLUNTARIO s
                             WHERE s.id_voluntario = v.id_voluntario),
                            0
                        ) AS total_strikes
                    FROM VOLUNTARIO v
                    WHERE v.id_usuario = %s
                    LIMIT 1
                    """,
                    (fila["id_usuario"],)
                )
                vol = cursor.fetchone()
                if not vol:
                    raise ValueError("La cuenta de usuario no está vinculada a ningún voluntario.")

                if vol["estado_vol"] == "Inactivo_Definitivo":
                    raise ValueError(
                        "Tu cuenta fue desactivada de forma irreversible por acumular 5 strikes."
                    )
                if vol["estado_vol"] == "Inactivo":
                    raise ValueError(
                        "Tu cuenta de voluntario ha sido desactivada por el Administrador."
                    )
                if vol["estado_vol"] != "Admitido":
                    raise ValueError(
                        f"Tu estado actual ({vol['estado_vol']}) no permite ingresar al portal."
                    )

                nombre_mostrar = vol["nombre_corto"]
                id_voluntario = vol["id_voluntario"]
                strikes_actuales = int(vol["total_strikes"])

            return {
                "id_usuario": fila["id_usuario"],
                "usuario": fila["usuario"],
                "rol": fila["rol"],
                "nombre_mostrar": nombre_mostrar,
                "id_voluntario": id_voluntario,
                "strikes_actuales": strikes_actuales
            }
        except Error as e:
            raise RuntimeError(f"Error de conexión al validar usuario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def registrar_auditoria_acceso(self, id_usuario: int):
        """Registra el inicio de sesión en AUDITORIA_ACCESO."""
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
                    u.rol,
                    COALESCE(
                        CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno),
                        u.usuario
                    ) AS persona
                FROM AUDITORIA_ACCESO aa
                INNER JOIN USUARIO u ON aa.id_usuario = u.id_usuario
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