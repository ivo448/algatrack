from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from app.db.mongo import get_mongo_db
from app.db.database import get_db
from app.utils.security import login_requerido, rol_requerido
# Importamos el cerebro de la simulación
from app.services.predictor import MotorSimulacion

bp = Blueprint('operaciones', __name__, url_prefix='/api')

@bp.route('/simulacion', methods=['POST'])
@login_requerido
@rol_requerido('Comercial', 'Gerencia')
def simulacion():
    """
    Endpoint principal para la simulación de escenarios productivos.
    Arquitectura: Híbrida (Lee SQL, Procesa Lógica Avanzada, Escribe NoSQL).
    """
    data = request.get_json()
    
    # 1. VALIDACIÓN DE ENTRADA
    try:
        cantidad = float(data.get('cantidad', 0))
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")
        
        fecha = data.get('fecha')
        if not fecha:
            raise ValueError("La fecha es obligatoria")
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # 2. OBTENER DATOS REALES (PostgreSQL)
    # Consultamos la superficie total activa para alimentar el simulador con datos reales
    db = get_db()
    superficie_total = 0.0
    
    try:
        with db.cursor() as cursor:
            # Sumamos la superficie de todos los lotes activos
            cursor.execute("SELECT SUM(superficie) as total FROM lotes WHERE estado = 'activo'")
            row = cursor.fetchone()
            if row and row['total']:
                superficie_total = float(row['total'])
            else:
                # Valor por defecto si no hay lotes cargados (para no romper la demo)
                superficie_total = 0.0
    except Exception as e:
        print(f"Error leyendo Postgres: {e}")
        return jsonify({'error': 'Error de conexión con base de datos SQL'}), 500

    # 3. EJECUTAR MOTOR DE SIMULACIÓN (Lógica de Negocio)
    try:
        # matemática (Estacionalidad, Costos, Tiempos)
        resultado_simulacion = MotorSimulacion.simular(cantidad, fecha, superficie_total)
    except Exception as e:
        return jsonify({'error': f"Error en el motor de cálculo: {str(e)}"}), 500

    # 4. PREPARAR RESPUESTA VISUAL
    # Definimos colores y mensajes resumen para el Frontend
    stock_actual = resultado_simulacion['resultado']['stock_disponible']
    deficit = resultado_simulacion['resultado']['deficit_a_cultivar']
    dias = resultado_simulacion['operaciones']['dias_totales_estimados']
    
    if deficit == 0:
        # Escenario Ideal: Tenemos Stock
        color = "green"
        mensaje = f"ENTREGA INMEDIATA. Stock suficiente ({stock_actual} Ton). Tiempo estimado: {dias} días."
    else:
        # Escenario Largo: Hay que cultivar
        color = "warning" # Amarillo (Precaución)
        mensaje = f"REQUIERE CULTIVO. Déficit de {deficit} Ton. Se incluye tiempo de siembra/cosecha ({dias} días)."

    # 5. GUARDAR EN MONGODB (Auditoría / Trazabilidad)
    # Guardamos el JSON completo del resultado para análisis futuro
    try:
        mongo_db = get_mongo_db()
        if mongo_db is not None:
            log_entry = {
                "tipo_evento": "SIMULACION_ESCENARIO",
                "usuario_id": session.get('usuario_id'),
                "usuario_nombre": session.get('nombre'), # ver quién fue
                "input_params": {
                    "cantidad": cantidad,
                    "fecha_objetivo": fecha
                },
                "output_resumen": resultado_simulacion['financiero'],
                "es_factible": deficit == 0,
                "timestamp": datetime.now(timezone.utc)
            }
            mongo_db.logs_auditoria.insert_one(log_entry)
            print("✅ Log de simulación guardado en MongoDB")
    except Exception as e:
        print(f"⚠️ Alerta: No se pudo guardar en Mongo: {e}")

    # 6. ENVIAR AL FRONTEND
    return jsonify({
        'resumen': mensaje,
        'color': color,
        'datos': resultado_simulacion # Enviamos toda la estructura compleja
    })