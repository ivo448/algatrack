from flask import Blueprint, jsonify
from app.db.database import get_db
from app.utils.security import login_requerido

bp = Blueprint('calendario', __name__, url_prefix='/api')

@bp.route('/calendario', methods=['GET'])
@login_requerido
def obtener_eventos():
    """
    Obtiene eventos combinados:
    1. Fechas de Entrega de Pedidos (Azul)
    2. Fechas Estimadas de Cosecha de Lotes (Verde)
    """
    try:
        db = get_db()
        eventos = []

        with db.cursor() as cursor:
            # 1. BUSCAR PEDIDOS (Entregas)
            # Solo los pendientes o en proceso
            cursor.execute("""
                SELECT cliente, producto, cantidad_ton, fecha_entrega 
                FROM pedidos 
                WHERE estado != 'cancelado'
            """)
            pedidos = cursor.fetchall()
            
            for p in pedidos:
                eventos.append({
                    "title": f"🚚 Entrega: {p['cliente']} ({p['cantidad_ton']} Ton)",
                    "date": p['fecha_entrega'].isoformat(), # Formato YYYY-MM-DD
                    "backgroundColor": "#0d6efd", # Azul Bootstrap
                    "borderColor": "#0d6efd",
                    "extendedProps": { "tipo": "pedido", "producto": p['producto'] }
                })

            # 2. BUSCAR LOTES (Cosechas)
            cursor.execute("""
                SELECT tipo_alga, superficie, fecha_cosecha_estimada 
                FROM lotes 
                WHERE estado = 'activo' AND fecha_cosecha_estimada IS NOT NULL
            """)
            lotes = cursor.fetchall()
            
            for l in lotes:
                eventos.append({
                    "title": f"🌾 Cosecha: {l['tipo_alga']} ({l['superficie']} Has)",
                    "date": l['fecha_cosecha_estimada'].isoformat(),
                    "backgroundColor": "#198754", # Verde Bootstrap
                    "borderColor": "#198754",
                    "extendedProps": { "tipo": "cosecha" }
                })

        return jsonify(eventos)

    except Exception as e:
        print(f"Error calendario: {e}")
        return jsonify({'error': 'Error obteniendo eventos'}), 500