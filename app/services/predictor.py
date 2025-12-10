from datetime import datetime

class MotorSimulacion:
    # --- CONSTANTES INDUSTRIALES ---
    CAPACIDAD_PROCESAMIENTO_DIARIO = 2.5 
    COSTO_BASE_OPERATIVO = 1200
    COSTO_ENERGIA_BASE = 300
    
    # --- NUEVAS CONSTANTES AGRÍCOLAS ---
    DIAS_CICLO_CULTIVO_BASE = 45 # Días promedio que tarda en crecer el alga
    CAPACIDAD_COSECHA_DIARIA = 5.0 # Toneladas que se pueden sacar del mar por día

    @staticmethod
    def obtener_factores_estacionales(mes):
        """Retorna factores climáticos (Invierno vs Verano)"""
        if mes in [5, 6, 7, 8]: # Invierno
            return { "biomasa": 0.7, "secado": 0.6, "energia": 1.4, "crecimiento": 0.8 } # Crece al 80% de velocidad
        elif mes in [1, 2, 12]: # Verano
            return { "biomasa": 1.2, "secado": 1.1, "energia": 1.0, "crecimiento": 1.2 } # Crece rápido (120%)
        else:
            return { "biomasa": 1.0, "secado": 1.0, "energia": 1.1, "crecimiento": 1.0 }

    @staticmethod
    def simular(cantidad_solicitada, fecha_objetivo, superficie_cultivada):
        if isinstance(fecha_objetivo, str):
            fecha_objetivo = datetime.strptime(fecha_objetivo, '%Y-%m-%d')
        
        mes = fecha_objetivo.month
        factores = MotorSimulacion.obtener_factores_estacionales(mes)

        # 1. ANÁLISIS DE STOCK
        stock_proyectado = superficie_cultivada * 10 * factores['biomasa']
        deficit = max(0, cantidad_solicitada - stock_proyectado)
        
        # 2. TIEMPO INDUSTRIAL (Procesamiento)
        velocidad_fabrica = MotorSimulacion.CAPACIDAD_PROCESAMIENTO_DIARIO * factores['secado']
        dias_fabrica = cantidad_solicitada / velocidad_fabrica
        
        # 3. TIEMPO AGRÍCOLA (¡NUEVO!)
        dias_agricola = 0
        mensaje_estado = "Stock Disponible"
        
        if deficit > 0:
            # Si falta materia prima, hay que esperar el ciclo de cultivo
            # Fórmula: Días Base / Factor Crecimiento (Si es verano, crece más rápido -> menos días)
            tiempo_crecimiento = MotorSimulacion.DIAS_CICLO_CULTIVO_BASE / factores['crecimiento']
            
            # Tiempo de cosechar lo que falta
            tiempo_cosecha = deficit / MotorSimulacion.CAPACIDAD_COSECHA_DIARIA
            
            dias_agricola = tiempo_crecimiento + tiempo_cosecha
            mensaje_estado = "Requiere Ciclo de Cultivo Completo"

        # Tiempo Total = (Tiempo de crecer/cosechar) + (Tiempo de fabricar) + (Logística)
        dias_totales = round(dias_agricola + dias_fabrica + 2, 1)

        # 4. COSTOS
        costo_energia = MotorSimulacion.COSTO_ENERGIA_BASE * factores['energia']
        costo_unitario = MotorSimulacion.COSTO_BASE_OPERATIVO + costo_energia
        costo_total = round(cantidad_solicitada * costo_unitario, 2)
        
        # Penalización de costo si hay que sembrar de urgencia (+15%)
        if deficit > 0:
            costo_total = costo_total * 1.15

        variacion = costo_total * 0.05 

        return {
            "escenario": {
                "fecha": fecha_objetivo.strftime("%Y-%m-%d"),
                "estacion": "Invierno" if mes in [5,6,7,8] else "Verano" if mes in [1,2,12] else "Media",
            },
            "resultado": {
                # Ahora es factible PERO con demora
                "es_factible": True, 
                "stock_disponible": round(stock_proyectado, 2),
                "deficit_a_cultivar": round(deficit, 2),
                "mensaje_origen": mensaje_estado
            },
            "operaciones": {
                "dias_totales_estimados": dias_totales,
                "desglose_dias": {
                    "cultivo_cosecha": round(dias_agricola, 1),
                    "procesamiento": round(dias_fabrica, 1),
                    "logistica": 2
                }
            },
            "financiero": {
                "costo_total_estimado": costo_total,
                "rango_confianza": {
                    "optimista": round(costo_total - variacion, 2),
                    "pesimista": round(costo_total + variacion, 2)
                }
            }
        }