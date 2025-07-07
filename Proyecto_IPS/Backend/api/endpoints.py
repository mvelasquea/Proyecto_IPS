from flask import Blueprint, request, jsonify,send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from io import BytesIO
import os
import uuid
import json
from datetime import datetime
import math
from AnalisisCombustible import get_analysis_results

api_blueprint = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_nans(obj):
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.floating, np.integer)):
        if pd.isnull(obj) or np.isinf(obj):
            return None
        return obj.item()
    else:
        return obj

@api_blueprint.route('/descargar_pdf', methods=['GET'])
def descargar_pdf():
    # Obtén los parámetros de mes y dependencia desde la URL (ajusta según tu frontend)
    mes = request.args.get('mes')
    dependencia = request.args.get('dependencia')
    if not mes or not dependencia:
        return jsonify({"error": "Faltan parámetros mes o dependencia"}), 400

    # Construye el nombre del archivo como lo hace tu función
    nombre_dependencia = "".join(x for x in dependencia if x.isalnum() or x in " _-")
    nombre_archivo = f"informe_{nombre_dependencia[:20]}_mes{mes}.pdf"
    ruta_archivo = os.path.join(os.getcwd(), nombre_archivo)  # Ajusta si guardas en otra carpeta

    if not os.path.exists(ruta_archivo):
        return jsonify({"error": "No se encontró el reporte PDF"}), 404

    # Envía el archivo al frontend
    return send_from_directory(os.getcwd(), nombre_archivo, as_attachment=True)

@api_blueprint.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de archivo no permitido. Use .xlsx, .xls o .csv'}), 400

    if file.content_length > MAX_FILE_SIZE:
        return jsonify({'error': 'El archivo es demasiado grande (máximo 20MB)'}), 400

    try:
        file_id = str(uuid.uuid4())
        filename = secure_filename(f"{file_id}_{file.filename}")
        upload_folder = os.getenv('UPLOAD_FOLDER', 'temp_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)

        file.save(filepath)

        if filename.endswith('.csv'):
            df = pd.read_csv(filepath, encoding='latin1')
        else:
            df = pd.read_excel(filepath)

        required_columns = ['Vehículo', 'Fecha', 'Galones', 'Kilometraje', 'Costo']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            os.remove(filepath)
            return jsonify({
                'error': f'Columnas requeridas faltantes: {", ".join(missing_columns)}',
                'required_columns': required_columns
            }), 400

        results = get_analysis_results(df)

        # Limpieza de NaN e infinitos antes de convertir a dict
        results = results.replace([np.inf, -np.inf], None)
        results = results.fillna(value=None)
        results_dict = results.to_dict(orient='records')

        os.remove(filepath)

        stats = calculate_basic_stats(results)
        stats = clean_nans(stats)

        response_data = {
            'success': True,
            'data': results_dict,
            'stats': stats,
            'timestamp': datetime.now().isoformat(),
            'message': 'Archivo analizado exitosamente'
        }

        return jsonify(clean_nans(response_data))

    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'error': str(e),
            'message': 'Error al procesar el archivo'
        }), 500


def calculate_basic_stats(df):
    stats = {}

    if 'EFICIENCIA' in df.columns:
        stats['eficiencia'] = {
            'promedio': df['EFICIENCIA'].mean(),
            'min': df['EFICIENCIA'].min(),
            'max': df['EFICIENCIA'].max(),
            'mediana': df['EFICIENCIA'].median()
        }

    if 'TOTAL_CONSUMO' in df.columns:
        stats['consumo'] = {
            'total': df['TOTAL_CONSUMO'].sum(),
            'promedio': df['TOTAL_CONSUMO'].mean()
        }

    if 'ANOMALIA' in df.columns:
        total_anomalias = df['ANOMALIA'].sum()
        stats['anomalias'] = {
            'total': total_anomalias,
            'porcentaje': (total_anomalias / len(df)) * 100,
            'criticas': df[df['NIVEL_RIESGO'] == 'Crítico'].shape[0]
        }

    if 'Vehículo' in df.columns:
        stats['vehiculos'] = {
            'total': df['Vehículo'].nunique(),
            'mas_eficiente': get_most_efficient_vehicle(df),
            'menos_eficiente': get_least_efficient_vehicle(df)
        }

    return stats


def get_most_efficient_vehicle(df):
    if 'EFICIENCIA' not in df.columns or df['EFICIENCIA'].isnull().all():
        return None
    return df.loc[df['EFICIENCIA'].idxmax(), 'Vehículo']


def get_least_efficient_vehicle(df):
    if 'EFICIENCIA' not in df.columns or df['EFICIENCIA'].isnull().all():
        return None
    return df.loc[df['EFICIENCIA'].idxmin(), 'Vehículo']
