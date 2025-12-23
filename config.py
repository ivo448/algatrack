import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 1. Configuración General
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_segura_por_defecto')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 2. Configuración de Base de Datos
    uri = os.getenv('POSTGRES_URI') 
    
    # Corrección para Supabase
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    # Asignamos a la variable estándar de Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = uri
    
    # --- AGREGA ESTA LÍNEA ---
    # Guardamos también el nombre antiguo para que database.py y seed.py no fallen
    POSTGRES_URI = uri 
    # -------------------------

    MONGO_URI = os.getenv('MONGO_URI')

    # 3. Configuración de Cookies
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

# Ajuste para Desarrollo Local
if os.getenv('ENV') != 'production':
    Config.SESSION_COOKIE_SAMESITE = 'Lax'
    Config.SESSION_COOKIE_SECURE = False
    Config.DEBUG = True