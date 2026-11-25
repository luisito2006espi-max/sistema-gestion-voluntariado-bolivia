from datetime import datetime, time, timedelta
import mysql.connector
from mysql.connector import Error
from config.database import Database


class ActividadModel:
    def __init__(self):
        self.db = Database()

    def _columnas_tabla(self, cursor, tabla: str) -> set[str]:
        cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        return {
            (f["Field"] if isinstance(f, dict) else f[0])
            for f in cursor.fetchall()
        }

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
        """Actualiza automáticamente estados 'Programada' -> 'En Curso' -> 'Finalizada' según reloj."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id_actividad, fecha, hora_inicio, hora_fin, estado
                FROM ACTIVIDAD
                WHERE estado IN ('Programada', 'En Curso')
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
                        "UPDATE ACTIVIDAD SET estado = 'Finalizada' WHERE id_actividad = %s",
                        (act["id_actividad"],)
                    )
                    hubo_cambios = True
                elif dt_inicio <= ahora < dt_fin and act["estado"] == "Programada":
                    cursor.execute(
                        "UPDATE ACTIVIDAD SET estado = 'En Curso' WHERE id_actividad = %s",
                        (act["id_actividad"],)
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
        """
        Crea una actividad en ACTIVIDAD (esquema v1.3 FNBC) calculando su estado
        inicial acorde a su fecha y horario sin bloqueos artificiales.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            ahora = datetime.now()
            dt_ini = datetime.combine(datos["fecha"], datos["hora_inicio"])
            dt_fin = datetime.combine(datos["fecha"], datos["hora_fin"])

            if ahora >= dt_fin:
                estado_inicial = "Finalizada"
            elif dt_ini <= ahora < dt_fin:
                estado_inicial = "En Curso"
            else:
                estado_inicial = "Programada"

            hora_ini_sql = datos["hora_inicio"].strftime("%H:%M:%S")
            hora_fin_sql = datos["hora_fin"].strftime("%H:%M:%S")

            cols = self._columnas_tabla(cursor, "ACTIVIDAD")
            campos = [
                "nombre", "descripcion", "fecha", "hora_inicio",
                "hora_fin", "lugar", "cupo_maximo", "estado"
            ]
            valores = [
                datos["nombre"],
                datos["descripcion"],
                datos["fecha"],
                hora_ini_sql,
                hora_fin_sql,
                datos["lugar"],
                datos["cupo_maximo"],
                estado_inicial
            ]

            for col_admin in ("id_admin_crea", "id_usuario_crea", "id_usuario_registra"):
                if col_admin in cols and datos.get("id_admin_crea"):
                    campos.append(col_admin)
                    valores.append(datos["id_admin_crea"])
                    break

            placeholders = ", ".join(["%s"] * len(campos))
            cursor.execute(
                f"INSERT INTO ACTIVIDAD ({', '.join(campos)}) VALUES ({placeholders})",
                tuple(valores)
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
                "SELECT estado FROM ACTIVIDAD WHERE id_actividad = %s LIMIT 1",
                (id_actividad,)
            )
            act = cursor.fetchone()
            if not act:
                raise ValueError("La actividad seleccionada no existe.")

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM ASIGNACION
                WHERE id_actividad = %s AND estado IN ('Pendiente', 'Confirmada')
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

            nuevo_estado = act["estado"]
            if act["estado"] != "Cancelada":
                ahora = datetime.now()
                dt_ini = datetime.combine(datos["fecha"], datos["hora_inicio"])
                dt_fin = datetime.combine(datos["fecha"], datos["hora_fin"])

                if ahora >= dt_fin:
                    nuevo_estado = "Finalizada"
                elif dt_ini <= ahora < dt_fin:
                    nuevo_estado = "En Curso"
                else:
                    nuevo_estado = "Programada"

            cursor.execute(
                """
                UPDATE ACTIVIDAD
                SET nombre = %s,
                    descripcion = %s,
                    fecha = %s,
                    hora_inicio = %s,
                    hora_fin = %s,
                    lugar = %s,
                    cupo_maximo = %s,
                    estado = %s
                WHERE id_actividad = %s
                """,
                (
                    datos["nombre"],
                    datos["descripcion"],
                    datos["fecha"],
                    hora_ini_sql,
                    hora_fin_sql,
                    datos["lugar"],
                    datos["cupo_maximo"],
                    nuevo_estado,
                    id_actividad
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
                    a.estado,
                    (
                        SELECT COUNT(*)
                        FROM ASIGNACION asig
                        WHERE asig.id_actividad = a.id_actividad
                          AND asig.estado IN ('Pendiente', 'Confirmada')
                    ) AS inscritos
                FROM ACTIVIDAD a
                WHERE 1=1
            """
            params = []
            if filtro_estado and filtro_estado != "Todas":
                sql += " AND a.estado = %s"
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
            cursor.execute(
                "UPDATE ACTIVIDAD SET estado = %s WHERE id_actividad = %s",
                (nuevo_estado, id_actividad)
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
        """Lista exclusivamente voluntarios con estado 'Admitido' e incluye sus strikes actuales."""
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
                    v.telefono,
                    COALESCE(
                        (SELECT SUM(s.cantidad_strikes)
                         FROM STRIKE_VOLUNTARIO s
                         WHERE s.id_voluntario = v.id_voluntario),
                        0
                    ) AS total_strikes
                FROM VOLUNTARIO v
                WHERE v.estado = 'Admitido'
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
            filas = cursor.fetchall()
            for f in filas:
                f["total_strikes"] = int(f.get("total_strikes") or 0)
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar voluntarios admitidos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_asignaciones_actividad(self, id_actividad: int) -> list[dict]:
        """Consulta asignaciones activas ('Pendiente' o 'Confirmada') con asistencia FNBC."""
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
                    asig.estado AS estado_asignacion,
                    asis.id_asignacion AS id_asistencia,
                    asis.asistio,
                    asis.hora_entrada,
                    asis.hora_salida,
                    ROUND(
                        COALESCE(
                            CASE WHEN asis.asistio = 1
                            THEN TIMESTAMPDIFF(MINUTE, asis.hora_entrada, asis.hora_salida) / 60.0
                            ELSE 0 END,
                            0
                        ),
                        2
                    ) AS horas_cumplidas,
                    asis.observaciones,
                    COALESCE(
                        (SELECT SUM(s.cantidad_strikes)
                         FROM STRIKE_VOLUNTARIO s
                         WHERE s.id_voluntario = v.id_voluntario),
                        0
                    ) AS total_strikes
                FROM ASIGNACION asig
                INNER JOIN VOLUNTARIO v ON asig.id_voluntario = v.id_voluntario
                LEFT JOIN ASISTENCIA asis ON asis.id_asignacion = asig.id_asignacion
                WHERE asig.id_actividad = %s
                  AND asig.estado IN ('Pendiente', 'Confirmada')
                ORDER BY v.apellido_paterno ASC, v.nombres ASC
                """,
                (id_actividad,)
            )
            filas = cursor.fetchall()
            for f in filas:
                f["hora_entrada_str"] = self.formatear_hora(f["hora_entrada"]) if f.get("hora_entrada") else None
                f["hora_salida_str"] = self.formatear_hora(f["hora_salida"]) if f.get("hora_salida") else None
                f["horas_cumplidas"] = float(f.get("horas_cumplidas") or 0.0)
                f["total_strikes"] = int(f.get("total_strikes") or 0)
            return filas
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
                "SELECT nombre, fecha, cupo_maximo, estado FROM ACTIVIDAD WHERE id_actividad = %s LIMIT 1",
                (id_actividad,)
            )
            act = cursor.fetchone()
            if not act:
                raise ValueError("La actividad seleccionada no existe.")
            if act["estado"] in ("Finalizada", "Cancelada"):
                raise ValueError(f"No se pueden asignar voluntarios a una actividad '{act['estado']}'.")

            cursor.execute(
                "SELECT estado FROM VOLUNTARIO WHERE id_voluntario = %s LIMIT 1",
                (id_voluntario,)
            )
            vol = cursor.fetchone()
            if not vol:
                raise ValueError("El voluntario seleccionado no existe.")
            if vol["estado"] != "Admitido":
                raise ValueError(
                    f"No se puede asignar al voluntario porque su estado actual es '{vol['estado']}'."
                )

            # Regla: Máximo 1 actividad activa por día
            cursor.execute(
                """
                SELECT a2.nombre AS actividad_existente
                FROM ASIGNACION asig
                INNER JOIN ACTIVIDAD a2 ON asig.id_actividad = a2.id_actividad
                WHERE asig.id_voluntario = %s
                  AND a2.fecha = %s
                  AND asig.estado IN ('Pendiente', 'Confirmada')
                  AND a2.estado != 'Cancelada'
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
                FROM ASIGNACION
                WHERE id_actividad = %s AND estado IN ('Pendiente', 'Confirmada')
                """,
                (id_actividad,)
            )
            ocupados = int(cursor.fetchone()["total"])
            if ocupados >= int(act["cupo_maximo"]):
                raise ValueError("Cupo máximo alcanzado. No hay lugares disponibles en esta actividad.")

            # Verificar si existió una asignación previa para la misma dupla (id_voluntario, id_actividad)
            cursor.execute(
                """
                SELECT id_asignacion, estado
                FROM ASIGNACION
                WHERE id_voluntario = %s AND id_actividad = %s
                LIMIT 1
                """,
                (id_voluntario, id_actividad)
            )
            previa = cursor.fetchone()
            if previa:
                if previa["estado"] in ("Pendiente", "Confirmada"):
                    raise ValueError("Este voluntario ya se encuentra asignado a esta actividad.")
                cursor.execute(
                    """
                    UPDATE ASIGNACION
                    SET estado = 'Confirmada',
                        id_admin_asigna = %s
                    WHERE id_asignacion = %s
                    """,
                    (id_admin, previa["id_asignacion"])
                )
            else:
                cols_asig = self._columnas_tabla(cursor, "ASIGNACION")
                campos = ["id_voluntario", "id_actividad", "id_admin_asigna", "estado"]
                valores = [id_voluntario, id_actividad, id_admin, "Confirmada"]

                if "fecha_asignacion" in cols_asig:
                    campos.append("fecha_asignacion")
                    valores.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                placeholders = ", ".join(["%s"] * len(campos))
                cursor.execute(
                    f"INSERT INTO ASIGNACION ({', '.join(campos)}) VALUES ({placeholders})",
                    tuple(valores)
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
        """Elimina una asignación por error operativo sin generar strike (si no tiene asistencia)."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT id_asignacion AS id_asistencia FROM ASISTENCIA WHERE id_asignacion = %s LIMIT 1",
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

    def cancelar_asignacion_con_strike(
        self,
        id_asignacion: int,
        cantidad_strikes: int,
        motivo: str,
        id_admin_registra: int | None = None
    ) -> dict:
        """
        Cancela una asignación ('Cancelada') y, si cantidad_strikes > 0, inserta en
        STRIKE_VOLUNTARIO. Si el acumulado llega a >= 5 strikes, marca al voluntario
        como 'Inactivo_Definitivo', bloquea USUARIO.activo = 0 y cancela sus futuras asignaciones.
        """
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
                    asig.estado AS estado_asignacion,
                    v.id_usuario,
                    v.estado AS estado_voluntario,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_voluntario,
                    a.nombre AS nombre_actividad
                FROM ASIGNACION asig
                INNER JOIN VOLUNTARIO v ON asig.id_voluntario = v.id_voluntario
                INNER JOIN ACTIVIDAD a ON asig.id_actividad = a.id_actividad
                WHERE asig.id_asignacion = %s
                FOR UPDATE
                """,
                (id_asignacion,)
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("La asignación seleccionada no existe.")

            if fila["estado_asignacion"] == "Cancelada":
                raise ValueError("Esta asignación ya fue cancelada previamente.")

            cursor.execute(
                "SELECT id_asignacion AS id_asistencia FROM ASISTENCIA WHERE id_asignacion = %s LIMIT 1",
                (id_asignacion,)
            )
            if cursor.fetchone():
                raise ValueError("No se puede cancelar una asignación que ya cuenta con registro de asistencia.")

            # 1. Marcar asignación como Cancelada
            cursor.execute(
                "UPDATE ASIGNACION SET estado = 'Cancelada' WHERE id_asignacion = %s",
                (id_asignacion,)
            )

            id_voluntario = fila["id_voluntario"]
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. Registrar en STRIKE_VOLUNTARIO si aplica penalización
            if cantidad_strikes > 0:
                cols_st = self._columnas_tabla(cursor, "STRIKE_VOLUNTARIO")
                campos_st = ["id_voluntario", "cantidad_strikes", "motivo"]
                valores_st = [id_voluntario, int(cantidad_strikes), motivo.strip()]

                if "id_asignacion" in cols_st:
                    campos_st.append("id_asignacion")
                    valores_st.append(id_asignacion)

                for col_f in ("fecha_strike", "fecha_registro", "fecha"):
                    if col_f in cols_st:
                        campos_st.append(col_f)
                        valores_st.append(ahora)
                        break

                for col_u in ("id_admin_registra", "id_usuario_registra", "id_usuario"):
                    if col_u in cols_st:
                        campos_st.append(col_u)
                        valores_st.append(id_admin_registra)
                        break

                placeholders = ", ".join(["%s"] * len(campos_st))
                cursor.execute(
                    f"INSERT INTO STRIKE_VOLUNTARIO ({', '.join(campos_st)}) VALUES ({placeholders})",
                    tuple(valores_st)
                )

            # 3. Calcular total acumulado de strikes
            cursor.execute(
                """
                SELECT COALESCE(SUM(cantidad_strikes), 0) AS total
                FROM STRIKE_VOLUNTARIO
                WHERE id_voluntario = %s
                """,
                (id_voluntario,)
            )
            total_strikes = int(cursor.fetchone()["total"])
            inactivado_definitivo = False

            # 4. Regla de los 5 Strikes -> Inactivo_Definitivo irreversible
            if total_strikes >= 5 and fila["estado_voluntario"] != "Inactivo_Definitivo":
                cursor.execute(
                    "UPDATE VOLUNTARIO SET estado = 'Inactivo_Definitivo' WHERE id_voluntario = %s",
                    (id_voluntario,)
                )
                if fila["id_usuario"]:
                    cursor.execute(
                        "UPDATE USUARIO SET activo = 0 WHERE id_usuario = %s",
                        (fila["id_usuario"],)
                    )
                cursor.execute(
                    """
                    UPDATE ASIGNACION
                    SET estado = 'Cancelada'
                    WHERE id_voluntario = %s
                      AND estado IN ('Pendiente', 'Confirmada')
                      AND id_asignacion != %s
                    """,
                    (id_voluntario, id_asignacion)
                )
                inactivado_definitivo = True

            conn.commit()
            return {
                "voluntario": fila["nombre_voluntario"],
                "actividad": fila["nombre_actividad"],
                "strikes_aplicados": int(cantidad_strikes),
                "total_strikes": total_strikes,
                "inactivado_definitivo": inactivado_definitivo
            }
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
        hora_entrada_sql: str | None,
        hora_salida_sql: str | None,
        horas_cumplidas: float,
        observaciones: str | None,
        id_admin_registra: int | None = None
    ):
        """
        Registra o actualiza ASISTENCIA en formato FNBC (hora_entrada y hora_salida)
        adaptándose dinámicamente a columnas opcionales de auditoría.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols = self._columnas_tabla(cursor, "ASISTENCIA")
            cursor.execute(
                "SELECT id_asignacion AS id_asistencia FROM ASISTENCIA WHERE id_asignacion = %s LIMIT 1",
                (id_asignacion,)
            )
            existente = cursor.fetchone()

            if existente:
                sets = ["asistio = %s", "observaciones = %s"]
                vals = [1 if asistio else 0, observaciones]

                if "hora_entrada" in cols:
                    sets.append("hora_entrada = %s")
                    vals.append(hora_entrada_sql if asistio else None)
                if "hora_salida" in cols:
                    sets.append("hora_salida = %s")
                    vals.append(hora_salida_sql if asistio else None)
                if "horas_cumplidas" in cols:
                    sets.append("horas_cumplidas = %s")
                    vals.append(horas_cumplidas if asistio else 0.0)

                vals.append(id_asignacion)
                cursor.execute(
                    f"UPDATE ASISTENCIA SET {', '.join(sets)} WHERE id_asignacion = %s",
                    tuple(vals)
                )
            else:
                campos = ["id_asignacion", "asistio", "observaciones"]
                vals = [id_asignacion, 1 if asistio else 0, observaciones]

                if "hora_entrada" in cols:
                    campos.append("hora_entrada")
                    vals.append(hora_entrada_sql if asistio else None)
                if "hora_salida" in cols:
                    campos.append("hora_salida")
                    vals.append(hora_salida_sql if asistio else None)
                if "horas_cumplidas" in cols:
                    campos.append("horas_cumplidas")
                    vals.append(horas_cumplidas if asistio else 0.0)
                for col_u in ("id_admin_registra", "id_usuario_registra", "id_usuario"):
                    if col_u in cols and id_admin_registra:
                        campos.append(col_u)
                        vals.append(id_admin_registra)
                        break

                placeholders = ", ".join(["%s"] * len(campos))
                cursor.execute(
                    f"INSERT INTO ASISTENCIA ({', '.join(campos)}) VALUES ({placeholders})",
                    tuple(vals)
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
                    v.estado,
                    COALESCE(
                        (SELECT SUM(s.cantidad_strikes)
                         FROM STRIKE_VOLUNTARIO s
                         WHERE s.id_voluntario = v.id_voluntario),
                        0
                    ) AS total_strikes
                FROM VOLUNTARIO v
                WHERE v.id_usuario = %s
                LIMIT 1
                """,
                (id_usuario,)
            )
            perfil = cursor.fetchone()
            if perfil:
                perfil["total_strikes"] = int(perfil.get("total_strikes") or 0)
            return perfil
        except Error as e:
            raise RuntimeError(f"Error al consultar perfil del voluntario: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def listar_strikes_voluntario(self, id_voluntario: int) -> list[dict]:
        """Consulta el detalle histórico de strikes de un voluntario."""
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cols_st = self._columnas_tabla(cursor, "STRIKE_VOLUNTARIO")
            col_fecha = next((c for c in ("fecha_strike", "fecha_registro", "fecha") if c in cols_st), None)
            tiene_asig = "id_asignacion" in cols_st

            sel_fecha = f"s.{col_fecha} AS fecha_strike," if col_fecha else "NULL AS fecha_strike,"
            sel_act = "a.nombre AS actividad," if tiene_asig else "NULL AS actividad,"
            joins = (
                "LEFT JOIN ASIGNACION asig ON s.id_asignacion = asig.id_asignacion "
                "LEFT JOIN ACTIVIDAD a ON asig.id_actividad = a.id_actividad"
                if tiene_asig else ""
            )
            order_by = f"s.{col_fecha} DESC" if col_fecha else "s.id_strike DESC"

            cursor.execute(
                f"""
                SELECT 
                    s.id_strike,
                    {sel_fecha}
                    {sel_act}
                    s.cantidad_strikes,
                    s.motivo
                FROM STRIKE_VOLUNTARIO s
                {joins}
                WHERE s.id_voluntario = %s
                ORDER BY {order_by}
                """,
                (id_voluntario,)
            )
            filas = cursor.fetchall()
            for f in filas:
                fs = f.get("fecha_strike")
                f["fecha_str"] = fs.strftime("%Y-%m-%d %H:%M") if hasattr(fs, "strftime") else str(fs or "-")
            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar strikes del voluntario: {e}")
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
                    a.estado AS estado_actividad,
                    asig.estado AS estado_asignacion,
                    asis.id_asignacion AS id_asistencia,
                    asis.asistio,
                    asis.hora_entrada,
                    asis.hora_salida,
                    ROUND(
                        COALESCE(
                            CASE WHEN asis.asistio = 1
                            THEN TIMESTAMPDIFF(MINUTE, asis.hora_entrada, asis.hora_salida) / 60.0
                            ELSE 0 END,
                            0
                        ),
                        2
                    ) AS horas_cumplidas,
                    asis.observaciones
                FROM ASIGNACION asig
                INNER JOIN ACTIVIDAD a ON asig.id_actividad = a.id_actividad
                LEFT JOIN ASISTENCIA asis ON asis.id_asignacion = asig.id_asignacion
                WHERE asig.id_voluntario = %s
            """
            params = [id_voluntario]

            if filtro_estado and filtro_estado != "Todas":
                sql += " AND a.estado = %s"
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