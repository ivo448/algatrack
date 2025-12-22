DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS lotes;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS clientes;

-- En Postgres usamos SERIAL en lugar de AUTOINCREMENT
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(20) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lotes (
    id SERIAL PRIMARY KEY,
    tipo_alga VARCHAR(50) NOT NULL,
    superficie NUMERIC(10,2) NOT NULL, -- NUMERIC es mejor para decimales exactos
    fecha_inicio DATE NOT NULL,
    fecha_cosecha_estimada DATE,
    estado VARCHAR(20) DEFAULT 'activo',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente VARCHAR(100) NOT NULL,
    producto VARCHAR(50) NOT NULL,
    cantidad_ton NUMERIC(10,2) NOT NULL,
    fecha_entrega DATE NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    empresa VARCHAR(100) UNIQUE NOT NULL, -- Nombre de la Razón Social
    contacto VARCHAR(100),                -- Persona de contacto (Ej: Juan Pérez)
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    estado VARCHAR(20) DEFAULT 'activo',  -- activo / inactivo
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS parametros_sistema;

CREATE TABLE parametros_sistema (
    clave VARCHAR(50) PRIMARY KEY,
    valor NUMERIC(10,4) NOT NULL, -- 4 decimales para precisión en coeficientes
    unidad VARCHAR(20),
    descripcion TEXT,
    categoria VARCHAR(20) -- 'economico' o 'tecnico'
);

-- Insertamos TODOS los valores que antes estaban fijos en Python
INSERT INTO parametros_sistema (clave, valor, unidad, descripcion, categoria) VALUES 
-- A. PRECIOS DE MERCADO (Lo que pagas)
('precio_agua_m3',      2500.00, 'CLP/m3',   'Costo agua industrial Atacama', 'economico'),
('precio_kwh',           180.00, 'CLP/kWh',  'Tarifa eléctrica industrial',   'economico'),
('precio_diesel_L',     1150.00, 'CLP/L',    'Precio litro petróleo',         'economico'),
('costo_hh_operario',   5500.00, 'CLP/Hora', 'Costo Hora Hombre promedio',    'economico'),

-- B. COEFICIENTES TÉCNICOS (Lo que gasta tu proceso por Tonelada)
('consumo_agua_ton',       3.00, 'm3/Ton',   'Agua para lavado por tonelada', 'tecnico'),
('consumo_energia_ton',   40.00, 'kWh/Ton',  'Electricidad proceso secado',   'tecnico'),
('consumo_diesel_ton',    12.50, 'L/Ton',    'Combustible grúas/lanchas',     'tecnico'),
('horas_hombre_ton',       4.50, 'HH/Ton',   'Horas de trabajo por tonelada', 'tecnico'),
('insumos_varios_ton',  5000.00, 'CLP/Ton',  'Sacos, etiquetas, otros',       'tecnico'),

-- C. PARÁMETROS OPERATIVOS (Tiempos y Capacidades)
('capacidad_cosecha_dia',  5.00, 'Ton/Dia',  'Capacidad máxima extracción',   'tecnico'),
('capacidad_planta_dia',   2.50, 'Ton/Dia',  'Capacidad máxima procesamiento','tecnico'),
('dias_ciclo_base',       45.00, 'Dias',     'Días crecimiento estándar',     'tecnico');

-- Tabla para definir el comportamiento biológico por temporada
CREATE TABLE configuracion_estacional (
    id SERIAL PRIMARY KEY,
    nombre_estacion VARCHAR(50) NOT NULL, -- Ej: 'Invierno', 'Verano'
    meses_asociados VARCHAR(50) NOT NULL, -- Ej: '5,6,7,8' (Lista separada por comas)
    
    -- FACTORES BIOLÓGICOS (1.0 = Normal, <1 = Lento, >1 = Rápido)
    factor_crecimiento NUMERIC(5,2) NOT NULL, -- Velocidad de crecimiento alga
    factor_biomasa NUMERIC(5,2) NOT NULL,     -- Rendimiento Ton/Ha
    
    -- FACTORES INDUSTRIALES CLIMÁTICOS
    factor_secado NUMERIC(5,2) NOT NULL,      -- Velocidad planta procesadora
    factor_energia NUMERIC(5,2) NOT NULL,     -- Consumo eléctrico (Calefacción)
    
    descripcion TEXT
);

-- Insertamos la lógica que antes tenías en Python, ahora en BD
INSERT INTO configuracion_estacional 
(nombre_estacion, meses_asociados, factor_biomasa, factor_secado, factor_energia, factor_crecimiento, descripcion) 
VALUES 
('Invierno', '5,6,7,8', 0.70, 0.60, 1.40, 0.80, 'Frio ralentiza crecimiento y secado, aumenta gasto energia'),
('Verano',   '1,2,12',  1.20, 1.10, 1.00, 1.20, 'Calor acelera biomasa y secado eficiente'),
('Media',    '3,4,9,10,11', 1.00, 1.00, 1.10, 1.00, 'Condiciones estandar de operacion');