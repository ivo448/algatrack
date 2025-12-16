from app import create_app
from app.db.database import get_db, init_db
from werkzeug.security import generate_password_hash

def seed_data():
    app = create_app()
    with app.app_context():
        print("1. Reiniciando esquema en PostgreSQL...")
        init_db()
        
        print("2. Insertando datos...")
        db = get_db()
        
        # --- USUARIOS ---
        usuarios = [
            ('personal', 'campo123', 'campo@alga.cl', 'Personal'),
            ('comercial', 'comercial123', 'comercial@alga.cl', 'Comercial'),
            ('gerente', 'gerente123', 'gerente@alga.cl', 'Gerencia')
        ]
        
        with db.cursor() as cursor:
            # A. USUARIOS
            for u, p, e, r in usuarios:
                ph = generate_password_hash(p)
                cursor.execute(
                    "INSERT INTO usuarios (usuario, contrasena, email, rol) VALUES (%s, %s, %s, %s)",
                    (u, ph, e, r)
                )

            # C. CLIENTES (NUEVO)
            print("   -> Insertando cartera de clientes...")
            cursor.execute("""
                INSERT INTO clientes (empresa, contacto, email, telefono, direccion) 
                VALUES 
                ('Salmonera Sur', 'Juan Pérez', 'jperez@sur.cl', '+56911111111', 'Puerto Montt 123'),
                ('AgroNorte', 'Maria Soto', 'msoto@agro.cl', '+56922222222', 'La Serena 456'),
                ('Exportadora Chile', 'Carlos Diaz', 'cdiaz@export.cl', '+56933333333', 'Valparaiso 789')
            """)

            # B. HISTORIAL DE COSECHAS (Pasado - Para el Gráfico del Dashboard)
            print("   -> Insertando lotes cosechados...")
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) 
                VALUES 
                ('Gracilaria', 5.0, '2024-11-15', '2025-01-10', 'cosechado'),
                ('Pelillo', 3.0, '2024-12-01', '2025-02-15', 'cosechado'),
                ('Gracilaria', 8.0, '2025-01-15', '2025-03-05', 'cosechado')
            """)

            # C. LOTES ACTIVOS (Futuro - Para el Simulador ATP y Calendario)
            # IMPORTANTE: Todos deben tener fecha_cosecha_estimada para que el ATP funcione
            print("   -> Insertando lotes activos...")
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) 
                VALUES 
                ('Gracilaria', 10.0, '2025-04-01', '2025-05-15', 'activo'),
                ('Gracilaria', 20.5, '2025-05-01', '2025-06-20', 'activo'),
                ('Pelillo', 15.0, '2025-05-10', '2025-07-10', 'activo')
            """)

            # D. PEDIDOS (Para el Calendario - Cuadros Azules)
            print("   -> Insertando pedidos...")
            cursor.execute("""
                INSERT INTO pedidos (cliente, producto, cantidad_ton, fecha_entrega, estado) 
                VALUES 
                ('Salmonera Sur', 'Pellet Premium', 10.0, '2025-04-20', 'pendiente'),
                ('AgroNorte', 'Fertilizante', 5.0, '2025-05-10', 'pendiente'),
                ('Exportadora Chile', 'Biomasa Seca', 25.0, '2025-06-30', 'pendiente')
            """)
        
        db.commit()
        print("✅ ¡Datos PostgreSQL cargados exitosamente!")

if __name__ == '__main__':
    seed_data()