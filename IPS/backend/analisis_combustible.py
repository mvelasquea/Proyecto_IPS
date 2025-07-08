import os
import pandas as pd
import numpy as np
import re
from fpdf import FPDF
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurar matplotlib para evitar problemas con GUI
plt.switch_backend('Agg')


def procesar_datos(df):
    # Realiza el procesamiento de datos después de cargar
    print("\nProcesando datos...")
    
    # Convertir fechas y verificación si existen
    date_cols = ['FECHA_INGRESO_VALE', 'FECHA_SOAT', 'FECHA_CORTE']
    for col in date_cols:
        if col in df.columns:
            try:
                # Intentar convertir formatos de fecha
                if df[col].dtype == 'object':
                    # Intentar múltiples formatos
                    df[col] = pd.to_datetime(df[col], errors='coerce', format='%d/%m/%Y')
                    if df[col].isnull().all():
                        df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y-%m-%d')
                else:
                    # Si es numérico, asumir formato de fecha de Excel
                    df[col] = pd.to_datetime(df[col], unit='D', origin='1899-12-30', errors='coerce')
            except Exception as e:
                print(f"Error al convertir {col}: {str(e)}")
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Manejar valores numéricos
    num_cols = ['KM_RECORRIDO', 'CANTIDAD_GALONES', 'PRECIO', 'TOTAL_CONSUMO']
    for col in num_cols:
        if col in df.columns:
            try:
                # Convertir a string y limpiar antes de convertir a numérico
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                print(f"Error al convertir {col}: {str(e)}")
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Crear valor eficiencia 
    if 'KM_RECORRIDO' in df.columns and 'CANTIDAD_GALONES' in df.columns:
        # Evitar división por cero
        df['EFICIENCIA'] = np.where(df['CANTIDAD_GALONES'] > 0, 
                                   df['KM_RECORRIDO'] / df['CANTIDAD_GALONES'], 
                                   np.nan)
        # Manejar infinitos y valores extremos
        df['EFICIENCIA'] = df['EFICIENCIA'].replace([np.inf, -np.inf], np.nan)
        df.loc[df['EFICIENCIA'] > 100, 'EFICIENCIA'] = np.nan
        
    # Calcular el costo por recorrido
    if 'TOTAL_CONSUMO' in df.columns and 'KM_RECORRIDO' in df.columns:
        # Evitar división por cero
        df['COSTO_POR_KM'] = np.where(df['KM_RECORRIDO'] > 0, 
                                     df['TOTAL_CONSUMO'] / df['KM_RECORRIDO'], 
                                     np.nan)
        df['COSTO_POR_KM'] = df['COSTO_POR_KM'].replace([np.inf, -np.inf], np.nan)
        df.loc[df['COSTO_POR_KM'] > 100, 'COSTO_POR_KM'] = np.nan
    
    # Extraer características de fecha
    if 'FECHA_INGRESO_VALE' in df.columns:
        df['DIA_SEMANA'] = df['FECHA_INGRESO_VALE'].dt.dayofweek
        df['MES'] = df['FECHA_INGRESO_VALE'].dt.month
        df['ES_FIN_DE_SEMANA'] = df['FECHA_INGRESO_VALE'].dt.dayofweek.isin([5, 6]).astype(int)
    
    print(f"\nDatos procesados: {len(df)} registros")
    return df

def aplicar_filtros(df, mes, dependencia):
    # Aplica los filtros seleccionados por el usuario
    try:
        # Verificar si los campos existen antes de filtrar
        if 'MES' not in df.columns or 'UNIDAD_ORGANICA' not in df.columns:
            print("Error: Columnas requeridas para filtrar no existen")
            return pd.DataFrame()
            
        df_filtrado = df[
            (df['MES'] == int(mes)) & 
            (df['UNIDAD_ORGANICA'] == dependencia)
        ].copy()
        
        print(f"\nRegistros encontrados: {len(df_filtrado)}")
        return df_filtrado
    except Exception as e:
        print(f"Error al aplicar filtros: {str(e)}")
        return pd.DataFrame()

def detectar_anomalias(df):
    # Detecta anomalías en los datos filtrados
    if df.empty or len(df) < 10:  # Necesitamos un mínimo de registros
        print("Datos insuficientes para detección de anomalías")
        if not df.empty:
            df['ANOMALIA'] = 0
            df['SCORE_ANOMALIA'] = 0
            df['NIVEL_RIESGO'] = 'Bajo'
        return df
    
    # Seleccionamos características relevantes del dataset
    features = [
        'TIPO_COMBUSTIBLE', 
        'KM_RECORRIDO',
        'CANTIDAD_GALONES',
        'PRECIO',
        'TOTAL_CONSUMO',
        'EFICIENCIA',
        'COSTO_POR_KM',
        'DIA_SEMANA'
    ]
    
    # Filtrar solo datos disponibles y con valores válidos
    features = [f for f in features if f in df.columns]
    df_model = df[features].copy().dropna()
    
    # Verificar si tenemos datos suficientes para modelar
    if df_model.empty or len(df_model) < 10:
        print("\nAdvertencia: No hay características suficientes para detección de anomalías")
        df['ANOMALIA'] = 0
        df['SCORE_ANOMALIA'] = 0
        df['NIVEL_RIESGO'] = 'Bajo'
        return df
    
    # Separar variables numéricas y categóricas
    numeric_features = df_model.select_dtypes(include=np.number).columns.tolist()
    categorical_features = df_model.select_dtypes(include='object').columns.tolist()
    
    # Preparar la pipeline para el procesamiento de datos
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    try:
        # Procesamiento
        X = preprocessor.fit_transform(df_model)
        
        # Detección de anomalías
        iso_forest = IsolationForest(n_estimators=150, contamination=0.05, random_state=42)
        iso_pred = iso_forest.fit_predict(X)
        
        # Añadir resultados al dataframe
        # Primero creamos un DataFrame temporal con los índices de df_model
        temp_df = pd.DataFrame(index=df_model.index)
        temp_df['ANOMALIA'] = np.where(iso_pred == -1, 1, 0)
        temp_df['SCORE_ANOMALIA'] = iso_forest.decision_function(X) * -1
        
        # Luego unimos con el df original
        df = df.join(temp_df, how='left')
        
        # Rellenar valores faltantes (registros que no estaban en df_model)
        df['ANOMALIA'] = df['ANOMALIA'].fillna(0)
        df['SCORE_ANOMALIA'] = df['SCORE_ANOMALIA'].fillna(0)
        
        # Clasificación de nivel de riesgo
        df['NIVEL_RIESGO'] = pd.cut(df['SCORE_ANOMALIA'],
                                    bins=[-1, 0.3, 0.6, 0.9, 1.1],
                                    labels=['Bajo', 'Moderado', 'Alto', 'Critico'],
                                    include_lowest=True)
    # Manejo de errores en la detección
    except Exception as e:
        print(f"Error en detección de anomalías: {str(e)}")
        df['ANOMALIA'] = 0
        df['SCORE_ANOMALIA'] = 0
        df['NIVEL_RIESGO'] = 'Bajo'
    
    return df

def crear_graficos_pdf(df, mes, dependencia):
    """Crea gráficos para incluir en el PDF"""
    graficos = {}
    
    # Crear directorio temporal para gráficos
    temp_dir = 'temp_graficos'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Configurar estilo de matplotlib
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # 1. Gráfico de eficiencia (histograma)
    if 'EFICIENCIA' in df.columns:
        plt.figure(figsize=(10, 6))
        eficiencia = df['EFICIENCIA'].dropna()
        if not eficiencia.empty:
            plt.hist(eficiencia, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            plt.axvline(eficiencia.mean(), color='red', linestyle='--', linewidth=2, label=f'Promedio: {eficiencia.mean():.2f}')
            plt.xlabel('Eficiencia (km/gal)')
            plt.ylabel('Frecuencia')
            plt.title('Distribución de Eficiencia de Combustible')
            plt.legend()
            plt.grid(True, alpha=0.3)
            grafico_path = os.path.join(temp_dir, 'eficiencia_hist.png')
            plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
            plt.close()
            graficos['eficiencia_hist'] = grafico_path
    
    # 2. Gráfico de consumo por día de la semana
    if 'DIA_SEMANA' in df.columns and 'TOTAL_CONSUMO' in df.columns:
        plt.figure(figsize=(12, 6))
        dias = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 
                4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        df['DIA_NOMBRE'] = df['DIA_SEMANA'].map(dias)
        consumo_diario = df.groupby('DIA_NOMBRE')['TOTAL_CONSUMO'].sum()
        
        # Reordenar días de la semana
        orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        consumo_diario = consumo_diario.reindex(orden_dias, fill_value=0)
        
        bars = plt.bar(consumo_diario.index, consumo_diario.values, color='lightcoral', alpha=0.8)
        plt.xlabel('Día de la Semana')
        plt.ylabel('Consumo Total (S/)')
        plt.title('Consumo de Combustible por Día de la Semana')
        plt.xticks(rotation=45)
        
        # Agregar valores en las barras
        for bar, valor in zip(bars, consumo_diario.values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(consumo_diario.values)*0.01, 
                    f'S/ {valor:,.0f}', ha='center', va='bottom', fontsize=9)
        
        plt.grid(True, alpha=0.3)
        grafico_path = os.path.join(temp_dir, 'consumo_diario.png')
        plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
        plt.close()
        graficos['consumo_diario'] = grafico_path
    
    # 3. Gráfico de anomalías por nivel de riesgo
    if 'NIVEL_RIESGO' in df.columns:
        plt.figure(figsize=(10, 8))
        distribucion = df['NIVEL_RIESGO'].value_counts()
        
        # Crear gráfico de pastel
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        wedges, texts, autotexts = plt.pie(distribucion.values, labels=distribucion.index, 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        
        # Mejorar la presentación
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.title('Distribución de Anomalías por Nivel de Riesgo', fontsize=14, fontweight='bold')
        grafico_path = os.path.join(temp_dir, 'anomalias_pie.png')
        plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
        plt.close()
        graficos['anomalias_pie'] = grafico_path
    
    # 4. Gráfico de dispersión: Eficiencia vs Consumo
    if 'EFICIENCIA' in df.columns and 'TOTAL_CONSUMO' in df.columns:
        plt.figure(figsize=(10, 6))
        
        # Separar datos normales y anómalos
        normales = df[df['ANOMALIA'] == 0] if 'ANOMALIA' in df.columns else df
        anomalos = df[df['ANOMALIA'] == 1] if 'ANOMALIA' in df.columns else pd.DataFrame()
        
        plt.scatter(normales['EFICIENCIA'], normales['TOTAL_CONSUMO'], 
                   alpha=0.6, color='blue', label='Normal', s=50)
        
        if not anomalos.empty:
            plt.scatter(anomalos['EFICIENCIA'], anomalos['TOTAL_CONSUMO'], 
                       alpha=0.8, color='red', label='Anomalía', s=100, marker='x')
        
        plt.xlabel('Eficiencia (km/gal)')
        plt.ylabel('Consumo Total (S/)')
        plt.title('Relación entre Eficiencia y Consumo Total')
        plt.legend()
        plt.grid(True, alpha=0.3)
        grafico_path = os.path.join(temp_dir, 'eficiencia_consumo.png')
        plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
        plt.close()
        graficos['eficiencia_consumo'] = grafico_path
    
    # 5. Gráfico de tendencia mensual (si hay datos de fecha)
    if 'FECHA_INGRESO_VALE' in df.columns:
        plt.figure(figsize=(12, 6))
        df_temp = df.copy()
        df_temp['FECHA'] = pd.to_datetime(df_temp['FECHA_INGRESO_VALE'])
        
        # Agrupar por día y calcular consumo total
        consumo_temporal = df_temp.groupby(df_temp['FECHA'].dt.date)['TOTAL_CONSUMO'].sum().reset_index()
        
        if len(consumo_temporal) > 1:
            plt.plot(consumo_temporal['FECHA'], consumo_temporal['TOTAL_CONSUMO'], 
                    marker='o', linewidth=2, markersize=6, color='green')
            plt.xlabel('Fecha')
            plt.ylabel('Consumo Total (S/)')
            plt.title('Tendencia de Consumo a lo largo del Tiempo')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            grafico_path = os.path.join(temp_dir, 'tendencia_temporal.png')
            plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
            plt.close()
            graficos['tendencia_temporal'] = grafico_path
    
    # 6. Top 10 vehículos con mayor consumo
    if 'PLACA' in df.columns:
        plt.figure(figsize=(12, 8))
        consumo_por_vehiculo = df.groupby('PLACA')['TOTAL_CONSUMO'].sum().sort_values(ascending=False).head(10)
        
        bars = plt.barh(range(len(consumo_por_vehiculo)), consumo_por_vehiculo.values, color='orange', alpha=0.8)
        plt.yticks(range(len(consumo_por_vehiculo)), consumo_por_vehiculo.index)
        plt.xlabel('Consumo Total (S/)')
        plt.title('Top 10 Vehículos con Mayor Consumo de Combustible')
        plt.gca().invert_yaxis()
        
        # Agregar valores en las barras
        for i, (bar, valor) in enumerate(zip(bars, consumo_por_vehiculo.values)):
            plt.text(bar.get_width() + max(consumo_por_vehiculo.values)*0.01, bar.get_y() + bar.get_height()/2, 
                    f'S/ {valor:,.0f}', va='center', fontsize=9)
        
        plt.grid(True, alpha=0.3)
        grafico_path = os.path.join(temp_dir, 'top_vehiculos.png')
        plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
        plt.close()
        graficos['top_vehiculos'] = grafico_path
    
    return graficos
    """Genera un reporte en PDF con gráficos y tablas de anomalías"""
    try:
        # Configurar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # Título
        pdf.cell(0, 10, f'Reporte de Anomalías - {dependencia} - Mes {mes}', 0, 1, 'C')
        pdf.ln(10)
        
        # Estadísticas resumen
        pdf.set_font('Arial', '', 12)
        if 'ANOMALIA' in df.columns:
            total_anomalias = df['ANOMALIA'].sum()
            total_consumo = df['TOTAL_CONSUMO'].sum() if 'TOTAL_CONSUMO' in df.columns else 0
            consumo_riesgo = total_consumo * 0.3  # Estimado del 30% en riesgo
            
            pdf.cell(0, 10, f'Total de registros analizados: {len(df)}', 0, 1)
            pdf.cell(0, 10, f'Total de anomalías detectadas: {total_anomalias}', 0, 1)
            pdf.cell(0, 10, f'Consumo total en riesgo estimado: S/ {consumo_riesgo:,.2f}', 0, 1)
            pdf.ln(15)
        
        # Gráfico de eficiencia (simulado con tabla)
        if 'EFICIENCIA' in df.columns:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Eficiencia de Combustible (km/gal)', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Calcular estadísticas
            eficiencia = df['EFICIENCIA'].dropna()
            if not eficiencia.empty:
                min_eff = eficiencia.min()
                avg_eff = eficiencia.mean()
                max_eff = eficiencia.max()
                
                # Crear tabla de eficiencia
                pdf.cell(60, 10, 'Métrica', 1)
                pdf.cell(60, 10, 'Valor (km/gal)', 1, 1)
                pdf.cell(60, 10, 'Mínimo', 1)
                pdf.cell(60, 10, f'{min_eff:.2f}', 1, 1)
                pdf.cell(60, 10, 'Promedio', 1)
                pdf.cell(60, 10, f'{avg_eff:.2f}', 1, 1)
                pdf.cell(60, 10, 'Máximo', 1)
                pdf.cell(60, 10, f'{max_eff:.2f}', 1, 1)
                pdf.ln(15)
        
        # Gráfico de consumo por día (simulado con tabla)
        if 'DIA_SEMANA' in df.columns and 'TOTAL_CONSUMO' in df.columns:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Consumo por Día de la Semana', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Agrupar por día
            dias = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 
                    4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
            df['DIA_NOMBRE'] = df['DIA_SEMANA'].map(dias)
            consumo_diario = df.groupby('DIA_NOMBRE')['TOTAL_CONSUMO'].sum()
            
            # Crear tabla de consumo diario
            pdf.cell(80, 10, 'Día', 1)
            pdf.cell(80, 10, 'Consumo Total (S/)', 1, 1)
            
            for dia, consumo in consumo_diario.items():
                pdf.cell(80, 10, dia, 1)
                pdf.cell(80, 10, f'S/ {consumo:,.2f}', 1, 1)
            pdf.ln(15)
        
        # Distribución de anomalías
        if 'NIVEL_RIESGO' in df.columns:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Distribución de Anomalías por Nivel de Riesgo', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Contar anomalías por nivel
            distribucion = df['NIVEL_RIESGO'].value_counts()
            
            # Crear tabla de distribución
            pdf.cell(80, 10, 'Nivel de Riesgo', 1)
            pdf.cell(80, 10, 'Cantidad de Anomalías', 1, 1)
            
            for nivel, cantidad in distribucion.items():
                pdf.cell(80, 10, str(nivel), 1)
                pdf.cell(80, 10, str(cantidad), 1, 1)
            pdf.ln(15)
        
        # Tabla de vehículos con anomalías
        if 'PLACA' in df.columns and 'ANOMALIA' in df.columns:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Vehículos con Anomalías', 0, 1)
            pdf.set_font('Arial', '', 8)
            
            # Filtrar solo vehículos con anomalías y agrupar
            vehiculos = df[df['ANOMALIA'] == 1].groupby('PLACA').agg({
                'ANOMALIA': 'count',
                'TOTAL_CONSUMO': 'sum',
                'EFICIENCIA': 'mean',
                'NIVEL_RIESGO': lambda x: x.value_counts().idxmax()
            }).sort_values('ANOMALIA', ascending=False).head(10)
            
            # Encabezados de tabla
            col_widths = [30, 20, 30, 30, 30]
            headers = ['Placa', 'Anomalías', 'Consumo Total', 'Eficiencia', 'Nivel Riesgo']
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1)
            pdf.ln()
            
            # Datos de tabla
            for placa, row in vehiculos.iterrows():
                pdf.cell(col_widths[0], 10, str(placa), 1)
                pdf.cell(col_widths[1], 10, str(row['ANOMALIA']), 1)
                pdf.cell(col_widths[2], 10, f"S/ {row['TOTAL_CONSUMO']:,.2f}", 1)
                pdf.cell(col_widths[3], 10, f"{row['EFICIENCIA']:.2f} km/gal", 1)
                pdf.cell(col_widths[4], 10, str(row['NIVEL_RIESGO']), 1)
                pdf.ln()
        
        # Pie de página
        pdf.ln(20)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, f'Reporte generado el: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        pdf.cell(0, 10, 'Sistema de Análisis de Combustible - Municipalidad de Ate', 0, 1)
        
        # Guardar archivo
        os.makedirs('uploads', exist_ok=True)
        nombre_archivo = f"reporte_{dependencia}_mes{mes}.pdf"
        nombre_archivo = re.sub(r'[^a-zA-Z0-9_.]', '', nombre_archivo)  # Limpiar nombre
        ruta_completa = os.path.join('uploads', nombre_archivo)
        pdf.output(ruta_completa)
        
        return nombre_archivo
    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        return None
    
def generar_reporte_anomalias(df, mes, dependencia):
    """Función que decide qué tipo de reporte generar (PDF por defecto)"""
    return generar_reporte_pdf(df, mes, dependencia)

def generar_reporte_pdf(df, mes, dependencia):
    """Genera un reporte en PDF mejorado con gráficos y tablas detalladas"""
    try:
        # Crear gráficos
        graficos = crear_graficos_pdf(df, mes, dependencia)
        
        # Configurar PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Página 1: Portada y resumen ejecutivo
        pdf.add_page()
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 20, 'REPORTE DE ANÁLISIS DE COMBUSTIBLE', 0, 1, 'C')
        pdf.ln(5)
        
        # Información general
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Dependencia: {dependencia}', 0, 1)
        pdf.cell(0, 10, f'Mes analizado: {mes}', 0, 1)
        pdf.cell(0, 10, f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
        pdf.ln(10)
        
        # Resumen ejecutivo
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'RESUMEN EJECUTIVO', 0, 1)
        pdf.ln(5)
        
        # Calcular estadísticas principales
        total_registros = len(df)
        total_consumo = df['TOTAL_CONSUMO'].sum() if 'TOTAL_CONSUMO' in df.columns else 0
        total_galones = df['CANTIDAD_GALONES'].sum() if 'CANTIDAD_GALONES' in df.columns else 0
        total_km = df['KM_RECORRIDO'].sum() if 'KM_RECORRIDO' in df.columns else 0
        total_anomalias = df['ANOMALIA'].sum() if 'ANOMALIA' in df.columns else 0
        eficiencia_promedio = df['EFICIENCIA'].mean() if 'EFICIENCIA' in df.columns else 0
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'• Total de registros analizados: {total_registros:,}', 0, 1)
        pdf.cell(0, 8, f'• Total de anomalías detectadas: {total_anomalias}', 0, 1)
        pdf.cell(0, 8, f'• Consumo total: S/ {total_consumo:,.2f}', 0, 1)
        pdf.cell(0, 8, f'• Galones consumidos: {total_galones:,.2f}', 0, 1)
        pdf.cell(0, 8, f'• Kilómetros recorridos: {total_km:,.2f}', 0, 1)
        pdf.cell(0, 8, f'• Eficiencia promedio: {eficiencia_promedio:.2f} km/gal', 0, 1)
        
        # Porcentaje de anomalías
        porcentaje_anomalias = (total_anomalias / total_registros * 100) if total_registros > 0 else 0
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        if porcentaje_anomalias > 10:
            pdf.set_text_color(255, 0, 0)  # Rojo para alto riesgo
            pdf.cell(0, 8, f'⚠️ ALERTA: {porcentaje_anomalias:.1f}% de los registros presentan anomalías', 0, 1)
        elif porcentaje_anomalias > 5:
            pdf.set_text_color(255, 165, 0)  # Naranja para riesgo moderado
            pdf.cell(0, 8, f'⚠️ ATENCIÓN: {porcentaje_anomalias:.1f}% de los registros presentan anomalías', 0, 1)
        else:
            pdf.set_text_color(0, 128, 0)  # Verde para bajo riesgo
            pdf.cell(0, 8, f'✅ NORMAL: {porcentaje_anomalias:.1f}% de los registros presentan anomalías', 0, 1)
        
        pdf.set_text_color(0, 0, 0)  # Volver a negro
        
        # Página 2: Gráfico de eficiencia
        if 'eficiencia_hist' in graficos:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'ANÁLISIS DE EFICIENCIA DE COMBUSTIBLE', 0, 1)
            pdf.ln(5)
            
            # Insertar gráfico de eficiencia
            pdf.image(graficos['eficiencia_hist'], x=10, y=40, w=190)
            
            # Análisis de eficiencia
            pdf.ln(120)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Análisis de Eficiencia:', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            eficiencia = df['EFICIENCIA'].dropna()
            if not eficiencia.empty:
                pdf.cell(0, 6, f'• Eficiencia mínima: {eficiencia.min():.2f} km/gal', 0, 1)
                pdf.cell(0, 6, f'• Eficiencia máxima: {eficiencia.max():.2f} km/gal', 0, 1)
                pdf.cell(0, 6, f'• Eficiencia promedio: {eficiencia.mean():.2f} km/gal', 0, 1)
                pdf.cell(0, 6, f'• Desviación estándar: {eficiencia.std():.2f} km/gal', 0, 1)
                
                if eficiencia.mean() < 8:
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(0, 6, '⚠️ La eficiencia promedio está por debajo del estándar (8 km/gal)', 0, 1)
                elif eficiencia.mean() > 12:
                    pdf.set_text_color(0, 128, 0)
                    pdf.cell(0, 6, '✅ Excelente eficiencia promedio de combustible', 0, 1)
                else:
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 6, '✅ Eficiencia promedio dentro del rango normal', 0, 1)
                
                pdf.set_text_color(0, 0, 0)
        
        # Página 3: Consumo por día de la semana
        if 'consumo_diario' in graficos:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'ANÁLISIS DE CONSUMO POR DÍA DE LA SEMANA', 0, 1)
            pdf.ln(5)
            
            # Insertar gráfico de consumo diario
            pdf.image(graficos['consumo_diario'], x=10, y=40, w=190)
            
            # Análisis del consumo diario
            pdf.ln(120)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Análisis del Consumo Diario:', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            if 'DIA_SEMANA' in df.columns:
                dias = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 
                        4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
                df['DIA_NOMBRE'] = df['DIA_SEMANA'].map(dias)
                consumo_diario = df.groupby('DIA_NOMBRE')['TOTAL_CONSUMO'].sum()
                
                dia_mayor_consumo = consumo_diario.idxmax()
                dia_menor_consumo = consumo_diario.idxmin()
                
                pdf.cell(0, 6, f'• Día con mayor consumo: {dia_mayor_consumo} (S/ {consumo_diario.max():,.2f})', 0, 1)
                pdf.cell(0, 6, f'• Día con menor consumo: {dia_menor_consumo} (S/ {consumo_diario.min():,.2f})', 0, 1)
                
                # Análisis de fines de semana
                consumo_fds = consumo_diario[['Sábado', 'Domingo']].sum()
                consumo_semana = consumo_diario[['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']].sum()
                
                pdf.cell(0, 6, f'• Consumo en días laborables: S/ {consumo_semana:,.2f}', 0, 1)
                pdf.cell(0, 6, f'• Consumo en fines de semana: S/ {consumo_fds:,.2f}', 0, 1)
        
        # Página 4: Distribución de anomalías
        if 'anomalias_pie' in graficos:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'DISTRIBUCIÓN DE ANOMALÍAS POR NIVEL DE RIESGO', 0, 1)
            pdf.ln(5)
            
            # Insertar gráfico de anomalías
            pdf.image(graficos['anomalias_pie'], x=10, y=40, w=190)
            
            # Tabla de distribución detallada
            pdf.ln(120)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Detalle de Anomalías por Nivel de Riesgo:', 0, 1)
            pdf.ln(5)
            
            # Encabezados de tabla
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 8, 'Nivel de Riesgo', 1, 0, 'C')
            pdf.cell(30, 8, 'Cantidad', 1, 0, 'C')
            pdf.cell(30, 8, 'Porcentaje', 1, 0, 'C')
            pdf.cell(40, 8, 'Consumo (S/)', 1, 0, 'C')
            pdf.cell(40, 8, 'Impacto', 1, 1, 'C')
            
            # Datos de la tabla
            pdf.set_font('Arial', '', 9)
            if 'NIVEL_RIESGO' in df.columns:
                distribucion = df['NIVEL_RIESGO'].value_counts()
                for nivel, cantidad in distribucion.items():
                    porcentaje = (cantidad / total_registros * 100) if total_registros > 0 else 0
                    consumo_nivel = df[df['NIVEL_RIESGO'] == nivel]['TOTAL_CONSUMO'].sum()
                    
                    # Determinar color según nivel
                    if nivel == 'Critico':
                        impacto = 'MUY ALTO'
                    elif nivel == 'Alto':
                        impacto = 'ALTO'
                    elif nivel == 'Moderado':
                        impacto = 'MEDIO'
                    else:
                        impacto = 'BAJO'
                    
                    pdf.cell(40, 8, str(nivel), 1, 0, 'C')
                    pdf.cell(30, 8, str(cantidad), 1, 0, 'C')
                    pdf.cell(30, 8, f'{porcentaje:.1f}%', 1, 0, 'C')
                    pdf.cell(40, 8, f'S/ {consumo_nivel:,.0f}', 1, 0, 'C')
                    pdf.cell(40, 8, impacto, 1, 1, 'C')
        
        # Página 5: Top vehículos con mayor consumo
        if 'top_vehiculos' in graficos:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'TOP 10 VEHÍCULOS CON MAYOR CONSUMO', 0, 1)
            pdf.ln(5)
            
            # Insertar gráfico de top vehículos
            pdf.image(graficos['top_vehiculos'], x=10, y=40, w=190)
            
            # Tabla detallada de vehículos con anomalías
            pdf.ln(120)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Vehículos con Anomalías Detectadas:', 0, 1)
            pdf.ln(5)
            
            if 'PLACA' in df.columns and 'ANOMALIA' in df.columns:
                vehiculos_anomalias = df[df['ANOMALIA'] == 1].groupby('PLACA').agg({
                    'ANOMALIA': 'count',
                    'TOTAL_CONSUMO': 'sum',
                    'EFICIENCIA': 'mean',
                    'NIVEL_RIESGO': lambda x: x.mode().iloc[0] if not x.mode().empty else 'N/A'
                }).sort_values('ANOMALIA', ascending=False).head(10)
                
                if not vehiculos_anomalias.empty:
                    # Encabezados de tabla
                    pdf.set_font('Arial', 'B', 8)
                    pdf.cell(25, 6, 'Placa', 1, 0, 'C')
                    pdf.cell(20, 6, 'Anomalías', 1, 0, 'C')
                    pdf.cell(35, 6, 'Consumo Total', 1, 0, 'C')
                    pdf.cell(30, 6, 'Eficiencia', 1, 0, 'C')
                    pdf.cell(30, 6, 'Nivel Riesgo', 1, 0, 'C')
                    pdf.cell(50, 6, 'Recomendación', 1, 1, 'C')
                    
                    # Datos de vehículos
                    pdf.set_font('Arial', '', 7)
                    for placa, row in vehiculos_anomalias.iterrows():
                        pdf.cell(25, 6, str(placa), 1, 0, 'C')
                        pdf.cell(20, 6, str(row['ANOMALIA']), 1, 0, 'C')
                        pdf.cell(35, 6, f"S/ {row['TOTAL_CONSUMO']:,.0f}", 1, 0, 'C')
                        pdf.cell(30, 6, f"{row['EFICIENCIA']:.2f} km/gal", 1, 0, 'C')
                        pdf.cell(30, 6, str(row['NIVEL_RIESGO']), 1, 0, 'C')
                        
                        # Recomendación basada en nivel de riesgo
                        if row['NIVEL_RIESGO'] == 'Critico':
                            recomendacion = 'REVISIÓN URGENTE'
                        elif row['NIVEL_RIESGO'] == 'Alto':
                            recomendacion = 'MANTENIMIENTO'
                        else:
                            recomendacion = 'SEGUIMIENTO'
                        
                        pdf.cell(50, 6, recomendacion, 1, 1, 'C')
        
        # Página final: Recomendaciones y conclusiones
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'RECOMENDACIONES Y CONCLUSIONES', 0, 1)
        pdf.ln(10)
        
        # Recomendaciones basadas en los datos
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Recomendaciones:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        recomendaciones = []
        
        if porcentaje_anomalias > 10:
            recomendaciones.append('• URGENTE: Implementar programa de mantenimiento preventivo')
            recomendaciones.append('• Revisar procedimientos de carga de combustible')
            recomendaciones.append('• Capacitar a conductores en manejo eficiente')
        
        if eficiencia_promedio < 8:
            recomendaciones.append('• Optimizar rutas para mejorar eficiencia')
            recomendaciones.append('• Revisar estado mecánico de vehículos')
        
        if 'DIA_SEMANA' in df.columns:
            consumo_fds = df[df['DIA_SEMANA'].isin([5, 6])]['TOTAL_CONSUMO'].sum()
            if consumo_fds > total_consumo * 0.3:
                recomendaciones.append('• Evaluar el uso de vehículos en fines de semana')
        
        recomendaciones.append('• Implementar sistema de monitoreo continuo')
        recomendaciones.append('• Generar reportes mensuales de seguimiento')
        
        for rec in recomendaciones:
            pdf.cell(0, 6, rec, 0, 1)
        
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Conclusiones:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        pdf.cell(0, 6, f'• Se analizaron {total_registros:,} registros de consumo de combustible', 0, 1)
        pdf.cell(0, 6, f'• Se detectaron {total_anomalias:,} anomalías ({porcentaje_anomalias:.1f}% del total)', 0, 1)
        pdf.cell(0, 6, f'• El consumo total asciende a S/ {total_consumo:,.2f}', 0, 1)
        pdf.cell(0, 6, f'• La eficiencia promedio es de {eficiencia_promedio:.2f} km/gal', 0, 1)
        
        # Pie de página
        pdf.ln(20)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, 'Sistema de Análisis de Combustible - Municipalidad de Ate', 0, 1, 'C')
        pdf.cell(0, 10, f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
        
        # Guardar archivo
        os.makedirs('uploads', exist_ok=True)
        nombre_archivo = f"reporte_completo_{dependencia}_mes{mes}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        nombre_archivo = re.sub(r'[^a-zA-Z0-9_.-]', '', nombre_archivo)  # Limpiar nombre
        ruta_completa = os.path.join('uploads', nombre_archivo)
        pdf.output(ruta_completa)
        
        # Limpiar archivos temporales de gráficos
        for grafico_path in graficos.values():
            if os.path.exists(grafico_path):
                os.remove(grafico_path)
        
        # Eliminar directorio temporal
        temp_dir = 'temp_graficos'
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        
        print(f"Reporte PDF mejorado generado: {nombre_archivo}")
        return nombre_archivo
        
    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        return None