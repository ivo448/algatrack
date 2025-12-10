from pymongo import MongoClient

# Pega aquí tu URL para probar
URI = "mongodb://localhost:27017/algatrack_nosql" 

try:
    client = MongoClient(URI)
    db = client.get_database()
    print(f"✅ ¡Conexión Exitosa a: {db.name}!")
except Exception as e:
    print(f"❌ Error de conexión: {e}")