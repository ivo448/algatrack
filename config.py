import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

ENV = os.getenv('ENV')

if ENV == 'production':
    class Config:
        DEBUG = False
        SECRET_KEY = os.getenv('SECRET_KEY')
        POSTGRES_URI = os.getenv('POSTGRES_URI')
        MONGO_URI = os.getenv('MONGO_URI')
        FRONT_END_URL = os.getenv('FRONTEND_URL')
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SESSION_COOKIE_SAMESITE = 'None'
        SESSION_COOKIE_SECURE = True
        PERMANENT_SESSION_LIFETIME = timedelta(days=1)
elif ENV == 'development':
    class Config:
        DEBUG = True
        FRONT_END_URL = os.getenv('FRONTEND_URL')
        POSTGRES_URI = os.getenv('POSTGRES_URI')
        SECRET_KEY = os.getenv('SECRET_KEY')
        MONGO_URI = os.getenv('MONGO_URI')
elif ENV == 'testing':
    class Config:
        TESTING = True
        POSTGRES_URI = os.getenv('POSTGRES_URI')
        MONGO_URI = os.getenv('MONGO_URI')