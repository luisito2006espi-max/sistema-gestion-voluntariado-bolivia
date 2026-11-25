from mysql.connector import Error
from config.database import Database


class UsuarioModel:
    def __init__(self):
        self.db = Database()

    def buscar_por_username(self, username: str) -> dict | None:
        """
        Obtiene los datos de acceso, el rol (ENUM), el estado y strikes del voluntario asociado.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    u.id_usuario,
                    u.usuario,
                    u.password_hash,
                    u.rol,
                    u.activo,
                    u.fecha_creacion,
                    v.id_voluntario,
                    v.estado AS estado_voluntario,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_voluntario,
                    COALESCE(
                        (SELECT SUM(s.cantidad_strikes)
                         FROM STRIKE_VOLUNTARIO s
                         WHERE s.id_voluntario = v.id_voluntario),
                        0
                    ) AS strikes_actuales
                FROM USUARIO u
                LEFT JOIN VOLUNTARIO v ON v.id_usuario = u.id_usuario
                WHERE u.usuario = %s
                LIMIT 1
            """
            cursor.execute(query, (username.strip(),))
            fila = cursor.fetchone()
            if fila:
                fila["strikes_actuales"] = int(fila["strikes_actuales"] or 0)
            return fila

        except Error as e:
            raise RuntimeError(f"Error de base de datos al consultar usuario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def actualizar_estado_usuario(self, id_usuario: int, activo: int) -> None:
        """
        Activa o desactiva una cuenta en USUARIO.
        Impide reactivar usuarios vinculados a un voluntario en 'Inactivo_Definitivo'.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            if int(activo) == 1:
                cursor.execute(
                    "SELECT estado FROM VOLUNTARIO WHERE id_usuario = %s LIMIT 1",
                    (id_usuario,)
                )
                vol = cursor.fetchone()
                if vol and vol["estado"] == "Inactivo_Definitivo":
                    raise ValueError(
                        "No es posible reactivar esta cuenta: el voluntario alcanzó los 5 strikes."
                    )

            cursor.execute(
                "UPDATE USUARIO SET activo = %s WHERE id_usuario = %s",
                (int(activo), id_usuario)
            )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()