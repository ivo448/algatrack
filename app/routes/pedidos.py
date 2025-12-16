from flask import Blueprint, request, jsonify
from app.db.database import get_db
from app.utils.security import login_requerido

bp = Blueprint('pedidos', __name__, url_prefix='/api')

@bp.route('/pedidos', methods=['GET'])
@login_requerido
def listar_pedidos():
    """Obtiene todos los pedidos ordenados por fecha de entrega"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM pedidos ORDER BY fecha_entrega ASC")
        pedidos = cursor.fetchall()
    return jsonify(pedidos)

@bp.route('/pedidos', methods=['POST'])
@login_requerido
def crear_pedido():
    """Crea un nuevo pedido manualmente"""
    data = request.get_json()
    try:
        cliente = data.get('cliente')
        producto = data.get('producto', 'Pellet Estándar')
        cantidad = data.get('cantidad_ton')
        fecha = data.get('fecha_entrega')

        if not all([cliente, cantidad, fecha]):
            return jsonify({'error': 'Faltan datos obligatorios'}), 400

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pedidos (cliente, producto, cantidad_ton, fecha_entrega, estado)
                VALUES (%s, %s, %s, %s, 'pendiente')
            """, (cliente, producto, float(cantidad), fecha))
        db.commit()
        return jsonify({'mensaje': 'Pedido registrado exitosamente'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/pedidos/<int:id>/estado', methods=['PUT'])
@login_requerido
def cambiar_estado(id):
    """Actualiza el estado (ej: de 'pendiente' a 'entregado' o 'cancelado')"""
    data = request.get_json()
    nuevo_estado = data.get('estado')
    
    if nuevo_estado not in ['pendiente', 'entregado', 'cancelado']:
        return jsonify({'error': 'Estado inválido'}), 400

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, id))
    db.commit()
    return jsonify({'mensaje': f'Estado actualizado a {nuevo_estado}'})

@bp.route('/pedidos/<int:id>', methods=['DELETE'])
@login_requerido
def eliminar_pedido(id):
    """Elimina un pedido permanentemente"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (id,))
    db.commit()
    return jsonify({'mensaje': 'Pedido eliminado'})