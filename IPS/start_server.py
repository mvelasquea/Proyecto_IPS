"""
Script simple para iniciar el servidor
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_server():
    """Iniciar el servidor de manera simple"""
    print("🚀 Iniciando Sistema de Análisis de Combustible IPS")
    print("=" * 60)
    
    try:
        # Importar la aplicación
        from run import app
        
        print("✓ Aplicación cargada correctamente")
        print("🌐 Servidor disponible en: http://localhost:5000")
        print("👤 Usuario: admin@ate.gob.pe")
        print("🔑 Password: admin123")
        print("=" * 60)
        print("Presiona Ctrl+C para detener el servidor")
        print("=" * 60)
        
        # Iniciar el servidor
        app.run(debug=False, host='127.0.0.1', port=5000)
        
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        print("Instala las dependencias con: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {str(e)}")
        print("Verifica que todas las dependencias estén instaladas")

if __name__ == '__main__':
    start_server()
