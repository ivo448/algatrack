import functools
from flask import session, jsonify
from app.db.database import get_db

def login_requerido(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autorizado', 'codigo': 401}), 401
        return f(*args, **kwargs)
    return decorated_function

def rol_requerido(*roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return jsonify({'error': 'No autorizado'}), 401
            
            db = get_db()
            
            try:
                with db.cursor() as cursor:
                    cursor.execute('SELECT rol FROM usuarios WHERE id = %s', (session['usuario_id'],))
                    user = cursor.fetchone()
            except Exception as e:
                print(f"Error verificando rol: {e}")
                return jsonify({'error': 'Error interno de seguridad'}), 500
            if not user or user['rol'] not in roles:
                return jsonify({'error': 'Acceso prohibido: Rol insuficiente', 'codigo': 403}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator