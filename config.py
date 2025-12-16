import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    POSTGRES_URI = os.getenv('POSTGRES_URI')
    MONGO_URI = os.getenv('MONGO_URI')

class DevelopmentConfig(Config):
    DEBUG = True

class TestConfig(Config):
    TESTING = True
    POSTGRES_URI = os.getenv('POSTGRES_URI')
    MONGO_URI = os.getenv('MONGO_URI')