-- ============================================================================
-- SISTEMA DE GESTIÓN DE VOLUNTARIADO, ACTIVIDADES Y DONACIONES
-- Organización: Save the Children Bolivia
-- Esquema: v2.0 (3FN, Auditoría Nativa, Integridad Referencial)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS save_the_children_bolivia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE save_the_children_bolivia;

-- ============================================================================
-- 1. MÓDULO DE SEGURIDAD, ROLES Y AUDITORÍA DE ACCESOS
-- ============================================================================

CREATE TABLE ROL (
    id_rol INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_rol),
    UNIQUE KEY uq_rol_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE USUARIO (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuario_login (usuario),
    CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES ROL(id_rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE AUDITORIA_ACCESO (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    fecha_hora_acceso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_auditoria),
    INDEX idx_auditoria_fecha (fecha_hora_acceso),
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2. MÓDULO DE VOLUNTARIADO
-- ============================================================================

CREATE TABLE ESTADO_VOLUNTARIO (
    id_estado_vol INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_estado_vol),
    UNIQUE KEY uq_estado_vol_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE VOLUNTARIO (
    id_voluntario INT NOT NULL AUTO_INCREMENT,
    ci VARCHAR(20) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NULL,
    fecha_nacimiento DATE NOT NULL,
    telefono VARCHAR(20) NULL,
    correo VARCHAR(100) NULL,
    fecha_inscripcion DATE NOT NULL,
    fecha_admision DATE NULL,
    id_estado_vol INT NOT NULL,
    id_usuario INT NULL,
    id_usuario_registra INT NULL,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_voluntario),
    UNIQUE KEY uq_voluntario_ci (ci),
    UNIQUE KEY uq_voluntario_usuario (id_usuario),
    INDEX idx_voluntario_inscripcion (fecha_inscripcion),
    CONSTRAINT fk_voluntario_estado FOREIGN KEY (id_estado_vol) REFERENCES ESTADO_VOLUNTARIO(id_estado_vol),
    CONSTRAINT fk_voluntario_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),
    CONSTRAINT fk_voluntario_registrador FOREIGN KEY (id_usuario_registra) REFERENCES USUARIO(id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. MÓDULO DE ACTIVIDADES, ASIGNACIONES Y CONTROL DE ASISTENCIA
-- ============================================================================

CREATE TABLE ESTADO_ACTIVIDAD (
    id_estado_actividad INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_estado_actividad),
    UNIQUE KEY uq_estado_act_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ACTIVIDAD (
    id_actividad INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    lugar VARCHAR(150) NOT NULL,
    cupo_maximo INT NOT NULL,
    id_estado_actividad INT NOT NULL,
    PRIMARY KEY (id_actividad),
    INDEX idx_actividad_fecha (fecha),
    CONSTRAINT fk_actividad_estado FOREIGN KEY (id_estado_actividad) REFERENCES ESTADO_ACTIVIDAD(id_estado_actividad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ESTADO_ASIGNACION (
    id_estado_asignacion INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_estado_asignacion),
    UNIQUE KEY uq_estado_asig_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ASIGNACION (
    id_asignacion INT NOT NULL AUTO_INCREMENT,
    id_voluntario INT NOT NULL,
    id_actividad INT NOT NULL,
    id_admin_asigna INT NOT NULL,
    id_estado_asignacion INT NOT NULL,
    PRIMARY KEY (id_asignacion),
    UNIQUE KEY uq_voluntario_actividad (id_voluntario, id_actividad),
    CONSTRAINT fk_asignacion_voluntario FOREIGN KEY (id_voluntario) REFERENCES VOLUNTARIO(id_voluntario),
    CONSTRAINT fk_asignacion_actividad FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad),
    CONSTRAINT fk_asignacion_admin FOREIGN KEY (id_admin_asigna) REFERENCES USUARIO(id_usuario),
    CONSTRAINT fk_asignacion_estado FOREIGN KEY (id_estado_asignacion) REFERENCES ESTADO_ASIGNACION(id_estado_asignacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ASISTENCIA (
    id_asistencia INT NOT NULL AUTO_INCREMENT,
    id_asignacion INT NOT NULL,
    asistio TINYINT(1) NOT NULL DEFAULT 0,
    horas_cumplidas DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    observaciones TEXT NULL,
    PRIMARY KEY (id_asistencia),
    UNIQUE KEY uq_asistencia_asignacion (id_asignacion),
    CONSTRAINT fk_asistencia_asignacion FOREIGN KEY (id_asignacion) REFERENCES ASIGNACION(id_asignacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. MÓDULO DE DONACIONES (MONETARIAS Y EN ESPECIE)
-- ============================================================================

CREATE TABLE DONANTE (
    id_donante INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(150) NOT NULL,
    ci_nit VARCHAR(30) NULL,
    telefono VARCHAR(20) NULL,
    correo VARCHAR(100) NULL,
    PRIMARY KEY (id_donante),
    UNIQUE KEY uq_donante_cinit (ci_nit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE TIPO_DONACION (
    id_tipo_donacion INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_tipo_donacion),
    UNIQUE KEY uq_tipo_donacion_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE METODO_PAGO (
    id_metodo_pago INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_metodo_pago),
    UNIQUE KEY uq_metodo_pago_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE INSUMO (
    id_insumo INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    unidad_medida VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_insumo),
    UNIQUE KEY uq_insumo_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE DONACION (
    id_donacion INT NOT NULL AUTO_INCREMENT,
    id_donante INT NOT NULL,
    id_tipo_donacion INT NOT NULL,
    id_metodo_pago INT NULL,
    monto DECIMAL(10,2) NULL,
    fecha_donacion DATE NOT NULL,
    observaciones TEXT NULL,
    id_usuario_registra INT NULL,
    PRIMARY KEY (id_donacion),
    INDEX idx_donacion_fecha (fecha_donacion),
    CONSTRAINT fk_donacion_donante FOREIGN KEY (id_donante) REFERENCES DONANTE(id_donante),
    CONSTRAINT fk_donacion_tipo FOREIGN KEY (id_tipo_donacion) REFERENCES TIPO_DONACION(id_tipo_donacion),
    CONSTRAINT fk_donacion_metodo FOREIGN KEY (id_metodo_pago) REFERENCES METODO_PAGO(id_metodo_pago),
    CONSTRAINT fk_donacion_usuario FOREIGN KEY (id_usuario_registra) REFERENCES USUARIO(id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE DONACION_DETALLE (
    id_detalle INT NOT NULL AUTO_INCREMENT,
    id_donacion INT NOT NULL,
    id_insumo INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id_detalle),
    UNIQUE KEY uq_donacion_insumo (id_donacion, id_insumo),
    CONSTRAINT fk_detalle_donacion FOREIGN KEY (id_donacion) REFERENCES DONACION(id_donacion),
    CONSTRAINT fk_detalle_insumo FOREIGN KEY (id_insumo) REFERENCES INSUMO(id_insumo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. DATOS INICIALES REQUERIDOS (TABLAS CATÁLOGO DEL SISTEMA)
-- ============================================================================

INSERT INTO ROL (id_rol, nombre) VALUES
(1, 'Administrador'),
(3, 'Voluntario');

INSERT INTO ESTADO_VOLUNTARIO (id_estado_vol, nombre) VALUES
(1, 'Postulante'),
(2, 'Admitido'),
(3, 'Rechazado'),
(4, 'Inactivo');

INSERT INTO ESTADO_ACTIVIDAD (id_estado_actividad, nombre) VALUES
(1, 'Programada'),
(2, 'En Curso'),
(3, 'Finalizada'),
(4, 'Cancelada');

INSERT INTO ESTADO_ASIGNACION (id_estado_asignacion, nombre) VALUES
(1, 'Confirmada'),
(2, 'Cancelada');

INSERT INTO TIPO_DONACION (id_tipo_donacion, nombre) VALUES
(1, 'DINERO'),
(2, 'MATERIAL');

INSERT INTO METODO_PAGO (id_metodo_pago, nombre) VALUES
(1, 'QR'),
(2, 'Tarjeta'),
(3, 'Efectivo'),
(4, 'Transferencia');

INSERT INTO INSUMO (id_insumo, nombre, unidad_medida) VALUES
(1, 'Ropa', 'Prendas'),
(2, 'Alimentos', 'Kilogramos (kg)'),
(3, 'Útiles escolares', 'Unidades / Kits'),
(4, 'Higiene', 'Unidades / Paquetes'),
(5, 'Medicamentos / Botiquín', 'Cajas / Unidades');