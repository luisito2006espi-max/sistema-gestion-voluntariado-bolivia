from mysql.connector import Error
from config.database import Database


class ReporteModel:
    def __init__(self):
        self.db = Database()

    def obtener_rendimiento_voluntarios(self, fecha_ini: str = None, fecha_fin: str = None) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    v.ci,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS voluntario,
                    ev.nombre AS estado_voluntario,
                    COUNT(DISTINCT asig.id_asignacion) AS actividades_asignadas,
                    COALESCE(SUM(CASE WHEN asis.asistio = 1 THEN 1 ELSE 0 END), 0) AS asistencias,
                    COALESCE(SUM(CASE WHEN asis.asistio = 0 THEN 1 ELSE 0 END), 0) AS inasistencias,
                    COALESCE(SUM(asis.horas_cumplidas), 0) AS total_horas
                FROM VOLUNTARIO v
                INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                LEFT JOIN ASIGNACION asig ON asig.id_voluntario = v.id_voluntario
                LEFT JOIN ACTIVIDAD act ON asig.id_actividad = act.id_actividad
                LEFT JOIN ASISTENCIA asis ON asis.id_asignacion = asig.id_asignacion
                WHERE ev.nombre IN ('Admitido', 'Inactivo')
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND (act.fecha IS NULL OR act.fecha BETWEEN %s AND %s)"
                params.extend([fecha_ini, fecha_fin])

            sql += """
                GROUP BY v.id_voluntario, v.ci, v.nombres, v.apellido_paterno, v.apellido_materno, ev.nombre
                ORDER BY total_horas DESC, asistencias DESC, voluntario ASC
            """
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                f["total_horas"] = float(f["total_horas"] or 0.0)
                f["asistencias"] = int(f["asistencias"] or 0)
                f["inasistencias"] = int(f["inasistencias"] or 0)
                f["actividades_asignadas"] = int(f["actividades_asignadas"] or 0)
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

            sql = """
                SELECT 
                    DATE_FORMAT(fecha_inscripcion, '%Y-%m') AS periodo,
                    COUNT(*) AS cantidad
                FROM VOLUNTARIO
                WHERE fecha_inscripcion IS NOT NULL
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND fecha_inscripcion BETWEEN %s AND %s"
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

            sql = """
                SELECT 
                    ev.nombre AS estado,
                    COUNT(v.id_voluntario) AS cantidad
                FROM VOLUNTARIO v
                INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND v.fecha_inscripcion BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY ev.id_estado_vol, ev.nombre ORDER BY cantidad DESC"
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

            sql = """
                SELECT 
                    COALESCE(u.usuario, 'Sin registro') AS registrador,
                    COUNT(v.id_voluntario) AS cantidad
                FROM VOLUNTARIO v
                LEFT JOIN USUARIO u ON v.id_usuario_registra = u.id_usuario
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND v.fecha_inscripcion BETWEEN %s AND %s"
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
                    ea.nombre AS estado,
                    COUNT(a.id_actividad) AS cantidad
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND a.fecha BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY ea.id_estado_actividad, ea.nombre ORDER BY cantidad DESC"
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
                    ea.nombre AS estado,
                    a.cupo_maximo,
                    COUNT(asig.id_asignacion) AS inscritos
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                LEFT JOIN ASIGNACION asig ON asig.id_actividad = a.id_actividad
                LEFT JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion AND eas.nombre != 'Cancelada'
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND a.fecha BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += """
                GROUP BY a.id_actividad, a.nombre, a.fecha, a.lugar, ea.nombre, a.cupo_maximo
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
                    COALESCE(SUM(d.monto), 0) AS total_monto,
                    COUNT(d.id_donacion) AS cantidad_donaciones
                FROM DONACION d
                WHERE d.fecha_donacion IS NOT NULL
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND d.fecha_donacion BETWEEN %s AND %s"
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
                    mp.nombre AS metodo,
                    COALESCE(SUM(d.monto), 0) AS total_monto,
                    COUNT(d.id_donacion) AS cantidad
                FROM DONACION d
                INNER JOIN METODO_PAGO mp ON d.id_metodo_pago = mp.id_metodo_pago
                WHERE d.monto IS NOT NULL
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND d.fecha_donacion BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY mp.id_metodo_pago, mp.nombre ORDER BY total_monto DESC"
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

            sql = """
                SELECT 
                    td.nombre AS tipo,
                    COUNT(d.id_donacion) AS cantidad
                FROM DONACION d
                INNER JOIN TIPO_DONACION td ON d.id_tipo_donacion = td.id_tipo_donacion
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND d.fecha_donacion BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY td.id_tipo_donacion, td.nombre ORDER BY cantidad DESC"
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
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND d.fecha_donacion BETWEEN %s AND %s"
                params.extend([fecha_ini, fecha_fin])

            sql += " GROUP BY i.id_insumo, i.nombre, i.unidad_medida ORDER BY total_cantidad DESC"
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
                    don.ci_nit AS documento,
                    COUNT(d.id_donacion) AS total_aportes,
                    COALESCE(SUM(d.monto), 0) AS total_dinero
                FROM DONACION d
                INNER JOIN DONANTE don ON d.id_donante = don.id_donante
                WHERE 1=1
            """
            params = []
            if fecha_ini and fecha_fin:
                sql += " AND d.fecha_donacion BETWEEN %s AND %s"
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