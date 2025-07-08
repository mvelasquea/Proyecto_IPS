#!/usr/bin/env python3
"""
Script de inicialización del Sistema de Análisis de Combustible
Ejecuta las tareas necesarias para el primer uso del sistema
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Muestra el banner del sistema"""
    print("=" * 60)
    print("🚀 SISTEMA DE ANÁLISIS DE COMBUSTIBLE")
    print("   Municipalidad de Ate - Versión 2.0.0")
    print("=" * 60)
    print()

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    print(f"📋 Verificando Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ ERROR: Se requiere Python 3.9 o superior")
        return False
    
    print("✅ Versión de Python compatible")
    return True

def install_requirements():
    """Instala las dependencias del proyecto"""
    print("\n📦 Instalando dependencias...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencias instaladas exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def create_directories():
    """Crea los directorios necesarios"""
    print("\n📁 Creando directorios...")
    
    directories = [
        "uploads",
        "reports", 
        "instance",
        "logs",
        "temp",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

def initialize_database():
    """Inicializa la base de datos"""
    print("\n🗃️ Inicializando base de datos...")
    
    try:
        # Importar y crear las tablas
        from backend.app import app, db
        
        with app.app_context():
            db.create_all()
            print("✅ Base de datos inicializada")
            return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def create_default_user():
    """Crea un usuario por defecto"""
    print("\n👤 Creando usuario por defecto...")
    
    try:
        from backend.app import app
        from models import db, User
        
        with app.app_context():
            # Verificar si ya existe un usuario admin
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@municipalidad.ate',
                    nombre='Administrador',
                    rol='admin'
                )
                admin.set_password('admin123')  # Contraseña por defecto
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuario admin creado")
                print("   Usuario: admin")
                print("   Contraseña: admin123")
                print("   ⚠️  CAMBIAR CONTRASEÑA EN PRIMER USO")
            else:
                print("✅ Usuario admin ya existe")
            
            return True
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        return False

def run_tests():
    """Ejecuta pruebas básicas del sistema"""
    print("\n🧪 Ejecutando pruebas básicas...")
    
    try:
        # Importar módulos principales
        from backend.app import app
        from backend.analisis_combustible import procesar_datos
        from backend.prediccion_ia import PrediccionConsumo
        from backend.sistema_alertas import SistemaAlertas
        
        print("✅ Módulos importados correctamente")
        
        # Verificar que Flask funciona
        with app.app_context():
            print("✅ Flask configurado correctamente")
        
        # Verificar módulos de IA
        prediccion = PrediccionConsumo()
        print("✅ Módulo de predicción funcionando")
        
        alertas = SistemaAlertas()
        print("✅ Sistema de alertas funcionando")
        
        return True
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        return False

def show_next_steps():
    """Muestra los próximos pasos"""
    print("\n" + "=" * 60)
    print("🎉 INICIALIZACIÓN COMPLETADA")
    print("=" * 60)
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Ejecutar el sistema:")
    print("   python -m backend.app")
    print("\n2. Abrir navegador web:")
    print("   http://127.0.0.1:5000")
    print("\n3. Iniciar sesión:")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("\n4. ⚠️  CAMBIAR CONTRASEÑA DE ADMINISTRADOR")
    print("\n5. Cargar datos y comenzar análisis")
    print("\n📚 Documentación completa en:")
    print("   - README_SISTEMA_COMPLETO.md")
    print("   - DOCUMENTACION_SISTEMA_COMPLETO.md")
    print("\n" + "=" * 60)

def main():
    """Función principal del script"""
    print_banner()
    
    # Verificar Python
    if not check_python_version():
        return False
    
    # Instalar dependencias
    if not install_requirements():
        return False
    
    # Crear directorios
    create_directories()
    
    # Inicializar base de datos
    if not initialize_database():
        return False
    
    # Crear usuario por defecto
    if not create_default_user():
        return False
    
    # Ejecutar pruebas
    if not run_tests():
        return False
    
    # Mostrar próximos pasos
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Inicialización cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
