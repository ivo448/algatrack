from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.db.database import get_db
from app.utils.security import login_requerido

bp = Blueprint('lotes', __name__, url_prefix='/api')

def calcular_fecha_cosecha(fecha_siembra_str, tipo_alga):
    """
    Calcula la fecha estimada basada en la estación y el tipo de alga.
    """
    fecha = datetime.strptime(fecha_siembra_str, '%Y-%m-%d')
    mes = fecha.month
    
    # 1. Días base según tipo de alga
    dias_base = 45 if tipo_alga == 'Gracilaria' else 60
    
    # 2. Factor Estacional (En invierno crece más lento)
    factor = 1.0
    if mes in [5, 6, 7, 8]: # Invierno
        factor = 1.3 # Tarda un 30% más
    elif mes in [1, 2, 12]: # Verano
        factor = 0.9 # Crece un 10% más rápido
        
    dias_totales = int(dias_base * factor)
    fecha_estimada = fecha + timedelta(days=dias_totales)
    
    return fecha_estimada.strftime('%Y-%m-%d')

@bp.route('/lotes', methods=['GET'])
@login_requerido
def obtener_lotes():
    """Listar todos los lotes"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM lotes ORDER BY fecha_inicio DESC")
        lotes = cursor.fetchall()
    return jsonify(lotes)

@bp.route('/lotes', methods=['POST'])
@login_requerido
def crear_lote():
    """Crear nueva plantación con cálculo automático de cosecha"""
    data = request.get_json()
    
    try:
        tipo = data['tipo_alga']
        superficie = float(data['superficie'])
        fecha_inicio = data['fecha_inicio']
        # Calculamos la fecha automáticamente
        fecha_cosecha = calcular_fecha_cosecha(fecha_inicio, tipo)
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada, estado)
                VALUES (%s, %s, %s, %s, 'activo')
            """, (tipo, superficie, fecha_inicio, fecha_cosecha))
            
        db.commit()
        return jsonify({'mensaje': 'Lote creado', 'fecha_cosecha_estimada': fecha_cosecha}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/lotes/<int:id>', methods=['DELETE'])
@login_requerido
def eliminar_lote(id):
    """Eliminar un lote (por error de carga o pérdida)"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM lotes WHERE id = %s", (id,))
    db.commit()
    return jsonify({'mensaje': 'Lote eliminado'})

@bp.route('/lotes/<int:id>/cosechar', methods=['PUT'])
@login_requerido
def marcar_cosechado(id):
    """Cambia el estado a 'cosechado' (El stock pasa a estar disponible físicamente)"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE lotes SET estado = 'cosechado' WHERE id = %s", (id,))
    db.commit()
    return jsonify({'mensaje': 'Lote marcado como cosechado'})