from flask import Flask
from flask_cors import CORS
from config import Config
import os

def create_app(config_class=Config):
    frontend_url = os.environ.get('FRONTEND_URL')
    app = Flask(__name__)
    app.config.from_object(config_class)
    print("CORS allowed for frontend URL:", frontend_url)
    CORS(app, 
         resources={r"/api/*": {"origins": [frontend_url]}},
         supports_credentials=True)
    from app.db import database
    database.init_app(app)

    from app.routes import auth, dashboard, operaciones, calendario, lotes, pedidos, clientes, configuracion
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(operaciones.bp)
    app.register_blueprint(calendario.bp)
    app.register_blueprint(lotes.bp)
    app.register_blueprint(pedidos.bp)
    app.register_blueprint(clientes.bp)
    app.register_blueprint(configuracion.bp)

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    
    @app.route('/')
    def home():
        return {"mensaje": "API Algatrack Funcionando", "estado": "OK"}, 200

    return app