def test_simulacion_sin_login(client):
    """No debe permitir simular si no estás logueado"""
    response = client.post('/api/simulacion', json={'cantidad': 10})
    assert response.status_code == 401

def test_simulacion_factible(client):
    """Debe calcular correctamente una simulación viable (ATP)"""
    # 1. Login previo
    client.post('/api/login', json={
        'usuario': 'usuario_pytest_autom',
        'contrasena': '123456'
    })

    # 2. Ejecutar simulación
    response = client.post('/api/simulacion', json={
        'cantidad': 10,
        'fecha': '2025-12-01'
    })

    # 3. Validar respuesta (ESTRUCTURA ACTUALIZADA)
    assert response.status_code == 200
    # Ahora verificamos 'color' y 'resumen', ya no 'resultado'
    assert response.json['color'] == 'green' 
    assert 'ENTREGA INMEDIATA' in response.json['resumen']

def test_simulacion_cantidad_negativa(client):
    """Debe validar que la cantidad sea positiva"""
    client.post('/api/login', json={
        'usuario': 'usuario_pytest_autom',
        'contrasena': '123456'
    })

    response = client.post('/api/simulacion', json={
        'cantidad': -5
    })

    assert response.status_code == 400
    assert 'error' in response.json