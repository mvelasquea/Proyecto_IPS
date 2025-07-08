#!/usr/bin/env python3
"""
Script de inicialización para el Sistema de Análisis de Combustible
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Mostrar banner del sistema"""
    print("=" * 60)
    print("   SISTEMA DE ANÁLISIS DE COMBUSTIBLE")
    print("   Municipalidad de Ate")
    print("=" * 60)
    print()

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Verificando versión de Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def create_directories():
    """Crear directorios necesarios"""
    print("📁 Creando directorios...")
    
    directories = [
        'uploads',
        'logs',
        'backups',
        'tests/__pycache__',
        'backend/__pycache__'
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def install_dependencies():
    """Instalar dependencias"""
    print("📦 Instalando dependencias...")
    
    requirements_file = Path('backend/requirements.txt')
    
    if not requirements_file.exists():
        print("❌ Error: No se encontró backend/requirements.txt")
        return False
    
    try:
        # Instalar dependencias
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ])
        print("✅ Dependencias instaladas correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def create_env_file():
    """Crear archivo .env desde .env.example"""
    print("⚙️  Configurando archivos de entorno...")
    
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_example.exists() and not env_file.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Archivo .env creado desde .env.example")
    else:
        print("ℹ️  Archivo .env ya existe o .env.example no encontrado")

def run_tests():
    """Ejecutar pruebas del sistema"""
    print("🧪 Ejecutando pruebas del sistema...")
    
    test_file = Path('tests/test_sistema.py')
    
    if not test_file.exists():
        print("⚠️  Archivo de pruebas no encontrado, omitiendo...")
        return True
    
    try:
        result = subprocess.run([
            sys.executable, str(test_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Todas las pruebas pasaron")
            return True
        else:
            print("❌ Algunas pruebas fallaron:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        return False

def show_next_steps():
    """Mostrar próximos pasos"""
    print("\n🎉 ¡Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar: python run.py")
    print("   2. Abrir navegador en: http://localhost:5000")
    print("   3. Cargar un archivo Excel con datos de combustible")
    print("   4. Seleccionar mes y dependencia")
    print("   5. Generar reporte")
    print("\n📖 Para más información, consultar README.md")
    print("\n🐛 Si hay problemas:")
    print("   - Verificar que todas las dependencias estén instaladas")
    print("   - Revisar los logs en la carpeta 'logs/'")
    print("   - Ejecutar pruebas: python tests/test_sistema.py")

def main():
    """Función principal de inicialización"""
    print_banner()
    
    # Lista de verificaciones
    checks = [
        ("Python", check_python_version),
        ("Directorios", create_directories),
        ("Dependencias", install_dependencies),
        ("Configuración", create_env_file),
        ("Pruebas", run_tests)
    ]
    
    failed_checks = []
    
    for name, check_func in checks:
        try:
            if not check_func():
                failed_checks.append(name)
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            failed_checks.append(name)
        print()
    
    if failed_checks:
        print(f"⚠️  Verificaciones fallidas: {', '.join(failed_checks)}")
        print("   Por favor, revisar los errores antes de continuar")
        return 1
    
    show_next_steps()
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
