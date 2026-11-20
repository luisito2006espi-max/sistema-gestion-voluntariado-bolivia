from mysql.connector import Error
from config.database import Database

class UsuarioModel:
    def __init__(self):
        self.db = Database()

    def buscar_por_username(self, username: str):
        """
        Obtiene los datos de acceso, el rol y (si aplica) los datos del voluntario.
        Usa consulta parametrizada (%s) para prevenir inyección SQL.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    u.id_usuario,
                    u.id_rol,
                    u.usuario,
                    u.contrasena,
                    u.activo,
                    r.nombre AS nombre_rol,
                    v.id_voluntario,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_voluntario
                FROM USUARIO u
                INNER JOIN ROL r ON u.id_rol = r.id_rol
                LEFT JOIN VOLUNTARIO v ON v.id_usuario = u.id_usuario
                WHERE u.usuario = %s
                LIMIT 1
            """
            cursor.execute(query, (username,))
            return cursor.fetchone()

        except Error as e:
            raise RuntimeError(f"Error de base de datos al consultar usuario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()