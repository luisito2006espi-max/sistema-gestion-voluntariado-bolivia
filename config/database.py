import mysql.connector
from mysql.connector import Error


class Database:
    # Configuración directa de MySQL en XAMPP
    DB_CONFIG = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",              # En XAMPP por defecto va vacío
        "database": "save_the_children_db",  # <-- Reemplaza por el nombre exacto de tu BD
        "autocommit": False
    }

    def get_connection(self):
        """Retorna una conexión activa a MySQL con manejo manual de transacciones."""
        try:
            connection = mysql.connector.connect(**self.DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"[Error MySQL] No se pudo conectar a la base de datos: {e}")
            raise e