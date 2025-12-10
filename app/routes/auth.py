from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from app.db.database import get_db

bp = Blueprint('auth', __name__, url_prefix='/api')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = data.get('usuario')
    contrasena = data.get('contrasena')

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (usuario,))
        user = cursor.fetchone()

    # Validamos la contraseña (el hash debe ser válido en la BD)
    if user and check_password_hash(user['contrasena'], contrasena):
        session['usuario_id'] = user['id']
        session['rol'] = user['rol']
        session['nombre'] = user['usuario']
        return jsonify({
            'mensaje': 'Login exitoso',
            'usuario': {'nombre': user['usuario'], 'rol': user['rol']}
        })
    return jsonify({'error': 'Credenciales inválidas'}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})