import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables del archivo .env (solo funciona en local)
load_dotenv()

class Config:
    # 1. SEGURIDAD BASE
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_dev_insegura')
    
    # 2. BASE DE DATOS (Soporte para Supabase y Render)
    # Obtenemos la URL cruda
    uri = os.getenv('POSTGRES_URI')
    
    # CORRECCIÓN AUTOMÁTICA PARA SUPABASE (postgres:// -> postgresql://)
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    # Asignamos a las dos variables que tu sistema usa
    SQLALCHEMY_DATABASE_URI = uri
    POSTGRES_URI = uri  # Para que no fallen tus scripts seed.py o database.py
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONGO_URI = os.getenv('MONGO_URI')

    # 3. CONFIGURACIÓN DE COOKIES (POR DEFECTO: PRODUCCIÓN)
    # Asumimos el escenario más estricto (Nube)
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

# 4. EXCEPCIÓN: DESARROLLO LOCAL
# Si la variable ENV dice 'development', relajamos la seguridad
if os.getenv('ENV') == 'development':
    Config.SESSION_COOKIE_SAMESITE = 'Lax'
    Config.SESSION_COOKIE_SECURE = False # Importante: False porque localhost no usa https
    Config.DEBUG = True