from datetime import date
import mysql.connector
from mysql.connector import Error
from config.database import Database


class DonacionModel:
    def __init__(self):
        self.db = Database()

    def _columnas_tabla(self, cursor, tabla: str) -> set[str]:
        cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        return {
            (f["Field"] if isinstance(f, dict) else f[0])
            for f in cursor.fetchall()
        }

    def obtener_tipos_donacion(self) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_tipo_donacion, nombre FROM TIPO_DONACION ORDER BY id_tipo_donacion ASC")
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al cargar tipos de donación: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_metodos_pago(self) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_metodo_pago, nombre FROM METODO_PAGO ORDER BY id_metodo_pago ASC")
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al cargar métodos de pago: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_insumos(self) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_insumo, nombre, unidad_medida FROM INSUMO ORDER BY nombre ASC")
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al cargar catálogo de insumos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def buscar_donante_por_documento(self, documento: str) -> dict | None:
        doc = documento.strip()
        if not doc:
            return None

        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id_donante, nombre, ci_nit, telefono, correo FROM DONANTE WHERE ci_nit = %s LIMIT 1",
                (doc,)
            )
            fila = cursor.fetchone()
            if not fila:
                return None

            return {
                "id_donante": fila["id_donante"],
                "nombre": fila["nombre"] or "",
                "documento": fila["ci_nit"] or "",
                "telefono": fila["telefono"] or "",
                "correo": fila["correo"] or ""
            }
        except Error:
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def registrar_donacion_transaccion(
        self,
        datos_donante: dict,
        tipo_nombre: str,
        id_tipo_donacion: int,
        monto: float | None,
        id_metodo_pago: int | None,
        detalles_material: list[dict],
        observaciones: str | None,
        id_usuario_registra: int
    ):
        """
        Flujo 4 (v2.0):
        1. Busca o registra DONANTE (ci_nit, telefono, correo en None si vacíos).
        2. Inserta DONACION con fecha_donacion (monto e id_metodo_pago en None si es MATERIAL).
        3. Inserta DONACION_DETALLE; si salta Error 1062 (UNIQUE id_donacion, id_insumo),
           ejecuta UPDATE sumando la cantidad nueva a la existente.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            doc_valor = datos_donante.get("documento", "").strip() or None
            tel_valor = datos_donante.get("telefono", "").strip() or None
            correo_valor = datos_donante.get("correo", "").strip() or None
            id_donante = None

            if doc_valor:
                cursor.execute("SELECT id_donante FROM DONANTE WHERE ci_nit = %s LIMIT 1", (doc_valor,))
                existente = cursor.fetchone()
                if existente:
                    id_donante = existente["id_donante"]
                    cursor.execute(
                        """
                        UPDATE DONANTE
                        SET nombre = %s,
                            telefono = COALESCE(%s, telefono),
                            correo = COALESCE(%s, correo)
                        WHERE id_donante = %s
                        """,
                        (datos_donante["nombre"], tel_valor, correo_valor, id_donante)
                    )

            if id_donante is None:
                cursor.execute(
                    """
                    INSERT INTO DONANTE (nombre, ci_nit, telefono, correo)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (datos_donante["nombre"], doc_valor, tel_valor, correo_valor)
                )
                id_donante = cursor.lastrowid

            cols_donacion = self._columnas_tabla(cursor, "DONACION")
            tipo_upper = tipo_nombre.strip().upper()

            if tipo_upper == "DINERO":
                monto_final = monto
                metodo_final = id_metodo_pago
            else:
                # Precaución v2.0: None explícito (NULL) en monto e id_metodo_pago para MATERIAL
                monto_final = None
                metodo_final = None

            campos_don = ["id_donante", "id_tipo_donacion", "id_metodo_pago", "monto", "fecha_donacion"]
            valores_don = [id_donante, id_tipo_donacion, metodo_final, monto_final, date.today()]

            if "id_usuario_registra" in cols_donacion:
                campos_don.append("id_usuario_registra")
                valores_don.append(id_usuario_registra)
            elif "id_usuario" in cols_donacion:
                campos_don.append("id_usuario")
                valores_don.append(id_usuario_registra)

            if "observaciones" in cols_donacion:
                campos_don.append("observaciones")
                valores_don.append(observaciones or None)

            placeholders = ", ".join(["%s"] * len(campos_don))
            cursor.execute(
                f"INSERT INTO DONACION ({', '.join(campos_don)}) VALUES ({placeholders})",
                tuple(valores_don)
            )
            id_donacion = cursor.lastrowid

            if tipo_upper == "MATERIAL":
                if not detalles_material:
                    raise ValueError("Una donación de tipo MATERIAL requiere al menos un insumo en el detalle.")

                for item in detalles_material:
                    try:
                        cursor.execute(
                            """
                            INSERT INTO DONACION_DETALLE (id_donacion, id_insumo, cantidad)
                            VALUES (%s, %s, %s)
                            """,
                            (id_donacion, item["id_insumo"], item["cantidad"])
                        )
                    except mysql.connector.IntegrityError as e:
                        # Flujo 4: Si salta índice UNIQUE (1062), sumar la nueva cantidad
                        if e.errno == 1062:
                            cursor.execute(
                                """
                                UPDATE DONACION_DETALLE
                                SET cantidad = cantidad + %s
                                WHERE id_donacion = %s AND id_insumo = %s
                                """,
                                (item["cantidad"], id_donacion, item["id_insumo"])
                            )
                        else:
                            raise e

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

    def listar_donaciones(self, filtro_tipo: str = "Todos") -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    d.id_donacion,
                    d.fecha_donacion AS fecha,
                    don.nombre AS donante,
                    don.ci_nit AS documento,
                    td.nombre AS tipo_donacion,
                    mp.nombre AS metodo_pago,
                    d.monto,
                    (
                        SELECT COUNT(*)
                        FROM DONACION_DETALLE dd
                        WHERE dd.id_donacion = d.id_donacion
                    ) AS cantidad_items
                FROM DONACION d
                INNER JOIN DONANTE don ON d.id_donante = don.id_donante
                INNER JOIN TIPO_DONACION td ON d.id_tipo_donacion = td.id_tipo_donacion
                LEFT JOIN METODO_PAGO mp ON d.id_metodo_pago = mp.id_metodo_pago
                WHERE 1=1
            """
            params = []
            if filtro_tipo and filtro_tipo != "Todos":
                sql += " AND td.nombre = %s"
                params.append(filtro_tipo)

            sql += " ORDER BY d.id_donacion DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al listar historial de donaciones: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_detalle_insumos(self, id_donacion: int) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT 
                    i.nombre AS insumo,
                    dd.cantidad,
                    i.unidad_medida
                FROM DONACION_DETALLE dd
                INNER JOIN INSUMO i ON dd.id_insumo = i.id_insumo
                WHERE dd.id_donacion = %s
                ORDER BY i.nombre ASC
                """,
                (id_donacion,)
            )
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar detalle de insumos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()