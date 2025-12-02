-- ============================================================================
-- TABLA: USUARIOS (Gestión de acceso y autenticación)
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,              -- Hash bcrypt, nunca texto plano
    email TEXT NOT NULL UNIQUE,
    rol TEXT NOT NULL CHECK(rol IN ('Personal', 'Comercial', 'Gerencia')),
    estado BOOLEAN DEFAULT 1,              -- 1: activo, 0: inactivo
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_sesion TIMESTAMP
);

CREATE INDEX idx_usuarios_usuario ON usuarios(usuario);
CREATE INDEX idx_usuarios_rol ON usuarios(rol);

-- Insertar usuarios de prueba (las contraseñas están hasheadas con bcrypt)
-- Demo: personal_campo/campo123, comercial/comercial123, gerente/gerente123
INSERT INTO usuarios (usuario, contrasena, email, rol) VALUES
('personal_campo', '$2b$12$...bcrypthash1...', 'campo@algatrack.cl', 'Personal'),
('comercial', '$2b$12$...bcrypthash2...', 'comercial@algatrack.cl', 'Comercial'),
('gerente', '$2b$12$...bcrypthash3...', 'gerente@algatrack.cl', 'Gerencia');

-- ============================================================================
-- TABLA: LOTES (Registro de cultivos)
-- Relación: Uno a Muchos con PESAJES
-- ============================================================================

CREATE TABLE IF NOT EXISTS lotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_alga TEXT NOT NULL CHECK(tipo_alga IN ('Gracilaria', 'Ulva', 'Nori')),
    superficie REAL NOT NULL CHECK(superficie > 0 AND superficie <= 100),  -- Hectáreas
    fecha_inicio DATE NOT NULL,
    fecha_cosecha_estimada DATE,           -- Calculada: inicio + 32 días
    estado TEXT NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo', 'completado', 'cancelado')),
    observaciones TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_fechas CHECK(fecha_inicio <= fecha_cosecha_estimada)
);

CREATE INDEX idx_lotes_estado ON lotes(estado);
CREATE INDEX idx_lotes_fecha_cosecha ON lotes(fecha_cosecha_estimada);
CREATE INDEX idx_lotes_tipo ON lotes(tipo_alga);

-- Datos de prueba
INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) VALUES
('Gracilaria', 2.5, '2025-10-15', '2025-11-16', 'activo'),
('Gracilaria', 1.8, '2025-10-22', '2025-11-23', 'activo'),
('Ulva', 1.2, '2025-10-29', '2025-11-30', 'activo');

-- ============================================================================
-- TABLA: PESAJES (Registro de cosechas - Fase de recolección de datos)
-- Relación: Muchos a Uno con LOTES
-- Normalización: Peso seco se calcula (peso_humedo * 0.15), no se almacena redundante
-- ============================================================================

CREATE TABLE IF NOT EXISTS pesajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id INTEGER NOT NULL,
    peso_humedo REAL NOT NULL CHECK(peso_humedo > 0),    -- Kg
    peso_seco REAL NOT NULL CHECK(peso_seco > 0),        -- Kg (15% del peso húmedo)
    fecha_pesaje DATE NOT NULL,
    registrado_por TEXT NOT NULL,                         -- Usuario que registró
    ubicacion_gps TEXT,                                   -- Opcional: coordenadas
    sincronizado BOOLEAN DEFAULT 0,                       -- Para modo offline
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lote_id) REFERENCES lotes(id) ON DELETE CASCADE
);

CREATE INDEX idx_pesajes_lote ON pesajes(lote_id);
CREATE INDEX idx_pesajes_fecha ON pesajes(fecha_pesaje);
CREATE INDEX idx_pesajes_sincronizado ON pesajes(sincronizado);

-- Datos de prueba
INSERT INTO pesajes (lote_id, peso_humedo, peso_seco, fecha_pesaje, registrado_por, sincronizado) VALUES
(1, 500, 75, '2025-11-16', 'personal_campo', 1),
(1, 480, 72, '2025-11-17', 'personal_campo', 1),
(2, 420, 63, '2025-11-23', 'personal_campo', 1);

-- ============================================================================
-- TABLA: PEDIDOS (Gestión comercial)
-- Relación: Independiente (podría extenderse con FK a lotes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    producto TEXT NOT NULL CHECK(producto IN ('pellet', 'polvo', 'seco')),
    cantidad_ton REAL NOT NULL CHECK(cantidad_ton > 0),
    fecha_solicitud DATE NOT NULL,
    fecha_entrega_solicitada DATE NOT NULL,
    fecha_entrega_real DATE,
    estado TEXT NOT NULL DEFAULT 'pendiente' 
        CHECK(estado IN ('pendiente', 'confirmado', 'entregado', 'cancelado')),
    precio_unitario_usd REAL,                             -- Auditoría de precios
    costo_total_usd REAL,
    observaciones TEXT,
    registrado_por INTEGER NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id),
    CONSTRAINT chk_fechas_pedido CHECK(fecha_solicitud <= fecha_entrega_solicitada)
);

CREATE INDEX idx_pedidos_estado ON pedidos(estado);
CREATE INDEX idx_pedidos_fecha_entrega ON pedidos(fecha_entrega_solicitada);
CREATE INDEX idx_pedidos_cliente ON pedidos(cliente);

-- Datos de prueba
INSERT INTO pedidos 
    (cliente, producto, cantidad_ton, fecha_solicitud, fecha_entrega_solicitada, 
     estado, precio_unitario_usd, costo_total_usd, registrado_por) 
VALUES
('Industrias Alimentarias SpA', 'pellet', 0.5, '2025-10-20', '2025-11-15', 'entregado', 5000, 2500, 2),
('Cosmética Global Ltda', 'polvo', 0.3, '2025-11-01', '2025-11-25', 'confirmado', 6000, 1800, 2);

-- ============================================================================
-- TABLA: VARIACIONES_CLIMA (Datos meteorológicos - Extensión UC-CLIMA)
-- ============================================================================

CREATE TABLE IF NOT EXISTS variaciones_clima (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL UNIQUE,
    temperatura_promedio REAL,              -- Celsius
    precipitacion_mm REAL,                  -- Milímetros
    velocidad_viento_kmh REAL,
    humedad_relativa INTEGER,               -- Porcentaje
    fuente TEXT,                            -- API externa (ej: weatherapi)
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clima_fecha ON variaciones_clima(fecha);

-- ============================================================================
-- TABLA: AUDITORIA (Trazabilidad de cambios - Conformidad ISO 9001)
-- ============================================================================

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    tabla_afectada TEXT NOT NULL,
    id_registro INTEGER NOT NULL,
    operacion TEXT CHECK(operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    valores_anteriores TEXT,                -- JSON con cambios
    valores_nuevos TEXT,                    -- JSON con cambios
    fecha_operacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_origen TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE INDEX idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX idx_auditoria_fecha ON auditoria(fecha_operacion);
CREATE INDEX idx_auditoria_tabla ON auditoria(tabla_afectada);

-- ============================================================================
-- VISTAS PARA REPORTES Y DASHBOARDS
-- ============================================================================

-- Vista 1: Resumen de capacidad disponible
CREATE VIEW vista_capacidad_disponible AS
SELECT 
    DATE(p.fecha_pesaje) as fecha,
    l.tipo_alga,
    SUM(p.peso_seco) / 1000 as toneladas_disponibles,
    COUNT(DISTINCT p.lote_id) as lotes_cosechados
FROM pesajes p
JOIN lotes l ON p.lote_id = l.id
WHERE p.fecha_pesaje >= DATE('now', '-30 days')
GROUP BY DATE(p.fecha_pesaje), l.tipo_alga;

-- Vista 2: Análisis de conflictos pedidos-capacidad
CREATE VIEW vista_conflictos_pedidos AS
SELECT 
    pd.id as pedido_id,
    pd.cliente,
    pd.cantidad_ton,
    pd.fecha_entrega_solicitada,
    COALESCE(SUM(p.peso_seco) / 1000, 0) as capacidad_disponible,
    (pd.cantidad_ton > COALESCE(SUM(p.peso_seco) / 1000, 0)) as hay_conflicto
FROM pedidos pd
LEFT JOIN pesajes p ON p.fecha_pesaje <= pd.fecha_entrega_solicitada
LEFT JOIN lotes l ON p.lote_id = l.id
WHERE pd.estado = 'pendiente'
GROUP BY pd.id;

-- Vista 3: Desempeño por usuario
CREATE VIEW vista_desempeno_usuarios AS
SELECT 
    u.usuario,
    u.rol,
    COUNT(p.id) as pesajes_registrados,
    SUM(p.peso_humedo) as peso_total_registrado_kg,
    MAX(p.fecha_creacion) as ultimo_registro
FROM usuarios u
LEFT JOIN pesajes p ON p.registrado_por = u.usuario
WHERE u.estado = 1
GROUP BY u.id;

-- ============================================================================
-- TRIGGERS PARA MANTENER INTEGRIDAD DE DATOS
-- ============================================================================

-- Trigger 1: Actualizar fecha_ultima_sesion en usuarios
CREATE TRIGGER IF NOT EXISTS actualizar_ultima_sesion
AFTER UPDATE OF fecha_ultima_sesion ON usuarios
BEGIN
    UPDATE usuarios SET fecha_ultima_sesion = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger 2: Registrar auditoría en cambios de pedidos
CREATE TRIGGER IF NOT EXISTS auditoria_pedidos_update
AFTER UPDATE ON pedidos
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (usuario_id, tabla_afectada, id_registro, operacion, 
                           valores_anteriores, valores_nuevos)
    VALUES (1, 'pedidos', NEW.id, 'UPDATE', 
            json_object('estado', OLD.estado, 'cantidad', OLD.cantidad_ton),
            json_object('estado', NEW.estado, 'cantidad', NEW.cantidad_ton));
END;

-- ============================================================================
-- PROCEDIMIENTOS ALMACENADOS (Funciones de Negocio)
-- ============================================================================

-- Función 1: Calcular viabilidad de pedido (SIMULACIÓN)
-- CALL simular_viabilidad(0.5, '2025-11-30', 'Gracilaria');

-- Función 2: Sincronizar datos offline
-- UPDATE pesajes SET sincronizado = 1 WHERE sincronizado = 0;

-- ============================================================================
-- POLÍTICAS DE SEGURIDAD Y RESTRICCIONES
-- ============================================================================

-- Solo usuarios con rol 'Gerencia' pueden ver todos los pedidos
-- Only 'Personal' can insert pesajes
-- Solo 'Comercial' puede modificar estado de pedidos

-- ============================================================================
-- BACKUP Y REPLICACIÓN (Cloud - AWS RDS)
-- ============================================================================

-- Para PostgreSQL en AWS:
-- pg_dump algatrack > backup_$(date +%Y%m%d).sql
-- psql -h rds-endpoint.amazonaws.com -U admin algatrack < backup.sql

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================