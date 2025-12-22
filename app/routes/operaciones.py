from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from app.db.mongo import get_mongo_db
from app.db.database import get_db
from app.utils.security import login_requerido, rol_requerido
from app.services.predictor import MotorSimulacion

bp = Blueprint('operaciones', __name__, url_prefix='/api')

@bp.route('/simulacion', methods=['POST'])
@login_requerido
@rol_requerido('Comercial', 'Gerencia')
def simulacion():
    """
    Simulación con lógica ATP (Available to Promise) y Costos Parametrizados.
    """
    # 1. OBTENER DATOS DEL FRONTEND (Esta debe ser la primera línea)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No se recibieron datos JSON'}), 400

    try:
        cantidad = float(data.get('cantidad', 0))
        if cantidad <= 0: raise ValueError("La cantidad debe ser positiva")
        fecha = data.get('fecha')
        if not fecha: raise ValueError("La fecha es obligatoria")
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    db = get_db()
    
    # ---------------------------------------------------------
    # 2. CARGAR PARÁMETROS DEL SISTEMA (Precios y Costos)
    # ---------------------------------------------------------
    params_dict = {}
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT clave, valor FROM parametros_sistema")
            rows = cursor.fetchall()
            for row in rows:
                params_dict[row['clave']] = float(row['valor'])
                
        # Fallback si la tabla está vacía
        if not params_dict:
            print("ADVERTENCIA: Tabla parametros_sistema vacía. Usando valores por defecto.")
            params_dict = {
                'precio_agua_m3': 2500.0, 'precio_kwh': 180.0, 'precio_diesel_L': 1150.0,
                'consumo_agua_ton': 3.0, 'consumo_energia_ton': 40.0, 'consumo_diesel_ton': 12.5,
                'horas_hombre_ton': 4.5, 'costo_hh_operario': 5500.0, 'insumos_varios_ton': 5000.0,
                'capacidad_planta_dia': 2.5, 'dias_ciclo_base': 45.0, 'capacidad_cosecha_dia': 5.0
            }
    except Exception as e:
        print(f"Error cargando parámetros: {e}")
        return jsonify({'error': 'Error de configuración del sistema (Costos)'}), 500

    # ---------------------------------------------------------
    # 3. CARGAR CONFIGURACIÓN BIOLÓGICA (Estacionalidad)
    # ---------------------------------------------------------
    lista_estaciones = []
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM configuracion_estacional")
            rows = cursor.fetchall()
            for row in rows:
                lista_estaciones.append({
                    'nombre_estacion': row['nombre_estacion'],
                    'meses_asociados': row['meses_asociados'],
                    'factor_biomasa': float(row['factor_biomasa']),
                    'factor_secado': float(row['factor_secado']),
                    'factor_energia': float(row['factor_energia']),
                    'factor_crecimiento': float(row['factor_crecimiento'])
                })
    except Exception as e:
        print(f"Error cargando biología: {e}")
        # No retornamos error, permitimos que el motor use sus valores por defecto

    # ---------------------------------------------------------
    # 4. OBTENER DATOS REALES (ATP - STOCK NETO)
    # ---------------------------------------------------------
    stock_neto = 0.0
    superficie_equivalente = 0.0
    
    try:
        with db.cursor() as cursor:
            # A) OFERTA
            query_oferta = """
                SELECT SUM(superficie) as total_ha
                FROM lotes 
                WHERE estado = 'cosechado' OR (estado = 'activo' AND fecha_cosecha_estimada <= %s)
            """
            cursor.execute(query_oferta, (fecha,))
            row_oferta = cursor.fetchone()
            oferta_ton = float(row_oferta['total_ha'] or 0) * 10.0

            # B) DEMANDA
            query_demanda = """
                SELECT SUM(cantidad_ton) as total_ton
                FROM pedidos
                WHERE estado != 'cancelado' AND fecha_entrega <= %s
            """
            cursor.execute(query_demanda, (fecha,))
            row_demanda = cursor.fetchone()
            demanda_ton = float(row_demanda['total_ton'] or 0)

            # C) CALCULO
            stock_neto = max(0, oferta_ton - demanda_ton)
            superficie_equivalente = stock_neto / 10.0 # Hectáreas virtuales disponibles

    except Exception as e:
        print(f"Error calculando stock neto: {e}")
        return jsonify({'error': 'Error de cálculo de inventario en BD'}), 500

    # ---------------------------------------------------------
    # 5. EJECUTAR MOTOR (Con todos los parámetros)
    # ---------------------------------------------------------
    try:
        resultado = MotorSimulacion.simular(
            cantidad, 
            fecha, 
            superficie_equivalente, 
            params_dict, 
            lista_estaciones
        )
    except Exception as e:
        return jsonify({'error': f"Error en Motor de Simulación: {str(e)}"}), 500

    # ---------------------------------------------------------
    # 6. RESPUESTA Y AUDITORÍA
    # ---------------------------------------------------------
    stock_proyectado = resultado['resultado']['stock_disponible']
    deficit = resultado['resultado']['deficit_a_cultivar']
    dias = resultado['operaciones']['dias_totales']
    costo_total = resultado['financiero']['costo_total']
    
    if deficit == 0:
        color = "green"
        mensaje = f"ENTREGA INMEDIATA. Stock proyectado suficiente ({stock_proyectado} Ton). Costo Est: ${costo_total:,.0f}"
    else:
        color = "warning"
        mensaje = f"REQUIERE CULTIVO. Déficit de {deficit} Ton. Tiempo total: {dias} días. Costo Est: ${costo_total:,.0f}"

    try:
        mongo_db = get_mongo_db()
        if mongo_db is not None:
            mongo_db.logs_auditoria.insert_one({
                "tipo": "SIMULACION_FINANCIERA",
                "usuario": session.get('usuario_id'),
                "input": {"cant": cantidad, "fecha": fecha},
                "parametros_usados": params_dict,
                "estacion_climatica": resultado['escenario']['estacion_detectada'],
                "resultado_financiero": resultado['financiero'],
                "resultado_operativo": mensaje,
                "timestamp": datetime.now(timezone.utc)
            })
    except Exception as e:
        print(f"Mongo Error: {e}")

    return jsonify({
        'resumen': mensaje,
        'color': color,
        'datos': resultado
    })