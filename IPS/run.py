"""
Archivo principal para ejecutar la aplicación
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_login import LoginManager, login_required, current_user
import pandas as pd
import numpy as np
import json

from models import db, User
from auth import auth_bp
from config import config
from backend.analisis_combustible import procesar_datos, aplicar_filtros, detectar_anomalias, generar_reporte_anomalias

# Crear la aplicación
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

# Solución para serialización de tipos numpy
app.json_encoder = json.JSONEncoder(
    default=lambda o: int(o) if isinstance(o, np.integer) else float(o) if isinstance(o, np.floating) else None
)

# Variable global para almacenar datos
global_df = None

# Ruta de login
@app.route('/login')
def login():
    return render_template('login.html')

# Ruta principal - redirecciona al login si no está autenticado
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('sistema'))
    return redirect(url_for('login'))

# Ruta del sistema principal - protegida por login
@app.route('/sistema')
@login_required
def sistema():
    return render_template('index.html', user=current_user)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    global global_df
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Cargar y procesar datos
            global_df = pd.read_excel(filepath)
            global_df = procesar_datos(global_df)
            
            if global_df is None or global_df.empty:
                return jsonify({'error': 'Error procesando el archivo'}), 500
                
            # Obtener meses y dependencias disponibles
            meses = sorted(global_df['MES'].dropna().unique().tolist()) if 'MES' in global_df.columns else []
            dependencias = sorted(global_df['UNIDAD_ORGANICA'].dropna().unique().tolist()) if 'UNIDAD_ORGANICA' in global_df.columns else []
            
            return jsonify({
                'success': True,
                'meses': meses,
                'dependencias': dependencias
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_data():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No data available'}), 400
    
    data = request.json
    mes = data.get('mes')
    dependencia = data.get('dependencia')
    
    if not mes or not dependencia:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Aplicar filtros
        df_filtrado = aplicar_filtros(global_df, int(mes), dependencia)
        
        if df_filtrado.empty:
            return jsonify({'error': 'No data for selected filters'}), 400
        
        # Detectar anomalías
        df_anomalias = detectar_anomalias(df_filtrado)
        
        # Generar reporte
        report_filename = generar_reporte_anomalias(df_anomalias, mes, dependencia)
        
        # Calcular estadísticas (convertimos explícitamente a float/int)
        stats = {
            'total_registros': int(len(df_filtrado)),
            'total_galones': float(df_filtrado['CANTIDAD_GALONES'].sum()),
            'total_km': float(df_filtrado['KM_RECORRIDO'].sum()),
            'total_consumo': float(df_filtrado['TOTAL_CONSUMO'].sum()),
            'total_anomalias': int(df_anomalias['ANOMALIA'].sum() if 'ANOMALIA' in df_anomalias else 0)
        }
        
        # Preparar datos para gráficos
        graficos = {}
        
        # Gráfico de eficiencia
        if 'EFICIENCIA' in df_filtrado.columns:
            graficos['eficiencia'] = df_filtrado['EFICIENCIA'].dropna().astype(float).tolist()
        
        # Gráfico de consumo por día
        if 'DIA_SEMANA' in df_filtrado.columns and 'TOTAL_CONSUMO' in df_filtrado.columns:
            dias = {0: 'Lun', 1: 'Mar', 2: 'Mie', 3: 'Jue', 4: 'Vie', 5: 'Sab', 6: 'Dom'}
            df_filtrado['DIA_NOMBRE'] = df_filtrado['DIA_SEMANA'].map(dias)
            consumo_diario = df_filtrado.groupby('DIA_NOMBRE')['TOTAL_CONSUMO'].sum()
            consumo_diario = consumo_diario.reindex(['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'], fill_value=0)
            graficos['consumo_diario'] = {
                'labels': consumo_diario.index.tolist(),
                'data': consumo_diario.astype(float).tolist()
            }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'graficos': graficos,
            'report_filename': report_filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
@login_required
def download_report(filename):
    try:
        # Asegurarse de que la carpeta uploads existe
        uploads_dir = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(uploads_dir, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Enviar el archivo con el tipo MIME correcto
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"Reporte_Anomalias_{filename}",
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Configurar logging
        import logging
        logging.basicConfig(level=logging.INFO)
        
        # Inicializar base de datos
        with app.app_context():
            db.create_all()
            
            # Crear usuario administrador por defecto si no existe
            admin_user = User.query.filter_by(email='admin@ate.gob.pe').first()
            if not admin_user:
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
                print("✓ Usuario administrador creado: admin@ate.gob.pe / admin123")
            else:
                print("✓ Usuario administrador ya existe")
        
        # Crear carpeta de uploads
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Mostrar información del sistema
        print("\n" + "="*60)
        print("🚀 SISTEMA DE ANÁLISIS DE COMBUSTIBLE IPS")
        print("   Municipalidad de Ate")
        print("="*60)
        print(f"🌐 URL: http://localhost:5000")
        print(f"👤 Usuario: admin@ate.gob.pe")
        print(f"🔑 Password: admin123")
        print("="*60)
        print("✓ Sistema iniciado correctamente")
        print("✓ Presiona Ctrl+C para detener el servidor")
        print("="*60 + "\n")
        
        # Ejecutar aplicación
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {str(e)}")
        print("Verifica que todas las dependencias estén instaladas:")
        print("pip install -r requirements.txt")
        import traceback
        traceback.print_exc()