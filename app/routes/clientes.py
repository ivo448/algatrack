from flask import Blueprint, request, jsonify
from app.db.database import get_db
from app.utils.security import login_requerido

bp = Blueprint('clientes', __name__, url_prefix='/api')

@bp.route('/clientes', methods=['GET'])
@login_requerido
def listar_clientes():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM clientes ORDER BY empresa ASC")
        clientes = cursor.fetchall()
    return jsonify(clientes)

@bp.route('/clientes', methods=['POST'])
@login_requerido
def crear_cliente():
    data = request.get_json()
    try:
        empresa = data.get('empresa')
        if not empresa:
            return jsonify({'error': 'El nombre de la empresa es obligatorio'}), 400

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO clientes (empresa, contacto, email, telefono, direccion)
                VALUES (%s, %s, %s, %s, %s)
            """, (empresa, data.get('contacto'), data.get('email'), data.get('telefono'), data.get('direccion')))
        db.commit()
        return jsonify({'mensaje': 'Cliente registrado exitosamente'}), 201
    except Exception as e:
        # Capturamos error de duplicados (UNIQUE constraint)
        if 'unique constraint' in str(e).lower():
            return jsonify({'error': 'Ya existe un cliente con ese nombre'}), 400
        return jsonify({'error': str(e)}), 500

@bp.route('/clientes/<int:id>', methods=['DELETE'])
@login_requerido
def eliminar_cliente(id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # Opcional: Verificar si tiene pedidos antes de borrar
            cursor.execute("SELECT COUNT(*) as c FROM pedidos WHERE cliente = (SELECT empresa FROM clientes WHERE id=%s)", (id,))
            if cursor.fetchone()['c'] > 0:
                return jsonify({'error': 'No se puede borrar: Este cliente tiene pedidos asociados.'}), 400
            
            cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
        db.commit()
        return jsonify({'mensaje': 'Cliente eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500