import re
from models.donacion_model import DonacionModel


class DonacionController:
    _RE_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$")
    _RE_NUMEROS = re.compile(r"^\d+$")
    _RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    TIPOS_DONACION = ("DINERO", "MATERIAL")
    # Se excluye 'Tarjeta' por seguridad de datos financieros del donante
    METODOS_PAGO = ("QR", "Efectivo", "Transferencia")
    TIPOS_DESTINO_DESPACHO = (
        "Actividad de la Fundación",
        "Otras Organizaciones (Hospitales, Escuelas, etc.)"
    )

    def __init__(self):
        self.model = DonacionModel()

    def cargar_catalogos(self) -> dict:
        return {
            "tipos": list(self.TIPOS_DONACION),
            "metodos": list(self.METODOS_PAGO),
            "insumos": self.model.obtener_insumos_con_stock(),
            "actividades": self.model.obtener_actividades_para_despacho()
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
        tipo_nombre: str,
        monto_str: str,
        metodo_pago: str | None,
        lista_insumos: list[dict],
        observaciones: str,
        id_usuario_registra: int | None = None
    ) -> tuple[bool, str | dict]:
        """
        Valida y registra una donación (tanto desde Administración con id_usuario_registra
        como desde el portal público de Autodonación con id_usuario_registra=None).
        """
        nombre_donante = " ".join((datos_donante.get("nombre") or "").split())
        documento = (datos_donante.get("documento") or "").strip()
        telefono = (datos_donante.get("telefono") or "").strip()
        correo = (datos_donante.get("correo") or "").strip()

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

        tipo_upper = (tipo_nombre or "").strip().upper()
        if tipo_upper not in self.TIPOS_DONACION:
            return False, "Selecciona el tipo de donación (DINERO o MATERIAL)."

        monto_val = None
        metodo_val = None
        detalles_finales = []

        if tipo_upper == "DINERO":
            if not metodo_pago or metodo_pago not in self.METODOS_PAGO:
                return False, "Selecciona un método de pago válido (QR, Efectivo o Transferencia)."
            try:
                monto_val = round(float(monto_str.replace(",", ".")), 2)
                if monto_val <= 0:
                    raise ValueError()
            except ValueError:
                return False, "Ingresa un monto válido mayor a 0.00 Bs."

            metodo_val = metodo_pago
        else:
            if not lista_insumos:
                return False, "Debes agregar al menos un insumo a la lista antes de registrar la donación material."
            detalles_finales = lista_insumos

        donante_limpio = {
            "nombre": nombre_donante.title(),
            "documento": documento,
            "telefono": telefono,
            "correo": correo.lower()
        }

        try:
            id_donacion = self.model.registrar_donacion_transaccion(
                datos_donante=donante_limpio,
                tipo_nombre=tipo_upper,
                monto=monto_val,
                metodo_pago=metodo_val,
                detalles_material=detalles_finales,
                observaciones=observaciones,
                id_usuario_registra=id_usuario_registra
            )
            resumen = (
                f"Bs. {monto_val:,.2f} ({metodo_val})"
                if tipo_upper == "DINERO"
                else f"{len(detalles_finales)} tipo(s) de insumo(s)"
            )
            return True, {
                "id_donacion": id_donacion,
                "codigo_comprobante": f"SCB-DON-{id_donacion:05d}",
                "donante": donante_limpio["nombre"],
                "tipo": tipo_upper,
                "resumen": resumen,
                "mensaje": f"Donación de {donante_limpio['nombre']} registrada correctamente: {resumen}."
            }
        except Exception as e:
            return False, str(e)

    def registrar_entrega_insumo(
        self,
        insumo_obj: dict | None,
        cantidad_str: str,
        tipo_destino: str,
        actividad_obj: dict | None,
        destino: str,
        id_usuario_entrega: int
    ) -> tuple[bool, str]:
        if not insumo_obj:
            return False, "No hay insumos con stock disponible o no seleccionaste ninguno."

        stock_disp = round(float(insumo_obj.get("stock_disponible") or 0), 2)
        if stock_disp <= 0:
            return False, f"El insumo '{insumo_obj['nombre']}' no cuenta con existencias disponibles."

        try:
            cantidad = round(float(cantidad_str.replace(",", ".")), 2)
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            return False, "La cantidad a entregar debe ser un número mayor a 0."

        if cantidad > stock_disp:
            return False, (
                f"Cantidad insuficiente en almacén. Disponible de '{insumo_obj['nombre']}': "
                f"{stock_disp:g} {insumo_obj['unidad_medida']}."
            )

        destino_limpio = " ".join((destino or "").split())

        if tipo_destino == "Actividad de la Fundación":
            if not actividad_obj:
                return False, "Selecciona la actividad de la fundación a la que se asignará el insumo."
            id_act = actividad_obj["id_actividad"]
            desc_destino = f"Actividad Fundación: {actividad_obj['nombre']}"
            if destino_limpio:
                desc_destino += f" ({destino_limpio})"
        else:
            if not destino_limpio:
                return False, "Ingresa el nombre de la organización, hospital, escuela o entidad destinataria."
            id_act = None
            desc_destino = f"Org. Externa: {destino_limpio}"

        try:
            self.model.registrar_entrega_insumo_transaccion(
                id_insumo=insumo_obj["id_insumo"],
                cantidad=cantidad,
                id_actividad=id_act,
                destino=desc_destino,
                id_usuario_entrega=int(id_usuario_entrega)
            )
            return True, (
                f"Salida registrada: {cantidad:g} {insumo_obj['unidad_medida']} de "
                f"'{insumo_obj['nombre']}' despachados correctamente."
            )
        except Exception as e:
            return False, str(e)

    def obtener_historial(self, filtro_tipo: str = "Todos") -> list[dict]:
        return self.model.listar_donaciones(filtro_tipo)

    def obtener_desglose_material(self, id_donacion: int) -> list[dict]:
        return self.model.obtener_detalle_insumos(id_donacion)

    def obtener_inventario(self) -> list[dict]:
        return self.model.obtener_insumos_con_stock()

    def obtener_historial_entregas(self) -> list[dict]:
        return self.model.listar_entregas_insumos()