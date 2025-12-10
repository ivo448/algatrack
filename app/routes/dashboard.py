from flask import Blueprint, jsonify
from app.db.database import get_db
from app.utils.security import login_requerido

bp = Blueprint('dashboard', __name__, url_prefix='/api')

@bp.route('/dashboard', methods=['GET'])
@login_requerido
def dashboard_data():
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as c FROM lotes WHERE estado='activo'")
            res_lotes = cursor.fetchone()
            lotes_activos = res_lotes['c'] if res_lotes else 0
            cursor.execute("SELECT COUNT(*) as c FROM pedidos WHERE estado='pendiente'")
            res_pedidos = cursor.fetchone()
            pedidos_pendientes = res_pedidos['c'] if res_pedidos else 0
            # Datos para gráfico de producción mensual
            cursor.execute("""
                        SELECT 
                            TO_CHAR(fecha_entrega, 'Mon') as mes, 
                            SUM(cantidad_ton) as total 
                        FROM pedidos 
                        GROUP BY TO_CHAR(fecha_entrega, 'Mon'), EXTRACT(MONTH FROM fecha_entrega)
                        ORDER BY EXTRACT(MONTH FROM fecha_entrega)
                    """)
            resultados_grafico = cursor.fetchall()

            # Transformamos el resultado de SQL al formato que espera React
            datos_grafico = []
            if resultados_grafico:
                for fila in resultados_grafico:
                    datos_grafico.append({
                        "name": fila['mes'],       # Ej: "Jan", "Feb"
                        "produccion": float(fila['total']) # Ej: 45.0
                    })
            else:
                # Datos por defecto si la BD está vacía
                datos_grafico = [{"name": "Sin Datos", "produccion": 0}]

        return jsonify({
            'kpis': {
                'lotes_activos': lotes_activos,
                'pedidos_pendientes': pedidos_pendientes
            },
            'grafico': datos_grafico
        })

    except Exception as e:
        print(f"Error Postgres Dashboard: {e}")
        return jsonify({'error': 'Error interno'}), 500