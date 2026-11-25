from datetime import date, datetime, timedelta
import mysql.connector
from mysql.connector import Error
from config.database import Database


class VoluntarioModel:
    def __init__(self):
        self.db = Database()

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
        Inserta un postulante en VOLUNTARIO (esquema v1.3 FNBC) con estado 'Postulante',
        fecha_inscripcion con hora exacta y trazabilidad obligatoria de id_admin_registra.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            fecha_inscripcion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO VOLUNTARIO (
                    ci,
                    nombres,
                    apellido_paterno,
                    apellido_materno,
                    fecha_nacimiento,
                    telefono,
                    correo,
                    direccion,
                    estado,
                    fecha_inscripcion,
                    fecha_admision,
                    id_usuario,
                    id_admin_registra
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Postulante', %s, NULL, NULL, %s)
                """,
                (
                    datos["ci"],
                    datos["nombres"],
                    datos["apellido_paterno"],
                    datos.get("apellido_materno"),
                    datos["fecha_nacimiento"],
                    datos["telefono"],
                    datos.get("correo"),
                    datos.get("direccion"),
                    fecha_inscripcion,
                    datos["id_admin_registra"]
                )
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
        """
        Consulta voluntarios junto con su evaluación documental (1:1), cuenta de usuario
        y strikes acumulados en STRIKE_VOLUNTARIO.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            sql = """
                SELECT 
                    v.id_voluntario,
                    v.ci,
                    v.nombres,
                    v.apellido_paterno,
                    v.apellido_materno,
                    CONCAT_WS(' ', v.nombres, v.apellido_paterno, v.apellido_materno) AS nombre_completo,
                    v.fecha_nacimiento,
                    v.telefono,
                    v.correo,
                    v.direccion,
                    v.estado,
                    v.fecha_inscripcion,
                    v.fecha_admision,
                    v.id_usuario,
                    u.usuario AS cuenta_usuario,
                    ea.ci_presentado,
                    ea.datos_verificados,
                    ea.disponibilidad,
                    ea.acepta_reglas,
                    ea.antecedentes_presentado,
                    ea.tiene_antecedentes,
                    ea.cv_presentado,
                    ea.nivel_educativo,
                    ea.situacion_laboral,
                    ea.resultado_automatico,
                    ea.decision_final,
                    ea.motivo_cambio,
                    ea.fecha_evaluacion,
                    COALESCE(
                        (SELECT SUM(s.cantidad_strikes)
                         FROM STRIKE_VOLUNTARIO s
                         WHERE s.id_voluntario = v.id_voluntario),
                        0
                    ) AS total_strikes
                FROM VOLUNTARIO v
                LEFT JOIN USUARIO u ON v.id_usuario = u.id_usuario
                LEFT JOIN EVALUACION_ADMISION ea ON v.id_voluntario = ea.id_voluntario
                WHERE 1=1
            """
            params = []

            if filtro_estado and filtro_estado != "Todos":
                sql += " AND v.estado = %s"
                params.append(filtro_estado)

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

                fi = f.get("fecha_inscripcion")
                f["fecha_inscripcion_str"] = (
                    fi.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(fi, "strftime") else str(fi or "-")
                )
                f["total_strikes"] = int(f.get("total_strikes") or 0)

            return filas
        except Error as e:
            raise RuntimeError(f"Error al consultar voluntarios: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def guardar_evaluacion_y_procesar(
        self,
        id_voluntario: int,
        evaluacion: dict,
        username: str | None = None,
        password_hash: str | None = None
    ) -> dict:
        """
        Registra o actualiza EVALUACION_ADMISION (1:1) y sincroniza VOLUNTARIO en una sola transacción:
        - Si decision_final == 'Admitido': crea cuenta en USUARIO (si no tiene) y marca estado = 'Admitido'.
        - Si decision_final == 'Rechazado': marca estado = 'Rechazado' y fecha_admision = NULL.
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT id_usuario, estado FROM VOLUNTARIO WHERE id_voluntario = %s LIMIT 1",
                (id_voluntario,)
            )
            vol = cursor.fetchone()
            if not vol:
                raise ValueError("El postulante seleccionado no existe.")

            if vol["estado"] == "Inactivo_Definitivo":
                raise ValueError("Este voluntario está en Inactivo_Definitivo (5 strikes) y no puede modificarse.")

            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO EVALUACION_ADMISION (
                    id_voluntario,
                    ci_presentado,
                    datos_verificados,
                    disponibilidad,
                    acepta_reglas,
                    antecedentes_presentado,
                    tiene_antecedentes,
                    cv_presentado,
                    nivel_educativo,
                    situacion_laboral,
                    resultado_automatico,
                    decision_final,
                    motivo_cambio,
                    id_admin_evalua,
                    fecha_evaluacion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    ci_presentado = VALUES(ci_presentado),
                    datos_verificados = VALUES(datos_verificados),
                    disponibilidad = VALUES(disponibilidad),
                    acepta_reglas = VALUES(acepta_reglas),
                    antecedentes_presentado = VALUES(antecedentes_presentado),
                    tiene_antecedentes = VALUES(tiene_antecedentes),
                    cv_presentado = VALUES(cv_presentado),
                    nivel_educativo = VALUES(nivel_educativo),
                    situacion_laboral = VALUES(situacion_laboral),
                    resultado_automatico = VALUES(resultado_automatico),
                    decision_final = VALUES(decision_final),
                    motivo_cambio = VALUES(motivo_cambio),
                    id_admin_evalua = VALUES(id_admin_evalua),
                    fecha_evaluacion = VALUES(fecha_evaluacion)
                """,
                (
                    id_voluntario,
                    int(evaluacion["ci_presentado"]),
                    int(evaluacion["datos_verificados"]),
                    evaluacion["disponibilidad"],
                    int(evaluacion["acepta_reglas"]),
                    int(evaluacion["antecedentes_presentado"]),
                    int(evaluacion["tiene_antecedentes"]),
                    int(evaluacion["cv_presentado"]),
                    evaluacion["nivel_educativo"],
                    evaluacion["situacion_laboral"],
                    evaluacion["resultado_automatico"],
                    evaluacion["decision_final"],
                    evaluacion.get("motivo_cambio"),
                    int(evaluacion["id_admin_evalua"]),
                    ahora
                )
            )

            cuenta_creada = False
            usuario_asignado = None

            if evaluacion["decision_final"] == "Admitido":
                id_usuario_final = vol["id_usuario"]
                if not id_usuario_final:
                    if not username or not password_hash:
                        raise ValueError("Faltan credenciales para crear la cuenta del voluntario.")
                    cursor.execute(
                        """
                        INSERT INTO USUARIO (usuario, password_hash, rol, activo)
                        VALUES (%s, %s, 'Voluntario', 1)
                        """,
                        (username, password_hash)
                    )
                    id_usuario_final = cursor.lastrowid
                    cuenta_creada = True
                    usuario_asignado = username
                else:
                    cursor.execute(
                        "UPDATE USUARIO SET activo = 1 WHERE id_usuario = %s",
                        (id_usuario_final,)
                    )

                cursor.execute(
                    """
                    UPDATE VOLUNTARIO
                    SET id_usuario = %s,
                        estado = 'Admitido',
                        fecha_admision = COALESCE(fecha_admision, %s)
                    WHERE id_voluntario = %s
                    """,
                    (id_usuario_final, date.today(), id_voluntario)
                )
            else:
                cursor.execute(
                    """
                    UPDATE VOLUNTARIO
                    SET estado = 'Rechazado',
                        fecha_admision = NULL
                    WHERE id_voluntario = %s
                    """,
                    (id_voluntario,)
                )

            conn.commit()
            return {
                "decision_final": evaluacion["decision_final"],
                "cuenta_creada": cuenta_creada,
                "usuario": usuario_asignado
            }
        except mysql.connector.IntegrityError as e:
            if conn:
                conn.rollback()
            if e.errno == 1062:
                raise ValueError("El nombre de usuario generado ya existe. Intenta nuevamente.")
            raise RuntimeError(f"Error de integridad en la evaluación: {e}")
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
        """
        Cambia estado entre 'Admitido' e 'Inactivo'.
        Bloquea cualquier modificación si el voluntario está en 'Inactivo_Definitivo' (5 strikes).
        """
        conn = None
        cursor = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT estado, id_usuario FROM VOLUNTARIO WHERE id_voluntario = %s LIMIT 1",
                (id_voluntario,)
            )
            vol = cursor.fetchone()
            if not vol:
                raise ValueError("El voluntario seleccionado no existe.")

            if vol["estado"] == "Inactivo_Definitivo":
                raise ValueError(
                    "Acción denegada: este voluntario acumuló 5 strikes y su inactivación es irreversible."
                )

            cursor.execute(
                "UPDATE VOLUNTARIO SET estado = %s WHERE id_voluntario = %s",
                (nuevo_estado, id_voluntario)
            )

            if vol["id_usuario"]:
                activo_val = 1 if nuevo_estado == "Admitido" else 0
                cursor.execute(
                    "UPDATE USUARIO SET activo = %s WHERE id_usuario = %s",
                    (activo_val, vol["id_usuario"])
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
        Obtiene KPIs completos, horas acumuladas (calculadas con TIMESTAMPDIFF),
        próximas actividades y últimas donaciones (Esquema v1.3 FNBC).
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
                    SUM(CASE WHEN estado = 'Postulante' THEN 1 ELSE 0 END) AS postulantes,
                    SUM(CASE WHEN estado = 'Admitido' THEN 1 ELSE 0 END) AS admitidos
                FROM VOLUNTARIO
                """
            )
            vols = cursor.fetchone() or {}
            resumen["postulantes"] = int(vols.get("postulantes") or 0)
            resumen["admitidos"] = int(vols.get("admitidos") or 0)

            # 2. Total de Horas Cumplidas (FNBC: calculadas desde hora_entrada y hora_salida)
            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(
                        CASE WHEN asistio = 1
                        THEN TIMESTAMPDIFF(MINUTE, hora_entrada, hora_salida) / 60.0
                        ELSE 0 END
                    ),
                    0
                ) AS horas
                FROM ASISTENCIA
                """
            )
            hrs = cursor.fetchone() or {}
            resumen["horas_totales"] = round(float(hrs.get("horas") or 0.0), 2)

            # 3. KPIs de Actividades
            cursor.execute(
                """
                SELECT 
                    COUNT(id_actividad) AS total,
                    SUM(CASE WHEN estado = 'Programada' THEN 1 ELSE 0 END) AS programadas,
                    SUM(CASE WHEN estado = 'En Curso' THEN 1 ELSE 0 END) AS en_curso
                FROM ACTIVIDAD
                """
            )
            acts = cursor.fetchone() or {}
            resumen["actividades_total"] = int(acts.get("total") or 0)
            resumen["actividades_programadas"] = int(acts.get("programadas") or 0)
            resumen["actividades_en_curso"] = int(acts.get("en_curso") or 0)

            # 4. KPIs de Donaciones (Super-tipo DONACION + Sub-tipo DONACION_MONETARIA)
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(CASE WHEN d.tipo_donacion = 'DINERO' THEN dm.monto ELSE 0 END), 0) AS total_dinero,
                    SUM(CASE WHEN d.tipo_donacion = 'MATERIAL' THEN 1 ELSE 0 END) AS total_material
                FROM DONACION d
                LEFT JOIN DONACION_MONETARIA dm ON d.id_donacion = dm.id_donacion
                """
            )
            dons = cursor.fetchone() or {}
            resumen["total_dinero"] = float(dons.get("total_dinero") or 0.0)
            resumen["donaciones_material"] = int(dons.get("total_material") or 0)

            # 5. Agenda Operativa: Próximas Actividades
            cursor.execute(
                """
                SELECT 
                    a.nombre,
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
                WHERE a.estado IN ('Programada', 'En Curso')
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
                    DATE(d.fecha_donacion) AS fecha_donacion,
                    don.nombre AS donante,
                    d.tipo_donacion AS tipo,
                    dm.monto,
                    (
                        SELECT COUNT(*)
                        FROM DONACION_DETALLE dd
                        WHERE dd.id_donacion = d.id_donacion
                    ) AS items_count
                FROM DONACION d
                INNER JOIN DONANTE don ON d.id_donante = don.id_donante
                LEFT JOIN DONACION_MONETARIA dm ON d.id_donacion = dm.id_donacion
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