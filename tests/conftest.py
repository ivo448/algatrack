import pytest
import os
from dotenv import load_dotenv
from app import create_app
from app.db.database import get_db
from werkzeug.security import generate_password_hash

load_dotenv()

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-key'
    POSTGRES_URI = os.getenv('POSTGRES_URI')
    MONGO_URI = os.getenv('MONGO_URI')

@pytest.fixture
def app():
    app = create_app(TestConfig)

    TEST_USER = 'usuario_pytest_autom'
    TEST_LOTE = 'Lote_Pytest_Autom'

    with app.app_context():
        db = get_db()
        
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios WHERE usuario = %s", (TEST_USER,))
            cursor.execute("DELETE FROM lotes WHERE tipo_alga = %s", (TEST_LOTE,))
            
            ph = generate_password_hash('123456')
            cursor.execute(
                "INSERT INTO usuarios (usuario, contrasena, email, rol) VALUES (%s, %s, %s, %s)",
                (TEST_USER, ph, 'test_auto@alga.cl', 'Comercial')
            )
            
            cursor.execute(
                "INSERT INTO lotes (tipo_alga, superficie, fecha_inicio, estado) VALUES (%s, %s, %s, %s)",
                (TEST_LOTE, 10.0, '2025-01-01', 'activo')
            )

    yield app

    with app.app_context():
        db = get_db()
        with db.cursor() as cursor:
            print(f"\n🧹 Limpiando datos de prueba ({TEST_USER})...")
            cursor.execute("DELETE FROM lotes WHERE tipo_alga = %s", (TEST_LOTE,))
            cursor.execute("DELETE FROM usuarios WHERE usuario = %s", (TEST_USER,))

@pytest.fixture
def client(app):
    return app.test_client()