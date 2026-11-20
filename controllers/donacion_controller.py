from models.donacion_model import DonacionModel


class DonacionController:
    def __init__(self):
        self.model = DonacionModel()

    def cargar_catalogos(self) -> dict:
        return {
            "tipos": self.model.obtener_tipos_donacion(),
            "metodos": self.model.obtener_metodos_pago(),
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
        nombre_donante = datos_donante.get("nombre", "").strip()
        if not nombre_donante:
            return False, "El nombre o razón social del donante es obligatorio."

        if not tipo_obj:
            return False, "Selecciona el tipo de donación (DINERO o MATERIAL)."

        tipo_nombre = tipo_obj["nombre"].strip().upper()
        monto_val = None
        id_metodo_val = None
        detalles_finales = []

        if tipo_nombre == "DINERO":
            if not metodo_obj:
                return False, "Selecciona un método de pago (QR, Tarjeta, Efectivo o Transferencia)."
            try:
                monto_val = round(float(monto_str.replace(",", ".")), 2)
                if monto_val <= 0:
                    raise ValueError()
            except ValueError:
                return False, "Ingresa un monto válido mayor a 0.00 Bs."

            id_metodo_val = metodo_obj["id_metodo_pago"]
            # Garantiza integridad: no se envían insumos en donación monetaria
            detalles_finales = []

        elif tipo_nombre == "MATERIAL":
            if not lista_insumos:
                return False, "Debes agregar al menos un insumo a la lista antes de registrar la donación material."

            # Garantiza integridad: monto y método de pago en None (NULL en MySQL)
            monto_val = None
            id_metodo_val = None
            detalles_finales = lista_insumos
        else:
            return False, f"Tipo de donación no reconocido: {tipo_nombre}"

        donante_limpio = {
            "nombre": nombre_donante,
            "documento": datos_donante.get("documento", "").strip(),
            "telefono": datos_donante.get("telefono", "").strip(),
            "correo": datos_donante.get("correo", "").strip()
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
            return True, f"Donación de {nombre_donante} registrada correctamente: {resumen}."
        except Exception as e:
            return False, str(e)

    def obtener_historial(self, filtro_tipo: str = "Todos") -> list[dict]:
        return self.model.listar_donaciones(filtro_tipo)

    def obtener_desglose_material(self, id_donacion: int) -> list[dict]:
        return self.model.obtener_detalle_insumos(id_donacion)