-- ============================================================================
-- SAVE THE CHILDREN BOLIVIA - SISTEMA DE GESTIÓN DE VOLUNTARIADO (v1.3 FNBC)
-- Compatible con XAMPP (MariaDB / MySQL 8.0+) — Sin Triggers
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS save_the_children_bolivia_db;
DROP DATABASE IF EXISTS save_the_children_db;
CREATE DATABASE save_the_children_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE save_the_children_db;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 1. SEGURIDAD Y AUDITORÍA DE ACCESOS
-- ============================================================================

CREATE TABLE USUARIO (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('Administrador', 'Voluntario') NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE AUDITORIA_ACCESO (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    fecha_hora_acceso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_auditoria_fecha (fecha_hora_acceso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2. VOLUNTARIADO Y ADMISIÓN ESTRICTA (1:1 EN FNBC)
-- ============================================================================

CREATE TABLE VOLUNTARIO (
    id_voluntario INT AUTO_INCREMENT PRIMARY KEY,
    ci VARCHAR(15) NOT NULL UNIQUE,
    nombres VARCHAR(80) NOT NULL,
    apellido_paterno VARCHAR(60) NOT NULL,
    apellido_materno VARCHAR(60) NULL,
    fecha_nacimiento DATE NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    correo VARCHAR(120) NULL,
    direccion VARCHAR(200) NULL,
    estado ENUM(
        'Postulante',
        'Admitido',
        'Rechazado',
        'Inactivo',
        'Inactivo_Definitivo'
    ) NOT NULL DEFAULT 'Postulante',
    fecha_inscripcion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_admision DATE NULL,
    id_usuario INT NULL UNIQUE,
    id_admin_registra INT NOT NULL,
    CONSTRAINT fk_voluntario_usuario
        FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_voluntario_admin
        FOREIGN KEY (id_admin_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE EVALUACION_ADMISION (
    id_voluntario INT PRIMARY KEY,
    ci_presentado TINYINT(1) NOT NULL DEFAULT 0,
    datos_verificados TINYINT(1) NOT NULL DEFAULT 0,
    disponibilidad ENUM('Mañanas', 'Tardes', 'Fines de Semana', 'Tiempo Completo') NOT NULL,
    acepta_reglas TINYINT(1) NOT NULL DEFAULT 0,
    antecedentes_presentado TINYINT(1) NOT NULL DEFAULT 0,
    tiene_antecedentes TINYINT(1) NOT NULL DEFAULT 0,
    cv_presentado TINYINT(1) NOT NULL DEFAULT 0,
    nivel_educativo ENUM(
        'Colegio Incompleto',
        'Bachiller',
        'Estudiante Universitario / Técnico',
        'Título Profesional'
    ) NOT NULL DEFAULT 'Bachiller',
    situacion_laboral ENUM(
        'No Trabaja',
        'Trabaja Medio Tiempo',
        'Trabaja Tiempo Completo',
        'Independiente'
    ) NOT NULL DEFAULT 'No Trabaja',
    resultado_automatico ENUM('Admitido', 'Rechazado') NOT NULL,
    decision_final ENUM('Admitido', 'Rechazado') NOT NULL,
    motivo_cambio VARCHAR(255) NULL,
    id_admin_evalua INT NOT NULL,
    fecha_evaluacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_motivo_cambio CHECK (
        (decision_final = resultado_automatico)
        OR (motivo_cambio IS NOT NULL AND TRIM(motivo_cambio) <> '')
    ),
    CONSTRAINT fk_evaluacion_voluntario
        FOREIGN KEY (id_voluntario) REFERENCES VOLUNTARIO(id_voluntario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_evaluacion_admin
        FOREIGN KEY (id_admin_evalua) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. ACTIVIDADES, CONFIRMACIÓN DE ASIGNACIONES, ASISTENCIA Y STRIKES
-- ============================================================================

CREATE TABLE ACTIVIDAD (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    lugar VARCHAR(150) NOT NULL,
    cupo_maximo INT NOT NULL DEFAULT 10,
    estado ENUM('Programada', 'En Curso', 'Finalizada', 'Cancelada') NOT NULL DEFAULT 'Programada',
    id_admin_crea INT NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_actividad_cupo CHECK (cupo_maximo BETWEEN 3 AND 15),
    CONSTRAINT chk_actividad_horas CHECK (hora_fin > hora_inicio),
    CONSTRAINT fk_actividad_admin
        FOREIGN KEY (id_admin_crea) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_actividad_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ASIGNACION (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_actividad INT NOT NULL,
    id_voluntario INT NOT NULL,
    tenia_disponibilidad TINYINT(1) NOT NULL DEFAULT 1,
    estado ENUM('Pendiente', 'Confirmada', 'Rechazada', 'Cancelada') NOT NULL DEFAULT 'Pendiente',
    motivo_rechazo VARCHAR(255) NULL,
    fecha_respuesta DATETIME NULL,
    id_admin_asigna INT NOT NULL,
    fecha_asignacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_actividad_voluntario UNIQUE (id_actividad, id_voluntario),
    CONSTRAINT fk_asignacion_actividad
        FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_asignacion_voluntario
        FOREIGN KEY (id_voluntario) REFERENCES VOLUNTARIO(id_voluntario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_asignacion_admin
        FOREIGN KEY (id_admin_asigna) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ASISTENCIA (
    id_asignacion INT PRIMARY KEY,
    asistio TINYINT(1) NOT NULL DEFAULT 0,
    hora_entrada TIME NULL,
    hora_salida TIME NULL,
    observaciones VARCHAR(255) NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_admin_registra INT NOT NULL,
    CONSTRAINT chk_asistencia_horarios CHECK (
        (asistio = 0 AND hora_entrada IS NULL AND hora_salida IS NULL)
        OR (asistio = 1 AND hora_entrada IS NOT NULL AND hora_salida IS NOT NULL AND hora_salida > hora_entrada)
    ),
    CONSTRAINT fk_asistencia_asignacion
        FOREIGN KEY (id_asignacion) REFERENCES ASIGNACION(id_asignacion)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_asistencia_admin
        FOREIGN KEY (id_admin_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE STRIKE_VOLUNTARIO (
    id_strike INT AUTO_INCREMENT PRIMARY KEY,
    id_voluntario INT NOT NULL,
    id_asignacion INT NOT NULL,
    motivo ENUM('Rechazo_Con_Disponibilidad', 'Inasistencia_Confirmada') NOT NULL,
    cantidad_strikes TINYINT NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_admin_registra INT NULL,
    CONSTRAINT uq_asignacion_motivo_strike UNIQUE (id_asignacion, motivo),
    CONSTRAINT chk_puntos_strike CHECK (
        (motivo = 'Rechazo_Con_Disponibilidad' AND cantidad_strikes = 1)
        OR (motivo = 'Inasistencia_Confirmada' AND cantidad_strikes = 2)
    ),
    CONSTRAINT fk_strike_voluntario
        FOREIGN KEY (id_voluntario) REFERENCES VOLUNTARIO(id_voluntario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_strike_asignacion
        FOREIGN KEY (id_asignacion) REFERENCES ASIGNACION(id_asignacion)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_strike_admin
        FOREIGN KEY (id_admin_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. DONANTES (PERSONAS / ORGANIZACIONES), DONACIONES E INVENTARIO (FNBC)
-- ============================================================================

CREATE TABLE DONANTE (
    id_donante INT AUTO_INCREMENT PRIMARY KEY,
    tipo_donante ENUM('Persona', 'Organizacion') NOT NULL DEFAULT 'Persona',
    ci_nit VARCHAR(15) NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(15) NULL,
    correo VARCHAR(120) NULL,
    origen_registro ENUM('Administrador', 'Autoregistro') NOT NULL,
    id_admin_registra INT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_donante_admin
        FOREIGN KEY (id_admin_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_donante_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE INSUMO (
    id_insumo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    unidad_medida VARCHAR(40) NOT NULL,
    stock_actual DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT chk_insumo_stock CHECK (stock_actual >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE DONACION (
    id_donacion INT AUTO_INCREMENT PRIMARY KEY,
    id_donante INT NOT NULL,
    id_actividad INT NULL,
    tipo_donacion ENUM('DINERO', 'MATERIAL') NOT NULL,
    canal_registro ENUM('Administrador', 'Autodonacion') NOT NULL,
    es_donante_recurrente TINYINT(1) NOT NULL DEFAULT 0,
    fecha_donacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones VARCHAR(255) NULL,
    id_admin_registra INT NULL,
    CONSTRAINT fk_donacion_donante
        FOREIGN KEY (id_donante) REFERENCES DONANTE(id_donante)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_donacion_actividad
        FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_donacion_admin
        FOREIGN KEY (id_admin_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_donacion_fecha (fecha_donacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE DONACION_MONETARIA (
    id_donacion INT PRIMARY KEY,
    monto DECIMAL(10,2) NOT NULL,
    metodo_pago ENUM('QR', 'Efectivo', 'Transferencia') NOT NULL,
    CONSTRAINT chk_donacion_monto CHECK (monto > 0),
    CONSTRAINT fk_donacion_monetaria_padre
        FOREIGN KEY (id_donacion) REFERENCES DONACION(id_donacion)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE DONACION_DETALLE (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_donacion INT NOT NULL,
    id_insumo INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    CONSTRAINT uq_donacion_insumo UNIQUE (id_donacion, id_insumo),
    CONSTRAINT chk_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT fk_detalle_donacion
        FOREIGN KEY (id_donacion) REFERENCES DONACION(id_donacion)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_detalle_insumo
        FOREIGN KEY (id_insumo) REFERENCES INSUMO(id_insumo)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ENTREGA_INSUMO (
    id_entrega INT AUTO_INCREMENT PRIMARY KEY,
    id_actividad INT NOT NULL,
    id_insumo INT NOT NULL,
    id_voluntario_responsable INT NOT NULL,
    cantidad_entregada DECIMAL(10,2) NOT NULL,
    fecha_entrega DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones VARCHAR(255) NULL,
    id_admin_autoriza INT NOT NULL,
    CONSTRAINT chk_entrega_cantidad CHECK (cantidad_entregada > 0),
    CONSTRAINT fk_entrega_actividad
        FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_entrega_insumo
        FOREIGN KEY (id_insumo) REFERENCES INSUMO(id_insumo)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_entrega_voluntario
        FOREIGN KEY (id_voluntario_responsable) REFERENCES VOLUNTARIO(id_voluntario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_entrega_admin
        FOREIGN KEY (id_admin_autoriza) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. CATÁLOGO BASE DE INSUMOS (USUARIO ADMIN SE CREA CON seed_admin.py)
-- ============================================================================

INSERT INTO INSUMO (id_insumo, nombre, unidad_medida, stock_actual) VALUES
(1, 'Ropa de Abrigo Infantil', 'Prendas', 0.00),
(2, 'Alimentos No Perecederos', 'Kilogramos (kg)', 0.00),
(3, 'Útiles Escolares', 'Unidades / Kits', 0.00),
(4, 'Artículos de Higiene y Bioseguridad', 'Unidades / Paquetes', 0.00),
(5, 'Medicamentos / Botiquín Básico', 'Cajas / Unidades', 0.00);