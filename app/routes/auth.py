from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.database import get_db
from app.utils.security import login_requerido, rol_requerido

bp = Blueprint('auth', __name__, url_prefix='/api')

# --- AUTENTICACIÓN ---

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = data.get('usuario')
    contrasena = data.get('contrasena')

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (usuario,))
        user = cursor.fetchone()

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

# --- GESTIÓN DE USUARIOS (Solo Gerencia) ---

@bp.route('/usuarios', methods=['GET'])
@login_requerido
@rol_requerido('Gerencia')
def listar_usuarios():
    """Ver todos los usuarios del sistema"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id, usuario, email, rol, creado_en FROM usuarios ORDER BY id ASC")
        users = cursor.fetchall()
    return jsonify(users)

@bp.route('/register', methods=['POST'])
@login_requerido
@rol_requerido('Gerencia')
def registrar_usuario():
    """Crear un nuevo usuario (Solo Admin/Gerencia)"""
    data = request.get_json()
    
    try:
        usuario = data.get('usuario')
        email = data.get('email')
        password = data.get('contrasena')
        rol = data.get('rol')

        if not all([usuario, email, password, rol]):
            return jsonify({'error': 'Todos los campos son obligatorios'}), 400

        # Hasheamos la contraseña antes de guardar
        pass_hash = generate_password_hash(password)

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO usuarios (usuario, email, contrasena, rol)
                VALUES (%s, %s, %s, %s)
            """, (usuario, email, pass_hash, rol))
        
        db.commit()
        return jsonify({'mensaje': 'Usuario creado exitosamente'}), 201

    except Exception as e:
        if 'unique' in str(e).lower():
            return jsonify({'error': 'El usuario o email ya existe'}), 400
        return jsonify({'error': str(e)}), 500

@bp.route('/usuarios/<int:id>', methods=['DELETE'])
@login_requerido
@rol_requerido('Gerencia')
def eliminar_usuario(id):
    """Borrar un usuario"""
    # Evitar que se borre a sí mismo
    if id == session.get('usuario_id'):
        return jsonify({'error': 'No puedes eliminar tu propia cuenta'}), 400

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    db.commit()
    return jsonify({'mensaje': 'Usuario eliminado'})