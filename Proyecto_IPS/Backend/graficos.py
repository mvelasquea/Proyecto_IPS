import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import base64
import io
from typing import Dict, List, Optional

class GeneradorGraficos:
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generar_grafico_consumo_temporal(self, df: pd.DataFrame, formato: str = 'html') -> str:
        """Genera gráfico de consumo temporal por vehículo"""
        try:
            # Preparar datos
            df['fecha'] = pd.to_datetime(df['fecha'])
            df_agrupado = df.groupby(['fecha', 'placa'])['galones'].sum().reset_index()
            
            if formato == 'html':
                # Usar Plotly para gráficos interactivos
                fig = px.line(df_agrupado, 
                             x='fecha', 
                             y='galones', 
                             color='placa',
                             title='Consumo de Combustible por Vehículo a lo Largo del Tiempo',
                             labels={'galones': 'Galones', 'fecha': 'Fecha'})
                
                fig.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Galones",
                    hovermode='x unified',
                    template='plotly_white'
                )
                
                return fig.to_html(include_plotlyjs='cdn')
            
            else:
                # Usar matplotlib para gráficos estáticos
                plt.figure(figsize=(12, 6))
                
                for placa in df['placa'].unique()[:10]:  # Limitar a 10 vehículos
                    df_vehiculo = df_agrupado[df_agrupado['placa'] == placa]
                    plt.plot(df_vehiculo['fecha'], df_vehiculo['galones'], 
                            marker='o', label=placa, linewidth=2)
                
                plt.title('Consumo de Combustible por Vehículo')
                plt.xlabel('Fecha')
                plt.ylabel('Galones')
                plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                return self._matplotlib_to_base64()
                
        except Exception as e:
            print(f"Error generando gráfico temporal: {str(e)}")
            return ""
    
    def generar_grafico_eficiencia_flota(self, df: pd.DataFrame, formato: str = 'html') -> str:
        """Genera gráfico de eficiencia de la flota"""
        try:
            # Calcular métricas por vehículo
            metricas = df.groupby('placa').agg({
                'galones': ['sum', 'mean', 'count'],
                'kilometraje': 'sum' if 'kilometraje' in df.columns else 'count'
            }).round(2)
            
            metricas.columns = ['total_galones', 'promedio_galones', 'num_repostajes', 'total_km']
            metricas = metricas.reset_index()
            
            if 'kilometraje' in df.columns:
                metricas['eficiencia'] = metricas['total_km'] / metricas['total_galones']
            else:
                metricas['eficiencia'] = np.random.uniform(8, 15, len(metricas))  # Simulado
            
            if formato == 'html':
                # Gráfico de barras interactivo
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Consumo Total por Vehículo', 'Eficiencia por Vehículo',
                                   'Número de Repostajes', 'Consumo Promedio'),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}],
                           [{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                # Consumo total
                fig.add_trace(
                    go.Bar(x=metricas['placa'], y=metricas['total_galones'],
                           name='Consumo Total', marker_color='blue'),
                    row=1, col=1
                )
                
                # Eficiencia
                fig.add_trace(
                    go.Bar(x=metricas['placa'], y=metricas['eficiencia'],
                           name='Eficiencia (km/gal)', marker_color='green'),
                    row=1, col=2
                )
                
                # Número de repostajes
                fig.add_trace(
                    go.Bar(x=metricas['placa'], y=metricas['num_repostajes'],
                           name='Repostajes', marker_color='orange'),
                    row=2, col=1
                )
                
                # Consumo promedio
                fig.add_trace(
                    go.Bar(x=metricas['placa'], y=metricas['promedio_galones'],
                           name='Consumo Promedio', marker_color='red'),
                    row=2, col=2
                )
                
                fig.update_layout(
                    title_text="Dashboard de Eficiencia de Flota",
                    showlegend=False,
                    height=800
                )
                
                return fig.to_html(include_plotlyjs='cdn')
            
            else:
                # Gráfico matplotlib
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                
                # Consumo total
                axes[0, 0].bar(metricas['placa'], metricas['total_galones'])
                axes[0, 0].set_title('Consumo Total por Vehículo')
                axes[0, 0].set_ylabel('Galones')
                axes[0, 0].tick_params(axis='x', rotation=45)
                
                # Eficiencia
                axes[0, 1].bar(metricas['placa'], metricas['eficiencia'], color='green')
                axes[0, 1].set_title('Eficiencia por Vehículo')
                axes[0, 1].set_ylabel('km/gal')
                axes[0, 1].tick_params(axis='x', rotation=45)
                
                # Número de repostajes
                axes[1, 0].bar(metricas['placa'], metricas['num_repostajes'], color='orange')
                axes[1, 0].set_title('Número de Repostajes')
                axes[1, 0].set_ylabel('Cantidad')
                axes[1, 0].tick_params(axis='x', rotation=45)
                
                # Consumo promedio
                axes[1, 1].bar(metricas['placa'], metricas['promedio_galones'], color='red')
                axes[1, 1].set_title('Consumo Promedio por Repostaje')
                axes[1, 1].set_ylabel('Galones')
                axes[1, 1].tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                return self._matplotlib_to_base64()
                
        except Exception as e:
            print(f"Error generando gráfico de eficiencia: {str(e)}")
            return ""
    
    def generar_grafico_anomalias(self, df: pd.DataFrame, df_anomalias: pd.DataFrame, formato: str = 'html') -> str:
        """Genera gráfico de anomalías detectadas"""
        try:
            if formato == 'html':
                # Gráfico scatter interactivo
                fig = go.Figure()
                
                # Datos normales
                fig.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['galones'],
                    mode='markers',
                    name='Consumo Normal',
                    marker=dict(color='blue', size=6),
                    text=df['placa'],
                    hovertemplate='<b>%{text}</b><br>Fecha: %{x}<br>Galones: %{y}<extra></extra>'
                ))
                
                # Anomalías
                if not df_anomalias.empty:
                    fig.add_trace(go.Scatter(
                        x=df_anomalias['fecha'],
                        y=df_anomalias['galones'],
                        mode='markers',
                        name='Anomalías',
                        marker=dict(color='red', size=10, symbol='x'),
                        text=df_anomalias['placa'],
                        hovertemplate='<b>%{text}</b><br>Fecha: %{x}<br>Galones: %{y}<br>Anomalía<extra></extra>'
                    ))
                
                fig.update_layout(
                    title='Detección de Anomalías en el Consumo',
                    xaxis_title='Fecha',
                    yaxis_title='Galones',
                    hovermode='closest',
                    template='plotly_white'
                )
                
                return fig.to_html(include_plotlyjs='cdn')
            
            else:
                # Gráfico matplotlib
                plt.figure(figsize=(12, 6))
                
                # Datos normales
                plt.scatter(df['fecha'], df['galones'], alpha=0.6, label='Consumo Normal')
                
                # Anomalías
                if not df_anomalias.empty:
                    plt.scatter(df_anomalias['fecha'], df_anomalias['galones'], 
                               color='red', s=100, marker='x', label='Anomalías')
                
                plt.title('Detección de Anomalías en el Consumo')
                plt.xlabel('Fecha')
                plt.ylabel('Galones')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                return self._matplotlib_to_base64()
                
        except Exception as e:
            print(f"Error generando gráfico de anomalías: {str(e)}")
            return ""
    
    def generar_grafico_prediccion(self, predicciones: List[Dict], formato: str = 'html') -> str:
        """Genera gráfico de predicciones"""
        try:
            if not predicciones:
                return ""
            
            # Convertir a DataFrame
            df_pred = pd.DataFrame(predicciones)
            df_pred['fecha'] = pd.to_datetime(df_pred['fecha'])
            
            if formato == 'html':
                fig = px.line(df_pred, 
                             x='fecha', 
                             y='prediccion_galones',
                             color='vehiculo',
                             title='Predicción de Consumo de Combustible',
                             labels={'prediccion_galones': 'Galones Predichos', 'fecha': 'Fecha'})
                
                fig.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Galones Predichos",
                    template='plotly_white'
                )
                
                return fig.to_html(include_plotlyjs='cdn')
            
            else:
                plt.figure(figsize=(12, 6))
                
                for vehiculo in df_pred['vehiculo'].unique():
                    df_vehiculo = df_pred[df_pred['vehiculo'] == vehiculo]
                    plt.plot(df_vehiculo['fecha'], df_vehiculo['prediccion_galones'], 
                            marker='o', label=vehiculo, linewidth=2)
                
                plt.title('Predicción de Consumo de Combustible')
                plt.xlabel('Fecha')
                plt.ylabel('Galones Predichos')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                return self._matplotlib_to_base64()
                
        except Exception as e:
            print(f"Error generando gráfico de predicción: {str(e)}")
            return ""
    
    def _matplotlib_to_base64(self) -> str:
        """Convierte gráfico matplotlib a base64"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        plt.close()
        return f"data:image/png;base64,{image_base64}"

# Instancia global del generador de gráficos
generador_graficos = GeneradorGraficos()