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
    Simulación con lógica ATP (Available to Promise).
    Solo considera stock que estará listo ANTES de la fecha solicitada.
    """
    data = request.get_json()
    
    try:
        cantidad = float(data.get('cantidad', 0))
        if cantidad <= 0: raise ValueError("La cantidad debe ser positiva")
        fecha = data.get('fecha')
        if not fecha: raise ValueError("La fecha es obligatoria")
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # 2. OBTENER DATOS REALES (ATP - STOCK NETO)
    db = get_db()
    stock_neto = 0.0
    
    try:
        with db.cursor() as cursor:
            # A) OFERTA: Sumamos lotes cosechados + futuros cercanos
            # Asumimos rendimiento: 1 Hectárea = 10 Toneladas (según predictor.py)
            query_oferta = """
                SELECT SUM(superficie) as total_ha
                FROM lotes 
                WHERE 
                    estado = 'cosechado' 
                    OR 
                    (estado = 'activo' AND fecha_cosecha_estimada <= %s)
            """
            cursor.execute(query_oferta, (fecha,))
            row_oferta = cursor.fetchone()
            oferta_ton = float(row_oferta['total_ha'] or 0) * 10.0 # Conversión Ha -> Ton

            # B) DEMANDA: Sumamos pedidos pendientes o entregados (que consumen stock)
            # Solo restamos pedidos cuya fecha de entrega sea ANTERIOR o IGUAL a la fecha simulada
            query_demanda = """
                SELECT SUM(cantidad_ton) as total_ton
                FROM pedidos
                WHERE estado != 'cancelado' AND fecha_entrega <= %s
            """
            cursor.execute(query_demanda, (fecha,))
            row_demanda = cursor.fetchone()
            demanda_ton = float(row_demanda['total_ton'] or 0)

            # C) CALCULO FINAL
            stock_neto = max(0, oferta_ton - demanda_ton)
            
            print(f"DEBUG ATP: Oferta={oferta_ton} - Demanda={demanda_ton} = Disponible={stock_neto}")

            # Pasamos este valor limpio al motor (reutilizamos la variable 'superficie_total' para no romper la firma)
            # Como el motor espera hectáreas para calcular, dividimos por 10
            superficie_total = stock_neto / 10.0

    except Exception as e:
        print(f"Error calculando stock neto: {e}")
        return jsonify({'error': 'Error de cálculo de inventario'}), 500

    # 3. EJECUTAR MOTOR
    try:
        resultado = MotorSimulacion.simular(cantidad, fecha, superficie_total)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # 4. RESPUESTA
    stock_actual = resultado['resultado']['stock_disponible']
    deficit = resultado['resultado']['deficit_a_cultivar']
    dias = resultado['operaciones']['dias_totales_estimados']
    
    if deficit == 0:
        color = "green"
        mensaje = f"ENTREGA INMEDIATA. Stock proyectado suficiente ({stock_actual} Ton). Lead time: {dias} días."
    else:
        color = "warning"
        mensaje = f"REQUIERE CULTIVO. Déficit de {deficit} Ton. Tiempo incluye siembra ({dias} días)."

    # 5. AUDITORÍA MONGO
    try:
        mongo_db = get_mongo_db()
        if mongo_db is not None:
            mongo_db.logs_auditoria.insert_one({
                "tipo": "SIMULACION",
                "usuario": session.get('usuario_id'),
                "input": {"cant": cantidad, "fecha": fecha},
                "resultado": mensaje,
                "timestamp": datetime.now(timezone.utc)
            })
    except Exception as e:
        print(f"Mongo Error: {e}")

    return jsonify({
        'resumen': mensaje,
        'color': color,
        'datos': resultado
    })