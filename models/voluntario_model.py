from datetime import date, timedelta
import mysql.connector
from mysql.connector import Error
from config.database import Database


class VoluntarioModel:
    def __init__(self):
        self.db = Database()

    def _columnas_tabla(self, cursor, tabla: str) -> set[str]:
        cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        return {
            (f["Field"] if isinstance(f, dict) else f[0])
            for f in cursor.fetchall()
        }

    def obtener_columnas_voluntario(self) -> set[str]:
        """Devuelve el conjunto de columnas reales existentes en la tabla VOLUNTARIO."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            return self._columnas_tabla(cursor, "VOLUNTARIO")
        except Error:
            return set()
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def _obtener_id_estado_vol(self, cursor, nombre_estado: str) -> int:
        cursor.execute(
            "SELECT id_estado_vol FROM ESTADO_VOLUNTARIO WHERE nombre = %s LIMIT 1",
            (nombre_estado,)
        )
        fila = cursor.fetchone()
        if not fila:
            raise ValueError(f"El estado '{nombre_estado}' no existe en ESTADO_VOLUNTARIO.")
        return fila["id_estado_vol"] if isinstance(fila, dict) else fila[0]

    @staticmethod
    def calcular_edad(fecha_nac: date) -> int:
        hoy = date.today()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))

    @staticmethod
    def _formatear_hora_td(valor_tiempo) -> str:
        if valor_tiempo is None:
            return "00:00"
        if isinstance(valor_tiempo, timedelta):
            total_seg = int(valor_tiempo.total_seconds())
            horas = (total_seg // 3600) % 24
            minutos = (total_seg % 3600) // 60
            return f"{horas:02d}:{minutos:02d}"
        return valor_tiempo.strftime("%H:%M")

    def registrar_postulante(self, datos: dict):
        """
        Inserta un postulante adaptándose dinámicamente a las columnas reales de VOLUNTARIO (v2.0).
        - Envía None (NULL) en campos opcionales vacíos.
        - No incluye fecha_creacion ni fecha_actualizacion (MySQL los asigna automáticamente).
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols = self._columnas_tabla(cursor, "VOLUNTARIO")
            id_estado_post = self._obtener_id_estado_vol(cursor, "Postulante")

            campos = ["ci", "nombres", "apellido_paterno"]
            valores = [datos["ci"], datos["nombres"], datos["apellido_paterno"]]

            opcionales = [
                ("apellido_materno", datos.get("apellido_materno")),
                ("fecha_nacimiento", datos.get("fecha_nacimiento")),
                ("telefono", datos.get("telefono")),
                ("correo", datos.get("correo")),
                ("direccion", datos.get("direccion")),
                ("fecha_inscripcion", date.today()),
            ]
            for col_nombre, val in opcionales:
                if col_nombre in cols:
                    campos.append(col_nombre)
                    valores.append(val)

            campos.append("id_estado_vol")
            valores.append(id_estado_post)

            if "id_usuario" in cols:
                campos.append("id_usuario")
                valores.append(None)

            if "fecha_admision" in cols:
                campos.append("fecha_admision")
                valores.append(None)

            if "id_usuario_registra" in cols:
                campos.append("id_usuario_registra")
                valores.append(datos.get("id_usuario_registra"))

            placeholders = ", ".join(["%s"] * len(campos))
            cursor.execute(
                f"INSERT INTO VOLUNTARIO ({', '.join(campos)}) VALUES ({placeholders})",
                tuple(valores)
            )
            conn.commit()
        except mysql.connector.IntegrityError as e:
            if conn:
                conn.rollback()
            if e.errno == 1062:
                raise ValueError("Este Carnet de Identidad (CI) ya se encuentra registrado en el sistema.")
            raise RuntimeError(f"Error de integridad al inscribir postulante: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_voluntarios(self, filtro_estado: str = "Todos", busqueda: str = "") -> list[dict]:
        """Consulta voluntarios verificando dinámicamente las columnas de VOLUNTARIO."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols = self._columnas_tabla(cursor, "VOLUNTARIO")

            def col_o_null(nombre_col: str) -> str:
                return f"v.{nombre_col}," if nombre_col in cols else f"NULL AS {nombre_col},"

            sql = f"""
                SELECT 
                    v.id_voluntario,
                    v.ci,
                    v.nombres,
                    v.apellido_paterno,
                    {col_o_null("apellido_materno")}
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, {"v.apellido_materno" if "apellido_materno" in cols else "NULL"}) AS nombre_completo,
                    {col_o_null("fecha_nacimiento")}
                    {col_o_null("telefono")}
                    {col_o_null("correo")}
                    {col_o_null("direccion")}
                    {col_o_null("fecha_inscripcion")}
                    {col_o_null("fecha_admision")}
                    {col_o_null("fecha_creacion")}
                    {col_o_null("fecha_actualizacion")}
                    ev.nombre AS estado,
                    u.usuario AS cuenta_usuario
                FROM VOLUNTARIO v
                INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                LEFT JOIN USUARIO u ON v.id_usuario = u.id_usuario
                WHERE 1=1
            """
            params = []

            if filtro_estado and filtro_estado != "Todos":
                sql += " AND ev.nombre = %s"
                params.append(filtro_estado)

            if busqueda.strip():
                if "apellido_materno" in cols:
                    sql += """
                        AND (
                            v.ci LIKE %s OR
                            v.nombres LIKE %s OR
                            v.apellido_paterno LIKE %s OR
                            v.apellido_materno LIKE %s
                        )
                    """
                    term = f"%{busqueda.strip()}%"
                    params.extend([term, term, term, term])
                else:
                    sql += """
                        AND (
                            v.ci LIKE %s OR
                            v.nombres LIKE %s OR
                            v.apellido_paterno LIKE %s
                        )
                    """
                    term = f"%{busqueda.strip()}%"
                    params.extend([term, term, term])

            sql += " ORDER BY v.id_voluntario DESC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                fn = f.get("fecha_nacimiento")
                if isinstance(fn, date):
                    f["edad"] = self.calcular_edad(fn)
                    f["fecha_nacimiento_str"] = fn.strftime("%Y-%m-%d")
                else:
                    f["edad"] = None
                    f["fecha_nacimiento_str"] = "-"

                f["fecha_creacion_str"] = (
                    f["fecha_creacion"].strftime("%Y-%m-%d %H:%M")
                    if f["fecha_creacion"] else "-"
                )
                f["fecha_actualizacion_str"] = (
                    f["fecha_actualizacion"].strftime("%Y-%m-%d %H:%M")
                    if f["fecha_actualizacion"] else "-"
                )

            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar voluntarios: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def admitir_voluntario_transaccion(self, id_voluntario: int, username: str, password_hash: str):
        """
        Crea cuenta en USUARIO y actualiza VOLUNTARIO con id_usuario, estado 'Admitido' y fecha_admision.
        MySQL actualiza fecha_actualizacion automáticamente.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_usr = self._columnas_tabla(cursor, "USUARIO")
            col_pass = "password_hash" if "password_hash" in cols_usr else (
                "contrasena" if "contrasena" in cols_usr else "password"
            )

            cursor.execute("SELECT id_rol FROM ROL WHERE nombre = 'Voluntario' LIMIT 1")
            rol_fila = cursor.fetchone()
            if not rol_fila:
                raise ValueError("El rol 'Voluntario' no existe en la tabla ROL.")

            cursor.execute(
                f"INSERT INTO USUARIO (usuario, {col_pass}, id_rol) VALUES (%s, %s, %s)",
                (username, password_hash, rol_fila["id_rol"])
            )
            nuevo_id_usuario = cursor.lastrowid

            id_estado_adm = self._obtener_id_estado_vol(cursor, "Admitido")
            cols_vol = self._columnas_tabla(cursor, "VOLUNTARIO")

            if "fecha_admision" in cols_vol:
                cursor.execute(
                    """
                    UPDATE VOLUNTARIO
                    SET id_usuario = %s,
                        id_estado_vol = %s,
                        fecha_admision = %s
                    WHERE id_voluntario = %s
                    """,
                    (nuevo_id_usuario, id_estado_adm, date.today(), id_voluntario)
                )
            else:
                cursor.execute(
                    """
                    UPDATE VOLUNTARIO
                    SET id_usuario = %s,
                        id_estado_vol = %s
                    WHERE id_voluntario = %s
                    """,
                    (nuevo_id_usuario, id_estado_adm, id_voluntario)
                )

            conn.commit()
        except mysql.connector.IntegrityError as e:
            if conn:
                conn.rollback()
            if e.errno == 1062:
                raise ValueError("El nombre de usuario generado ya existe. Intenta nuevamente.")
            raise RuntimeError(f"Error de integridad al admitir voluntario: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def cambiar_estado_voluntario(self, id_voluntario: int, nuevo_estado: str):
        """Cambia estado a 'Rechazado' o 'Inactivo'; MySQL actualiza fecha_actualizacion."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            id_estado = self._obtener_id_estado_vol(cursor, nuevo_estado)
            cursor.execute(
                "UPDATE VOLUNTARIO SET id_estado_vol = %s WHERE id_voluntario = %s",
                (id_estado, id_voluntario)
            )

            if nuevo_estado == "Inactivo":
                cols_usr = self._columnas_tabla(cursor, "USUARIO")
                if "activo" in cols_usr:
                    cursor.execute(
                        "SELECT id_usuario FROM VOLUNTARIO WHERE id_voluntario = %s",
                        (id_voluntario,)
                    )
                    vol = cursor.fetchone()
                    if vol and vol["id_usuario"]:
                        cursor.execute(
                            "UPDATE USUARIO SET activo = 0 WHERE id_usuario = %s",
                            (vol["id_usuario"],)
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

    def obtener_metricas_dashboard(self) -> dict:
        """
        Obtiene KPIs completos, horas acumuladas, próximas actividades y últimas donaciones
        para el Panel General Ejecutivo (Esquema v2.0).
        """
        resumen = {
            "postulantes": 0,
            "admitidos": 0,
            "horas_totales": 0.0,
            "actividades_total": 0,
            "actividades_programadas": 0,
            "actividades_en_curso": 0,
            "total_dinero": 0.0,
            "donaciones_material": 0,
            "proximas_actividades": [],
            "ultimas_donaciones": []
        }

        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            # 1. KPIs de Voluntarios
            cursor.execute(
                """
                SELECT 
                    SUM(CASE WHEN ev.nombre = 'Postulante' THEN 1 ELSE 0 END) AS postulantes,
                    SUM(CASE WHEN ev.nombre = 'Admitido' THEN 1 ELSE 0 END) AS admitidos
                FROM VOLUNTARIO v
                INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                """
            )
            vols = cursor.fetchone() or {}
            resumen["postulantes"] = int(vols.get("postulantes") or 0)
            resumen["admitidos"] = int(vols.get("admitidos") or 0)

            # 2. Total de Horas Cumplidas
            cursor.execute("SELECT COALESCE(SUM(horas_cumplidas), 0) AS horas FROM ASISTENCIA")
            hrs = cursor.fetchone() or {}
            resumen["horas_totales"] = float(hrs.get("horas") or 0.0)

            # 3. KPIs de Actividades
            cursor.execute(
                """
                SELECT 
                    COUNT(a.id_actividad) AS total,
                    SUM(CASE WHEN ea.nombre = 'Programada' THEN 1 ELSE 0 END) AS programadas,
                    SUM(CASE WHEN ea.nombre = 'En Curso' THEN 1 ELSE 0 END) AS en_curso
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                """
            )
            acts = cursor.fetchone() or {}
            resumen["actividades_total"] = int(acts.get("total") or 0)
            resumen["actividades_programadas"] = int(acts.get("programadas") or 0)
            resumen["actividades_en_curso"] = int(acts.get("en_curso") or 0)

            # 4. KPIs de Donaciones (Monetarias y en Especie)
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(CASE WHEN td.nombre = 'DINERO' THEN d.monto ELSE 0 END), 0) AS total_dinero,
                    SUM(CASE WHEN td.nombre = 'MATERIAL' THEN 1 ELSE 0 END) AS total_material
                FROM DONACION d
                INNER JOIN TIPO_DONACION td ON d.id_tipo_donacion = td.id_tipo_donacion
                """
            )
            dons = cursor.fetchone() or {}
            resumen["total_dinero"] = float(dons.get("total_dinero") or 0.0)
            resumen["donaciones_material"] = int(dons.get("total_material") or 0)

            # 5. Agenda Operativa: Próximas Actividades (Programadas o En Curso)
            cursor.execute(
                """
                SELECT 
                    a.nombre,
                    a.fecha,
                    a.hora_inicio,
                    a.hora_fin,
                    a.lugar,
                    a.cupo_maximo,
                    ea.nombre AS estado,
                    (
                        SELECT COUNT(*)
                        FROM ASIGNACION asig
                        INNER JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion
                        WHERE asig.id_actividad = a.id_actividad
                          AND eas.nombre != 'Cancelada'
                    ) AS inscritos
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                WHERE ea.nombre IN ('Programada', 'En Curso')
                ORDER BY a.fecha ASC, a.hora_inicio ASC
                LIMIT 6
                """
            )
            proximas = cursor.fetchall()
            for p in proximas:
                p["horario"] = f"{self._formatear_hora_td(p['hora_inicio'])} - {self._formatear_hora_td(p['hora_fin'])}"
                p["cupos_str"] = f"{int(p['inscritos'])} / {int(p['cupo_maximo'])}"
            resumen["proximas_actividades"] = proximas

            # 6. Últimas Donaciones Recibidas
            cursor.execute(
                """
                SELECT 
                    d.fecha_donacion,
                    don.nombre AS donante,
                    td.nombre AS tipo,
                    d.monto,
                    (
                        SELECT COUNT(*)
                        FROM DONACION_DETALLE dd
                        WHERE dd.id_donacion = d.id_donacion
                    ) AS items_count
                FROM DONACION d
                INNER JOIN DONANTE don ON d.id_donante = don.id_donante
                INNER JOIN TIPO_DONACION td ON d.id_tipo_donacion = td.id_tipo_donacion
                ORDER BY d.id_donacion DESC
                LIMIT 6
                """
            )
            ultimas = cursor.fetchall()
            for u in ultimas:
                if u["tipo"] == "DINERO" and u["monto"] is not None:
                    u["detalle_str"] = f"Bs. {float(u['monto']):,.2f}"
                else:
                    cant_items = int(u["items_count"] or 0)
                    u["detalle_str"] = f"{cant_items} tipo(s) de insumo"
            resumen["ultimas_donaciones"] = ultimas

            return resumen
        except Error:
            return resumen
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()