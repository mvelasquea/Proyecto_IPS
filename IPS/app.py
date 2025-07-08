"""
Archivo principal de la aplicación
"""
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, User
from auth import auth_bp
from config import config

def create_app():
    """Factory function para crear la aplicación"""
    app = Flask(__name__, 
                template_folder='backend/templates',
                static_folder='frontend/static')
    
    # Configurar la aplicación
    app.config.from_object(config['development'])
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Importar y registrar las rutas del backend
    from backend.app import app as backend_app
    
    # Copiar las rutas del backend al app principal
    for rule in backend_app.url_map.iter_rules():
        if rule.endpoint not in ['static']:
            app.add_url_rule(
                rule.rule,
                endpoint=rule.endpoint,
                view_func=backend_app.view_functions[rule.endpoint],
                methods=rule.methods
            )
    
    # Ruta de login
    @app.route('/login')
    def login():
        return render_template('login.html')
    
    # Ruta principal - redirecciona al login
    @app.route('/')
    def home():
        return redirect(url_for('login'))
    
    # Ruta del sistema principal - protegida por login
    @app.route('/sistema')
    @login_required
    def sistema():
        return render_template('index.html', user=current_user)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
