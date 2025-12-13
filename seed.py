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
            # 4. INSERTAR COSECHAS HISTÓRICAS (Producción Real)
            print("   -> Insertando historial de cosechas (Lotes)...")
            
            # Enero: Se cosechó un lote grande de 5 Has
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) 
                VALUES (%s, %s, %s, %s, 'cosechado')
            """, ('Gracilaria', 5.0, '2024-11-15', '2025-01-10'))

            # Febrero: Se cosecharon 3 Has
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) 
                VALUES (%s, %s, %s, %s, 'cosechado')
            """, ('Pelillo', 3.0, '2024-12-01', '2025-02-15'))

            # Marzo: Gran cosecha de 8 Has
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) 
                VALUES (%s, %s, %s, %s, 'cosechado')
            """, ('Gracilaria', 8.0, '2025-01-15', '2025-03-05'))

            # Lotes Activos (Futuro) - Estos ya los tenías, déjalos como están o agrégalos aquí si borraste todo
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado) 
                VALUES (%s, %s, %s, %s, 'activo')
            """, ('Gracilaria', 10.0, '2025-04-01', '2025-05-15'))
            
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