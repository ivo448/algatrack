from pymongo import MongoClient
from flask import current_app, g

def get_mongo_db():
    if 'mongo_db' not in g:
        mongo_uri = current_app.config.get('MONGO_URI', 'mongodb://localhost:27017/')
        try:
            client = MongoClient(mongo_uri)
            g.mongo_db = client['algatrack_nosql'] 
        except Exception as e:
            print(f"Error conectando a Mongo: {e}")
            g.mongo_db = None
    return g.mongo_db

def init_mongo(app):
    app.config.setdefault('MONGO_URI', 'mongodb://localhost:27017/')