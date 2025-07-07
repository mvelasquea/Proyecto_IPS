"""
Sistema de Análisis de Consumo de Combustible Municipalidad de Ate
"""

"""
Sistema de Análisis de Consumo de Combustible Municipalidad de Ate
Versión Mejorada - Soluciona problemas con gráficos y PDF
"""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_analysis_results(df):
    """Wrapper para usar en la API"""
    df_procesado = procesar_datos(df)
    return detectar_anomalias(df_procesado)

# Configuración inicial
def configurar_entorno():
    try:
        print("Iniciando configuración del entorno...")
        # Configura el entorno de visualización y rutas
        plt.style.use('ggplot')
        sns.set_palette("Set2")
        # Configuración de pandas para mostrar las tablas con los resultados
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_colwidth', 30)
        
        # Ruta del script actual
        if '__file__' in globals():
            script_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            script_dir = os.getcwd()
        print(f"Directorio de trabajo configurado: {script_dir}")
        
        # Crear directorio para gráficos si no existe
        plot_dir = os.path.join(script_dir, "graficos_analisis")
        os.makedirs(plot_dir, exist_ok=True)
        print(f"Directorio para gráficos: {plot_dir}")
        
        return script_dir
    except Exception as e:
        print(f"Error en configurar_entorno: {str(e)}")
        return os.getcwd()

# Carga de datos 
def cargar_datos_excel(script_dir):
    try:
        print("\nIniciando carga de datos...")
        # Lista de nombres posibles del archivo dataset
        nombres_posibles = [
            "DatasetGASTO_COMBUSTIBLE_2022.xlsx",
            "DatasetGASTO_COMBUSTIBLE_2022.XLSX",
            "datasetgasto_combustible_2022.xlsx",
            "DatasetGastoCombustible2022.xlsx",
            "DATASETGASTOCOMBUSTIBLE2022.XLSX"
        ]
        
        # Variable y bucle para encontrar la ruta del archivo e intentar cargarlo
        df = None
        for nombre_archivo in nombres_posibles:
            ruta_archivo = os.path.join(script_dir, nombre_archivo)
            if os.path.exists(ruta_archivo):
                try:
                    print(f"Intentando cargar: {ruta_archivo}")
                    # Leer archivo Excel
                    df = pd.read_excel(ruta_archivo)
                    print("¡Archivo Excel cargado exitosamente!")
                    print(f"Registros cargados: {len(df)}")
                    print(f"Columnas: {list(df.columns)}")
                    
                    # Mostrar muestra inicial de datos para diagnóstico
                    print("\nMuestra inicial de datos:")
                    print(df.iloc[:3, :5])
                    
                    break
                except Exception as e:
                    print(f"Error al cargar {ruta_archivo}: {str(e)}")
        
        # En caso que no se encuentre el archivo 
        if df is None:
            print("\nNo se pudo cargar el archivo. Posibles soluciones:")
            print("1. Asegúrese que el archivo Excel (.xlsx) está en la misma carpeta que este script")
            print("2. Verifique que el nombre coincide con: DatasetGASTO_COMBUSTIBLE_2022.xlsx")
            print("3. Revise que el archivo no esté dañado o vacío")
            print("4. Si el archivo tiene varias hojas, especifique el nombre de la hoja")
            
            # Intentar con ruta absoluta manual
            ruta_manual = input("\nIngrese la ruta completa del archivo Excel: ").strip()
            try:
                # Preguntar por el nombre de la hoja si hay varias
                if os.path.exists(ruta_manual):
                    xl = pd.ExcelFile(ruta_manual)
                    # Si hay más de una hoja en el dataset le pide al usuario que elija la hoja que usará
                    if len(xl.sheet_names) > 1:
                        print(f"\nHojas disponibles: {', '.join(xl.sheet_names)}")
                        nombre_hoja = input("Ingrese el nombre de la hoja a cargar: ").strip()
                        df = pd.read_excel(ruta_manual, sheet_name=nombre_hoja)
                    else:
                        df = pd.read_excel(ruta_manual)
                    print("¡Archivo cargado usando ruta manual!")
                else:
                    print("¡El archivo no existe en la ruta especificada!")
                    return None
            except Exception as e:
                print(f"Error crítico: {str(e)}")
                return None

        # Procesamiento de datos posterior si se cargó el archivo
        if df is not None:
            return procesar_datos(df)
        return None
    except Exception as e:
        print(f"Error en cargar_datos_excel: {str(e)}")
        return None

def procesar_datos(df):
    """
    Procesa y limpia los datos del DataFrame
    """
    try:
        # Hacer una copia para no modificar el original
        df_procesado = df.copy()
        
        # Mapear columnas comunes a nombres estándar
        column_mapping = {
            'FECHA_INGRESO_VALE': 'fecha',
            'Fecha': 'fecha',
            'NOMBRE_PLACA': 'placa',
            'Vehículo': 'placa',
            'Placa': 'placa',
            'GALONES': 'galones',
            'Galones': 'galones',
            'KILOMETRAJE': 'kilometraje',
            'Kilometraje': 'kilometraje',
            'COSTO_TOTAL': 'costo',
            'Costo': 'costo',
            'UNIDAD_ORGANICA': 'unidad',
            'Unidad': 'unidad'
        }
        
        # Renombrar columnas
        df_procesado = df_procesado.rename(columns=column_mapping)
        
        # Verificar columnas esenciales
        columnas_requeridas = ['fecha', 'placa', 'galones']
        columnas_existentes = df_procesado.columns.tolist()
        
        for col in columnas_requeridas:
            if col not in columnas_existentes:
                raise ValueError(f"Columna requerida '{col}' no encontrada. Columnas disponibles: {columnas_existentes}")
        
        # Procesar fecha
        if 'fecha' in df_procesado.columns:
            df_procesado['fecha'] = pd.to_datetime(df_procesado['fecha'], errors='coerce')
            df_procesado = df_procesado.dropna(subset=['fecha'])
        
        # Procesar columnas numéricas
        columnas_numericas = ['galones', 'kilometraje', 'costo']
        for col in columnas_numericas:
            if col in df_procesado.columns:
                df_procesado[col] = pd.to_numeric(df_procesado[col], errors='coerce')
        
        # Eliminar filas con valores nulos en columnas críticas
        df_procesado = df_procesado.dropna(subset=['galones'])
        
        # Filtrar valores negativos o cero
        df_procesado = df_procesado[df_procesado['galones'] > 0]
        
        # Agregar columnas derivadas
        if 'fecha' in df_procesado.columns:
            df_procesado['año'] = df_procesado['fecha'].dt.year
            df_procesado['mes'] = df_procesado['fecha'].dt.month
            df_procesado['dia_semana'] = df_procesado['fecha'].dt.dayofweek
        
        # Calcular rendimiento si es posible
        if 'kilometraje' in df_procesado.columns and 'galones' in df_procesado.columns:
            df_procesado['rendimiento'] = df_procesado['kilometraje'] / df_procesado['galones']
            df_procesado['rendimiento'] = df_procesado['rendimiento'].replace([np.inf, -np.inf], np.nan)
        
        print(f"Datos procesados: {len(df_procesado)} registros")
        return df_procesado
        
    except Exception as e:
        print(f"Error procesando datos: {str(e)}")
        raise

def detectar_anomalias(df):
    """
    Detecta anomalías en los datos usando múltiples métodos
    """
    try:
        df_anomalias = df.copy()
        
        # Inicializar columnas de detección
        df_anomalias['anomalia_consumo'] = False
        df_anomalias['anomalia_frecuencia'] = False
        df_anomalias['anomalia_rendimiento'] = False
        df_anomalias['score_anomalia'] = 0.0
        df_anomalias['tipo_anomalia'] = 'Normal'
        
        # 1. Detección por consumo excesivo
        if 'galones' in df_anomalias.columns:
            Q1 = df_anomalias['galones'].quantile(0.25)
            Q3 = df_anomalias['galones'].quantile(0.75)
            IQR = Q3 - Q1
            umbral_superior = Q3 + 1.5 * IQR
            
            df_anomalias['anomalia_consumo'] = df_anomalias['galones'] > umbral_superior
        
        # 2. Detección por frecuencia de repostaje
        if 'placa' in df_anomalias.columns and 'fecha' in df_anomalias.columns:
            # Calcular días entre repostajes por vehículo
            df_freq = df_anomalias.groupby('placa')['fecha'].apply(
                lambda x: x.sort_values().diff().dt.days.mean()
            ).reset_index()
            df_freq.columns = ['placa', 'dias_promedio']
            
            # Detectar frecuencia anormal (muy frecuente)
            umbral_frecuencia = df_freq['dias_promedio'].quantile(0.1)  # 10% más frecuente
            vehiculos_frecuentes = df_freq[df_freq['dias_promedio'] < umbral_frecuencia]['placa'].tolist()
            
            df_anomalias['anomalia_frecuencia'] = df_anomalias['placa'].isin(vehiculos_frecuentes)
        
        # 3. Detección por rendimiento anormal
        if 'rendimiento' in df_anomalias.columns:
            # Filtrar valores válidos
            rendimiento_valido = df_anomalias['rendimiento'].dropna()
            if len(rendimiento_valido) > 0:
                Q1_rend = rendimiento_valido.quantile(0.25)
                Q3_rend = rendimiento_valido.quantile(0.75)
                IQR_rend = Q3_rend - Q1_rend
                umbral_inf_rend = Q1_rend - 1.5 * IQR_rend
                umbral_sup_rend = Q3_rend + 1.5 * IQR_rend
                
                df_anomalias['anomalia_rendimiento'] = (
                    (df_anomalias['rendimiento'] < umbral_inf_rend) |
                    (df_anomalias['rendimiento'] > umbral_sup_rend)
                )
        
        # 4. Usar Isolation Forest para detección avanzada
        columnas_numericas = ['galones']
        if 'kilometraje' in df_anomalias.columns:
            columnas_numericas.append('kilometraje')
        if 'costo' in df_anomalias.columns:
            columnas_numericas.append('costo')
        
        # Preparar datos para Isolation Forest
        datos_ml = df_anomalias[columnas_numericas].dropna()
        
        if len(datos_ml) > 10:  # Mínimo de datos para ML
            # Normalizar datos
            scaler = StandardScaler()
            datos_normalizados = scaler.fit_transform(datos_ml)
            
            # Aplicar Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomalias_ml = iso_forest.fit_predict(datos_normalizados)
            scores_ml = iso_forest.score_samples(datos_normalizados)
            
            # Asignar scores a los registros correspondientes
            indices_validos = datos_ml.index
            df_anomalias.loc[indices_validos, 'score_anomalia'] = scores_ml
            df_anomalias.loc[indices_validos, 'anomalia_ml'] = (anomalias_ml == -1)
        
        # 5. Consolidar detección de anomalías
        df_anomalias['es_anomalia'] = (
            df_anomalias['anomalia_consumo'] |
            df_anomalias['anomalia_frecuencia'] |
            df_anomalias['anomalia_rendimiento']
        )
        
        if 'anomalia_ml' in df_anomalias.columns:
            df_anomalias['es_anomalia'] = df_anomalias['es_anomalia'] | df_anomalias['anomalia_ml']
        
        # Clasificar tipos de anomalía
        def clasificar_anomalia(row):
            if not row['es_anomalia']:
                return 'Normal'
            
            tipos = []
            if row['anomalia_consumo']:
                tipos.append('Consumo Excesivo')
            if row['anomalia_frecuencia']:
                tipos.append('Frecuencia Alta')
            if row['anomalia_rendimiento']:
                tipos.append('Rendimiento Anormal')
            
            return '; '.join(tipos) if tipos else 'Anomalía Detectada'
        
        df_anomalias['tipo_anomalia'] = df_anomalias.apply(clasificar_anomalia, axis=1)
        
        # Filtrar solo anomalías para el resultado
        anomalias_detectadas = df_anomalias[df_anomalias['es_anomalia']].copy()
        
        print(f"Anomalías detectadas: {len(anomalias_detectadas)} de {len(df_anomalias)} registros")
        
        return anomalias_detectadas
        
    except Exception as e:
        print(f"Error detectando anomalías: {str(e)}")
        # Retornar DataFrame vacío en caso de error
        return pd.DataFrame()

def generar_estadisticas(df):
    """
    Genera estadísticas descriptivas del análisis
    """
    try:
        stats = {
            'total_registros': len(df),
            'periodo_analisis': {
                'inicio': df['fecha'].min().strftime('%Y-%m-%d') if 'fecha' in df.columns else 'N/A',
                'fin': df['fecha'].max().strftime('%Y-%m-%d') if 'fecha' in df.columns else 'N/A'
            },
            'vehiculos_unicos': df['placa'].nunique() if 'placa' in df.columns else 0,
            'consumo_total': df['galones'].sum() if 'galones' in df.columns else 0,
            'consumo_promedio': df['galones'].mean() if 'galones' in df.columns else 0,
            'costo_total': df['costo'].sum() if 'costo' in df.columns else 0
        }
        
        return stats
        
    except Exception as e:
        print(f"Error generando estadísticas: {str(e)}")
        return {}