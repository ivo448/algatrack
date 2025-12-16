import time
import unittest
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager

class AlgatrackFrontendTest(unittest.TestCase):

    def setUp(self):
        print("\n🔵 Configurando Microsoft Edge...")
        
        # 1. Configurar Opciones de Edge
        options = Options()
        # IMPORTANTE: Ruta estándar de Edge en Windows. 
        # Si tu Edge está en otro lado, cambia esta línea:
        options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        try:
            # 2. Intentar instalar el driver automáticamente
            # Si tienes internet restringido, esto podría fallar.
            driver_path = EdgeChromiumDriverManager().install()
            service = Service(driver_path)
        except Exception as e:
            print(f"⚠️ No se pudo descargar el driver automáticamente (Error de red).")
            print("Intentando usar 'msedgedriver.exe' si existe en la carpeta...")
            # Plan B: Buscar si descargaste el driver manualmente en la carpeta actual
            if os.path.exists("msedgedriver.exe"):
                service = Service("msedgedriver.exe")
            else:
                raise Exception("❌ ERROR: Necesitas internet para descargar el driver O colocar 'msedgedriver.exe' en esta carpeta.")

        # 3. Iniciar el Navegador
        self.driver = webdriver.Edge(service=service, options=options)
        self.driver.maximize_window()
        self.base_url = "http://localhost:5173"

    def test_flujo_login_exitoso(self):
        """CP-01: Validar inicio de sesión correcto en Edge"""
        driver = self.driver
        print("🚀 Ejecutando prueba de Login en Edge...")

        driver.get(self.base_url)
        time.sleep(2) 

        # Ingresar datos
        driver.find_element(By.CSS_SELECTOR, "input[type='text']").send_keys("gerente")
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("gerente123")
        
        # Click en entrar
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(3) # Esperar redirección
        
        # Validar
        if "/dashboard" in driver.current_url:
            print("✅ ÉXITO: Redirigido al Dashboard correctamente.")
            driver.save_screenshot("evidencia_edge_login.png")
        else:
            self.fail(f"❌ FALLO: No se redirigió. URL actual: {driver.current_url}")

    def tearDown(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    unittest.main()