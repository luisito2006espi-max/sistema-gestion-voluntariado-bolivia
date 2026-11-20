from datetime import datetime, time, timedelta
import mysql.connector
from mysql.connector import Error
from config.database import Database


class ActividadModel:
    def __init__(self):
        self.db = Database()

    def _obtener_id_estado_actividad(self, cursor, nombre_estado: str) -> int:
        cursor.execute(
            "SELECT id_estado_actividad FROM ESTADO_ACTIVIDAD WHERE nombre = %s LIMIT 1",
            (nombre_estado,)
        )
        fila = cursor.fetchone()
        if not fila:
            raise ValueError(f"El estado '{nombre_estado}' no existe en ESTADO_ACTIVIDAD.")
        return fila["id_estado_actividad"] if isinstance(fila, dict) else fila[0]

    def _obtener_id_estado_asignacion(self, cursor, nombre_estado: str) -> int:
        cursor.execute(
            "SELECT id_estado_asignacion FROM ESTADO_ASIGNACION WHERE nombre = %s LIMIT 1",
            (nombre_estado,)
        )
        fila = cursor.fetchone()
        if not fila:
            raise ValueError(f"El estado '{nombre_estado}' no existe en ESTADO_ASIGNACION.")
        return fila["id_estado_asignacion"] if isinstance(fila, dict) else fila[0]

    @staticmethod
    def formatear_hora(valor_tiempo) -> str:
        if valor_tiempo is None:
            return "00:00"
        if isinstance(valor_tiempo, timedelta):
            total_seg = int(valor_tiempo.total_seconds())
            horas = (total_seg // 3600) % 24
            minutos = (total_seg % 3600) // 60
            return f"{horas:02d}:{minutos:02d}"
        return valor_tiempo.strftime("%H:%M")

    @staticmethod
    def _combinar_fecha_hora(fecha_val, hora_val) -> datetime:
        if isinstance(hora_val, timedelta):
            return datetime.combine(fecha_val, time.min) + hora_val
        return datetime.combine(fecha_val, hora_val)

    @staticmethod
    def calcular_duracion_horas(hora_inicio, hora_fin) -> float:
        if isinstance(hora_inicio, timedelta) and isinstance(hora_fin, timedelta):
            diff = (hora_fin - hora_inicio).total_seconds() / 3600.0
            return round(max(diff, 0.0), 2)
        return 0.0

    def sincronizar_estados_por_horario(self):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            id_en_curso = self._obtener_id_estado_actividad(cursor, "En Curso")
            id_finalizada = self._obtener_id_estado_actividad(cursor, "Finalizada")

            cursor.execute(
                """
                SELECT a.id_actividad, a.fecha, a.hora_inicio, a.hora_fin, ea.nombre AS estado
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                WHERE ea.nombre IN ('Programada', 'En Curso')
                """
            )
            actividades = cursor.fetchall()
            ahora = datetime.now()
            hubo_cambios = False

            for act in actividades:
                dt_inicio = self._combinar_fecha_hora(act["fecha"], act["hora_inicio"])
                dt_fin = self._combinar_fecha_hora(act["fecha"], act["hora_fin"])

                if ahora >= dt_fin and act["estado"] in ("Programada", "En Curso"):
                    cursor.execute(
                        "UPDATE ACTIVIDAD SET id_estado_actividad = %s WHERE id_actividad = %s",
                        (id_finalizada, act["id_actividad"])
                    )
                    hubo_cambios = True
                elif dt_inicio <= ahora < dt_fin and act["estado"] == "Programada":
                    cursor.execute(
                        "UPDATE ACTIVIDAD SET id_estado_actividad = %s WHERE id_actividad = %s",
                        (id_en_curso, act["id_actividad"])
                    )
                    hubo_cambios = True

            if hubo_cambios:
                conn.commit()
        except Exception:
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def crear_actividad(self, datos: dict):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            id_estado_prog = self._obtener_id_estado_actividad(cursor, "Programada")
            # Precaución v2.0: formato exacto HH:MM:SS para columnas TIME
            hora_ini_sql = datos["hora_inicio"].strftime("%H:%M:%S")
            hora_fin_sql = datos["hora_fin"].strftime("%H:%M:%S")

            cursor.execute(
                """
                INSERT INTO ACTIVIDAD (
                    nombre, descripcion, fecha, hora_inicio, hora_fin,
                    lugar, cupo_maximo, id_estado_actividad
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    datos["nombre"],
                    datos["descripcion"],
                    datos["fecha"],
                    hora_ini_sql,
                    hora_fin_sql,
                    datos["lugar"],
                    datos["cupo_maximo"],
                    id_estado_prog
                )
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

    def editar_actividad(self, id_actividad: int, datos: dict):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT ea.nombre AS estado
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                WHERE a.id_actividad = %s
                """,
                (id_actividad,)
            )
            act = cursor.fetchone()
            if not act:
                raise ValueError("La actividad seleccionada no existe.")

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM ASIGNACION asig
                INNER JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion
                WHERE asig.id_actividad = %s AND eas.nombre != 'Cancelada'
                """,
                (id_actividad,)
            )
            inscritos = int(cursor.fetchone()["total"])
            if datos["cupo_maximo"] < inscritos:
                raise ValueError(
                    f"No puedes reducir el cupo a {datos['cupo_maximo']} porque ya hay {inscritos} voluntarios asignados."
                )

            hora_ini_sql = datos["hora_inicio"].strftime("%H:%M:%S")
            hora_fin_sql = datos["hora_fin"].strftime("%H:%M:%S")

            nuevo_estado_sql = ""
            params = [
                datos["nombre"],
                datos["descripcion"],
                datos["fecha"],
                hora_ini_sql,
                hora_fin_sql,
                datos["lugar"],
                datos["cupo_maximo"]
            ]

            if act["estado"] != "Cancelada":
                ahora = datetime.now()
                dt_ini = datetime.combine(datos["fecha"], datos["hora_inicio"])
                dt_fin = datetime.combine(datos["fecha"], datos["hora_fin"])

                if ahora >= dt_fin:
                    estado_obj = "Finalizada"
                elif dt_ini <= ahora < dt_fin:
                    estado_obj = "En Curso"
                else:
                    estado_obj = "Programada"

                id_est = self._obtener_id_estado_actividad(cursor, estado_obj)
                nuevo_estado_sql = ", id_estado_actividad = %s"
                params.append(id_est)

            params.append(id_actividad)

            cursor.execute(
                f"""
                UPDATE ACTIVIDAD
                SET nombre = %s,
                    descripcion = %s,
                    fecha = %s,
                    hora_inicio = %s,
                    hora_fin = %s,
                    lugar = %s,
                    cupo_maximo = %s
                    {nuevo_estado_sql}
                WHERE id_actividad = %s
                """,
                tuple(params)
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

    def listar_actividades(self, filtro_estado: str = "Todas") -> list[dict]:
        self.sincronizar_estados_por_horario()

        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    a.id_actividad,
                    a.nombre,
                    a.descripcion,
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
                WHERE 1=1
            """
            params = []
            if filtro_estado and filtro_estado != "Todas":
                sql += " AND ea.nombre = %s"
                params.append(filtro_estado)

            sql += " ORDER BY a.fecha DESC, a.hora_inicio ASC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                f["hora_inicio_str"] = self.formatear_hora(f["hora_inicio"])
                f["hora_fin_str"] = self.formatear_hora(f["hora_fin"])
                f["duracion_horas"] = self.calcular_duracion_horas(f["hora_inicio"], f["hora_fin"])
                f["cupos_disponibles"] = max(int(f["cupo_maximo"]) - int(f["inscritos"]), 0)

            return filas
        except Error as e:
            raise RuntimeError(f"Error MySQL al listar actividades: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def cambiar_estado_actividad(self, id_actividad: int, nuevo_estado: str):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            id_estado = self._obtener_id_estado_actividad(cursor, nuevo_estado)
            cursor.execute(
                "UPDATE ACTIVIDAD SET id_estado_actividad = %s WHERE id_actividad = %s",
                (id_estado, id_actividad)
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

    def listar_voluntarios_disponibles(self, busqueda: str = "") -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    v.id_voluntario,
                    v.ci,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_completo,
                    v.telefono
                FROM VOLUNTARIO v
                INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                WHERE ev.nombre = 'Admitido'
            """
            params = []
            if busqueda.strip():
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

            sql += " ORDER BY v.apellido_paterno ASC, v.nombres ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al consultar voluntarios admitidos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_asignaciones_actividad(self, id_actividad: int) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT 
                    asig.id_asignacion,
                    asig.id_voluntario,
                    asig.id_actividad,
                    v.ci,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_completo,
                    v.telefono,
                    eas.nombre AS estado_asignacion,
                    asis.id_asistencia,
                    asis.asistio,
                    asis.horas_cumplidas,
                    asis.observaciones
                FROM ASIGNACION asig
                INNER JOIN VOLUNTARIO v ON asig.id_voluntario = v.id_voluntario
                INNER JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion
                LEFT JOIN ASISTENCIA asis ON asis.id_asignacion = asig.id_asignacion
                WHERE asig.id_actividad = %s
                  AND eas.nombre != 'Cancelada'
                ORDER BY v.apellido_paterno ASC, v.nombres ASC
                """,
                (id_actividad,)
            )
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Error al listar asignaciones: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def asignar_voluntario_actividad(self, id_actividad: int, id_voluntario: int, id_admin: int):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT a.nombre, a.fecha, a.cupo_maximo, ea.nombre AS estado
                FROM ACTIVIDAD a
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                WHERE a.id_actividad = %s
                """,
                (id_actividad,)
            )
            act = cursor.fetchone()
            if not act:
                raise ValueError("La actividad seleccionada no existe.")
            if act["estado"] in ("Finalizada", "Cancelada"):
                raise ValueError(f"No se pueden asignar voluntarios a una actividad '{act['estado']}'.")

            cursor.execute(
                """
                SELECT a2.nombre AS actividad_existente
                FROM ASIGNACION asig
                INNER JOIN ACTIVIDAD a2 ON asig.id_actividad = a2.id_actividad
                INNER JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion
                INNER JOIN ESTADO_ACTIVIDAD ea2 ON a2.id_estado_actividad = ea2.id_estado_actividad
                WHERE asig.id_voluntario = %s
                  AND a2.fecha = %s
                  AND eas.nombre != 'Cancelada'
                  AND ea2.nombre != 'Cancelada'
                LIMIT 1
                """,
                (id_voluntario, act["fecha"])
            )
            conflicto = cursor.fetchone()
            if conflicto:
                raise ValueError(
                    f"El voluntario ya tiene asignada la actividad '{conflicto['actividad_existente']}' "
                    f"el día {act['fecha']}. No puede tener 2 actividades el mismo día."
                )

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM ASIGNACION asig
                INNER JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion
                WHERE asig.id_actividad = %s AND eas.nombre != 'Cancelada'
                """,
                (id_actividad,)
            )
            ocupados = int(cursor.fetchone()["total"])
            if ocupados >= int(act["cupo_maximo"]):
                raise ValueError("Cupo máximo alcanzado. No hay lugares disponibles en esta actividad.")

            id_estado_conf = self._obtener_id_estado_asignacion(cursor, "Confirmada")
            cursor.execute(
                """
                INSERT INTO ASIGNACION (id_voluntario, id_actividad, id_admin_asigna, id_estado_asignacion)
                VALUES (%s, %s, %s, %s)
                """,
                (id_voluntario, id_actividad, id_admin, id_estado_conf)
            )
            conn.commit()
        except mysql.connector.IntegrityError as e:
            if conn:
                conn.rollback()
            if e.errno == 1062:
                raise ValueError("Este voluntario ya se encuentra asignado a esta actividad.")
            raise RuntimeError(f"Error de integridad al asignar voluntario: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def quitar_asignacion(self, id_asignacion: int):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT id_asistencia FROM ASISTENCIA WHERE id_asignacion = %s",
                (id_asignacion,)
            )
            if cursor.fetchone():
                raise ValueError("No se puede quitar esta asignación porque ya tiene asistencia registrada.")

            cursor.execute("DELETE FROM ASIGNACION WHERE id_asignacion = %s", (id_asignacion,))
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

    def registrar_o_actualizar_asistencia(
        self,
        id_asignacion: int,
        asistio: bool,
        horas_cumplidas: float,
        observaciones: str
    ):
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT id_asistencia FROM ASISTENCIA WHERE id_asignacion = %s LIMIT 1",
                (id_asignacion,)
            )
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    """
                    UPDATE ASISTENCIA
                    SET asistio = %s,
                        horas_cumplidas = %s,
                        observaciones = %s
                    WHERE id_asignacion = %s
                    """,
                    (1 if asistio else 0, horas_cumplidas, observaciones, id_asignacion)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO ASISTENCIA (id_asignacion, asistio, horas_cumplidas, observaciones)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_asignacion, 1 if asistio else 0, horas_cumplidas, observaciones)
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

    def obtener_perfil_voluntario_por_usuario(self, id_usuario: int) -> dict | None:
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT 
                    v.id_voluntario,
                    v.ci,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_completo,
                    v.fecha_admision,
                    ev.nombre AS estado
                FROM VOLUNTARIO v
                INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
                WHERE v.id_usuario = %s
                LIMIT 1
                """,
                (id_usuario,)
            )
            return cursor.fetchone()
        except Error as e:
            raise RuntimeError(f"Error al consultar perfil del voluntario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_actividades_voluntario(self, id_voluntario: int, filtro_estado: str = "Todas") -> list[dict]:
        self.sincronizar_estados_por_horario()

        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    asig.id_asignacion,
                    a.id_actividad,
                    a.nombre AS actividad,
                    a.descripcion,
                    a.fecha,
                    a.hora_inicio,
                    a.hora_fin,
                    a.lugar,
                    ea.nombre AS estado_actividad,
                    eas.nombre AS estado_asignacion,
                    asis.id_asistencia,
                    asis.asistio,
                    asis.horas_cumplidas,
                    asis.observaciones
                FROM ASIGNACION asig
                INNER JOIN ACTIVIDAD a ON asig.id_actividad = a.id_actividad
                INNER JOIN ESTADO_ACTIVIDAD ea ON a.id_estado_actividad = ea.id_estado_actividad
                INNER JOIN ESTADO_ASIGNACION eas ON asig.id_estado_asignacion = eas.id_estado_asignacion
                LEFT JOIN ASISTENCIA asis ON asis.id_asignacion = asig.id_asignacion
                WHERE asig.id_voluntario = %s
            """
            params = [id_voluntario]

            if filtro_estado and filtro_estado != "Todas":
                sql += " AND ea.nombre = %s"
                params.append(filtro_estado)

            sql += " ORDER BY a.fecha DESC, a.hora_inicio ASC"
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                f["hora_inicio_str"] = self.formatear_hora(f["hora_inicio"])
                f["hora_fin_str"] = self.formatear_hora(f["hora_fin"])
                f["duracion_horas"] = self.calcular_duracion_horas(f["hora_inicio"], f["hora_fin"])
                f["horas_cumplidas"] = float(f["horas_cumplidas"] or 0.0)

            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar actividades del voluntario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()