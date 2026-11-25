# Sistema de Gestión de Voluntariado — Save the Children Bolivia


Aplicación de escritorio desarrollada en **Python (arquitectura MVC)** con interfaz gráfica en **Tkinter / ttkbootstrap** y base de datos relacional **MySQL (FNBC v1.3)**.

## Módulos Principales
- **Autenticación y Auditoría:** Inicio de sesión con hashes SHA-256, control de roles (`Administrador` y `Voluntario`) y trazabilidad automática de accesos (`AUDITORIA_ACCESO`).
- **Voluntariado y Admisión Documental:** Inscripción de postulantes (validación de edad 18–60 años), evaluación física de los 5 requisitos documentales con dictamen automático o manual auditado, generación automática de credenciales y control de strikes.
- **Operaciones y Asistencia:** Programación de actividades con sincronización automática de horarios (`HH:MM:SS`), asignación por cupos (máx. 1 actividad/día), portal del voluntario y registro de horas cumplidas (`ASISTENCIA`).
- **Donaciones, Autodonación e Inventario:** Registro administrativo y **portal público de autodonación** desde el login (aportes monetarios y materiales con comprobante), control de stock disponible, despacho hacia actividades internas u organizaciones externas (`ENTREGA_INSUMO`), dashboard ejecutivo (`matplotlib`) y exportación a Excel (`openpyxl`).

## Requisitos Previos
- **Python 3.10 o superior** (compatible con Python 3.15).
- **XAMPP** (con **MySQL** iniciado) o servidor MySQL / MariaDB.
- **Git** (Git Bash o terminal).

## Ejecución
1. Iniciar **Apache** y **MySQL** en XAMPP, abrir **phpMyAdmin** (`http://localhost/phpmyadmin`) e importar el archivo `bdv1_3.sql` (en la carpeta '\database') para crear la base de datos `save_the_children_db`.
2. Configurar las credenciales de conexión en `config/database.py`.
3. Ejecutar los siguientes comando en git bash `git clone https://github.com/luisito2006espi-max/sistema-gestion-voluntariado-bolivia.git`
4. Luego busca la carpeta "sistema-gestion-voluntariado-bolivia" `cd sistema-gestion-voluntariado-bolivia`
5. En el git introduce `git cheackout main`
6. Para instalar las librerias necesarias: `python -m venv venv`
7. luego: `source venv/Scripts/activate`
8. Por ultimo: `pip install -r requirements.txt`
9. Ejecutar `python seed_admin.py` para crear el usuario Administrador y luego `python main.py`.