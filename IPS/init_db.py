"""
Script para inicializar la base de datos
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User
from config import config

def init_db():
    """Inicializar la base de datos"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    db.init_app(app)
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya existe un usuario admin
        admin_user = User.query.filter_by(email='admin@ate.gob.pe').first()
        if not admin_user:
            # Crear usuario administrador por defecto
            admin_user = User(
                email='admin@ate.gob.pe',
                nombre='Administrador',
                apellido='Sistema',
                cargo='Administrador',
                dependencia='Sistemas',
                is_admin=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuario administrador creado: admin@ate.gob.pe / admin123")
        
        print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_db()
