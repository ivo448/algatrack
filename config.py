import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 1. Configuración General
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_segura_por_defecto')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 2. Configuración de Base de Datos (Supabase/PostgreSQL)
    # Obtenemos la URL de la variable de entorno
    uri = os.getenv('POSTGRES_URI') 
    
    # CORRECCIÓN CRÍTICA PARA SUPABASE:
    # Si la URL empieza con 'postgres://', la cambiamos a 'postgresql://'
    # para que SQLAlchemy no de error.
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    # Asignamos la URL corregida a la variable que Flask espera
    SQLALCHEMY_DATABASE_URI = uri
    
    # Configuración de MongoDB (Auditoría)
    MONGO_URI = os.getenv('MONGO_URI')

    # 3. Configuración de Cookies (CORS entre Vercel y Render)
    # Por defecto asumimos configuración segura para Producción
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

# Ajuste para Desarrollo Local (Cuando ENV no es production)
if os.getenv('ENV') != 'production':
    # En local (localhost) no usamos HTTPS, así que relajamos la seguridad
    Config.SESSION_COOKIE_SAMESITE = 'Lax'
    Config.SESSION_COOKIE_SECURE = False
    Config.DEBUG = True