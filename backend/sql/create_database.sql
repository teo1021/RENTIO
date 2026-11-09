-- RENTIO PostgreSQL bootstrap. Execute against a newly created empty database.
BEGIN;

CREATE TYPE rol_usuario AS ENUM ('arrendatario', 'propietario', 'admin');
CREATE TYPE tipo_propiedad AS ENUM ('casa', 'apartamento', 'habitacion', 'finca');
CREATE TYPE estado_propiedad AS ENUM ('disponible', 'arrendada', 'inactiva');
CREATE TYPE estado_solicitud AS ENUM ('pendiente', 'aceptada', 'rechazada');
CREATE TYPE estado_contrato AS ENUM ('activo', 'finalizado', 'cancelado');

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    correo VARCHAR(255) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL DEFAULT 'arrendatario',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_usuarios_correo ON usuarios(correo);

CREATE TABLE perfiles_usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100), apellido VARCHAR(100), telefono VARCHAR(20),
    cedula VARCHAR(20), foto_perfil VARCHAR(500),
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE
);
CREATE TABLE barrios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    comuna VARCHAR(100) NOT NULL,
    zona VARCHAR(100) NOT NULL
);
CREATE INDEX ix_barrios_nombre ON barrios(nombre);
CREATE TABLE caracteristicas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    icono VARCHAR(100)
);
CREATE INDEX ix_caracteristicas_nombre ON caracteristicas(nombre);

CREATE TABLE propiedades (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio_mensual NUMERIC(10,2) NOT NULL,
    direccion VARCHAR(500) NOT NULL,
    estrato INTEGER NOT NULL,
    area_m2 NUMERIC(10,2),
    habitaciones INTEGER NOT NULL DEFAULT 1,
    banos INTEGER NOT NULL DEFAULT 1,
    tipo tipo_propiedad NOT NULL DEFAULT 'apartamento',
    estado estado_propiedad NOT NULL DEFAULT 'disponible',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    barrio_id INTEGER REFERENCES barrios(id),
    propietario_id INTEGER NOT NULL REFERENCES usuarios(id)
);
CREATE TABLE imagenes_propiedad (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    propiedad_id INTEGER NOT NULL REFERENCES propiedades(id) ON DELETE CASCADE
);
CREATE TABLE propiedad_caracteristica (
    propiedad_id INTEGER NOT NULL REFERENCES propiedades(id) ON DELETE CASCADE,
    caracteristica_id INTEGER NOT NULL REFERENCES caracteristicas(id) ON DELETE CASCADE,
    PRIMARY KEY (propiedad_id, caracteristica_id)
);
CREATE TABLE solicitudes_arriendo (
    id SERIAL PRIMARY KEY,
    propiedad_id INTEGER NOT NULL REFERENCES propiedades(id) ON DELETE CASCADE,
    arrendatario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    mensaje TEXT,
    estado estado_solicitud NOT NULL DEFAULT 'pendiente',
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE contratos_arriendo (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL UNIQUE REFERENCES solicitudes_arriendo(id) ON DELETE CASCADE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    precio_acordado NUMERIC(10,2) NOT NULL,
    estado estado_contrato NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE SCHEMA ia_marketing;
CREATE TABLE ia_marketing.conversaciones (
    id SERIAL PRIMARY KEY,
    propietario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    propiedad_id INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'recopilando'
        CHECK (estado IN ('recopilando','lista','generada','cerrada')),
    datos_recopilados JSON NOT NULL DEFAULT '{}'::json,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_ia_conversaciones_propietario ON ia_marketing.conversaciones(propietario_id, fecha_actualizacion DESC);
CREATE INDEX ix_ia_conversaciones_propiedad ON ia_marketing.conversaciones(propiedad_id);
CREATE TABLE ia_marketing.mensajes (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES ia_marketing.conversaciones(id) ON DELETE CASCADE,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('usuario','asistente')),
    contenido TEXT NOT NULL,
    datos_extraidos JSON NOT NULL DEFAULT '{}'::json,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_ia_mensajes_conversacion_id ON ia_marketing.mensajes(conversacion_id);
CREATE TABLE ia_marketing.resultados_generados (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES ia_marketing.conversaciones(id) ON DELETE CASCADE,
    propiedad_id INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    descripcion TEXT NOT NULL,
    precio_sugerido NUMERIC(12,2),
    precio_minimo NUMERIC(12,2),
    precio_maximo NUMERIC(12,2),
    moneda VARCHAR(3) NOT NULL DEFAULT 'COP',
    datos_usados JSON NOT NULL DEFAULT '{}'::json,
    fuente_datos VARCHAR(100),
    version_datos VARCHAR(100),
    metadatos_calculo JSON NOT NULL DEFAULT '{}'::json,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_ia_rango_precio CHECK (
        precio_minimo IS NULL OR precio_maximo IS NULL OR precio_minimo <= precio_maximo
    )
);
CREATE INDEX ix_ia_resultados_conversacion_id ON ia_marketing.resultados_generados(conversacion_id);
CREATE INDEX ix_ia_resultados_propiedad_id ON ia_marketing.resultados_generados(propiedad_id);
COMMIT;
