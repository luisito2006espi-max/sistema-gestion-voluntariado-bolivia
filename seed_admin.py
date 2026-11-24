import getpass
import mysql.connector
from mysql.connector import Error
from config.database import Database
from models.auth_model import AuthModel


class SeedAdminManager:
    def __init__(self):
        self.db = Database()

    def _detectar_columna_password(self, cursor) -> str:
        cursor.execute("SHOW COLUMNS FROM USUARIO")
        cols = {
            (f["Field"] if isinstance(f, dict) else f[0])
            for f in cursor.fetchall()
        }
        for candidata in ("password_hash", "contrasena", "password"):
            if candidata in cols:
                return candidata
        raise RuntimeError("No se encontró columna de contraseña en la tabla USUARIO.")

    def asegurar_catalogos_base(self):
        """Garantiza los catálogos obligatorios (esquema v2.0) sin Tarjeta ni Recepcionista."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ROL (id_rol, nombre) VALUES
                (1, 'Administrador'),
                (3, 'Voluntario')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
            """)

            cursor.execute("""
                INSERT INTO ESTADO_VOLUNTARIO (id_estado_vol, nombre) VALUES
                (1, 'Postulante'),
                (2, 'Admitido'),
                (3, 'Rechazado'),
                (4, 'Inactivo')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
            """)

            cursor.execute("""
                INSERT INTO ESTADO_ACTIVIDAD (id_estado_actividad, nombre) VALUES
                (1, 'Programada'),
                (2, 'En Curso'),
                (3, 'Finalizada'),
                (4, 'Cancelada')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
            """)

            cursor.execute("""
                INSERT INTO ESTADO_ASIGNACION (id_estado_asignacion, nombre) VALUES
                (1, 'Confirmada'),
                (2, 'Cancelada')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
            """)

            cursor.execute("""
                INSERT INTO TIPO_DONACION (id_tipo_donacion, nombre) VALUES
                (1, 'DINERO'),
                (2, 'MATERIAL')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
            """)

            cursor.execute("DELETE FROM METODO_PAGO WHERE LOWER(nombre) = 'tarjeta'")
            cursor.execute("""
                INSERT INTO METODO_PAGO (id_metodo_pago, nombre) VALUES
                (1, 'QR'),
                (3, 'Efectivo'),
                (4, 'Transferencia')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
            """)

            cursor.execute("""
                INSERT INTO INSUMO (id_insumo, nombre, unidad_medida) VALUES
                (1, 'Ropa', 'Prendas'),
                (2, 'Alimentos', 'Kilogramos (kg)'),
                (3, 'Útiles escolares', 'Unidades / Kits'),
                (4, 'Higiene', 'Unidades / Paquetes'),
                (5, 'Medicamentos / Botiquín', 'Cajas / Unidades')
                ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), unidad_medida = VALUES(unidad_medida)
            """)

            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"Error al verificar catálogos base: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def crear_administrador(self, usuario: str, password: str) -> tuple[bool, str]:
        """Crea un nuevo Administrador usando AuthModel.hashear_password (utils/security.py)."""
        user_limpio = usuario.strip().lower()
        if len(user_limpio) < 4:
            return False, "El nombre de usuario debe tener al menos 4 caracteres."
        if " " in user_limpio:
            return False, "El nombre de usuario no debe contener espacios."
        if len(password.strip()) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."

        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_rol FROM ROL WHERE nombre = 'Administrador' LIMIT 1")
            rol_fila = cursor.fetchone()
            if not rol_fila:
                return False, "El rol 'Administrador' no existe en la tabla ROL."

            col_pass = self._detectar_columna_password(cursor)
            password_hash = AuthModel.hashear_password(password.strip())

            cursor.execute(
                f"INSERT INTO USUARIO (usuario, {col_pass}, id_rol) VALUES (%s, %s, %s)",
                (user_limpio, password_hash, rol_fila["id_rol"])
            )
            conn.commit()
            return True, f"Administrador '{user_limpio}' creado correctamente."

        except mysql.connector.IntegrityError as e:
            if conn:
                conn.rollback()
            if e.errno == 1062:
                return False, f"El usuario '{user_limpio}' ya existe en la base de datos. Elige otro nombre."
            return False, f"Error de integridad en MySQL: {e}"
        except Error as e:
            if conn:
                conn.rollback()
            return False, f"Error de conexión MySQL: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_administradores(self):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.usuario, r.nombre AS rol
                FROM USUARIO u
                INNER JOIN ROL r ON u.id_rol = r.id_rol
                WHERE r.nombre = 'Administrador'
                ORDER BY u.usuario ASC
            """)
            filas = cursor.fetchall()
            print("\n--- Administradores Registrados ---")
            if not filas:
                print("  (Ningún administrador registrado aún)")
            for f in filas:
                print(f"  • Usuario: {f['usuario']:<20} | Rol: {f['rol']}")
            print("-------------------------------------\n")
        except Error as e:
            print(f"\n[Error] No se pudo listar administradores: {e}\n")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()


def main():
    gestor = SeedAdminManager()
    print("=======================================================")
    print("  Save the Children Bolivia — Gestión de Administradores ")
    print("=======================================================")

    try:
        gestor.asegurar_catalogos_base()
    except Exception as e:
        print(f"[Error crítico de conexión]: {e}")
        return

    while True:
        print("\nSelecciona una opción:")
        print("  1. Crear nuevo Administrador")
        print("  2. Ver administradores existentes")
        print("  0. Salir")

        opcion = input("\nOpción: ").strip()

        if opcion == "1":
            nuevo_user = input("Nuevo nombre de usuario (Administrador): ").strip()
            clave1 = getpass.getpass("Contraseña (mín. 6 caracteres): ")
            clave2 = getpass.getpass("Confirmar contraseña: ")

            if clave1 != clave2:
                print("\n[Error] Las contraseñas no coinciden. Intenta de nuevo.")
                continue

            exito, mensaje = gestor.crear_administrador(nuevo_user, clave1)
            prefijo = "[OK]" if exito else "[Aviso]"
            print(f"\n{prefijo} {mensaje}")

        elif opcion == "2":
            gestor.listar_administradores()

        elif opcion == "0":
            print("\nSaliendo del gestor de administradores.")
            break
        else:
            print("\nOpción no válida.")


if __name__ == "__main__":
    main()