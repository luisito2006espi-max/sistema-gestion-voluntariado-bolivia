import re
import unicodedata
from datetime import date, datetime
from models.voluntario_model import VoluntarioModel
from models.auth_model import AuthModel


class VoluntarioController:
    _RE_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$")
    _RE_NUMEROS = re.compile(r"^\d+$")
    _RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self):
        self.model = VoluntarioModel()

    @staticmethod
    def _normalizar_texto_usuario(texto: str) -> str:
        sin_tildes = "".join(
            c for c in unicodedata.normalize("NFD", texto.strip().lower())
            if unicodedata.category(c) != "Mn"
        )
        return re.sub(r"[^a-z0-9]", "", sin_tildes)

    @staticmethod
    def parsear_fecha(fecha_str: str) -> date:
        texto = (fecha_str or "").strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(texto, fmt).date()
            except ValueError:
                continue
        raise ValueError("La fecha de nacimiento debe tener el formato AAAA-MM-DD.")

    def calcular_edad(self, fecha_nac: date) -> int:
        return self.model.calcular_edad(fecha_nac)

    def registrar_postulante(self, datos: dict) -> tuple[bool, str]:
        ci = (datos.get("ci") or "").strip()
        nombres = " ".join((datos.get("nombres") or "").split())
        ap_paterno = " ".join((datos.get("apellido_paterno") or "").split())
        ap_materno = " ".join((datos.get("apellido_materno") or "").split())
        telefono = (datos.get("telefono") or "").strip()
        correo = (datos.get("correo") or "").strip()
        direccion = " ".join((datos.get("direccion") or "").split())
        fecha_nac_raw = datos.get("fecha_nacimiento")

        # 1. Validaciones obligatorias y estrictas (números vs. letras)
        if not ci:
            return False, "El Carnet de Identidad (CI) es obligatorio."
        if not self._RE_NUMEROS.match(ci) or not (5 <= len(ci) <= 12):
            return False, "El CI debe contener únicamente números (entre 5 y 12 dígitos)."

        if not nombres or not self._RE_LETRAS.match(nombres):
            return False, "El campo Nombres es obligatorio y solo admite letras."

        if not ap_paterno or not self._RE_LETRAS.match(ap_paterno):
            return False, "El Apellido Paterno es obligatorio y solo admite letras."

        if ap_materno and not self._RE_LETRAS.match(ap_materno):
            return False, "El Apellido Materno solo admite letras."

        # 2. Validación de fecha de nacimiento y rango de edad (18 - 60 años)
        try:
            fecha_nac = (
                fecha_nac_raw
                if isinstance(fecha_nac_raw, date)
                else self.parsear_fecha(str(fecha_nac_raw))
            )
        except ValueError as e:
            return False, str(e)

        if fecha_nac >= date.today():
            return False, "La fecha de nacimiento no puede ser igual o posterior a hoy."

        edad = self.calcular_edad(fecha_nac)
        if edad < 18 or edad > 60:
            return False, f"Edad calculada: {edad} años. El voluntario debe tener entre 18 y 60 años."

        # 3. Validaciones de contacto opcionales
        if telefono and (not self._RE_NUMEROS.match(telefono) or not (7 <= len(telefono) <= 10)):
            return False, "El teléfono debe contener únicamente números (7 a 10 dígitos)."

        if correo and not self._RE_CORREO.match(correo):
            return False, "El formato del correo electrónico no es válido."

        payload = {
            "ci": ci,
            "nombres": nombres.title(),
            "apellido_paterno": ap_paterno.title(),
            "apellido_materno": ap_materno.title() if ap_materno else None,
            "fecha_nacimiento": fecha_nac,
            "telefono": telefono if telefono else None,
            "correo": correo.lower() if correo else None,
            "direccion": direccion if direccion else None,
            "id_usuario_registra": datos.get("id_usuario_registra"),
        }

        try:
            self.model.registrar_postulante(payload)
            return True, f"Postulante {payload['nombres']} {payload['apellido_paterno']} ({edad} años) registrado correctamente."
        except Exception as e:
            return False, str(e)

    def listar_voluntarios(self, filtro_estado: str = "Todos", busqueda: str = "") -> list[dict]:
        return self.model.listar_voluntarios(filtro_estado=filtro_estado, busqueda=busqueda)

    def admitir_voluntario(self, voluntario: dict) -> tuple[bool, str | dict]:
        if not voluntario:
            return False, "Selecciona un postulante de la tabla."
        if voluntario.get("estado") != "Postulante":
            return False, "Solo se puede admitir a registros con estado 'Postulante'."

        primer_nombre = self._normalizar_texto_usuario(voluntario["nombres"].split()[0])
        primer_apellido = self._normalizar_texto_usuario(voluntario["apellido_paterno"].split()[0])
        ci_limpio = re.sub(r"\D", "", str(voluntario["ci"]))

        base_user = f"{primer_nombre}.{primer_apellido}" if primer_nombre and primer_apellido else f"vol.{ci_limpio}"
        password_plana = f"Scb{ci_limpio}"
        password_hash = AuthModel.hashear_password(password_plana)

        candidatos = [
            base_user,
            f"{base_user}.{ci_limpio[-2:]}" if len(ci_limpio) >= 2 else f"{base_user}1",
            f"{base_user}.{ci_limpio}"
        ]

        ultimo_error = "No se pudo generar un usuario único."
        for usuario_candidato in candidatos:
            try:
                self.model.admitir_voluntario_transaccion(
                    id_voluntario=voluntario["id_voluntario"],
                    username=usuario_candidato,
                    password_hash=password_hash
                )
                return True, {
                    "nombre": voluntario["nombre_completo"],
                    "usuario": usuario_candidato,
                    "password": password_plana
                }
            except ValueError as e:
                ultimo_error = str(e)
                if "ya existe" in ultimo_error.lower():
                    continue
                return False, ultimo_error
            except Exception as e:
                return False, str(e)

        return False, ultimo_error

    def cambiar_estado(self, voluntario: dict, nuevo_estado: str) -> tuple[bool, str]:
        if not voluntario:
            return False, "Selecciona un registro de la tabla."
        try:
            self.model.cambiar_estado_voluntario(voluntario["id_voluntario"], nuevo_estado)
            return True, f"Estado actualizado a '{nuevo_estado}' correctamente."
        except Exception as e:
            return False, str(e)

    def obtener_resumen_dashboard(self) -> dict:
        return self.model.obtener_metricas_dashboard()