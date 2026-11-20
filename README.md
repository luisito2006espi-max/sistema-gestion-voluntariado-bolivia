# Sistema de Gestión de Voluntariado — Save the Children Bolivia

Aplicación de escritorio desarrollada en **Python (arquitectura MVC)** con interfaz gráfica en **Tkinter / ttkbootstrap** y base de datos relacional **MySQL (3FN)**.

## Módulos Principales
- **Autenticación y Auditoría:** Inicio de sesión con hashes SHA-256, control de roles (`Administrador` y `Voluntario`) y trazabilidad automática de accesos (`AUDITORIA_ACCESO`).
- **Voluntariado:** Inscripción de postulantes (validación de edad 18–60 años), admisión con generación automática de credenciales y control de estados.
- **Operaciones y Asistencia:** Programación de actividades con sincronización automática de horarios (`HH:MM:SS`), asignación por cupos (máx. 1 actividad/día) y registro de horas cumplidas.
- **Donaciones y Analítica:** Registro de aportes monetarios y en especie (3FN), dashboard ejecutivo, 12 gráficos estadísticos (`matplotlib`) y exportación a Excel (`openpyxl`).

## Ejecución
1. Importar el esquema y catálogos SQL en MySQL.
2. Configurar las credenciales de conexión en `config/database.py`.
3. Instalar dependencias: `pip install -r requirements.txt`
4. Ejecutar `python seed_admin.py` para crear el usuario Administrador y luego `python main.py`.