from datetime import date, time
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from models.actividad_model import ActividadModel


class ActividadController:
    def __init__(self):
        self.model = ActividadModel()

    @staticmethod
    def generar_horas_inicio() -> list[str]:
        horas = []
        for mins in range(6 * 60 + 30, 19 * 60 + 31, 30):
            horas.append(f"{mins // 60:02d}:{mins % 60:02d}")
        return horas

    @staticmethod
    def generar_horas_fin_validas(hora_inicio_str: str) -> list[str]:
        try:
            h, m = map(int, hora_inicio_str.split(":"))
            inicio_min = h * 60 + m
        except Exception:
            return []

        min_fin = inicio_min + 60
        max_fin = min(inicio_min + 300, 20 * 60 + 30)

        opciones = []
        for mins in range(min_fin, max_fin + 1, 30):
            opciones.append(f"{mins // 60:02d}:{mins % 60:02d}")
        return opciones

    @staticmethod
    def generar_cupos_validos() -> list[str]:
        return [str(c) for c in range(3, 16)]

    def _validar_datos_actividad(self, datos: dict) -> tuple[bool, str, dict | None]:
        nombre = datos.get("nombre", "").strip()
        lugar = datos.get("lugar", "").strip()
        descripcion = datos.get("descripcion", "").strip()
        fecha_str = datos.get("fecha", "").strip()
        hora_ini_str = datos.get("hora_inicio", "").strip()
        hora_fin_str = datos.get("hora_fin", "").strip()
        cupo_str = datos.get("cupo_maximo", "").strip()

        if not nombre:
            return False, "El nombre de la actividad es obligatorio.", None
        if not lugar:
            return False, "El lugar de la actividad es obligatorio.", None

        try:
            fecha_obj = date.fromisoformat(fecha_str)
        except ValueError:
            return False, "Formato de fecha inválido. Usa AAAA-MM-DD.", None

        if hora_ini_str not in self.generar_horas_inicio():
            return False, "Selecciona una hora de inicio válida (06:30 a 19:30).", None

        horas_fin_permitidas = self.generar_horas_fin_validas(hora_ini_str)
        if hora_fin_str not in horas_fin_permitidas:
            return False, "La hora de fin debe durar entre 1 y 5 horas y no pasar de las 20:30.", None

        h_ini_obj = time.fromisoformat(hora_ini_str)
        h_fin_obj = time.fromisoformat(hora_fin_str)

        try:
            cupo = int(cupo_str)
            if cupo < 3 or cupo > 15:
                raise ValueError()
        except ValueError:
            return False, "El cupo máximo debe estar entre 3 y 15 voluntarios.", None

        payload = {
            "nombre": nombre,
            "descripcion": descripcion or None,
            "fecha": fecha_obj,
            "hora_inicio": h_ini_obj,
            "hora_fin": h_fin_obj,
            "lugar": lugar,
            "cupo_maximo": cupo
        }
        return True, "", payload

    def registrar_actividad(self, datos: dict) -> tuple[bool, str]:
        ok, msg, payload = self._validar_datos_actividad(datos)
        if not ok:
            return False, msg

        try:
            self.model.crear_actividad(payload)
            return True, f"Actividad '{payload['nombre']}' programada correctamente."
        except Exception as e:
            return False, str(e)

    def editar_actividad(self, actividad: dict, datos: dict) -> tuple[bool, str]:
        if not actividad:
            return False, "No hay ninguna actividad seleccionada para editar."

        if actividad["estado"] == "Finalizada":
            return False, "No se puede editar una actividad que ya ha finalizado."

        ok, msg, payload = self._validar_datos_actividad(datos)
        if not ok:
            return False, msg

        try:
            self.model.editar_actividad(actividad["id_actividad"], payload)
            return True, f"Actividad '{payload['nombre']}' actualizada correctamente."
        except Exception as e:
            return False, str(e)

    def obtener_actividades(self, filtro_estado: str = "Todas") -> list[dict]:
        return self.model.listar_actividades(filtro_estado)

    def cancelar_actividad(self, actividad: dict) -> tuple[bool, str]:
        if not actividad:
            return False, "Selecciona primero una actividad de la tabla."
        if actividad["estado"] == "Cancelada":
            return False, "Esta actividad ya se encuentra cancelada."
        if actividad["estado"] == "Finalizada":
            return False, "No se puede cancelar una actividad que ya finalizó."

        try:
            self.model.cambiar_estado_actividad(actividad["id_actividad"], "Cancelada")
            return True, f"La actividad '{actividad['nombre']}' ha sido cancelada."
        except Exception as e:
            return False, str(e)

    def restablecer_actividad(self, actividad: dict) -> tuple[bool, str]:
        if not actividad:
            return False, "Selecciona primero una actividad de la tabla."
        if actividad["estado"] != "Cancelada":
            return False, "Solo se pueden restablecer actividades que estén en estado 'Cancelada'."

        try:
            self.model.cambiar_estado_actividad(actividad["id_actividad"], "Programada")
            return True, f"La actividad '{actividad['nombre']}' ha sido restablecida."
        except Exception as e:
            return False, str(e)

    def obtener_voluntarios_admitidos(self, busqueda: str = "") -> list[dict]:
        return self.model.listar_voluntarios_disponibles(busqueda)

    def obtener_asignados(self, id_actividad: int) -> list[dict]:
        return self.model.listar_asignaciones_actividad(id_actividad)

    def asignar_voluntario(self, actividad: dict, voluntario: dict, id_admin: int) -> tuple[bool, str]:
        if not actividad:
            return False, "Selecciona una actividad en la parte superior."
        if not voluntario:
            return False, "Selecciona un voluntario admitido de la lista izquierda."

        try:
            self.model.asignar_voluntario_actividad(
                id_actividad=actividad["id_actividad"],
                id_voluntario=voluntario["id_voluntario"],
                id_admin=id_admin
            )
            return True, f"{voluntario['nombre_completo']} asignado a '{actividad['nombre']}'."
        except Exception as e:
            return False, str(e)

    def remover_asignacion(self, asignacion: dict) -> tuple[bool, str]:
        if not asignacion:
            return False, "Selecciona un voluntario de la lista de asignados."

        try:
            self.model.quitar_asignacion(asignacion["id_asignacion"])
            return True, f"Se quitó la asignación de {asignacion['nombre_completo']}."
        except Exception as e:
            return False, str(e)

    def guardar_asistencia(
        self,
        asignacion: dict,
        asistio: bool,
        horas_str: str,
        observaciones: str
    ) -> tuple[bool, str]:
        if not asignacion:
            return False, "Selecciona un voluntario de la lista de asistencia."

        if not asistio:
            horas = 0.0
        else:
            try:
                horas = round(float(horas_str.replace(",", ".")), 2)
                if horas <= 0:
                    return False, "Si el voluntario asistió, las horas cumplidas deben ser mayores a 0."
            except ValueError:
                return False, "Ingresa un número válido para las horas cumplidas (ej. 4 o 3.5)."

        obs = observaciones.strip() or None

        try:
            self.model.registrar_o_actualizar_asistencia(
                id_asignacion=asignacion["id_asignacion"],
                asistio=asistio,
                horas_cumplidas=horas,
                observaciones=obs
            )
            estado_txt = f"Asistió ({horas} hrs)" if asistio else "Inasistencia (0 hrs)"
            return True, f"Asistencia guardada para {asignacion['nombre_completo']}: {estado_txt}."
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # PORTAL DEL VOLUNTARIO
    # =========================================================================

    def obtener_datos_portal_voluntario(self, id_usuario: int, filtro_estado: str = "Todas") -> dict:
        """
        Verifica el perfil activo del voluntario y retorna sus actividades e indicadores personales.
        """
        perfil = self.model.obtener_perfil_voluntario_por_usuario(id_usuario)
        if not perfil:
            raise ValueError("No se encontró un perfil de voluntario asociado a esta cuenta.")

        if perfil["estado"] == "Inactivo":
            raise ValueError("Tu cuenta de voluntario ha sido desactivada por el Administrador.")

        actividades = self.model.listar_actividades_voluntario(perfil["id_voluntario"], filtro_estado)
        todas = self.model.listar_actividades_voluntario(perfil["id_voluntario"], "Todas")

        programadas = sum(1 for a in todas if a["estado_actividad"] == "Programada" and a["estado_asignacion"] != "Cancelada")
        en_curso = sum(1 for a in todas if a["estado_actividad"] == "En Curso" and a["estado_asignacion"] != "Cancelada")
        asistencias = sum(1 for a in todas if a["id_asistencia"] is not None and bool(a["asistio"]))
        inasistencias = sum(1 for a in todas if a["id_asistencia"] is not None and not bool(a["asistio"]))
        total_horas = round(sum(a["horas_cumplidas"] for a in todas), 2)

        evaluadas = asistencias + inasistencias
        cumplimiento = round((asistencias / evaluadas) * 100, 1) if evaluadas > 0 else 100.0

        return {
            "perfil": perfil,
            "actividades": actividades,
            "todas": todas,
            "resumen": {
                "programadas": programadas,
                "en_curso": en_curso,
                "asistencias": asistencias,
                "inasistencias": inasistencias,
                "total_horas": total_horas,
                "cumplimiento": cumplimiento
            }
        }

    def exportar_historial_voluntario_excel(self, ruta_archivo: str, paquete: dict) -> tuple[bool, str]:
        """Exporta el historial personal de horas y actividades del voluntario a Excel."""
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Mi Historial Voluntariado"

            perfil = paquete["perfil"]
            resumen = paquete["resumen"]

            fill_header = PatternFill(start_color="7F1D1D", end_color="7F1D1D", fill_type="solid")
            font_header = Font(color="FFFFFF", bold=True, size=11)

            ws["A1"] = "Save the Children Bolivia — Constancia de Horas de Voluntariado"
            ws["A1"].font = Font(color="7F1D1D", bold=True, size=14)
            ws["A2"] = f"Voluntario: {perfil['nombre_completo']}  |  CI: {perfil['ci']}"
            ws["A2"].font = Font(bold=True, size=10)
            ws["A3"] = (
                f"Total Horas Cumplidas: {resumen['total_horas']} hrs  |  "
                f"Asistencias: {resumen['asistencias']}  |  Cumplimiento: {resumen['cumplimiento']}%"
            )
            ws["A3"].font = Font(italic=True, color="555555", size=10)

            encabezados = ["Fecha", "Actividad", "Horario", "Lugar", "Asistencia", "Horas Cumplidas", "Observaciones"]
            fila_hdr = 5
            for idx, txt in enumerate(encabezados, start=1):
                c = ws.cell(row=fila_hdr, column=idx, value=txt)
                c.fill = fill_header
                c.font = font_header
                c.alignment = Alignment(horizontal="center", vertical="center")

            for r_idx, item in enumerate(paquete["todas"], start=fila_hdr + 1):
                if item["id_asistencia"] is None:
                    estado_asis = "Pendiente de registro"
                elif bool(item["asistio"]):
                    estado_asis = "Asistió"
                else:
                    estado_asis = "Faltó"

                fila_vals = [
                    str(item["fecha"]),
                    item["actividad"],
                    f"{item['hora_inicio_str']} - {item['hora_fin_str']}",
                    item["lugar"],
                    estado_asis,
                    item["horas_cumplidas"],
                    item["observaciones"] or "-"
                ]
                for c_idx, val in enumerate(fila_vals, start=1):
                    ws.cell(row=r_idx, column=c_idx, value=val)

            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.row >= fila_hdr and cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

            wb.save(ruta_archivo)
            return True, f"Historial exportado correctamente en:\n{ruta_archivo}"
        except Exception as e:
            return False, f"No se pudo generar el archivo Excel: {e}"