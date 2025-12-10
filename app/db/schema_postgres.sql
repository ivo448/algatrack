DROP TABLE IF EXISTS pesajes;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS lotes;
DROP TABLE IF EXISTS usuarios;

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