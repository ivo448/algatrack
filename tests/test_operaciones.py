def test_simulacion_sin_login(client):
    """No debe permitir simular si no estás logueado"""
    response = client.post('/api/simulacion', json={'cantidad': 10})
    assert response.status_code == 401  # No autorizado

def test_simulacion_factible(client):
    """Debe calcular correctamente una simulación viable"""
    client.post('/api/login', json={
        'usuario': 'usuario_pytest_autom',
        'contrasena': '123456'
    })

    response = client.post('/api/simulacion', json={
        'cantidad': 10,
        'fecha': '2025-12-01'
    })

    assert response.status_code == 200
    assert response.json['resultado'] == 'FACTIBLE'
    assert response.json['color'] == 'green'

def test_simulacion_cantidad_negativa(client):
    """Debe validar que la cantidad sea positiva (Seguridad)"""
    client.post('/api/login', json={
        'usuario': 'usuario_pytest_autom',
        'contrasena': '123456'
    })

    response = client.post('/api/simulacion', json={
        'cantidad': -5
    })

    assert response.status_code == 400
    assert 'error' in response.json