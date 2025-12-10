def test_login_exitoso(client):
    response = client.post('/api/login', json={
        'usuario': 'usuario_pytest_autom',
        'contrasena': '123456'
    })
    assert response.status_code == 200
    assert response.json['mensaje'] == 'Login exitoso'

def test_login_fallido(client):
    """Debe rechazar credenciales incorrectas"""
    response = client.post('/api/login', json={
        'usuario': 'testuser',
        'contrasena': 'incorrecta'
    })
    assert response.status_code == 401