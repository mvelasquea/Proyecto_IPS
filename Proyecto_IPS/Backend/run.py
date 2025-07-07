from flask import Flask, jsonify
from flask_cors import CORS
from api.endpoints import api_blueprint
from AnalisisCombustible import get_analysis_results
import os

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuración de directorios
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Registrar blueprints
app.register_blueprint(api_blueprint, url_prefix='/api')

@app.route('/')
def health_check():
    return jsonify({
        "status": "active", 
        "message": "Fuel Analysis API is running",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)