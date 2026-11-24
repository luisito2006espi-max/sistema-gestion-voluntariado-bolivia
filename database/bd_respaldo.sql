CREATE DATABASE save_the_children_bolivia;

USE save_the_children_bolivia;

CREATE TABLE ROL (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE USUARIO (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    ultimo_acceso DATETIME NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol) REFERENCES ROL(id_rol)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE AUDITORIA_ACCESO (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    fecha_hora_acceso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_auditoria_fecha (fecha_hora_acceso)
);

CREATE TABLE ESTADO_VOLUNTARIO (
    id_estado_vol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE ESTADO_ACTIVIDAD (
    id_estado_actividad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE ESTADO_ASIGNACION (
    id_estado_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE VOLUNTARIO (
    id_voluntario INT AUTO_INCREMENT PRIMARY KEY,
    ci VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    fecha_nacimiento DATE NULL,
    telefono VARCHAR(20) NULL,
    correo VARCHAR(120) NULL,
    direccion VARCHAR(200) NULL,
    habilidades VARCHAR(200) NULL,
    disponibilidad VARCHAR(100) NULL,
    id_estado_vol INT NOT NULL DEFAULT 1,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_admision DATE NULL,
    id_usuario INT NULL UNIQUE,
    id_usuario_registra INT NULL,
    CONSTRAINT fk_voluntario_estado
        FOREIGN KEY (id_estado_vol) REFERENCES ESTADO_VOLUNTARIO(id_estado_vol)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_voluntario_usuario
        FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_voluntario_registrador
        FOREIGN KEY (id_usuario_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE ACTIVIDAD (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    lugar VARCHAR(150) NOT NULL,
    cupo_maximo INT NOT NULL DEFAULT 10,
    id_estado_actividad INT NOT NULL DEFAULT 1,
    id_usuario_crea INT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_actividad_cupo CHECK (cupo_maximo > 0),
    CONSTRAINT chk_actividad_horas CHECK (hora_fin > hora_inicio),
    CONSTRAINT fk_actividad_estado
        FOREIGN KEY (id_estado_actividad) REFERENCES ESTADO_ACTIVIDAD(id_estado_actividad)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_actividad_usuario
        FOREIGN KEY (id_usuario_crea) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_actividad_fecha (fecha)
);

CREATE TABLE ASIGNACION_VOLUNTARIO (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_actividad INT NOT NULL,
    id_voluntario INT NOT NULL,
    id_estado_asignacion INT NOT NULL DEFAULT 1,
    fecha_asignacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_actividad_voluntario UNIQUE (id_actividad, id_voluntario),
    CONSTRAINT fk_asignacion_actividad
        FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_asignacion_voluntario
        FOREIGN KEY (id_voluntario) REFERENCES VOLUNTARIO(id_voluntario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_asignacion_estado
        FOREIGN KEY (id_estado_asignacion) REFERENCES ESTADO_ASIGNACION(id_estado_asignacion)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE ASISTENCIA (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL UNIQUE,
    asistio TINYINT(1) NOT NULL DEFAULT 0,
    horas_cumplidas DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    observaciones VARCHAR(255) NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario_registra INT NULL,
    CONSTRAINT chk_asistencia_horas CHECK (horas_cumplidas >= 0),
    CONSTRAINT fk_asistencia_asignacion
        FOREIGN KEY (id_asignacion) REFERENCES ASIGNACION_VOLUNTARIO(id_asignacion)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_asistencia_usuario
        FOREIGN KEY (id_usuario_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE DONANTE (
    id_donante INT AUTO_INCREMENT PRIMARY KEY,
    documento VARCHAR(30) NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(20) NULL,
    correo VARCHAR(120) NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE TIPO_DONACION (
    id_tipo_donacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE METODO_PAGO (
    id_metodo_pago INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE INSUMO (
    id_insumo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    unidad_medida VARCHAR(40) NOT NULL,
    stock_actual DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT chk_insumo_stock CHECK (stock_actual >= 0)
);

CREATE TABLE DONACION (
    id_donacion INT AUTO_INCREMENT PRIMARY KEY,
    id_donante INT NOT NULL,
    id_tipo_donacion INT NOT NULL,
    monto DECIMAL(10,2) NULL,
    id_metodo_pago INT NULL,
    fecha DATE NOT NULL,
    observaciones VARCHAR(255) NULL,
    id_usuario_registra INT NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_donacion_donante
        FOREIGN KEY (id_donante) REFERENCES DONANTE(id_donante)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_donacion_tipo
        FOREIGN KEY (id_tipo_donacion) REFERENCES TIPO_DONACION(id_tipo_donacion)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_donacion_metodo
        FOREIGN KEY (id_metodo_pago) REFERENCES METODO_PAGO(id_metodo_pago)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_donacion_usuario
        FOREIGN KEY (id_usuario_registra) REFERENCES USUARIO(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_donacion_fecha (fecha)
);

CREATE TABLE DONACION_DETALLE (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_donacion INT NOT NULL,
    id_insumo INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    CONSTRAINT chk_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT fk_detalle_donacion
        FOREIGN KEY (id_donacion) REFERENCES DONACION(id_donacion)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_detalle_insumo
        FOREIGN KEY (id_insumo) REFERENCES INSUMO(id_insumo)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

DELIMITER //

CREATE TRIGGER trg_auditoria_login
AFTER UPDATE ON USUARIO
FOR EACH ROW
BEGIN
    IF NEW.ultimo_acceso IS NOT NULL
       AND (OLD.ultimo_acceso IS NULL OR NEW.ultimo_acceso <> OLD.ultimo_acceso) THEN
        INSERT INTO AUDITORIA_ACCESO (id_usuario, fecha_hora_acceso)
        VALUES (NEW.id_usuario, NEW.ultimo_acceso);
    END IF;
END//

CREATE TRIGGER trg_validar_asignacion_bi
BEFORE INSERT ON ASIGNACION_VOLUNTARIO
FOR EACH ROW
BEGIN
    DECLARE v_estado_vol VARCHAR(30);
    DECLARE v_cupo_max INT;
    DECLARE v_asignados INT;

    SELECT ev.nombre INTO v_estado_vol
    FROM VOLUNTARIO v
    INNER JOIN ESTADO_VOLUNTARIO ev ON v.id_estado_vol = ev.id_estado_vol
    WHERE v.id_voluntario = NEW.id_voluntario;

    IF v_estado_vol <> 'Admitido' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Solo los voluntarios con estado Admitido pueden ser asignados a actividades.';
    END IF;

    SELECT cupo_maximo INTO v_cupo_max
    FROM ACTIVIDAD
    WHERE id_actividad = NEW.id_actividad;

    SELECT COUNT(*) INTO v_asignados
    FROM ASIGNACION_VOLUNTARIO a
    INNER JOIN ESTADO_ASIGNACION ea ON a.id_estado_asignacion = ea.id_estado_asignacion
    WHERE a.id_actividad = NEW.id_actividad
      AND ea.nombre = 'Confirmada';

    IF v_asignados >= v_cupo_max THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La actividad ya alcanzó su cupo máximo de voluntarios.';
    END IF;
END//

CREATE TRIGGER trg_validar_donacion_bi
BEFORE INSERT ON DONACION
FOR EACH ROW
BEGIN
    DECLARE v_tipo VARCHAR(30);
    DECLARE v_metodo VARCHAR(50);

    SELECT UPPER(nombre) INTO v_tipo
    FROM TIPO_DONACION
    WHERE id_tipo_donacion = NEW.id_tipo_donacion;

    IF v_tipo = 'DINERO' THEN
        IF NEW.monto IS NULL OR NEW.monto <= 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Una donación monetaria requiere un monto mayor a 0.00 Bs.';
        END IF;
        IF NEW.id_metodo_pago IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Una donación monetaria requiere un método de pago.';
        END IF;

        SELECT LOWER(nombre) INTO v_metodo
        FROM METODO_PAGO
        WHERE id_metodo_pago = NEW.id_metodo_pago;

        IF v_metodo = 'tarjeta' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'El método de pago Tarjeta está deshabilitado por seguridad del donante.';
        END IF;
    ELSEIF v_tipo = 'MATERIAL' THEN
        SET NEW.monto = NULL;
        SET NEW.id_metodo_pago = NULL;
    END IF;
END//

CREATE TRIGGER trg_sumar_stock_insumo
AFTER INSERT ON DONACION_DETALLE
FOR EACH ROW
BEGIN
    UPDATE INSUMO
    SET stock_actual = stock_actual + NEW.cantidad
    WHERE id_insumo = NEW.id_insumo;
END//

DELIMITER ;

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
(3, 'Efectivo'),
(4, 'Transferencia');

INSERT INTO INSUMO (id_insumo, nombre, unidad_medida, stock_actual) VALUES
(1, 'Ropa', 'Prendas', 0.00),
(2, 'Alimentos', 'Kilogramos (kg)', 0.00),
(3, 'Útiles escolares', 'Unidades / Kits', 0.00),
(4, 'Higiene', 'Unidades / Paquetes', 0.00),
(5, 'Medicamentos / Botiquín', 'Cajas / Unidades', 0.00);