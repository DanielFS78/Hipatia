-- ===============================================================================
-- ESQUEMA POSTGRESQL - Sistema de Cálculo de Tiempos de Fabricación
-- Versión unificada que combina montaje.db y pilas.db en un solo esquema
-- ===============================================================================

-- Configuración inicial
SET client_encoding = 'UTF8';
SET timezone = 'UTC';

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===============================================================================
-- TABLA: products (Nueva estructura expandida)
-- Evolución de la tabla productos con 7 campos específicos
-- ===============================================================================
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,

    -- Nuevos campos específicos del dominio (reemplazan codigo/descripcion)
    nivel INTEGER,
    capitulo VARCHAR(100),
    componente VARCHAR(200) NOT NULL UNIQUE, -- Equivale al antiguo 'codigo'
    denominacion VARCHAR(500) NOT NULL,      -- Equivale al antiguo 'descripcion'
    cantidad DECIMAL(10,3),
    tipo VARCHAR(20) CHECK (tipo IN ('Compuesto', 'Articulo', 'Proceso')) NOT NULL DEFAULT 'Articulo',
    ubicacion VARCHAR(200),

    -- Campos heredados de la estructura anterior
    departamento VARCHAR(100) NOT NULL,
    tipo_trabajador INTEGER NOT NULL,
    donde VARCHAR(200),
    tiene_subfabricaciones BOOLEAN NOT NULL DEFAULT FALSE,
    tiempo_optimo DECIMAL(8,2),

    -- Metadatos y auditoria
    legacy_data JSONB, -- Almacena datos originales para no perder información
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    -- Índices implícitos por UNIQUE y PK ya definidos arriba
    CONSTRAINT products_componente_not_empty CHECK (LENGTH(TRIM(componente)) > 0),
    CONSTRAINT products_denominacion_not_empty CHECK (LENGTH(TRIM(denominacion)) > 0)
);

-- Índices adicionales para optimizar consultas frecuentes
CREATE INDEX idx_products_departamento ON products(departamento);
CREATE INDEX idx_products_tipo ON products(tipo);
CREATE INDEX idx_products_active ON products(activo) WHERE activo = TRUE;
CREATE INDEX idx_products_legacy_data ON products USING GIN(legacy_data);

-- ===============================================================================
-- TABLA: workers (Evolución de trabajadores)
-- ===============================================================================
CREATE TABLE workers (
    id BIGSERIAL PRIMARY KEY,
    nombre_completo VARCHAR(200) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    notas TEXT,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(50),

    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT workers_nombre_not_empty CHECK (LENGTH(TRIM(nombre_completo)) > 0)
);

CREATE INDEX idx_workers_active ON workers(activo) WHERE activo = TRUE;
CREATE INDEX idx_workers_username ON workers(username) WHERE username IS NOT NULL;

-- ===============================================================================
-- TABLA: machines (Evolución de maquinas)
-- ===============================================================================
CREATE TABLE machines (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL UNIQUE,
    departamento VARCHAR(100) NOT NULL,
    tipo_proceso VARCHAR(100),
    activa BOOLEAN NOT NULL DEFAULT TRUE,

    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT machines_nombre_not_empty CHECK (LENGTH(TRIM(nombre)) > 0)
);

CREATE INDEX idx_machines_active ON machines(activa) WHERE activa = TRUE;
CREATE INDEX idx_machines_departamento ON machines(departamento);

-- ===============================================================================
-- TABLA: materials (Evolución de materiales)
-- ===============================================================================
CREATE TABLE materials (
    id BIGSERIAL PRIMARY KEY,
    codigo_componente VARCHAR(200) NOT NULL UNIQUE,
    descripcion_componente TEXT,

    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- ===============================================================================
-- NUEVA TABLA: preassemblies (Gestión de Premontajes)
-- ===============================================================================
CREATE TABLE preassemblies (
    id BIGSERIAL PRIMARY KEY,
    descripcion VARCHAR(500) NOT NULL,
    notas TEXT,
    imagenes TEXT[], -- Array de rutas de imágenes
    tiempo_estimado_minutos DECIMAL(8,2) NOT NULL DEFAULT 0,

    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT preassemblies_descripcion_not_empty CHECK (LENGTH(TRIM(descripcion)) > 0),
    CONSTRAINT preassemblies_tiempo_positive CHECK (tiempo_estimado_minutos >= 0)
);

-- ===============================================================================
-- TABLA: preassembly_components (Relación Many-to-Many premontajes-componentes)
-- ===============================================================================
CREATE TABLE preassembly_components (
    preassembly_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    cantidad DECIMAL(10,3) DEFAULT 1,
    notas VARCHAR(500),

    PRIMARY KEY (preassembly_id, product_id),
    FOREIGN KEY (preassembly_id) REFERENCES preassemblies(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ===============================================================================
-- TABLA: production_stacks (Evolución unificada de pilas)
-- Combina información de pilas.db en una estructura mejorada
-- ===============================================================================
CREATE TABLE production_stacks (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,

    -- Información de origen y resultados
    producto_origen_codigo VARCHAR(200), -- Para compatibilidad con datos legacy
    resultados_simulacion JSONB,
    fabricacion_origen_codigo VARCHAR(200),

    -- Metadatos mejorados
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_worker_id BIGINT,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),

    -- Campos de auditoria
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    legacy_data JSONB,

    FOREIGN KEY (created_by_worker_id) REFERENCES workers(id) ON DELETE SET NULL,

    CONSTRAINT production_stacks_nombre_not_empty CHECK (LENGTH(TRIM(nombre)) > 0)
);

-- Índices para optimizar consultas de pilas
CREATE INDEX idx_production_stacks_status ON production_stacks(status);
CREATE INDEX idx_production_stacks_fecha ON production_stacks(fecha_creacion);
CREATE INDEX idx_production_stacks_origen ON production_stacks(producto_origen_codigo);

-- ===============================================================================
-- TABLA: stack_steps (Evolución de pasos_pila)
-- ===============================================================================
CREATE TABLE stack_steps (
    id BIGSERIAL PRIMARY KEY,
    stack_id BIGINT NOT NULL,
    orden INTEGER NOT NULL,

    -- Datos del paso
    datos_paso JSONB NOT NULL,
    tipo_paso VARCHAR(50) DEFAULT 'task' CHECK (tipo_paso IN ('task', 'preassembly', 'manual')),

    -- Referencias opcionales
    product_id BIGINT,
    preassembly_id BIGINT,

    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (stack_id) REFERENCES production_stacks(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (preassembly_id) REFERENCES preassemblies(id) ON DELETE SET NULL,

    UNIQUE(stack_id, orden)
);

CREATE INDEX idx_stack_steps_stack_orden ON stack_steps(stack_id, orden);

-- ===============================================================================
-- TABLAS HEREDADAS (mantenidas para compatibilidad durante migración)
-- ===============================================================================

-- Subfabricaciones (evoluciona hacia componentes del producto)
CREATE TABLE subfabricaciones (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    descripcion TEXT NOT NULL,
    tiempo DECIMAL(8,2) NOT NULL,
    tipo_trabajador INTEGER NOT NULL,
    requiere_maquina_tipo VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Procesos mecánicos
CREATE TABLE procesos_mecanicos (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    tiempo DECIMAL(8,2) NOT NULL,
    tipo_trabajador INTEGER NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Fabricaciones
CREATE TABLE fabricaciones (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(200) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Contenido de fabricaciones
CREATE TABLE fabricacion_contenido (
    id BIGSERIAL PRIMARY KEY,
    fabricacion_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,

    UNIQUE(fabricacion_id, product_id)
);

-- ===============================================================================
-- FUNCIONES Y TRIGGERS PARA AUDITORIA AUTOMÁTICA
-- ===============================================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workers_updated_at BEFORE UPDATE ON workers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_machines_updated_at BEFORE UPDATE ON machines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preassemblies_updated_at BEFORE UPDATE ON preassemblies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_production_stacks_updated_at BEFORE UPDATE ON production_stacks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===============================================================================
-- DATOS INICIALES Y CONFIGURACIÓN
-- ===============================================================================

-- Insertar configuración básica del sistema
CREATE TABLE system_config (
    clave VARCHAR(100) PRIMARY KEY,
    valor TEXT NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Configuración inicial
INSERT INTO system_config (clave, valor, descripcion) VALUES
('schema_version', '1.0', 'Versión del esquema de base de datos'),
('migration_completed', 'false', 'Indica si la migración desde SQLite fue completada'),
('system_initialized', 'true', 'Sistema inicializado correctamente');

-- ===============================================================================
-- COMENTARIOS FINALES
-- ===============================================================================

COMMENT ON TABLE products IS 'Tabla principal de productos con estructura expandida de 7 campos específicos del dominio';
COMMENT ON TABLE preassemblies IS 'Nueva funcionalidad: gestión de premontajes con detección automática';
COMMENT ON TABLE production_stacks IS 'Pilas de producción unificadas (antigua pilas.db)';
COMMENT ON TABLE stack_steps IS 'Pasos individuales de las pilas de producción';

-- Completado: esquema PostgreSQL unificado listo para la migración