"""
Script para probar el sistema de login
"""
import os
import sys
import time
import requests

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_login_system():
    """Probar el sistema de login"""
    base_url = "http://localhost:5000"
    
    print("🔍 Probando sistema de login...")
    print("=" * 50)
    
    try:
        # Probar acceso a la página principal
        print("1. Probando acceso a página principal...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✓ Página principal accesible")
        else:
            print(f"⚠ Código de respuesta: {response.status_code}")
        
        # Probar acceso a página de login
        print("\n2. Probando acceso a página de login...")
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code == 200:
            print("✓ Página de login accesible")
        else:
            print(f"⚠ Código de respuesta: {response.status_code}")
        
        # Probar endpoint de verificación de autenticación
        print("\n3. Probando endpoint de verificación...")
        response = requests.get(f"{base_url}/auth/check-auth", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Endpoint de verificación funciona: {data}")
        else:
            print(f"⚠ Código de respuesta: {response.status_code}")
        
        # Probar login con credenciales correctas
        print("\n4. Probando login con credenciales correctas...")
        login_data = {
            "email": "admin@ate.gob.pe",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Login exitoso")
            else:
                print(f"⚠ Error en login: {data.get('error')}")
        else:
            print(f"⚠ Código de respuesta: {response.status_code}")
            
        print("\n" + "=" * 50)
        print("✓ Pruebas completadas")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor")
        print("Asegúrate de que el servidor esté ejecutándose:")
        print("python run.py")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout en la conexión")
        print("El servidor puede estar sobrecargado")
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == '__main__':
    test_login_system()
