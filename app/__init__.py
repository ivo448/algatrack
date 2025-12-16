from flask import Flask
from flask_cors import CORS
from config import DevelopmentConfig

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "https://algatrack-frontend-gu22hyvl7-iavo.vercel.app"}})
    from app.db import database
    database.init_app(app)

    from app.routes import auth, dashboard, operaciones, calendario, lotes, pedidos, clientes
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(operaciones.bp)
    app.register_blueprint(calendario.bp)
    app.register_blueprint(lotes.bp)
    app.register_blueprint(pedidos.bp)
    app.register_blueprint(clientes.bp)

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    
    @app.route('/')
    def home():
        return {"mensaje": "API Algatrack Funcionando", "estado": "OK"}, 200

    return app