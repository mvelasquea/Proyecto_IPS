"""
Archivo de configuración para debug
"""
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

def setup_debug_logging(app):
    """Configurar logging para debug"""
    if app.debug:
        # Configurar logging para Flask
        app.logger.setLevel(logging.DEBUG)
        
        # Configurar logging para SQLAlchemy
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        
        # Configurar logging para requests
        logging.getLogger('requests.packages.urllib3').setLevel(logging.DEBUG)
        
        app.logger.info("=== Sistema de Login IPS iniciado ===")
        app.logger.info("Modo debug activado")
        app.logger.info("Puerto: 5000")
        app.logger.info("URL: http://localhost:5000")
        app.logger.info("Usuario por defecto: admin@ate.gob.pe / admin123")
        app.logger.info("=" * 50)

def log_request(app):
    """Middleware para logging de requests"""
    from flask import request
    
    @app.before_request
    def log_request_info():
        app.logger.debug('Request: %s %s', request.method, request.url)
        
    @app.after_request
    def log_response_info(response):
        app.logger.debug('Response: %s', response.status_code)
        return response
