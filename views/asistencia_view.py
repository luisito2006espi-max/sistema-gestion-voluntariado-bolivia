import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controllers.actividad_controller import ActividadController


class ControlAsistenciaView(tb.Frame):
    """Vista para Administrador: Registro de asistencia y horas cumplidas por actividad."""

    def __init__(self, master, sesion: dict):
        super().__init__(master)
        self.sesion = sesion
        self.controller = ActividadController()
        self.actividades_map = {}
        self.actividad_actual = None
        self.asignados_cache = {}
        self.asignacion_seleccionada = None

        self.pack(fill=BOTH, expand=True)
        self._construir_ui()
        self._cargar_actividades()

    def _construir_ui(self):
        header = tk.Frame(self, bg="#FFF5F5")
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="Control de Asistencia y Horas Cumplidas",
            font=("Segoe UI", 20, "bold"),
            bg="#FFF5F5",
            fg="#7F1D1D"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Registra la asistencia y horas cumplidas de los voluntarios asignados (vital para reportes de rendimiento).",
            font=("Segoe UI", 10),
            bg="#FFF5F5",
            fg="#64748B"
        ).pack(anchor="w", pady=(2, 0))

        # Barra superior de selección de actividad
        top_bar = tk.Frame(self, bg="#FFFFFF", padx=18, pady=14)
        top_bar.pack(fill="x", pady=(0, 14))

        tk.Label(
            top_bar,
            text="Actividad a Evaluar:",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(side="left", padx=(0, 10))

        self.combo_actividad = tb.Combobox(
            top_bar,
            state="readonly",
            width=52,
            font=("Segoe UI", 10),
            bootstyle="danger"
        )
        self.combo_actividad.pack(side="left", padx=(0, 14))
        self.combo_actividad.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_actividad())

        self.lbl_duracion = tk.Label(
            top_bar,
            text="Duración programada: -",
            font=("Segoe UI", 9, "bold"),
            bg="#FEF2F2",
            fg="#7F1D1D",
            padx=12,
            pady=5
        )
        self.lbl_duracion.pack(side="right")

        # Contenedor dividido: Tabla de voluntarios asignados (izquierda) + Formulario asistencia (derecha)
        cuerpo = tk.Frame(self, bg="#FFF5F5")
        cuerpo.pack(fill=BOTH, expand=True)
        cuerpo.columnconfigure(0, weight=64)
        cuerpo.columnconfigure(1, weight=36)
        cuerpo.rowconfigure(0, weight=1)

        # Tabla SIN ID visible
        tabla_card = tk.Frame(cuerpo, bg="#FFFFFF", padx=16, pady=14)
        tabla_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(
            tabla_card,
            text="Planilla de Voluntarios Asignados",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(0, 10))

        columnas = ("ci", "nombre", "estado_asis", "horas", "obs")
        self.tabla = tb.Treeview(
            tabla_card,
            columns=columnas,
            show="headings",
            bootstyle="danger"
        )
        cols_cfg = {
            "ci": ("CI", 95),
            "nombre": ("Voluntario", 195),
            "estado_asis": ("Asistencia", 105),
            "horas": ("Horas", 75),
            "obs": ("Observaciones", 170)
        }
        for col, (titulo, ancho) in cols_cfg.items():
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="center" if col in ("ci", "estado_asis", "horas") else "w")

        self.tabla.pack(fill=BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar_voluntario)

        # Panel derecho: Registro de Asistencia
        form_card = tk.Frame(cuerpo, bg="#FFFFFF", padx=18, pady=18)
        form_card.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            form_card,
            text="Registro Individual",
            font=("Segoe UI", 12, "bold"),
            bg="#FFFFFF",
            fg="#7F1D1D"
        ).pack(anchor="w", pady=(0, 10))

        self.lbl_voluntario = tk.Label(
            form_card,
            text="Selecciona un voluntario de la planilla izquierda.",
            font=("Segoe UI", 9),
            bg="#FEF2F2",
            fg="#7F1D1D",
            padx=12,
            pady=10,
            wraplength=280,
            justify="left"
        )
        self.lbl_voluntario.pack(fill="x", pady=(0, 14))

        # Switch Asistió / Faltó
        self.var_asistio = tk.BooleanVar(value=True)
        self.chk_asistio = tb.Checkbutton(
            form_card,
            text="El voluntario ASISTIÓ a la actividad",
            variable=self.var_asistio,
            bootstyle="success-round-toggle",
            command=self._al_cambiar_check_asistio
        )
        self.chk_asistio.pack(anchor="w", pady=(0, 14))

        # Horas cumplidas
        tk.Label(
            form_card,
            text="Horas Cumplidas (Decimal):",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(anchor="w", pady=(0, 4))

        self.entry_horas = tb.Entry(form_card, font=("Segoe UI", 10), bootstyle="danger")
        self.entry_horas.pack(fill="x", ipady=4, pady=(0, 14))

        # Observaciones
        tk.Label(
            form_card,
            text="Observaciones de desempeño:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        ).pack(anchor="w", pady=(0, 4))

        self.txt_obs = tk.Text(
            form_card,
            height=4,
            font=("Segoe UI", 9),
            bd=1,
            relief="solid"
        )
        self.txt_obs.pack(fill="x", pady=(0, 16))

        tb.Button(
            form_card,
            text="✓ Guardar Asistencia",
            bootstyle="danger",
            command=self._guardar_asistencia
        ).pack(fill="x", ipady=6)

    def _cargar_actividades(self):
        try:
            todas = self.controller.obtener_actividades("Todas")
            validas = [a for a in todas if a["estado"] != "Cancelada"]

            self.actividades_map.clear()
            etiquetas = []
            for a in validas:
                etiqueta = f"[{a['estado']}] {a['nombre']} — {a['fecha']}"
                self.actividades_map[etiqueta] = a
                etiquetas.append(etiqueta)

            self.combo_actividad["values"] = etiquetas
            if etiquetas:
                self.combo_actividad.set(etiquetas[0])
                self._al_cambiar_actividad()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_cambiar_actividad(self):
        etiqueta = self.combo_actividad.get()
        act = self.actividades_map.get(etiqueta)
        if not act:
            return

        self.actividad_actual = act
        self.asignacion_seleccionada = None
        self.lbl_duracion.config(
            text=f"Duración programada: {act['duracion_horas']} hrs ({act['hora_inicio_str']} - {act['hora_fin_str']})"
        )
        self._cargar_planilla()

    def _cargar_planilla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.asignados_cache.clear()

        if not self.actividad_actual:
            return

        try:
            lista = self.controller.obtener_asignados(self.actividad_actual["id_actividad"])
            for row in lista:
                iid = str(row["id_asignacion"])
                self.asignados_cache[iid] = row

                if row["id_asistencia"] is None:
                    estado_txt = "Pendiente"
                    horas_txt = "-"
                elif bool(row["asistio"]):
                    estado_txt = "Asistió"
                    horas_txt = f"{float(row['horas_cumplidas']):.2f}"
                else:
                    estado_txt = "Faltó"
                    horas_txt = "0.00"

                self.tabla.insert("", tk.END, iid=iid, values=(
                    row["ci"],
                    row["nombre_completo"],
                    estado_txt,
                    horas_txt,
                    row["observaciones"] or ""
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _al_seleccionar_voluntario(self, _event):
        sel = self.tabla.selection()
        if not sel:
            return
        row = self.asignados_cache.get(sel[0])
        if not row:
            return

        self.asignacion_seleccionada = row
        self.lbl_voluntario.config(
            text=f"Voluntario: {row['nombre_completo']}\nCI: {row['ci']}  |  Tel: {row['telefono'] or 'N/A'}"
        )

        if row["id_asistencia"] is not None:
            asistio = bool(row["asistio"])
            self.var_asistio.set(asistio)
            self._al_cambiar_check_asistio()
            self.entry_horas.config(state="normal")
            self.entry_horas.delete(0, tk.END)
            self.entry_horas.insert(0, f"{float(row['horas_cumplidas']):.2f}")
            if not asistio:
                self.entry_horas.config(state="disabled")
        else:
            self.var_asistio.set(True)
            self.entry_horas.config(state="normal")
            self.entry_horas.delete(0, tk.END)
            self.entry_horas.insert(0, f"{self.actividad_actual['duracion_horas']:.2f}")

        self.txt_obs.delete("1.0", tk.END)
        if row["observaciones"]:
            self.txt_obs.insert("1.0", row["observaciones"])

    def _al_cambiar_check_asistio(self):
        if self.var_asistio.get():
            self.entry_horas.config(state="normal")
            if self.actividad_actual and (not self.entry_horas.get() or float(self.entry_horas.get() or 0) == 0):
                self.entry_horas.delete(0, tk.END)
                self.entry_horas.insert(0, f"{self.actividad_actual['duracion_horas']:.2f}")
        else:
            self.entry_horas.config(state="normal")
            self.entry_horas.delete(0, tk.END)
            self.entry_horas.insert(0, "0.00")
            self.entry_horas.config(state="disabled")

    def _guardar_asistencia(self):
        exito, mensaje = self.controller.guardar_asistencia(
            asignacion=self.asignacion_seleccionada,
            asistio=self.var_asistio.get(),
            horas_str=self.entry_horas.get(),
            observaciones=self.txt_obs.get("1.0", tk.END)
        )
        if not exito:
            messagebox.showwarning("Validación de Asistencia", mensaje)
            return

        messagebox.showinfo("Asistencia Registrada", mensaje)
        self._cargar_planilla()