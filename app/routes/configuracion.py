from flask import Blueprint, request, jsonify
from app.db.database import get_db
from app.utils.security import login_requerido, rol_requerido

bp = Blueprint('configuracion', __name__, url_prefix='/api/config')

# --- 1. PARÁMETROS ECONÓMICOS Y TÉCNICOS ---

@bp.route('/sistema', methods=['GET'])
@login_requerido
def get_parametros_sistema():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT clave, valor, unidad, descripcion, categoria FROM parametros_sistema ORDER BY categoria, clave")
            rows = cursor.fetchall()
            # Convertimos Decimal a float para JSON
            data = []
            for row in rows:
                row['valor'] = float(row['valor'])
                data.append(row)
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/sistema', methods=['PUT'])
@login_requerido
@rol_requerido('Gerencia') # Solo gerentes pueden cambiar precios
def update_parametros_sistema():
    data = request.get_json() # Esperamos una lista de objetos: [{clave: 'precio_agua', valor: 3000}, ...]
    db = get_db()
    
    try:
        with db.cursor() as cursor:
            for item in data:
                cursor.execute(
                    "UPDATE parametros_sistema SET valor = %s WHERE clave = %s",
                    (item['valor'], item['clave'])
                )
        db.commit()
        return jsonify({'mensaje': 'Parámetros actualizados correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# --- 2. CONFIGURACIÓN BIOLÓGICA (ESTACIONES) ---

@bp.route('/estaciones', methods=['GET'])
@login_requerido
def get_estaciones():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM configuracion_estacional ORDER BY id")
            rows = cursor.fetchall()
            # Convertir Decimals
            res = []
            for row in rows:
                res.append({
                    'id': row['id'],
                    'nombre_estacion': row['nombre_estacion'],
                    'meses_asociados': row['meses_asociados'],
                    'factor_biomasa': float(row['factor_biomasa']),
                    'factor_secado': float(row['factor_secado']),
                    'factor_energia': float(row['factor_energia']),
                    'factor_crecimiento': float(row['factor_crecimiento']),
                    'descripcion': row['descripcion']
                })
            return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/estaciones', methods=['PUT'])
@login_requerido
@rol_requerido('Gerencia')
def update_estacion():
    # Actualiza una sola estación por ID
    data = request.get_json()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE configuracion_estacional 
                SET factor_biomasa=%s, factor_secado=%s, factor_energia=%s, factor_crecimiento=%s, meses_asociados=%s
                WHERE id=%s
            """, (
                data['factor_biomasa'], data['factor_secado'], 
                data['factor_energia'], data['factor_crecimiento'],
                data['meses_asociados'], data['id']
            ))
        db.commit()
        return jsonify({'mensaje': 'Estación actualizada'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500