import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PredictorConsumo:
    def __init__(self):
        self.modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)
        self.modelo_linear = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.features = []
        
    def preparar_datos(self, df):
        """
        Prepara los datos para el entrenamiento del modelo
        """
        try:
            # Crear características temporales
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['año'] = df['fecha'].dt.year
            df['mes'] = df['fecha'].dt.month
            df['dia'] = df['fecha'].dt.day
            df['dia_semana'] = df['fecha'].dt.dayofweek
            df['semana_año'] = df['fecha'].dt.isocalendar().week
            
            # Características de consumo histórico por vehículo
            df['consumo_promedio_vehiculo'] = df.groupby('placa')['galones'].transform('mean')
            df['consumo_std_vehiculo'] = df.groupby('placa')['galones'].transform('std')
            
            # Características de tendencia temporal
            df['consumo_promedio_mes'] = df.groupby(['año', 'mes'])['galones'].transform('mean')
            df['consumo_promedio_semana'] = df.groupby(['año', 'semana_año'])['galones'].transform('mean')
            
            # Lag features (valores previos)
            df = df.sort_values(['placa', 'fecha'])
            df['galones_lag1'] = df.groupby('placa')['galones'].shift(1)
            df['galones_lag7'] = df.groupby('placa')['galones'].shift(7)
            
            # Características de kilometraje si está disponible
            if 'kilometraje' in df.columns:
                df['km_por_galon'] = df['kilometraje'] / df['galones']
                df['km_por_galon'] = df['km_por_galon'].replace([np.inf, -np.inf], np.nan)
                df['km_promedio_vehiculo'] = df.groupby('placa')['kilometraje'].transform('mean')
            
            # Eliminar filas con valores nulos
            df = df.dropna()
            
            return df
            
        except Exception as e:
            print(f"Error preparando datos: {str(e)}")
            return pd.DataFrame()
    
    def entrenar_modelo(self, df):
        """
        Entrena el modelo de predicción
        """
        try:
            # Preparar datos
            df_prep = self.preparar_datos(df)
            
            if df_prep.empty:
                raise ValueError("No hay datos suficientes para entrenar el modelo")
            
            # Seleccionar características
            self.features = [
                'año', 'mes', 'dia', 'dia_semana', 'semana_año',
                'consumo_promedio_vehiculo', 'consumo_std_vehiculo',
                'consumo_promedio_mes', 'consumo_promedio_semana',
                'galones_lag1', 'galones_lag7'
            ]
            
            # Agregar características de kilometraje si están disponibles
            if 'km_por_galon' in df_prep.columns:
                self.features.extend(['km_por_galon', 'km_promedio_vehiculo'])
            
            # Filtrar características que existen
            self.features = [f for f in self.features if f in df_prep.columns]
            
            X = df_prep[self.features]
            y = df_prep['galones']
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Escalar características
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelos
            self.modelo_rf.fit(X_train, y_train)
            self.modelo_linear.fit(X_train_scaled, y_train)
            
            # Evaluación
            y_pred_rf = self.modelo_rf.predict(X_test)
            y_pred_linear = self.modelo_linear.predict(X_test_scaled)
            
            # Métricas
            mae_rf = mean_absolute_error(y_test, y_pred_rf)
            r2_rf = r2_score(y_test, y_pred_rf)
            
            mae_linear = mean_absolute_error(y_test, y_pred_linear)
            r2_linear = r2_score(y_test, y_pred_linear)
            
            print(f"Random Forest - MAE: {mae_rf:.2f}, R²: {r2_rf:.3f}")
            print(f"Linear Regression - MAE: {mae_linear:.2f}, R²: {r2_linear:.3f}")
            
            self.is_trained = True
            
            return {
                "modelo_entrenado": True,
                "metricas": {
                    "random_forest": {"mae": mae_rf, "r2": r2_rf},
                    "linear": {"mae": mae_linear, "r2": r2_linear}
                },
                "features_usadas": self.features,
                "datos_entrenamiento": len(X_train)
            }
            
        except Exception as e:
            print(f"Error entrenando modelo: {str(e)}")
            return {"error": str(e)}
    
    def predecir_consumo(self, df_base, vehiculo, periodo_dias=30):
        """
        Predice el consumo para un vehículo específico
        """
        try:
            if not self.is_trained:
                raise ValueError("El modelo no ha sido entrenado")
            
            # Obtener datos históricos del vehículo
            df_vehiculo = df_base[df_base['placa'] == vehiculo].copy()
            
            if df_vehiculo.empty:
                raise ValueError(f"No se encontraron datos para el vehículo {vehiculo}")
            
            # Preparar datos base
            df_vehiculo = self.preparar_datos(df_vehiculo)
            
            # Generar fechas futuras
            ultima_fecha = df_vehiculo['fecha'].max()
            fechas_futuras = pd.date_range(
                start=ultima_fecha + timedelta(days=1),
                periods=periodo_dias,
                freq='D'
            )
            
            predicciones = []
            
            for fecha in fechas_futuras:
                # Crear características para la fecha
                caracteristicas = {
                    'año': fecha.year,
                    'mes': fecha.month,
                    'dia': fecha.day,
                    'dia_semana': fecha.dayofweek,
                    'semana_año': fecha.isocalendar().week,
                    'consumo_promedio_vehiculo': df_vehiculo['galones'].mean(),
                    'consumo_std_vehiculo': df_vehiculo['galones'].std(),
                    'consumo_promedio_mes': df_vehiculo[df_vehiculo['mes'] == fecha.month]['galones'].mean(),
                    'consumo_promedio_semana': df_vehiculo['galones'].mean(),  # Aproximación
                    'galones_lag1': df_vehiculo['galones'].iloc[-1],
                    'galones_lag7': df_vehiculo['galones'].iloc[-7] if len(df_vehiculo) >= 7 else df_vehiculo['galones'].mean()
                }
                
                # Agregar características de kilometraje si están disponibles
                if 'km_por_galon' in df_vehiculo.columns:
                    caracteristicas['km_por_galon'] = df_vehiculo['km_por_galon'].mean()
                    caracteristicas['km_promedio_vehiculo'] = df_vehiculo['kilometraje'].mean()
                
                # Filtrar características que existen
                X_pred = pd.DataFrame([caracteristicas])
                X_pred = X_pred[[f for f in self.features if f in X_pred.columns]]
                
                # Predecir
                pred_rf = self.modelo_rf.predict(X_pred)[0]
                
                predicciones.append({
                    'fecha': fecha.strftime('%Y-%m-%d'),
                    'prediccion_galones': max(0, pred_rf),  # Asegurar que no sea negativo
                    'vehiculo': vehiculo
                })
            
            return predicciones
            
        except Exception as e:
            print(f"Error prediciendo consumo: {str(e)}")
            return []
    
    def generar_reporte_prediccion(self, df_base, vehiculos=None, periodo_dias=30):
        """
        Genera reporte de predicción para múltiples vehículos
        """
        try:
            if vehiculos is None:
                vehiculos = df_base['placa'].unique()[:10]  # Limitar a 10 vehículos
            
            reporte = {
                'fecha_generacion': datetime.now().isoformat(),
                'periodo_prediccion_dias': periodo_dias,
                'vehiculos_analizados': len(vehiculos),
                'predicciones': {}
            }
            
            for vehiculo in vehiculos:
                predicciones = self.predecir_consumo(df_base, vehiculo, periodo_dias)
                
                if predicciones:
                    consumo_total = sum([p['prediccion_galones'] for p in predicciones])
                    consumo_promedio = consumo_total / len(predicciones)
                    
                    reporte['predicciones'][vehiculo] = {
                        'consumo_total_predicho': round(consumo_total, 2),
                        'consumo_promedio_diario': round(consumo_promedio, 2),
                        'predicciones_detalle': predicciones
                    }
            
            return reporte
            
        except Exception as e:
            print(f"Error generando reporte: {str(e)}")
            return {"error": str(e)}

# Instancia global del predictor
predictor = PredictorConsumo()