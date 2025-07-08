"""
Script para verificar la configuración de la base de datos
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Probar las importaciones"""
    try:
        from models import db, User
        print("✓ Importación de modelos exitosa")
        
        from auth import auth_bp
        print("✓ Importación de auth blueprint exitosa")
        
        from config import config
        print("✓ Importación de config exitosa")
        
        from backend.analisis_combustible import procesar_datos
        print("✓ Importación de análisis de combustible exitosa")
        
        return True
    except Exception as e:
        print(f"✗ Error en importaciones: {str(e)}")
        return False

def test_db_creation():
    """Probar creación de base de datos"""
    try:
        from flask import Flask
        from models import db, User
        from config import config
        
        app = Flask(__name__)
        app.config.from_object(config['development'])
        
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            print("✓ Base de datos creada exitosamente")
            
            # Verificar si se puede crear un usuario de prueba
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                test_user = User(
                    email='test@example.com',
                    nombre='Test',
                    apellido='User',
                    cargo='Test',
                    dependencia='Test'
                )
                test_user.set_password('test123')
                db.session.add(test_user)
                db.session.commit()
                print("✓ Usuario de prueba creado")
            else:
                print("✓ Usuario de prueba ya existe")
                
        return True
    except Exception as e:
        print(f"✗ Error en creación de base de datos: {str(e)}")
        return False

if __name__ == '__main__':
    print("Verificando configuración del sistema...")
    print("=" * 50)
    
    if test_imports():
        print("\n" + "=" * 50)
        if test_db_creation():
            print("\n" + "=" * 50)
            print("✓ Sistema configurado correctamente")
            print("\nPuedes ejecutar la aplicación con:")
            print("python run.py")
            print("\nCredenciales por defecto:")
            print("Email: admin@ate.gob.pe")
            print("Password: admin123")
        else:
            print("\n✗ Error en configuración de base de datos")
    else:
        print("\n✗ Error en importaciones")
