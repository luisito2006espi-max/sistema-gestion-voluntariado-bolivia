from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from models.reporte_model import ReporteModel


class ReporteController:
    def __init__(self):
        self.model = ReporteModel()

    def validar_fechas(self, fecha_ini_str: str, fecha_fin_str: str) -> tuple[bool, str, str | None, str | None]:
        ini = fecha_ini_str.strip()
        fin = fecha_fin_str.strip()

        if not ini and not fin:
            return True, "", None, None

        if not ini or not fin:
            return False, "Completa tanto la fecha 'Desde' como 'Hasta', o limpia ambas para ver todo el historial.", None, None

        try:
            d_ini = date.fromisoformat(ini)
            d_fin = date.fromisoformat(fin)
        except ValueError:
            return False, "Formato de fecha inválido. Usa AAAA-MM-DD.", None, None

        if d_fin < d_ini:
            return False, "La fecha 'Hasta' no puede ser anterior a la fecha 'Desde'.", None, None

        return True, "", d_ini.isoformat(), d_fin.isoformat()

    def generar_paquete_analitico(self, fecha_ini: str = None, fecha_fin: str = None) -> dict:
        """Obtiene todas las relaciones de 2 variables para gráficos, tablas y Excel."""
        rendimiento = self.model.obtener_rendimiento_voluntarios(fecha_ini, fecha_fin)
        vol_tiempo = self.model.obtener_voluntarios_por_tiempo(fecha_ini, fecha_fin)
        vol_estado = self.model.obtener_voluntarios_por_estado(fecha_ini, fecha_fin)
        vol_registrador = self.model.obtener_inscripciones_por_registrador(fecha_ini, fecha_fin)

        act_tiempo = self.model.obtener_actividades_por_tiempo(fecha_ini, fecha_fin)
        act_estado = self.model.obtener_actividades_por_estado(fecha_ini, fecha_fin)
        act_ocupacion = self.model.obtener_ocupacion_actividades(fecha_ini, fecha_fin)

        don_tiempo = self.model.obtener_donaciones_por_tiempo(fecha_ini, fecha_fin)
        don_metodo = self.model.obtener_donaciones_por_metodo_pago(fecha_ini, fecha_fin)
        don_tipo = self.model.obtener_donaciones_por_tipo(fecha_ini, fecha_fin)
        don_insumos = self.model.obtener_insumos_recibidos(fecha_ini, fecha_fin)
        top_donantes = self.model.obtener_top_donantes(fecha_ini, fecha_fin)

        # Totales globales
        total_horas = round(sum(r["total_horas"] for r in rendimiento), 2)
        total_asistencias = sum(r["asistencias"] for r in rendimiento)
        total_inasistencias = sum(r["inasistencias"] for r in rendimiento)
        total_recaudado = round(sum(d["total_monto"] for d in don_metodo), 2)
        total_voluntarios = sum(v["cantidad"] for v in vol_estado)
        total_actividades = sum(a["cantidad"] for a in act_estado)

        return {
            "periodo": f"{fecha_ini} al {fecha_fin}" if (fecha_ini and fecha_fin) else "Todo el historial",
            "kpis": {
                "total_horas": total_horas,
                "total_asistencias": total_asistencias,
                "total_inasistencias": total_inasistencias,
                "total_recaudado": total_recaudado,
                "total_voluntarios": total_voluntarios,
                "total_actividades": total_actividades
            },
            "rendimiento": rendimiento,
            "vol_tiempo": vol_tiempo,
            "vol_estado": vol_estado,
            "vol_registrador": vol_registrador,
            "act_tiempo": act_tiempo,
            "act_estado": act_estado,
            "act_ocupacion": act_ocupacion,
            "don_tiempo": don_tiempo,
            "don_metodo": don_metodo,
            "don_tipo": don_tipo,
            "don_insumos": don_insumos,
            "top_donantes": top_donantes
        }

    def exportar_a_excel(self, ruta_archivo: str, datos: dict) -> tuple[bool, str]:
        """Exporta el reporte completo a un archivo Excel (.xlsx) sencillo con 5 hojas."""
        try:
            wb = openpyxl.Workbook()

            # Estilos rojos institucionales
            fill_header = PatternFill(start_color="7F1D1D", end_color="7F1D1D", fill_type="solid")
            font_header = Font(color="FFFFFF", bold=True, size=11)
            font_titulo = Font(color="7F1D1D", bold=True, size=14)

            def estilizar_hoja(ws, titulo: str, encabezados: list[str], filas: list[list]):
                ws["A1"] = titulo
                ws["A1"].font = font_titulo
                ws["A2"] = f"Período: {datos['periodo']}  |  Generado: {date.today().isoformat()}"
                ws["A2"].font = Font(italic=True, color="555555", size=10)

                fila_inicio_tabla = 4
                for col_idx, texto in enumerate(encabezados, start=1):
                    celda = ws.cell(row=fila_inicio_tabla, column=col_idx, value=texto)
                    celda.fill = fill_header
                    celda.font = font_header
                    celda.alignment = Alignment(horizontal="center", vertical="center")

                for r_idx, fila in enumerate(filas, start=fila_inicio_tabla + 1):
                    for c_idx, val in enumerate(fila, start=1):
                        ws.cell(row=r_idx, column=c_idx, value=val)

                # Ajustar ancho de columnas automáticamente
                for col in ws.columns:
                    max_len = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        if cell.row >= fila_inicio_tabla and cell.value is not None:
                            max_len = max(max_len, len(str(cell.value)))
                    ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

            # HOJA 1: Resumen General
            ws1 = wb.active
            ws1.title = "Resumen General"
            kpis = datos["kpis"]
            filas_kpi = [
                ["Total Voluntarios Registrados", kpis["total_voluntarios"]],
                ["Total Actividades Registradas", kpis["total_actividades"]],
                ["Horas de Voluntariado Cumplidas", kpis["total_horas"]],
                ["Asistencias Confirmadas", kpis["total_asistencias"]],
                ["Inasistencias Registradas", kpis["total_inasistencias"]],
                ["Recaudación Monetaria Total (Bs.)", kpis["total_recaudado"]],
            ]
            estilizar_hoja(ws1, "Save the Children Bolivia — Resumen Ejecutivo", ["Indicador", "Valor"], filas_kpi)

            # HOJA 2: Rendimiento de Voluntarios
            ws2 = wb.create_sheet("Rendimiento Voluntarios")
            filas_rend = [
                [
                    r["ci"],
                    r["voluntario"],
                    r["estado_voluntario"],
                    r["actividades_asignadas"],
                    r["asistencias"],
                    r["inasistencias"],
                    r["total_horas"],
                    f"{r['porcentaje_cumplimiento']}%"
                ]
                for r in datos["rendimiento"]
            ]
            estilizar_hoja(
                ws2,
                "Rendimiento y Asistencia por Voluntario",
                ["CI", "Voluntario", "Estado", "Asignadas", "Asistencias", "Faltas", "Horas Totales", "% Cumplimiento"],
                filas_rend
            )

            # HOJA 3: Voluntarios por Estado y Tiempo
            ws3 = wb.create_sheet("Voluntarios")
            filas_vol = [[v["estado"], v["cantidad"]] for v in datos["vol_estado"]]
            filas_vol.append(["", ""])
            filas_vol.append(["--- Evolución Mensual ---", "Inscritos"])
            for vt in datos["vol_tiempo"]:
                filas_vol.append([vt["periodo"], vt["cantidad"]])
            estilizar_hoja(ws3, "Distribución y Evolución de Voluntarios", ["Categoría / Mes", "Cantidad"], filas_vol)

            # HOJA 4: Actividades y Cupos
            ws4 = wb.create_sheet("Actividades")
            filas_act = [
                [
                    a["actividad"],
                    str(a["fecha"]),
                    a["lugar"],
                    a["estado"],
                    a["cupo_maximo"],
                    a["inscritos"],
                    f"{a['porcentaje_ocupacion']}%"
                ]
                for a in datos["act_ocupacion"]
            ]
            estilizar_hoja(
                ws4,
                "Actividades y Ocupación de Cupos",
                ["Actividad", "Fecha", "Lugar", "Estado", "Cupo Máximo", "Asignados", "% Ocupación"],
                filas_act
            )

            # HOJA 5: Donaciones e Insumos
            ws5 = wb.create_sheet("Donaciones e Insumos")
            filas_don = [[m["metodo"], m["cantidad"], m["total_monto"]] for m in datos["don_metodo"]]
            filas_don.append(["", "", ""])
            filas_don.append(["--- Insumos en Especie ---", "Unidad de Medida", "Cantidad Total"])
            for ins in datos["don_insumos"]:
                filas_don.append([ins["insumo"], ins["unidad_medida"], ins["total_cantidad"]])
            estilizar_hoja(
                ws5,
                "Reporte Financiero y de Insumos Donados",
                ["Método de Pago / Insumo", "N° Aportes / Unidad", "Monto (Bs.) / Cantidad"],
                filas_don
            )

            wb.save(ruta_archivo)
            return True, f"Reporte Excel exportado correctamente en:\n{ruta_archivo}"
        except Exception as e:
            return False, f"Error al exportar el archivo Excel: {e}"