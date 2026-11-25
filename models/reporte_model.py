from mysql.connector import Error
from config.database import Database


class ReporteModel:
    def __init__(self):
        self.db = Database()

    def _columnas_tabla(self, cursor, tabla: str) -> set[str]:
        cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        return {
            (f["Field"] if isinstance(f, dict) else f[0])
            for f in cursor.fetchall()
        }

    def _tabla_existe(self, cursor, tabla: str) -> bool:
        cursor.execute("SHOW TABLES LIKE %s", (tabla,))
        return cursor.fetchone() is not None

    def obtener_rendimiento_voluntarios(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_asis = self._columnas_tabla(cursor, "ASISTENCIA")
            if "hora_entrada" in cols_asis and "hora_salida" in cols_asis:
                expr_horas = """
                    ROUND(
                        COALESCE(
                            SUM(
                                CASE WHEN asis.asistio = 1
                                THEN TIMESTAMPDIFF(MINUTE, asis.hora_entrada, asis.hora_salida) / 60.0
                                ELSE 0 END
                            ),
                            0
                        ),
                        2
                    )
                """
            else:
                expr_horas = "ROUND(COALESCE(SUM(asis.horas_cumplidas), 0), 2)"

            sql = f"""
                SELECT 
                    v.ci,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS voluntario,
                    v.estado AS estado_voluntario,
                    COUNT(
                        DISTINCT CASE
                            WHEN asig.estado IN ('Pendiente', 'Confirmada') THEN asig.id_asignacion
                        END
                    ) AS actividades_asignadas,
                    COALESCE(SUM(CASE WHEN asis.asistio = 1 THEN 1 ELSE 0 END), 0) AS asistencias,
                    COALESCE(SUM(CASE WHEN asis.asistio = 0 THEN 1 ELSE 0 END), 0) AS inasistencias,
                    {expr_horas} AS total_horas,
                    COALESCE(
                        (SELECT SUM(s.cantidad_strikes)
                         FROM STRIKE_VOLUNTARIO s
                         WHERE s.id_voluntario = v.id_voluntario),
                        0
                    ) AS total_strikes
                FROM VOLUNTARIO v
                LEFT JOIN ASIGNACION asig ON asig.id_voluntario = v.id_voluntario
                LEFT JOIN ACTIVIDAD act ON asig.id_actividad = act.id_actividad
                LEFT JOIN ASISTENCIA asis ON asis.id_asignacion = asig.id_asignacion
                WHERE v.estado IN ('Admitido', 'Inactivo', 'Inactivo_Definitivo')
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND (act.fecha IS NULL OR act.fecha BETWEEN %s AND %s)"
                params.extend([fecha_ini, fecha_fin])

            sql += """
                GROUP BY v.id_voluntario, v.ci, v.nombres, v.apellido_paterno, v.apellido_materno, v.estado
                ORDER BY total_horas DESC, asistencias DESC, voluntario ASC
            """
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                f["total_horas"] = float(f["total_horas"] or 0.0)
                f["asistencias"] = int(f["asistencias"] or 0)
                f["inasistencias"] = int(f["inasistencias"] or 0)
                f["actividades_asignadas"] = int(f["actividades_asignadas"] or 0)
                f["total_strikes"] = int(f["total_strikes"] or 0)
                evaluadas = f["asistencias"] + f["inasistencias"]
                f["porcentaje_cumplimiento"] = round((f["asistencias"] / evaluadas) * 100, 1) if evaluadas > 0 else 0.0

            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar rendimiento de voluntarios: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_voluntarios_por_tiempo(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_vol = self._columnas_tabla(cursor, "VOLUNTARIO")
            col_fecha = next(
                (c for c in ("fecha_inscripcion", "fecha_registro", "fecha_admision") if c in cols_vol),
                "fecha_inscripcion"
            )

            sql = f"""
                SELECT 
                    DATE_FORMAT({col_fecha}, '%Y-%m') AS periodo,
                    COUNT(*) AS cantidad
                FROM VOLUNTARIO
                WHERE {col_fecha} IS NOT NULL
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += f" AND DATE({col_fecha}) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY periodo ORDER BY periodo ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar voluntarios por tiempo: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_voluntarios_por_estado(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_vol = self._columnas_tabla(cursor, "VOLUNTARIO")
            col_fecha = next(
                (c for c in ("fecha_inscripcion", "fecha_registro", "fecha_admision") if c in cols_vol),
                None
            )

            sql = """
                SELECT 
                    estado,
                    COUNT(id_voluntario) AS cantidad
                FROM VOLUNTARIO
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin and col_fecha:
                sql += f" AND DATE({col_fecha}) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY estado ORDER BY cantidad DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar voluntarios por estado: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_inscripciones_por_registrador(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_vol = self._columnas_tabla(cursor, "VOLUNTARIO")
            col_reg = next(
                (c for c in ("id_usuario_registra", "id_admin_registra") if c in cols_vol),
                None
            )
            col_fecha = next(
                (c for c in ("fecha_inscripcion", "fecha_registro", "fecha_admision") if c in cols_vol),
                None
            )

            if not col_reg:
                return []

            sql = f"""
                SELECT 
                    COALESCE(u.usuario, 'Sin registro') AS registrador,
                    COUNT(v.id_voluntario) AS cantidad
                FROM VOLUNTARIO v
                LEFT JOIN USUARIO u ON v.{col_reg} = u.id_usuario
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin and col_fecha:
                sql += f" AND DATE(v.{col_fecha}) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY u.id_usuario, u.usuario ORDER BY cantidad DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar inscripciones por usuario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_actividades_por_tiempo(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    DATE_FORMAT(fecha, '%Y-%m') AS periodo,
                    COUNT(*) AS cantidad
                FROM ACTIVIDAD
                WHERE fecha IS NOT NULL
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND fecha BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY periodo ORDER BY periodo ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar actividades por tiempo: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_actividades_por_estado(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    estado,
                    COUNT(id_actividad) AS cantidad
                FROM ACTIVIDAD
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND fecha BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY estado ORDER BY cantidad DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar actividades por estado: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_ocupacion_actividades(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    a.nombre AS actividad,
                    a.fecha,
                    a.lugar,
                    a.estado,
                    a.cupo_maximo,
                    COALESCE(
                        SUM(
                            CASE WHEN asig.estado IN ('Pendiente', 'Confirmada') THEN 1 ELSE 0 END
                        ),
                        0
                    ) AS inscritos
                FROM ACTIVIDAD a
                LEFT JOIN ASIGNACION asig ON asig.id_actividad = a.id_actividad
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND a.fecha BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += """
                GROUP BY a.id_actividad, a.nombre, a.fecha, a.lugar, a.estado, a.cupo_maximo
                ORDER BY a.fecha DESC
            """
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()
            for f in filas:
                cupo = int(f["cupo_maximo"] or 0)
                insc = int(f["inscritos"] or 0)
                f["cupo_maximo"] = cupo
                f["inscritos"] = insc
                f["porcentaje_ocupacion"] = round((insc / cupo) * 100, 1) if cupo > 0 else 0.0
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar ocupación de actividades: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_donaciones_por_tiempo(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    DATE_FORMAT(d.fecha_donacion, '%Y-%m') AS periodo,
                    COALESCE(SUM(dm.monto), 0) AS total_monto,
                    COUNT(d.id_donacion) AS cantidad_donaciones
                FROM DONACION d
                INNER JOIN DONACION_MONETARIA dm ON dm.id_donacion = d.id_donacion
                WHERE d.fecha_donacion IS NOT NULL
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND DATE(d.fecha_donacion) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY periodo ORDER BY periodo ASC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()
            for f in filas:
                f["total_monto"] = float(f["total_monto"] or 0.0)
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar donaciones por tiempo: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_donaciones_por_metodo_pago(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    dm.metodo_pago AS metodo,
                    COALESCE(SUM(dm.monto), 0) AS total_monto,
                    COUNT(d.id_donacion) AS cantidad
                FROM DONACION d
                INNER JOIN DONACION_MONETARIA dm ON dm.id_donacion = d.id_donacion
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND DATE(d.fecha_donacion) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY dm.metodo_pago ORDER BY total_monto DESC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()
            for f in filas:
                f["total_monto"] = float(f["total_monto"] or 0.0)
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar donaciones por método de pago: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_donaciones_por_tipo(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_don = self._columnas_tabla(cursor, "DONACION")
            col_fecha = "fecha_donacion" if "fecha_donacion" in cols_don else "fecha"

            if "tipo_donacion" in cols_don:
                sql = """
                    SELECT 
                        COALESCE(d.tipo_donacion, 'No especificado') AS tipo,
                        COUNT(d.id_donacion) AS cantidad
                    FROM DONACION d
                    WHERE 1=1
                """
                group_by = "d.tipo_donacion"
            else:
                sql = """
                    SELECT 
                        td.nombre AS tipo,
                        COUNT(d.id_donacion) AS cantidad
                    FROM DONACION d
                    INNER JOIN TIPO_DONACION td ON d.id_tipo_donacion = td.id_tipo_donacion
                    WHERE 1=1
                """
                group_by = "td.id_tipo_donacion, td.nombre"

            params = []
            if fecha_ini and fecha_fin:
                sql += f" AND DATE(d.{col_fecha}) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += f" GROUP BY {group_by} ORDER BY cantidad DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar donaciones por tipo: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_insumos_recibidos(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_don = self._columnas_tabla(cursor, "DONACION")
            col_fecha = "fecha_donacion" if "fecha_donacion" in cols_don else "fecha"
            cols_det = self._columnas_tabla(cursor, "DONACION_DETALLE")

            if "id_insumo" in cols_det and self._tabla_existe(cursor, "INSUMO"):
                sql = """
                    SELECT 
                        i.nombre AS insumo,
                        i.unidad_medida,
                        COALESCE(SUM(dd.cantidad), 0) AS total_cantidad
                    FROM DONACION_DETALLE dd
                    INNER JOIN INSUMO i ON dd.id_insumo = i.id_insumo
                    INNER JOIN DONACION d ON dd.id_donacion = d.id_donacion
                    WHERE 1=1
                """
                group_by = "i.id_insumo, i.nombre, i.unidad_medida"
            else:
                col_nom = next(
                    (c for c in ("nombre_insumo", "insumo", "descripcion", "articulo") if c in cols_det),
                    "descripcion"
                )
                col_uni = next(
                    (c for c in ("unidad_medida", "unidad") if c in cols_det),
                    None
                )
                sel_uni = f"COALESCE(dd.{col_uni}, 'Unid.')" if col_uni else "'Unid.'"
                group_by = f"dd.{col_nom}, dd.{col_uni}" if col_uni else f"dd.{col_nom}"

                sql = f"""
                    SELECT 
                        dd.{col_nom} AS insumo,
                        {sel_uni} AS unidad_medida,
                        COALESCE(SUM(dd.cantidad), 0) AS total_cantidad
                    FROM DONACION_DETALLE dd
                    INNER JOIN DONACION d ON dd.id_donacion = d.id_donacion
                    WHERE 1=1
                """

            params = []
            if fecha_ini and fecha_fin:
                sql += f" AND DATE(d.{col_fecha}) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += f" GROUP BY {group_by} ORDER BY total_cantidad DESC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()
            for f in filas:
                f["total_cantidad"] = float(f["total_cantidad"] or 0.0)
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar insumos recibidos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def obtener_top_donantes(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    don.nombre AS donante,
                    COALESCE(don.ci_nit, '-') AS documento,
                    COUNT(d.id_donacion) AS total_aportes,
                    COALESCE(SUM(dm.monto), 0) AS total_dinero
                FROM DONACION d
                INNER JOIN DONANTE don ON d.id_donante = don.id_donante
                LEFT JOIN DONACION_MONETARIA dm ON dm.id_donacion = d.id_donacion
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND DATE(d.fecha_donacion) BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY don.id_donante, don.nombre, don.ci_nit ORDER BY total_dinero DESC, total_aportes DESC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()
            for f in filas:
                f["total_dinero"] = float(f["total_dinero"] or 0.0)
                f["total_aportes"] = int(f["total_aportes"] or 0)
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar ranking de donantes: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()