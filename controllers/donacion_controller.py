import re
from models.donacion_model import DonacionModel


class DonacionController:
    _RE_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$")
    _RE_NUMEROS = re.compile(r"^\d+$")
    _RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self):
        self.model = DonacionModel()

    def cargar_catalogos(self) -> dict:
        # Excluimos 'Tarjeta' por seguridad de datos del donante
        metodos_filtrados = [
            m for m in self.model.obtener_metodos_pago()
            if m["nombre"].strip().lower() != "tarjeta"
        ]
        return {
            "tipos": self.model.obtener_tipos_donacion(),
            "metodos": metodos_filtrados,
            "insumos": self.model.obtener_insumos()
        }

    def buscar_donante(self, documento: str) -> dict | None:
        return self.model.buscar_donante_por_documento(documento)

    def validar_item_insumo(self, insumo_obj: dict | None, cantidad_str: str) -> tuple[bool, str, dict | None]:
        """Valida un ítem antes de añadirlo a la lista temporal de donación material."""
        if not insumo_obj:
            return False, "Selecciona un insumo del catálogo.", None

        try:
            cantidad = round(float(cantidad_str.replace(",", ".")), 2)
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            return False, "La cantidad del insumo debe ser un número mayor a 0.", None

        item = {
            "id_insumo": insumo_obj["id_insumo"],
            "nombre": insumo_obj["nombre"],
            "unidad_medida": insumo_obj["unidad_medida"],
            "cantidad": cantidad
        }
        return True, "", item

    def registrar_donacion(
        self,
        datos_donante: dict,
        tipo_obj: dict | None,
        monto_str: str,
        metodo_obj: dict | None,
        lista_insumos: list[dict],
        observaciones: str,
        id_usuario_registra: int
    ) -> tuple[bool, str]:
        nombre_donante = " ".join((datos_donante.get("nombre") or "").split())
        documento = (datos_donante.get("documento") or "").strip()
        telefono = (datos_donante.get("telefono") or "").strip()
        correo = (datos_donante.get("correo") or "").strip()

        # 1. Validaciones estrictas del donante (letras a letras, números a números)
        if not nombre_donante:
            return False, "El nombre completo o razón social del donante es obligatorio."
        if not self._RE_LETRAS.match(nombre_donante):
            return False, "El nombre del donante solo admite letras y espacios."

        if documento and not self._RE_NUMEROS.match(documento):
            return False, "El CI / NIT debe contener únicamente números."

        if telefono and (not self._RE_NUMEROS.match(telefono) or not (7 <= len(telefono) <= 10)):
            return False, "El teléfono debe contener únicamente números (entre 7 y 10 dígitos)."

        if correo and not self._RE_CORREO.match(correo):
            return False, "El formato del correo electrónico no es válido."

        if not tipo_obj:
            return False, "Selecciona el tipo de donación (DINERO o MATERIAL)."

        tipo_nombre = tipo_obj["nombre"].strip().upper()
        monto_val = None
        id_metodo_val = None
        detalles_finales = []

        # 2. Validación según tipo de aporte
        if tipo_nombre == "DINERO":
            if not metodo_obj or metodo_obj["nombre"].strip().lower() == "tarjeta":
                return False, "Selecciona un método de pago válido (QR, Efectivo o Transferencia)."
            try:
                monto_val = round(float(monto_str.replace(",", ".")), 2)
                if monto_val <= 0:
                    raise ValueError()
            except ValueError:
                return False, "Ingresa un monto válido mayor a 0.00 Bs."

            id_metodo_val = metodo_obj["id_metodo_pago"]
            detalles_finales = []

        elif tipo_nombre == "MATERIAL":
            if not lista_insumos:
                return False, "Debes agregar al menos un insumo a la lista antes de registrar la donación material."

            monto_val = None
            id_metodo_val = None
            detalles_finales = lista_insumos
        else:
            return False, f"Tipo de donación no reconocido: {tipo_nombre}"

        donante_limpio = {
            "nombre": nombre_donante.title(),
            "documento": documento,
            "telefono": telefono,
            "correo": correo.lower()
        }

        try:
            self.model.registrar_donacion_transaccion(
                datos_donante=donante_limpio,
                tipo_nombre=tipo_nombre,
                id_tipo_donacion=tipo_obj["id_tipo_donacion"],
                monto=monto_val,
                id_metodo_pago=id_metodo_val,
                detalles_material=detalles_finales,
                observaciones=observaciones.strip(),
                id_usuario_registra=id_usuario_registra
            )
            resumen = (
                f"Bs. {monto_val:,.2f} ({metodo_obj['nombre']})"
                if tipo_nombre == "DINERO"
                else f"{len(detalles_finales)} tipo(s) de insumo(s)"
            )
            return True, f"Donación de {donante_limpio['nombre']} registrada correctamente: {resumen}."
        except Exception as e:
            return False, str(e)

    def obtener_historial(self, filtro_tipo: str = "Todos") -> list[dict]:
        return self.model.listar_donaciones(filtro_tipo)

    def obtener_desglose_material(self, id_donacion: int) -> list[dict]:
        return self.model.obtener_detalle_insumos(id_donacion)