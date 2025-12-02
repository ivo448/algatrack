from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import functools
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================

app = Flask(__name__)
app.secret_key = 'algatrack-secret-key-2025'  # Cambiar en producción
DB_PATH = 'algatrack.db'

# ============================================================================
# GESTIÓN DE BASE DE DATOS
# ============================================================================

def get_db():
    """Obtiene conexión a la base de datos SQLite"""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Inicializa la base de datos con esquema"""
    if os.path.exists(DB_PATH):
        return
    
    db = get_db()
    cursor = db.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL,
            email TEXT NOT NULL,
            rol TEXT NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de lotes
    cursor.execute('''
        CREATE TABLE lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_alga TEXT NOT NULL,
            superficie REAL NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_cosecha_estimada DATE,
            estado TEXT DEFAULT 'activo',
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de pesajes
    cursor.execute('''
        CREATE TABLE pesajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER NOT NULL,
            peso_humedo REAL NOT NULL,
            peso_seco REAL NOT NULL,
            fecha_pesaje DATE NOT NULL,
            registrado_por TEXT NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lote_id) REFERENCES lotes(id)
        )
    ''')
    
    # Tabla de pedidos
    cursor.execute('''
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            producto TEXT NOT NULL,
            cantidad_ton REAL NOT NULL,
            fecha_entrega DATE NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar usuarios de prueba
    usuarios_prueba = [
        ('personal_campo', 'campo123', 'campo@algatrack.cl', 'Personal'),
        ('comercial', 'comercial123', 'comercial@algatrack.cl', 'Comercial'),
        ('gerente', 'gerente123', 'gerente@algatrack.cl', 'Gerencia'),
    ]
    
    for usuario, pwd, email, rol in usuarios_prueba:
        cursor.execute('''
            INSERT INTO usuarios (usuario, contrasena, email, rol)
            VALUES (?, ?, ?, ?)
        ''', (usuario, generate_password_hash(pwd), email, rol))
    
    db.commit()
    db.close()

# ============================================================================
# DECORADORES DE AUTENTICACIÓN
# ============================================================================

def login_requerido(f):
    """Decorador para validar sesión activa"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def rol_requerido(*roles_permitidos):
    """Decorador para validar rol del usuario"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('login'))
            
            db = get_db()
            usuario = db.execute(
                'SELECT rol FROM usuarios WHERE id = ?',
                (session['usuario_id'],)
            ).fetchone()
            db.close()
            
            if usuario['rol'] not in roles_permitidos:
                return render_template_string(ERROR_403_TEMPLATE), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# RUTAS: AUTENTICACIÓN
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Endpoint de login - Autenticación con validación de entrada"""
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        contrasena = request.form.get('contrasena', '')
        
        # Validación de entrada (prevenir inyección)
        if not usuario or not contrasena:
            return render_template_string(LOGIN_TEMPLATE, error='Usuario y contraseña requeridos'), 400
        
        db = get_db()
        user = db.execute(
            'SELECT id, usuario, contrasena, rol FROM usuarios WHERE usuario = ?',
            (usuario,)
        ).fetchone()
        db.close()
        
        if user and check_password_hash(user['contrasena'], contrasena):
            session['usuario_id'] = user['id']
            session['usuario'] = user['usuario']
            session['rol'] = user['rol']
            return redirect(url_for('dashboard'))
        
        return render_template_string(LOGIN_TEMPLATE, error='Credenciales inválidas'), 401
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario"""
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# RUTAS: DASHBOARD
# ============================================================================

@app.route('/')
@app.route('/dashboard')
@login_requerido
def dashboard():
    """Dashboard principal con resumen de datos"""
    db = get_db()
    
    # Obtener estadísticas
    lotes_activos = db.execute(
        'SELECT COUNT(*) as cantidad FROM lotes WHERE estado = "activo"'
    ).fetchone()['cantidad']
    
    pesajes_recientes = db.execute(
        'SELECT COUNT(*) as cantidad FROM pesajes WHERE fecha_pesaje >= date("now", "-7 days")'
    ).fetchone()['cantidad']
    
    pedidos_pendientes = db.execute(
        'SELECT COUNT(*) as cantidad FROM pedidos WHERE estado = "pendiente"'
    ).fetchone()['cantidad']
    
    # Obtener lotes próximos a cosechar
    lotes_proximamente = db.execute('''
        SELECT id, tipo_alga, superficie, fecha_cosecha_estimada
        FROM lotes WHERE estado = "activo"
        ORDER BY fecha_cosecha_estimada ASC LIMIT 5
    ''').fetchall()
    
    db.close()
    
    return render_template_string(DASHBOARD_TEMPLATE, 
        lotes_activos=lotes_activos,
        pesajes_recientes=pesajes_recientes,
        pedidos_pendientes=pedidos_pendientes,
        lotes_proximamente=lotes_proximamente)

# ============================================================================
# RUTAS: LOTES
# ============================================================================

@app.route('/lotes', methods=['GET', 'POST'])
@login_requerido
def lotes():
    """Listar y registrar lotes de cultivo"""
    if request.method == 'POST':
        tipo_alga = request.form.get('tipo_alga', '').strip()
        superficie = request.form.get('superficie', '0')
        fecha_inicio = request.form.get('fecha_inicio', '')
        
        # Validación
        try:
            superficie = float(superficie)
            if superficie <= 0 or superficie > 100:
                raise ValueError("Superficie inválida")
        except ValueError:
            return jsonify({'error': 'Superficie debe ser número positivo'}), 400
        
        if not tipo_alga or tipo_alga not in ['Gracilaria', 'Ulva', 'Nori']:
            return jsonify({'error': 'Tipo de alga inválido'}), 400
        
        db = get_db()
        fecha_cosecha = datetime.strptime(fecha_inicio, '%Y-%m-%d') + timedelta(days=32)
        
        try:
            db.execute('''
                INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, fecha_cosecha_estimada)
                VALUES (?, ?, ?, ?)
            ''', (tipo_alga, superficie, fecha_inicio, fecha_cosecha.date()))
            db.commit()
            db.close()
            return jsonify({'success': True, 'mensaje': 'Lote registrado exitosamente'})
        except Exception as e:
            db.close()
            return jsonify({'error': str(e)}), 500
    
    db = get_db()
    lotes_list = db.execute(
        'SELECT * FROM lotes ORDER BY fecha_cosecha_estimada ASC'
    ).fetchall()
    db.close()
    
    return render_template_string(LOTES_TEMPLATE, lotes=lotes_list)

# ============================================================================
# RUTAS: PESAJES
# ============================================================================

@app.route('/pesajes', methods=['GET', 'POST'])
@login_requerido
def pesajes():
    """Registrar pesajes de cosecha"""
    if request.method == 'POST':
        lote_id = request.form.get('lote_id', '')
        peso_humedo = request.form.get('peso_humedo', '0')
        
        # Validaciones
        try:
            lote_id = int(lote_id)
            peso_humedo = float(peso_humedo)
            if peso_humedo <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({'error': 'Datos de entrada inválidos'}), 400
        
        # Cálculo automático de peso seco (conversión 15%)
        peso_seco = peso_humedo * 0.15
        fecha_pesaje = datetime.now().date()
        
        db = get_db()
        try:
            db.execute('''
                INSERT INTO pesajes (lote_id, peso_humedo, peso_seco, fecha_pesaje, registrado_por)
                VALUES (?, ?, ?, ?, ?)
            ''', (lote_id, peso_humedo, peso_seco, fecha_pesaje, session['usuario']))
            db.commit()
            db.close()
            return jsonify({
                'success': True,
                'mensaje': f'Pesaje registrado: {peso_seco:.2f} kg peso seco'
            })
        except Exception as e:
            db.close()
            return jsonify({'error': str(e)}), 500
    
    db = get_db()
    lotes_activos = db.execute(
        'SELECT id, tipo_alga, superficie FROM lotes WHERE estado = "activo"'
    ).fetchall()
    
    pesajes_list = db.execute('''
        SELECT p.*, l.tipo_alga FROM pesajes p
        JOIN lotes l ON p.lote_id = l.id
        ORDER BY p.fecha_pesaje DESC LIMIT 20
    ''').fetchall()
    db.close()
    
    return render_template_string(PESAJES_TEMPLATE, 
        lotes=lotes_activos, 
        pesajes=pesajes_list)

# ============================================================================
# RUTAS: SIMULACIÓN
# ============================================================================

@app.route('/simulacion', methods=['GET', 'POST'])
@rol_requerido('Comercial', 'Gerencia')
def simulacion():
    """Simular viabilidad de pedidos"""
    resultado = None
    
    if request.method == 'POST':
        producto = request.form.get('producto', '').strip()
        cantidad_solicitada = request.form.get('cantidad', '0')
        fecha_entrega = request.form.get('fecha_entrega', '')
        
        # Validaciones
        try:
            cantidad_solicitada = float(cantidad_solicitada)
            if cantidad_solicitada <= 0:
                raise ValueError()
        except ValueError:
            return render_template_string(SIMULACION_TEMPLATE, 
                error='Cantidad debe ser número positivo')
        
        db = get_db()
        
        # Calcular capacidad disponible
        lotes_disponibles = db.execute('''
            SELECT COALESCE(SUM(p.peso_seco), 0) as total_disponible
            FROM pesajes p
            JOIN lotes l ON p.lote_id = l.id
            WHERE l.fecha_cosecha_estimada <= ?
        ''', (fecha_entrega,)).fetchone()['total_disponible']
        
        # Consultar pedidos ya comprometidos
        pedidos_comprometidos = db.execute('''
            SELECT COALESCE(SUM(cantidad_ton), 0) as total FROM pedidos
            WHERE fecha_entrega = ? AND estado != "cancelado"
        ''', (fecha_entrega,)).fetchone()['total']
        
        # Disponibilidad en toneladas
        disponible_ton = (lotes_disponibles / 1000) - pedidos_comprometidos
        
        # Lógica de simulación
        if disponible_ton >= cantidad_solicitada:
            resultado = {
                'viabilidad': 'FACTIBLE',
                'color': 'success',
                'cantidad_disponible': disponible_ton,
                'costo_estimado': cantidad_solicitada * 5000,  # $5000 por tonelada
                'tiempo_entrega': '5 días hábiles',
                'mensaje': f'Pedido viable. Capacidad: {disponible_ton:.2f} toneladas'
            }
        else:
            resultado = {
                'viabilidad': 'NO FACTIBLE',
                'color': 'danger',
                'cantidad_disponible': disponible_ton,
                'cantidad_solicitada': cantidad_solicitada,
                'deficit': cantidad_solicitada - disponible_ton,
                'mensaje': f'Insuficiente capacidad. Falta: {(cantidad_solicitada - disponible_ton):.2f} ton'
            }
        
        db.close()
    
    return render_template_string(SIMULACION_TEMPLATE, resultado=resultado)

# ============================================================================
# RUTA: API JSON (para integraciones)
# ============================================================================

@app.route('/api/lotes', methods=['GET'])
@login_requerido
def api_lotes():
    """API REST para obtener lotes en JSON"""
    db = get_db()
    lotes_list = db.execute('SELECT * FROM lotes').fetchall()
    db.close()
    
    return jsonify([dict(l) for l in lotes_list])

# ============================================================================
# TEMPLATES HTML
# ============================================================================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Algatrack - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); min-height: 100vh; }
        .login-container { max-width: 400px; margin-top: 100px; }
        .card { border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .btn-login { background-color: #1abc9c; border: none; padding: 10px; font-weight: bold; }
        .btn-login:hover { background-color: #16a085; }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-container mx-auto">
            <div class="card">
                <div class="card-body p-5">
                    <h2 class="text-center mb-4" style="color: #1abc9c;">🌿 Algatrack</h2>
                    <p class="text-center text-muted mb-4">Plataforma de Trazabilidad de Algas</p>
                    
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Usuario</label>
                            <input type="text" name="usuario" class="form-control" required>
                            <small class="text-muted">Demo: personal_campo, comercial, gerente</small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Contraseña</label>
                            <input type="password" name="contrasena" class="form-control" required>
                            <small class="text-muted">Demo: [usuario]123 (ej: campo123)</small>
                        </div>
                        <button type="submit" class="btn btn-login w-100">Iniciar Sesión</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dashboard - Algatrack</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f5f7fa; }
        .navbar { background-color: #1abc9c; }
        .stat-card { border-radius: 10px; padding: 20px; color: white; font-weight: bold; }
        .stat-card.lotes { background-color: #3498db; }
        .stat-card.pesajes { background-color: #e74c3c; }
        .stat-card.pedidos { background-color: #f39c12; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <span class="navbar-brand text-white">🌿 Algatrack</span>
            <div>
                <a href="/lotes" class="btn btn-light btn-sm">Lotes</a>
                <a href="/pesajes" class="btn btn-light btn-sm">Pesajes</a>
                <a href="/simulacion" class="btn btn-light btn-sm">Simulación</a>
                <a href="/logout" class="btn btn-outline-light btn-sm">Cerrar Sesión</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-5">
        <h1>Dashboard - {{ session.rol }}</h1>
        
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="stat-card lotes">
                    <h5>Lotes Activos</h5>
                    <h2>{{ lotes_activos }}</h2>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card pesajes">
                    <h5>Pesajes (7 días)</h5>
                    <h2>{{ pesajes_recientes }}</h2>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card pedidos">
                    <h5>Pedidos Pendientes</h5>
                    <h2>{{ pedidos_pendientes }}</h2>
                </div>
            </div>
        </div>
        
        <div class="row mt-5">
            <div class="col-md-8">
                <h4>Lotes Próximos a Cosechar</h4>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Tipo de Alga</th>
                            <th>Superficie (ha)</th>
                            <th>Fecha Cosecha</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lote in lotes_proximamente %}
                        <tr>
                            <td>{{ lote.tipo_alga }}</td>
                            <td>{{ "%.2f"|format(lote.superficie) }}</td>
                            <td>{{ lote.fecha_cosecha_estimada }}</td>
                            <td><span class="badge bg-success">Activo</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''

LOTES_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Lotes - Algatrack</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar" style="background-color: #1abc9c;">
        <div class="container">
            <span class="navbar-brand text-white">🌿 Algatrack</span>
            <a href="/dashboard" class="btn btn-light btn-sm">← Volver</a>
        </div>
    </nav>
    
    <div class="container mt-5">
        <h2>Registrar Lote de Cultivo</h2>
        <form method="POST" class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Tipo de Alga</label>
                <select name="tipo_alga" class="form-control" required>
                    <option value="">Seleccione...</option>
                    <option value="Gracilaria">Gracilaria (Pelillo)</option>
                    <option value="Ulva">Ulva</option>
                    <option value="Nori">Nori</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Superficie (hectáreas)</label>
                <input type="number" name="superficie" class="form-control" step="0.1" required>
            </div>
            <div class="col-md-4">
                <label class="form-label">Fecha Inicio</label>
                <input type="date" name="fecha_inicio" class="form-control" required>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">Guardar Lote</button>
            </div>
        </form>
        
        <h3 class="mt-5">Lotes Registrados</h3>
        <table class="table table-hover">
            <thead style="background-color: #ecf0f1;">
                <tr>
                    <th>ID</th>
                    <th>Tipo</th>
                    <th>Superficie (ha)</th>
                    <th>Fecha Inicio</th>
                    <th>Fecha Cosecha Est.</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {% for lote in lotes %}
                <tr>
                    <td>{{ lote.id }}</td>
                    <td>{{ lote.tipo_alga }}</td>
                    <td>{{ "%.2f"|format(lote.superficie) }}</td>
                    <td>{{ lote.fecha_inicio }}</td>
                    <td>{{ lote.fecha_cosecha_estimada }}</td>
                    <td><span class="badge bg-info">{{ lote.estado }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

PESAJES_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Pesajes - Algatrack</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar" style="background-color: #1abc9c;">
        <div class="container">
            <span class="navbar-brand text-white">🌿 Algatrack</span>
            <a href="/dashboard" class="btn btn-light btn-sm">← Volver</a>
        </div>
    </nav>
    
    <div class="container mt-5">
        <h2>Registrar Pesaje (Móvil)</h2>
        <form method="POST" class="row g-3">
            <div class="col-md-6">
                <label class="form-label">Lote</label>
                <select name="lote_id" class="form-control" required>
                    <option value="">Seleccione lote...</option>
                    {% for lote in lotes %}
                    <option value="{{ lote.id }}">{{ lote.tipo_alga }} - {{ lote.superficie }}ha</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label">Peso Húmedo (kg)</label>
                <input type="number" name="peso_humedo" class="form-control" step="0.1" required>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">Registrar Pesaje</button>
                <small class="text-muted d-block mt-2">* Peso seco calculado automáticamente (15% del peso húmedo)</small>
            </div>
        </form>
        
        <h3 class="mt-5">Pesajes Recientes</h3>
        <table class="table table-sm">
            <thead style="background-color: #ecf0f1;">
                <tr>
                    <th>Lote</th>
                    <th>Peso Húmedo (kg)</th>
                    <th>Peso Seco (kg)</th>
                    <th>Fecha</th>
                    <th>Registrado por</th>
                </tr>
            </thead>
            <tbody>
                {% for pesaje in pesajes %}
                <tr>
                    <td>{{ pesaje.tipo_alga }}</td>
                    <td>{{ "%.2f"|format(pesaje.peso_humedo) }}</td>
                    <td>{{ "%.2f"|format(pesaje.peso_seco) }}</td>
                    <td>{{ pesaje.fecha_pesaje }}</td>
                    <td>{{ pesaje.registrado_por }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

SIMULACION_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Simulación - Algatrack</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar" style="background-color: #1abc9c;">
        <div class="container">
            <span class="navbar-brand text-white">🌿 Algatrack</span>
            <a href="/dashboard" class="btn btn-light btn-sm">← Volver</a>
        </div>
    </nav>
    
    <div class="container mt-5">
        <h2>Simulador de Pedidos</h2>
        <form method="POST" class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Producto</label>
                <select name="producto" class="form-control" required>
                    <option value="">Seleccione...</option>
                    <option value="pellet">Pellet</option>
                    <option value="polvo">Polvo</option>
                    <option value="seco">Alga Seca</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Cantidad (toneladas)</label>
                <input type="number" name="cantidad" class="form-control" step="0.1" required>
            </div>
            <div class="col-md-4">
                <label class="form-label">Fecha Entrega</label>
                <input type="date" name="fecha_entrega" class="form-control" required>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">Simular Viabilidad</button>
            </div>
        </form>
        
        {% if resultado %}
        <div class="alert alert-{{ resultado.color }} mt-4" role="alert">
            <h4 class="alert-heading">{{ resultado.viabilidad }}</h4>
            <p>{{ resultado.mensaje }}</p>
            {% if resultado.viabilidad == 'FACTIBLE' %}
            <hr>
            <p><strong>Capacidad Disponible:</strong> {{ "%.2f"|format(resultado.cantidad_disponible) }} toneladas</p>
            <p><strong>Costo Estimado:</strong> ${{ "%.0f"|format(resultado.costo_estimado) }}</p>
            <p><strong>Tiempo Entrega:</strong> {{ resultado.tiempo_entrega }}</p>
            {% else %}
            <hr>
            <p><strong>Deficit:</strong> {{ "%.2f"|format(resultado.deficit) }} toneladas</p>
            <p><strong>Alternativa:</strong> Considere fecha posterior o cantidad menor</p>
            {% endif %}
        </div>
        {% endif %}
        
        {% if error %}
        <div class="alert alert-danger mt-4">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

ERROR_403_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Acceso Denegado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="d-flex align-items-center justify-content-center" style="height: 100vh; background-color: #ecf0f1;">
    <div class="text-center">
        <h1 class="display-1">403</h1>
        <p class="fs-3">Acceso Denegado</p>
        <p class="text-muted">No tienes permiso para acceder a este recurso.</p>
        <a href="/dashboard" class="btn btn-primary">Volver al Dashboard</a>
    </div>
</body>
</html>
'''

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)