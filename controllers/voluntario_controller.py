from datetime import date
from models.voluntario_model import VoluntarioModel
from models.auth_model import AuthModel


class VoluntarioController:
    EDAD_MINIMA = 18
    EDAD_MAXIMA = 60

    def __init__(self):
        self.model = VoluntarioModel()

    def validar_fecha_nacimiento_partes(
        self, anio_str: str, mes_num: int, dia_str: str
    ) -> tuple[bool, str, date | None, int | None]:
        """Valida que la fecha sea real y que la edad esté entre 18 y 60 años."""
        try:
            anio = int(anio_str)
            dia = int(dia_str)
            fecha_nac = date(anio, mes_num, dia)
        except ValueError:
            return False, "Selecciona una fecha de nacimiento válida (Día, Mes y Año).", None, None

        edad = self.model.calcular_edad(fecha_nac)
        if edad < self.EDAD_MINIMA:
            return (
                False,
                f"El postulante tiene {edad} años. No se permiten voluntarios menores de {self.EDAD_MINIMA} años.",
                fecha_nac,
                edad
            )
        if edad > self.EDAD_MAXIMA:
            return (
                False,
                f"El postulante tiene {edad} años. No se permiten voluntarios mayores de {self.EDAD_MAXIMA} años.",
                fecha_nac,
                edad
            )

        return True, "", fecha_nac, edad

    def inscribir_postulante(self, datos: dict, id_usuario_registra: int) -> tuple[bool, str]:
        ci = datos.get("ci", "").strip()
        nombres = datos.get("nombres", "").strip()
        ap_pat = datos.get("apellido_paterno", "").strip()
        ap_mat = datos.get("apellido_materno", "").strip()

        if not ci:
            return False, "El Carnet de Identidad (CI) es obligatorio."
        if not nombres:
            return False, "El campo Nombres es obligatorio."
        if not ap_pat:
            return False, "El Apellido Paterno es obligatorio."

        ok_fecha, msg_fecha, fecha_nac, _edad = self.validar_fecha_nacimiento_partes(
            datos.get("anio", ""),
            datos.get("mes_num", 0),
            datos.get("dia", "")
        )
        if not ok_fecha:
            return False, msg_fecha

        # Esquema v2.0: enviar None (NULL) en campos opcionales vacíos
        payload = {
            "ci": ci,
            "nombres": nombres,
            "apellido_paterno": ap_pat,
            "apellido_materno": ap_mat or None,
            "fecha_nacimiento": fecha_nac,
            "telefono": datos.get("telefono", "").strip() or None,
            "correo": datos.get("correo", "").strip() or None,
            "direccion": datos.get("direccion", "").strip() or None,
            "id_usuario_registra": id_usuario_registra
        }

        try:
            self.model.registrar_postulante(payload)
            return True, f"Postulante '{nombres} {ap_pat}' inscrito correctamente."
        except Exception as e:
            return False, str(e)

    def obtener_voluntarios(self, filtro_estado: str = "Todos", busqueda: str = "") -> list[dict]:
        return self.model.listar_voluntarios(filtro_estado, busqueda)

    def aprobar_postulante(self, voluntario: dict) -> tuple[bool, str]:
        if not voluntario:
            return False, "Selecciona primero un postulante de la tabla."
        if voluntario["estado"] != "Postulante":
            return False, f"Solo se pueden admitir personas en estado 'Postulante' (actual: {voluntario['estado']})."

        primer_nombre = voluntario["nombres"].strip().split()[0].lower()
        ap_pat = voluntario["apellido_paterno"].strip().split()[0].lower()
        sufijo_ci = voluntario["ci"].strip()[-3:]

        username = f"{primer_nombre}.{ap_pat}{sufijo_ci}"
        password_temp = f"Scb{voluntario['ci'].strip()}"
        password_hash = AuthModel.hashear_password(password_temp)

        try:
            self.model.admitir_voluntario_transaccion(
                id_voluntario=voluntario["id_voluntario"],
                username=username,
                password_hash=password_hash
            )
            return True, (
                f"¡Voluntario admitido exitosamente!\n\n"
                f"Credenciales generadas:\n"
                f"• Usuario: {username}\n"
                f"• Contraseña temporal: {password_temp}"
            )
        except Exception as e:
            return False, str(e)

    def rechazar_postulante(self, voluntario: dict) -> tuple[bool, str]:
        if not voluntario:
            return False, "Selecciona primero un postulante de la tabla."
        if voluntario["estado"] != "Postulante":
            return False, "Solo se pueden rechazar postulantes pendientes."

        try:
            self.model.cambiar_estado_voluntario(voluntario["id_voluntario"], "Rechazado")
            return True, f"La postulación de {voluntario['nombre_completo']} ha sido rechazada."
        except Exception as e:
            return False, str(e)

    def desactivar_voluntario(self, voluntario: dict) -> tuple[bool, str]:
        if not voluntario:
            return False, "Selecciona un voluntario admitido de la tabla."
        if voluntario["estado"] != "Admitido":
            return False, "Solo se pueden desactivar voluntarios en estado 'Admitido'."

        try:
            self.model.cambiar_estado_voluntario(voluntario["id_voluntario"], "Inactivo")
            return True, f"El voluntario {voluntario['nombre_completo']} ha sido desactivado."
        except Exception as e:
            return False, str(e)

    def obtener_resumen_dashboard(self) -> dict:
        return self.model.obtener_metricas_dashboard()