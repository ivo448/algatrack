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
        
        usuarios = [
            ('personal', 'campo123', 'campo@alga.cl', 'Personal'),
            ('comercial', 'comercial123', 'comercial@alga.cl', 'Comercial'),
            ('gerente', 'gerente123', 'gerente@alga.cl', 'Gerencia')
        ]
        
        with db.cursor() as cursor:
            # Pedidos históricos (Enero, Febrero, Marzo)
            cursor.execute("INSERT INTO pedidos (cliente, producto, cantidad_ton, fecha_entrega, estado) VALUES (%s, %s, %s, %s, %s)", ('Cliente A', 'Pellet', 45.0, '2025-01-15', 'entregado'))
            cursor.execute("INSERT INTO pedidos (cliente, producto, cantidad_ton, fecha_entrega, estado) VALUES (%s, %s, %s, %s, %s)", ('Cliente B', 'Pellet', 30.0, '2025-02-20', 'entregado'))
            cursor.execute("INSERT INTO pedidos (cliente, producto, cantidad_ton, fecha_entrega, estado) VALUES (%s, %s, %s, %s, %s)", ('Cliente C', 'Pellet', 60.0, '2025-03-10', 'entregado'))
            for u, p, e, r in usuarios:
                ph = generate_password_hash(p)
                cursor.execute(
                    "INSERT INTO usuarios (usuario, contrasena, email, rol) VALUES (%s, %s, %s, %s)",
                    (u, ph, e, r)
                )
            
            cursor.execute(
                "INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, estado) VALUES (%s, %s, %s, %s)",
                ('Gracilaria', 20.5, '2025-01-01', 'activo')
            )
            cursor.execute(
                "INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, estado) VALUES (%s, %s, %s, %s)",
                ('Pelillo', 15.0, '2025-02-01', 'activo')
            )
        
        db.commit()
        print("✅ ¡Datos PostgreSQL cargados!")

if __name__ == '__main__':
    seed_data()