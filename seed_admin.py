import getpass
import mysql.connector
from mysql.connector import Error
from config.database import Database
from utils.security import encriptar_password


class SeedAdminManager:
    def __init__(self):
        self.db = Database()

    def asegurar_catalogos_base(self):
        """
        Garantiza el catálogo base de INSUMO (esquema v1.3 FNBC).
        Los estados, roles, tipos de donación y métodos de pago ahora son ENUM nativos.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO INSUMO (id_insumo, nombre, unidad_medida, stock_actual) VALUES
                (1, 'Ropa de Abrigo Infantil', 'Prendas', 0.00),
                (2, 'Alimentos No Perecederos', 'Kilogramos (kg)', 0.00),
                (3, 'Útiles Escolares', 'Unidades / Kits', 0.00),
                (4, 'Artículos de Higiene y Bioseguridad', 'Unidades / Paquetes', 0.00),
                (5, 'Medicamentos / Botiquín Básico', 'Cajas / Unidades', 0.00)
                ON DUPLICATE KEY UPDATE
                    nombre = VALUES(nombre),
                    unidad_medida = VALUES(unidad_medida)
            """)

            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"Error al verificar catálogo base de insumos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def crear_administrador(self, usuario: str, password: str) -> tuple[bool, str]:
        """Crea un nuevo Administrador en USUARIO usando rol ENUM('Administrador')."""
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
            cursor = conn.cursor()

            password_hash = encriptar_password(password.strip())

            cursor.execute(
                """
                INSERT INTO USUARIO (usuario, password_hash, rol, activo)
                VALUES (%s, %s, 'Administrador', 1)
                """,
                (user_limpio, password_hash)
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
                SELECT usuario, rol, activo, fecha_creacion
                FROM USUARIO
                WHERE rol = 'Administrador'
                ORDER BY usuario ASC
            """)
            filas = cursor.fetchall()
            print("\n--- Administradores Registrados ---")
            if not filas:
                print("  (Ningún administrador registrado aún)")
            for f in filas:
                estado_txt = "Activo" if f["activo"] == 1 else "Inactivo"
                print(
                    f"  • Usuario: {f['usuario']:<20} | Rol: {f['rol']:<13} "
                    f"| Estado: {estado_txt:<8} | Creado: {f['fecha_creacion']}"
                )
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