from datetime import datetime
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

    def obtener_insumos_con_stock(self) -> list[dict]:
        """
        Devuelve el catálogo INSUMO calculando dinámicamente en FNBC:
        stock_disponible = total_ingresado (DONACION_DETALLE) - total_entregado (ENTREGA_INSUMO).
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT 
                    i.id_insumo,
                    i.nombre,
                    i.unidad_medida,
                    COALESCE(
                        (SELECT SUM(dd.cantidad)
                         FROM DONACION_DETALLE dd
                         WHERE dd.id_insumo = i.id_insumo),
                        0
                    ) AS total_ingresado,
                    COALESCE(
                        (SELECT SUM(ei.cantidad_entregada)
                         FROM ENTREGA_INSUMO ei
                         WHERE ei.id_insumo = i.id_insumo),
                        0
                    ) AS total_entregado
                FROM INSUMO i
                ORDER BY i.nombre ASC
                """
            )
            filas = cursor.fetchall()
            for f in filas:
                ing = float(f.get("total_ingresado") or 0)
                ent = float(f.get("total_entregado") or 0)
                f["total_ingresado"] = round(ing, 2)
                f["total_entregado"] = round(ent, 2)
                f["stock_disponible"] = round(ing - ent, 2)
            return filas
        except Error as e:
            raise RuntimeError(f"Error al cargar catálogo e inventario de insumos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_actividades_para_despacho(self) -> list[dict]:
        """Lista actividades Programadas o En Curso para vincular entregas de insumos."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id_actividad, nombre, fecha, lugar, estado
                FROM ACTIVIDAD
                WHERE estado IN ('Programada', 'En Curso')
                ORDER BY fecha ASC, nombre ASC
                """
            )
            return cursor.fetchall()
        except Error:
            return []
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
        monto: float | None,
        metodo_pago: str | None,
        detalles_material: list[dict],
        observaciones: str | None,
        id_usuario_registra: int | None = None
    ) -> int:
        """
        Transacción FNBC v1.3 (válida tanto para Administración como para Autodonación pública):
        1. Busca o registra DONANTE respetando origen_registro ('Administrador' | 'Autoregistro').
        2. Inserta cabecera en DONACION con canal_registro ('Administrador' | 'Autodonacion').
        3. Si es DINERO -> inserta en DONACION_MONETARIA.
        4. Si es MATERIAL -> inserta en DONACION_DETALLE y actualiza stock_actual en INSUMO.
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
            es_recurrente = 0

            if doc_valor:
                cursor.execute("SELECT id_donante FROM DONANTE WHERE ci_nit = %s LIMIT 1", (doc_valor,))
                existente = cursor.fetchone()
                if existente:
                    id_donante = existente["id_donante"]
                    es_recurrente = 1
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
                cols_dte = self._columnas_tabla(cursor, "DONANTE")
                campos_dte = ["nombre", "ci_nit", "telefono", "correo"]
                valores_dte = [datos_donante["nombre"], doc_valor, tel_valor, correo_valor]

                if "origen_registro" in cols_dte:
                    campos_dte.append("origen_registro")
                    valores_dte.append("Administrador" if id_usuario_registra is not None else "Autoregistro")

                if "id_admin_registra" in cols_dte:
                    campos_dte.append("id_admin_registra")
                    valores_dte.append(id_usuario_registra)

                placeholders_dte = ", ".join(["%s"] * len(campos_dte))
                cursor.execute(
                    f"INSERT INTO DONANTE ({', '.join(campos_dte)}) VALUES ({placeholders_dte})",
                    tuple(valores_dte)
                )
                id_donante = cursor.lastrowid

            tipo_upper = tipo_nombre.strip().upper()
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cols_don = self._columnas_tabla(cursor, "DONACION")

            campos_don = ["id_donante", "tipo_donacion", "fecha_donacion"]
            valores_don = [id_donante, tipo_upper, ahora]

            if "canal_registro" in cols_don:
                campos_don.append("canal_registro")
                valores_don.append("Administrador" if id_usuario_registra is not None else "Autodonacion")

            if "es_donante_recurrente" in cols_don:
                campos_don.append("es_donante_recurrente")
                valores_don.append(es_recurrente)

            if "observaciones" in cols_don:
                campos_don.append("observaciones")
                valores_don.append(observaciones.strip() if observaciones else None)

            for col_usr in ("id_admin_registra", "id_usuario_registra", "id_usuario"):
                if col_usr in cols_don:
                    campos_don.append(col_usr)
                    valores_don.append(id_usuario_registra)
                    break

            placeholders = ", ".join(["%s"] * len(campos_don))
            cursor.execute(
                f"INSERT INTO DONACION ({', '.join(campos_don)}) VALUES ({placeholders})",
                tuple(valores_don)
            )
            id_donacion = cursor.lastrowid

            if tipo_upper == "DINERO":
                if monto is None or monto <= 0 or not metodo_pago:
                    raise ValueError("Datos monetarios incompletos para DONACION_MONETARIA.")

                cursor.execute(
                    """
                    INSERT INTO DONACION_MONETARIA (id_donacion, monto, metodo_pago)
                    VALUES (%s, %s, %s)
                    """,
                    (id_donacion, monto, metodo_pago)
                )

            elif tipo_upper == "MATERIAL":
                if not detalles_material:
                    raise ValueError("Una donación de tipo MATERIAL requiere al menos un insumo en el detalle.")

                cols_ins = self._columnas_tabla(cursor, "INSUMO")
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

                    if "stock_actual" in cols_ins:
                        cursor.execute(
                            "UPDATE INSUMO SET stock_actual = stock_actual + %s WHERE id_insumo = %s",
                            (item["cantidad"], item["id_insumo"])
                        )
            else:
                raise ValueError(f"Tipo de donación inválido: {tipo_upper}")

            conn.commit()
            return int(id_donacion)
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
        """Consulta el historial unificando DONACION + DONACION_MONETARIA + conteo de DONACION_DETALLE."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_don = self._columnas_tabla(cursor, "DONACION")
            col_usr = next(
                (c for c in ("id_admin_registra", "id_usuario_registra", "id_usuario") if c in cols_don),
                None
            )
            if "canal_registro" in cols_don:
                origen_expr = (
                    "CASE WHEN d.canal_registro = 'Autodonacion' "
                    "THEN 'Portal Público' ELSE 'Administración' END AS origen,"
                )
            elif col_usr:
                origen_expr = (
                    f"CASE WHEN d.{col_usr} IS NULL THEN 'Portal Público' ELSE 'Administración' END AS origen,"
                )
            else:
                origen_expr = "'Sistema' AS origen,"

            obs_expr = "d.observaciones," if "observaciones" in cols_don else "NULL AS observaciones,"

            sql = f"""
                SELECT 
                    d.id_donacion,
                    d.fecha_donacion,
                    DATE(d.fecha_donacion) AS fecha,
                    don.nombre AS donante,
                    don.ci_nit AS documento,
                    d.tipo_donacion,
                    dm.metodo_pago,
                    dm.monto,
                    {origen_expr}
                    {obs_expr}
                    (
                        SELECT COUNT(*)
                        FROM DONACION_DETALLE dd
                        WHERE dd.id_donacion = d.id_donacion
                    ) AS cantidad_items
                FROM DONACION d
                INNER JOIN DONANTE don ON d.id_donante = don.id_donante
                LEFT JOIN DONACION_MONETARIA dm ON d.id_donacion = dm.id_donacion
                WHERE 1=1
            """
            params = []
            if filtro_tipo and filtro_tipo != "Todos":
                sql += " AND d.tipo_donacion = %s"
                params.append(filtro_tipo.upper())

            sql += " ORDER BY d.id_donacion DESC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                fd = f.get("fecha_donacion")
                f["fecha_hora_str"] = (
                    fd.strftime("%Y-%m-%d %H:%M")
                    if hasattr(fd, "strftime") else str(f.get("fecha") or "-")
                )
            return filas
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

    def registrar_entrega_insumo_transaccion(
        self,
        id_insumo: int,
        cantidad: float,
        id_actividad: int | None,
        destino: str,
        id_usuario_entrega: int
    ):
        """
        Registra una salida de inventario en ENTREGA_INSUMO verificando atómicamente
        que exista stock disponible suficiente para evitar inventario negativo.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT 
                    i.id_insumo,
                    i.nombre,
                    i.unidad_medida,
                    COALESCE((SELECT SUM(dd.cantidad) FROM DONACION_DETALLE dd WHERE dd.id_insumo = i.id_insumo), 0) AS ing,
                    COALESCE((SELECT SUM(ei.cantidad_entregada) FROM ENTREGA_INSUMO ei WHERE ei.id_insumo = i.id_insumo), 0) AS ent
                FROM INSUMO i
                WHERE i.id_insumo = %s
                FOR UPDATE
                """,
                (id_insumo,)
            )
            ins = cursor.fetchone()
            if not ins:
                raise ValueError("El insumo seleccionado no existe en el catálogo.")

            stock_disp = round(float(ins["ing"]) - float(ins["ent"]), 2)
            if cantidad > stock_disp:
                raise ValueError(
                    f"Stock insuficiente para '{ins['nombre']}'. "
                    f"Disponible actual: {stock_disp:g} {ins['unidad_medida']}."
                )

            cols_ent = self._columnas_tabla(cursor, "ENTREGA_INSUMO")
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            col_cant = "cantidad_entregada" if "cantidad_entregada" in cols_ent else "cantidad"

            campos = ["id_insumo", col_cant, "fecha_entrega"]
            valores = [id_insumo, cantidad, ahora]

            if "id_actividad" in cols_ent:
                campos.append("id_actividad")
                valores.append(id_actividad)

            if "id_voluntario_responsable" in cols_ent:
                campos.append("id_voluntario_responsable")
                valores.append(None)

            if "destino" in cols_ent:
                campos.append("destino")
                valores.append(destino.strip())

            if "observaciones" in cols_ent:
                campos.append("observaciones")
                valores.append(destino.strip())

            for col_usr in (
                "id_admin_autoriza",
                "id_admin_entrega",
                "id_usuario_entrega",
                "id_usuario_registra",
                "id_usuario"
            ):
                if col_usr in cols_ent:
                    campos.append(col_usr)
                    valores.append(id_usuario_entrega)
                    break

            placeholders = ", ".join(["%s"] * len(campos))
            cursor.execute(
                f"INSERT INTO ENTREGA_INSUMO ({', '.join(campos)}) VALUES ({placeholders})",
                tuple(valores)
            )

            cols_ins = self._columnas_tabla(cursor, "INSUMO")
            if "stock_actual" in cols_ins:
                cursor.execute(
                    "UPDATE INSUMO SET stock_actual = GREATEST(0, stock_actual - %s) WHERE id_insumo = %s",
                    (cantidad, id_insumo)
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

    def listar_entregas_insumos(self, limite: int = 100) -> list[dict]:
        """Consulta el historial de salidas de insumos (ENTREGA_INSUMO)."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_ent = self._columnas_tabla(cursor, "ENTREGA_INSUMO")
            tiene_act = "id_actividad" in cols_ent
            col_dest = "destino" if "destino" in cols_ent else ("observaciones" if "observaciones" in cols_ent else None)
            col_usr = next(
                (
                    c for c in (
                        "id_admin_autoriza",
                        "id_admin_entrega",
                        "id_usuario_entrega",
                        "id_usuario_registra",
                        "id_usuario"
                    )
                    if c in cols_ent
                ),
                None
            )

            join_act = "LEFT JOIN ACTIVIDAD a ON ei.id_actividad = a.id_actividad" if tiene_act else ""
            select_act = "a.nombre AS actividad," if tiene_act else "NULL AS actividad,"
            select_dest = f"ei.{col_dest} AS destino," if col_dest else "NULL AS destino,"
            join_usr = f"LEFT JOIN USUARIO u ON ei.{col_usr} = u.id_usuario" if col_usr else ""
            select_usr = "u.usuario AS responsable" if col_usr else "'Admin' AS responsable"

            cursor.execute(
                f"""
                SELECT 
                    ei.id_entrega,
                    ei.fecha_entrega,
                    i.nombre AS insumo,
                    ei.cantidad_entregada AS cantidad,
                    i.unidad_medida,
                    {select_act}
                    {select_dest}
                    {select_usr}
                FROM ENTREGA_INSUMO ei
                INNER JOIN INSUMO i ON ei.id_insumo = i.id_insumo
                {join_act}
                {join_usr}
                ORDER BY ei.id_entrega DESC
                LIMIT %s
                """,
                (limite,)
            )
            filas = cursor.fetchall()
            for f in filas:
                fe = f.get("fecha_entrega")
                f["fecha_str"] = fe.strftime("%Y-%m-%d %H:%M") if hasattr(fe, "strftime") else str(fe or "-")
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar entregas de insumos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()