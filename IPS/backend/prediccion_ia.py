"""
Módulo de predicción de consumo usando algoritmos de análisis de datos
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PrediccionConsumo:
    def __init__(self):
        self.modelo = None
        self.scaler = StandardScaler()
        self.modelo_entrenado = False
        self.metricas = {}
        
    def preparar_datos_prediccion(self, df):
        """Prepara los datos para entrenamiento del modelo"""
        if df.empty:
            return None, None
            
        # Crear características temporales
        df['dia_mes'] = pd.to_datetime(df['FECHA_INGRESO_VALE']).dt.day
        df['dia_semana'] = pd.to_datetime(df['FECHA_INGRESO_VALE']).dt.dayofweek
        df['mes'] = pd.to_datetime(df['FECHA_INGRESO_VALE']).dt.month
        df['trimestre'] = pd.to_datetime(df['FECHA_INGRESO_VALE']).dt.quarter
        
        # Variables categóricas numéricas
        df['tipo_combustible_num'] = pd.Categorical(df['TIPO_COMBUSTIBLE']).codes
        df['unidad_organica_num'] = pd.Categorical(df['UNIDAD_ORGANICA']).codes
        
        # Características del vehículo
        df['km_promedio'] = df.groupby('PLACA')['KM_RECORRIDO'].transform('mean')
        df['consumo_historico'] = df.groupby('PLACA')['TOTAL_CONSUMO'].transform('mean')
        
        # Variables objetivo y predictoras
        features = [
            'dia_mes', 'dia_semana', 'mes', 'trimestre',
            'tipo_combustible_num', 'unidad_organica_num',
            'KM_RECORRIDO', 'CANTIDAD_GALONES', 'PRECIO',
            'km_promedio', 'consumo_historico'
        ]
        
        # Filtrar solo las columnas que existen
        features_disponibles = [f for f in features if f in df.columns]
        
        if len(features_disponibles) < 5:
            return None, None
            
        X = df[features_disponibles].fillna(0)
        y = df['TOTAL_CONSUMO'].fillna(0)
        
        return X, y
    
    def entrenar_modelo(self, df):
        """Entrena el modelo de predicción"""
        X, y = self.preparar_datos_prediccion(df)
        
        if X is None or len(X) < 50:
            return False
            
        try:
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Escalar datos
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelo Random Forest para mejor precisión
            self.modelo = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.modelo.fit(X_train_scaled, y_train)
            
            # Evaluar modelo
            y_pred = self.modelo.predict(X_test_scaled)
            
            self.metricas = {
                'mae': mean_absolute_error(y_test, y_pred),
                'r2': r2_score(y_test, y_pred),
                'precision': max(0, min(100, self.modelo.score(X_test_scaled, y_test) * 100))
            }
            
            self.modelo_entrenado = True
            
            # Guardar modelo
            os.makedirs('models', exist_ok=True)
            joblib.dump(self.modelo, 'models/modelo_prediccion.pkl')
            joblib.dump(self.scaler, 'models/scaler_prediccion.pkl')
            
            return True
            
        except Exception as e:
            print(f"Error entrenando modelo: {e}")
            return False
    
    def cargar_modelo(self):
        """Carga un modelo previamente entrenado"""
        try:
            if os.path.exists('models/modelo_prediccion.pkl'):
                self.modelo = joblib.load('models/modelo_prediccion.pkl')
                self.scaler = joblib.load('models/scaler_prediccion.pkl')
                self.modelo_entrenado = True
                return True
        except:
            pass
        return False
    
    def predecir_consumo_semanal(self, df, placa=None, dependencia=None):
        """Predice el consumo para la próxima semana"""
        if not self.modelo_entrenado:
            return None
            
        try:
            # Filtrar datos si se especifica placa o dependencia
            df_filtrado = df.copy()
            if placa:
                df_filtrado = df_filtrado[df_filtrado['PLACA'] == placa]
            if dependencia:
                df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
                
            if df_filtrado.empty:
                return None
                
            # Obtener datos promedio de los últimos registros
            datos_recientes = df_filtrado.tail(30)
            
            predicciones = []
            fecha_inicio = datetime.now()
            
            for i in range(7):  # 7 días
                fecha_pred = fecha_inicio + timedelta(days=i)
                
                # Crear características para predicción
                features_pred = {
                    'dia_mes': fecha_pred.day,
                    'dia_semana': fecha_pred.weekday(),
                    'mes': fecha_pred.month,
                    'trimestre': (fecha_pred.month - 1) // 3 + 1,
                    'tipo_combustible_num': datos_recientes['TIPO_COMBUSTIBLE'].mode().iloc[0] if not datos_recientes.empty else 0,
                    'unidad_organica_num': datos_recientes['UNIDAD_ORGANICA'].mode().iloc[0] if not datos_recientes.empty else 0,
                    'KM_RECORRIDO': datos_recientes['KM_RECORRIDO'].mean(),
                    'CANTIDAD_GALONES': datos_recientes['CANTIDAD_GALONES'].mean(),
                    'PRECIO': datos_recientes['PRECIO'].mean(),
                    'km_promedio': datos_recientes['KM_RECORRIDO'].mean(),
                    'consumo_historico': datos_recientes['TOTAL_CONSUMO'].mean()
                }
                
                # Convertir a DataFrame
                X_pred = pd.DataFrame([features_pred])
                
                # Predecir
                X_pred_scaled = self.scaler.transform(X_pred.fillna(0))
                consumo_pred = self.modelo.predict(X_pred_scaled)[0]
                
                predicciones.append({
                    'fecha': fecha_pred.strftime('%Y-%m-%d'),
                    'dia_semana': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_pred.weekday()],
                    'consumo_predicho': max(0, consumo_pred)
                })
            
            return predicciones
            
        except Exception as e:
            print(f"Error en predicción semanal: {e}")
            return None
    
    def predecir_consumo_mensual(self, df, dependencia=None):
        """Predice el consumo para el próximo mes"""
        if not self.modelo_entrenado:
            return None
            
        try:
            df_filtrado = df.copy()
            if dependencia:
                df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
                
            if df_filtrado.empty:
                return None
                
            # Agrupar por mes histórico
            df_filtrado['fecha'] = pd.to_datetime(df_filtrado['FECHA_INGRESO_VALE'])
            consumo_mensual = df_filtrado.groupby(df_filtrado['fecha'].dt.to_period('M')).agg({
                'TOTAL_CONSUMO': 'sum',
                'KM_RECORRIDO': 'sum',
                'CANTIDAD_GALONES': 'sum'
            }).reset_index()
            
            if len(consumo_mensual) < 3:
                return None
                
            # Tendencia simple
            consumo_promedio = consumo_mensual['TOTAL_CONSUMO'].mean()
            tendencia = consumo_mensual['TOTAL_CONSUMO'].pct_change().mean()
            
            # Predicción para próximo mes
            proximo_mes = datetime.now().replace(day=1) + timedelta(days=32)
            proximo_mes = proximo_mes.replace(day=1)
            
            consumo_predicho = consumo_promedio * (1 + tendencia)
            
            return {
                'mes': proximo_mes.strftime('%Y-%m'),
                'consumo_predicho': max(0, consumo_predicho),
                'consumo_promedio_historico': consumo_promedio,
                'tendencia': tendencia * 100,  # En porcentaje
                'confianza': min(100, self.metricas.get('precision', 70))
            }
            
        except Exception as e:
            print(f"Error en predicción mensual: {e}")
            return None
    
    def predecir_consumo_anual(self, df, dependencia=None):
        """Predice el consumo para el próximo año"""
        if not self.modelo_entrenado:
            return None
            
        try:
            df_filtrado = df.copy()
            if dependencia:
                df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
                
            if df_filtrado.empty:
                return None
                
            df_filtrado['fecha'] = pd.to_datetime(df_filtrado['FECHA_INGRESO_VALE'])
            
            # Consumo por mes
            consumo_mensual = df_filtrado.groupby(df_filtrado['fecha'].dt.month)['TOTAL_CONSUMO'].sum()
            
            # Predicción simple basada en patrones estacionales
            consumo_anual_predicho = consumo_mensual.sum() * 12 / len(consumo_mensual)
            
            # Análisis de estacionalidad
            meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            
            predicciones_mensuales = []
            for i in range(1, 13):
                consumo_mes = consumo_mensual.get(i, consumo_mensual.mean())
                predicciones_mensuales.append({
                    'mes': meses[i-1],
                    'consumo_predicho': consumo_mes
                })
            
            return {
                'año': datetime.now().year + 1,
                'consumo_anual_predicho': consumo_anual_predicho,
                'predicciones_mensuales': predicciones_mensuales,
                'confianza': min(100, self.metricas.get('precision', 60))
            }
            
        except Exception as e:
            print(f"Error en predicción anual: {e}")
            return None
    
    def obtener_metricas(self):
        """Retorna las métricas del modelo"""
        return self.metricas
    
    def analizar_patrones(self, df):
        """Analiza patrones de consumo"""
        try:
            df['fecha'] = pd.to_datetime(df['FECHA_INGRESO_VALE'])
            
            patrones = {
                'consumo_por_dia_semana': df.groupby(df['fecha'].dt.dayofweek)['TOTAL_CONSUMO'].mean().to_dict(),
                'consumo_por_mes': df.groupby(df['fecha'].dt.month)['TOTAL_CONSUMO'].mean().to_dict(),
                'eficiencia_por_dependencia': df.groupby('UNIDAD_ORGANICA')['EFICIENCIA'].mean().to_dict(),
                'vehiculos_mayor_consumo': df.groupby('PLACA')['TOTAL_CONSUMO'].sum().sort_values(ascending=False).head(10).to_dict()
            }
            
            return patrones
            
        except Exception as e:
            print(f"Error analizando patrones: {e}")
            return {}
