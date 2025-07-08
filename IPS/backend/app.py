from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_login import LoginManager, login_required, current_user
import os
import pandas as pd
import numpy as np
from datetime import datetime
from functools import wraps
from .analisis_combustible import procesar_datos, aplicar_filtros, detectar_anomalias, generar_reporte_anomalias
from .prediccion_ia import PrediccionConsumo
from .sistema_alertas import SistemaAlertas
from .historial_notificaciones import GestorHistorialNotificaciones
from .filtros_avanzados import FiltrosAvanzados
from .modulo_emisiones import CalculadorEmisiones
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, User
from auth import auth_bp
from config import config

app = Flask(__name__, 
            template_folder='../backend/templates',
            static_folder='../frontend/static')

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
global_data_analyzed = False  # Flag para indicar si los datos han sido analizados

# Decorador para verificar si el análisis ha sido realizado
def require_analysis(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global global_data_analyzed
        if not global_data_analyzed:
            return jsonify({
                'error': 'Primero debes realizar un análisis tradicional para acceder a esta funcionalidad avanzada.',
                'codigo': 'ANALISIS_REQUERIDO'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

# Inicializar módulos
prediccion_ia = PrediccionConsumo()
sistema_alertas = SistemaAlertas()
historial_notificaciones = GestorHistorialNotificaciones()
filtros_avanzados = FiltrosAvanzados()
modulo_emisiones = CalculadorEmisiones()

# Ruta de login
@app.route('/login')
def login():
    return render_template('login.html')

# Ruta principal - ahora requiere login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Ruta del sistema principal - protegida por login
@app.route('/sistema')
@login_required
def sistema():
    return render_template('index.html', user=current_user, seccion='sistema')

# Ruta de reportes - protegida por login
@app.route('/reportes')
@login_required
def reportes():
    global global_df, global_data_analyzed
    
    # Verificar si hay datos analizados
    if not global_data_analyzed:
        return render_template('index.html', user=current_user, seccion='reportes', 
                             mensaje='Primero debes realizar un análisis tradicional para ver los reportes.')
    
    # Obtener reportes disponibles si hay datos
    reportes_disponibles = []
    if global_df is not None:
        reportes_disponibles = [
            {'nombre': 'Reporte de Anomalías', 'tipo': 'anomalias'},
            {'nombre': 'Reporte de Emisiones', 'tipo': 'emisiones'},
            {'nombre': 'Reporte de Eficiencia', 'tipo': 'eficiencia'}
        ]
    
    return render_template('index.html', user=current_user, seccion='reportes', 
                         reportes=reportes_disponibles)

# Ruta de historial - protegida por login  
@app.route('/historial')
@login_required
def historial():
    global global_data_analyzed
    
    # Verificar si hay datos analizados
    if not global_data_analyzed:
        return render_template('index.html', user=current_user, seccion='historial',
                             mensaje='Primero debes realizar un análisis tradicional para ver el historial.')
    
    # Obtener historial del usuario
    try:
        historial_busquedas = historial_notificaciones.obtener_historial_usuario(current_user.id, limite=10)
        notificaciones = historial_notificaciones.obtener_notificaciones_usuario(current_user.id, limite=5)
    except Exception as e:
        historial_busquedas = []
        notificaciones = []
    
    return render_template('index.html', user=current_user, seccion='historial',
                         historial=historial_busquedas, notificaciones=notificaciones)

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
    global global_df, global_data_analyzed
    
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
        
        # MARCAR QUE LOS DATOS HAN SIDO ANALIZADOS
        global_data_analyzed = True
        
        # Registrar análisis en historial
        historial_notificaciones.guardar_busqueda(
            current_user.id, 
            {'mes': mes, 'dependencia': dependencia}, 
            df_filtrado
        )
        
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

# ===============================
# NUEVAS RUTAS PARA MÓDULOS
# ===============================

# PREDICCIÓN CON IA
@app.route('/prediccion/entrenar', methods=['POST'])
@login_required
@require_analysis
def entrenar_modelo():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles. Primero carga un archivo.'}), 400
    
    try:
        resultado = prediccion_ia.entrenar_modelo(global_df)
        return jsonify({
            'success': True,
            'metricas': resultado['metricas'],
            'mensaje': 'Modelo entrenado exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/prediccion/predecir', methods=['POST'])
@login_required
@require_analysis
def predecir_consumo():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles. Primero carga un archivo.'}), 400
    
    data = request.json
    try:
        tipo_prediccion = data.get('tipo', 'semanal')
        placa = data.get('placa')
        dependencia = data.get('dependencia')
        
        if tipo_prediccion == 'semanal':
            prediccion = prediccion_ia.predecir_consumo_semanal(global_df, placa=placa, dependencia=dependencia)
        elif tipo_prediccion == 'mensual':
            prediccion = prediccion_ia.predecir_consumo_mensual(global_df, dependencia=dependencia)
        elif tipo_prediccion == 'anual':
            prediccion = prediccion_ia.predecir_consumo_anual(global_df, dependencia=dependencia)
        else:
            prediccion = prediccion_ia.predecir_consumo_semanal(global_df, placa=placa, dependencia=dependencia)
        
        return jsonify({
            'success': True,
            'prediccion': prediccion
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/prediccion/analizar-tendencias', methods=['POST'])
@login_required
@require_analysis
def analizar_tendencias():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles. Primero carga un archivo.'}), 400
    
    data = request.json
    try:
        # Usar análisis de patrones en lugar de tendencias
        patrones = prediccion_ia.analizar_patrones(global_df)
        return jsonify({
            'success': True,
            'tendencias': patrones
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SISTEMA DE ALERTAS
@app.route('/alertas/configurar', methods=['POST'])
@login_required
@require_analysis
def configurar_alerta():
    data = request.json
    try:
        tipo = data.get('tipo')
        parametros = data.get('parametros')
        
        # Usar el método correcto de la clase SistemaAlertas
        resultado = sistema_alertas.configurar_alerta(tipo, parametros)
        
        if resultado:
            return jsonify({
                'success': True,
                'mensaje': 'Alerta configurada exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tipo de alerta no válido'
            }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/alertas/verificar', methods=['POST'])
@login_required
@require_analysis
def verificar_alertas():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    try:
        # Usar el método correcto para ejecutar todas las verificaciones
        alertas = sistema_alertas.ejecutar_todas_las_verificaciones(global_df)
        return jsonify({
            'success': True,
            'alertas': alertas
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/alertas/listar', methods=['GET'])
@login_required
@require_analysis
def listar_alertas():
    try:
        # Obtener configuraciones actuales del sistema de alertas
        configuraciones = sistema_alertas.obtener_configuraciones()
        return jsonify({
            'success': True,
            'alertas': configuraciones
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/alertas/eliminar/<tipo_alerta>', methods=['DELETE'])
@login_required
@require_analysis
def eliminar_alerta(tipo_alerta):
    try:
        # Deshabilitar el tipo de alerta
        resultado = sistema_alertas.configurar_alerta(tipo_alerta, {'habilitado': False})
        if resultado:
            return jsonify({
                'success': True,
                'mensaje': f'Alerta {tipo_alerta} deshabilitada exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tipo de alerta no válido'
            }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HISTORIAL Y NOTIFICACIONES
@app.route('/historial/buscar', methods=['POST'])
@login_required
@require_analysis
def buscar_historial():
    data = request.json
    try:
        # Obtener historial del usuario
        resultados = historial_notificaciones.obtener_historial_usuario(current_user.id, limite=50)
        return jsonify({
            'success': True,
            'resultados': resultados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historial/notificaciones', methods=['GET'])
@login_required
@require_analysis
def obtener_notificaciones():
    try:
        notificaciones = historial_notificaciones.obtener_notificaciones_usuario(current_user.id)
        return jsonify({
            'success': True,
            'notificaciones': notificaciones
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historial/marcar-leida/<int:notificacion_id>', methods=['POST'])
@login_required
@require_analysis
def marcar_notificacion_leida(notificacion_id):
    try:
        historial_notificaciones.marcar_notificacion_leida(notificacion_id, current_user.id)
        return jsonify({
            'success': True,
            'mensaje': 'Notificación marcada como leída'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# FILTROS AVANZADOS
@app.route('/filtros/aplicar', methods=['POST'])
@login_required
@require_analysis
def aplicar_filtros_avanzados():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    data = request.json
    try:
        filtros = data.get('filtros', {})
        datos_filtrados = filtros_avanzados.aplicar_filtros_combinados(global_df, filtros)
        
        # Estadísticas básicas
        stats = {
            'total_registros': int(len(datos_filtrados)),
            'total_galones': float(datos_filtrados['CANTIDAD_GALONES'].sum()) if 'CANTIDAD_GALONES' in datos_filtrados.columns else 0,
            'total_consumo': float(datos_filtrados['TOTAL_CONSUMO'].sum()) if 'TOTAL_CONSUMO' in datos_filtrados.columns else 0,
            'vehiculos_unicos': int(datos_filtrados['PLACA'].nunique()) if 'PLACA' in datos_filtrados.columns else 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'total_filtrados': len(datos_filtrados)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/filtros/obtener-opciones', methods=['GET'])
@login_required
@require_analysis
def obtener_opciones_filtros():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    try:
        opciones = filtros_avanzados.obtener_opciones_filtro(global_df)
        return jsonify({
            'success': True,
            'opciones': opciones
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/filtros/exportar', methods=['POST'])
@login_required
@require_analysis
def exportar_datos_filtrados():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    data = request.json
    try:
        filtros = data.get('filtros', {})
        datos_filtrados = filtros_avanzados.aplicar_filtros_combinados(global_df, filtros)
        
        # Generar nombre de archivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f'datos_filtrados_{timestamp}.xlsx'
        ruta_archivo = os.path.join('uploads', nombre_archivo)
        
        # Exportar a Excel
        datos_filtrados.to_excel(ruta_archivo, index=False)
        
        return jsonify({
            'success': True,
            'archivo': nombre_archivo,
            'mensaje': 'Datos exportados exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# MÓDULO DE EMISIONES
@app.route('/emisiones/calcular', methods=['POST'])
@login_required
@require_analysis
def calcular_emisiones():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    data = request.json
    try:
        placa = data.get('placa')
        dependencia = data.get('dependencia')
        
        # Filtrar datos si se especifica vehículo o dependencia
        df_filtrado = global_df.copy()
        if placa:
            df_filtrado = df_filtrado[df_filtrado['PLACA'] == placa]
        if dependencia:
            df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
        
        if df_filtrado.empty:
            return jsonify({'error': 'No hay datos para los filtros especificados'}), 400
        
        # Calcular emisiones
        emisiones = modulo_emisiones.calcular_emisiones_dataframe(df_filtrado)
        estadisticas = modulo_emisiones.generar_estadisticas_emisiones(df_filtrado)
        
        return jsonify({
            'success': True,
            'emisiones': emisiones,
            'estadisticas': estadisticas
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/emisiones/flota', methods=['POST'])
@login_required
@require_analysis
def calcular_emisiones_flota():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    data = request.json
    try:
        dependencia = data.get('dependencia')
        
        # Filtrar por dependencia si se especifica
        df_filtrado = global_df.copy()
        if dependencia:
            df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
        
        # Calcular huella de carbono de la flota
        huella_carbono = modulo_emisiones.calcular_huella_carbono_flota(df_filtrado)
        
        return jsonify({
            'success': True,
            'emisiones': huella_carbono
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/emisiones/reporte', methods=['POST'])
@login_required
@require_analysis
def generar_reporte_emisiones():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    data = request.json
    try:
        dependencia = data.get('dependencia')
        mes = data.get('mes')
        
        # Filtrar datos
        df_filtrado = global_df.copy()
        if dependencia:
            df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
        if mes:
            df_filtrado = df_filtrado[df_filtrado['MES'] == int(mes)]
        
        # Generar reporte PDF
        archivo = modulo_emisiones.generar_reporte_emisiones_pdf(df_filtrado, mes, dependencia)
        
        return jsonify({
            'success': True,
            'archivo': archivo,
            'mensaje': 'Reporte de emisiones generado exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/emisiones/download/<filename>')
@login_required
def download_reporte_emisiones(filename):
    try:
        # Usar la misma lógica que download_report pero para reportes de emisiones
        uploads_dir = os.path.join(os.getcwd(), 'reports')
        file_path = os.path.join(uploads_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Archivo no encontrado'}), 404
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"Reporte_Emisiones_{filename}",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# NUEVA FUNCIONALIDAD: Procesamiento automático de datos cargados
@app.route('/procesar-automatico', methods=['POST'])
@login_required
@require_analysis
def procesar_datos_automatico():
    global global_df
    
    if global_df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 400
    
    try:
        # Entrenar modelo de predicción automáticamente
        resultado_entrenamiento = prediccion_ia.entrenar_modelo(global_df)
        
        # Verificar alertas automáticamente
        alertas = sistema_alertas.ejecutar_todas_las_verificaciones(global_df)
        
        # Registrar procesamiento en historial
        historial_notificaciones.guardar_busqueda(
            current_user.id,
            {'tipo': 'procesamiento_automatico'},
            global_df
        )
        
        return jsonify({
            'success': True,
            'alertas_activas': len(alertas),
            'modelo_entrenado': resultado_entrenamiento is not None,
            'mensaje': 'Procesamiento automático completado'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# FUNCIONALIDAD EXTRA: Resumen completo del sistema
@app.route('/estado-analisis', methods=['GET'])
@login_required
def obtener_estado_analisis():
    global global_df, global_data_analyzed
    
    return jsonify({
        'success': True,
        'datos_cargados': global_df is not None,
        'analisis_realizado': global_data_analyzed,
        'mensaje': 'Análisis completado' if global_data_analyzed else 'Análisis pendiente'
    })

@app.route('/resumen-sistema', methods=['GET'])
@login_required
def resumen_sistema():
    global global_df, global_data_analyzed
    
    try:
        resumen = {
            'datos_cargados': global_df is not None,
            'datos_analizados': global_data_analyzed,
            'registros_total': len(global_df) if global_df is not None else 0,
            'alertas_disponibles': len(sistema_alertas.obtener_configuraciones()) if global_data_analyzed else 0,
            'usuario_actual': current_user.username
        }
        
        if global_df is not None and global_data_analyzed:
            resumen['dependencias_disponibles'] = sorted(global_df['UNIDAD_ORGANICA'].unique().tolist()) if 'UNIDAD_ORGANICA' in global_df.columns else []
            resumen['vehiculos_total'] = global_df['PLACA'].nunique() if 'PLACA' in global_df.columns else 0
            if 'FECHA_INGRESO_VALE' in global_df.columns:
                resumen['fecha_inicio'] = global_df['FECHA_INGRESO_VALE'].min().strftime('%Y-%m-%d')
                resumen['fecha_fin'] = global_df['FECHA_INGRESO_VALE'].max().strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'resumen': resumen
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('reports', exist_ok=True)  # Para reportes de emisiones
    app.run(debug=True)