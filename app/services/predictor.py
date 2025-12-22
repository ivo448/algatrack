from datetime import datetime

class MotorSimulacion:
    
    @staticmethod
    def obtener_factores_dinamicos(mes, lista_estaciones):
        """
        Busca en la lista de estaciones (desde BD) cuál coincide con el mes actual.
        Si no encuentra, devuelve factores neutros (1.0).
        """
        for estacion in lista_estaciones:
            # Convertimos el string '5,6,7,8' a una lista de enteros [5, 6, 7, 8]
            try:
                meses = [int(x) for x in estacion['meses_asociados'].split(',')]
                if mes in meses:
                    return {
                        "nombre": estacion['nombre_estacion'],
                        "biomasa": float(estacion['factor_biomasa']),
                        "secado": float(estacion['factor_secado']),
                        "energia": float(estacion['factor_energia']),
                        "crecimiento": float(estacion['factor_crecimiento'])
                    }
            except Exception as e:
                print(f"Error parseando meses de estacion {estacion['nombre_estacion']}: {e}")
                continue
        
        # Fallback (Por defecto)
        return { 
            "nombre": "Estandar (Fallback)", 
            "biomasa": 1.0, "secado": 1.0, "energia": 1.1, "crecimiento": 1.0 
        }

    @staticmethod
    def simular(cantidad_solicitada, fecha_objetivo, superficie_cultivada, params_economicos, lista_estaciones):
        """
        Ahora recibe DOS configuraciones:
        1. params_economicos: Precios y costos ($)
        2. lista_estaciones: Reglas biológicas (Clima)
        """
        if isinstance(fecha_objetivo, str):
            fecha_objetivo = datetime.strptime(fecha_objetivo, '%Y-%m-%d')
        
        mes = fecha_objetivo.month
        
        # 1. OBTENER FACTORES BIOLÓGICOS DESDE BD
        factores = MotorSimulacion.obtener_factores_dinamicos(mes, lista_estaciones)

        # ---------------------------------------------------------
        # 2. ANÁLISIS DE STOCK (Afectado por Factor Biomasa)
        # ---------------------------------------------------------
        rendimiento_base = 10.0 # Esto también podría venir de params_economicos si quisieras
        stock_proyectado = superficie_cultivada * rendimiento_base * factores['biomasa']
        deficit = max(0, cantidad_solicitada - stock_proyectado)
        
        # ---------------------------------------------------------
        # 3. TIEMPO OPERATIVO (Afectado por Factor Secado)
        # ---------------------------------------------------------
        cap_planta = params_economicos.get('capacidad_planta_dia', 2.5) * factores['secado']
        dias_fabrica = cantidad_solicitada / cap_planta
        
        dias_agricola = 0
        mensaje_estado = "Stock Disponible"
        
        if deficit > 0:
            ciclo_base = params_economicos.get('dias_ciclo_base', 45)
            # Afectado por Factor Crecimiento (Verano crece más rápido)
            tiempo_crecimiento = ciclo_base / factores['crecimiento']
            
            cap_cosecha = params_economicos.get('capacidad_cosecha_dia', 5.0)
            tiempo_cosecha = deficit / cap_cosecha
            
            dias_agricola = tiempo_crecimiento + tiempo_cosecha
            mensaje_estado = "Requiere Ciclo de Cultivo Completo"

        dias_totales = round(dias_agricola + dias_fabrica + 2, 1)

        # ---------------------------------------------------------
        # 4. CÁLCULO DE COSTOS (Afectado por Factor Energía)
        # ---------------------------------------------------------
        costo_agua = cantidad_solicitada * params_economicos['consumo_agua_ton'] * params_economicos['precio_agua_m3']
        
        # En invierno (factor energía > 1) se paga más luz
        costo_energia = cantidad_solicitada * params_economicos['consumo_energia_ton'] * params_economicos['precio_kwh'] * factores['energia']
        
        costo_diesel = cantidad_solicitada * params_economicos['consumo_diesel_ton'] * params_economicos['precio_diesel_L']
        costo_mo = cantidad_solicitada * params_economicos['horas_hombre_ton'] * params_economicos['costo_hh_operario']
        costo_insumos = cantidad_solicitada * params_economicos['insumos_varios_ton']

        costo_total_neto = costo_agua + costo_energia + costo_diesel + costo_mo + costo_insumos
        
        if deficit > 0:
            costo_total_neto = costo_total_neto * 1.15

        return {
            "escenario": {
                "fecha": fecha_objetivo.strftime("%Y-%m-%d"),
                "estacion_detectada": factores['nombre'], # Mostramos qué detectó la BD
                "factores_aplicados": factores
            },
            "resultado": {
                "es_factible": True,
                "stock_disponible": round(stock_proyectado, 2),
                "deficit_a_cultivar": round(deficit, 2),
                "mensaje_origen": mensaje_estado
            },
            "operaciones": {
                "dias_totales": dias_totales
            },
            "financiero": {
                "costo_total": round(costo_total_neto, 0),
                "detalle_costos": {
                    "agua": round(costo_agua, 0),
                    "energia": round(costo_energia, 0),
                    "diesel": round(costo_diesel, 0),
                    "mano_obra": round(costo_mo, 0)
                }
            }
        }