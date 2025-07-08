"""
Módulo de cálculo y reporte de emisiones de CO2
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import os
from datetime import datetime

class CalculadorEmisiones:
    def __init__(self):
        # Factores de emisión por tipo de combustible (kg CO2 por galón)
        self.factores_emision = {
            'GASOLINE': 8.887,  # Gasolina
            'DIESEL': 10.15,    # Diesel
            'GLP': 5.68,        # Gas Licuado de Petróleo
            'GAS': 5.68,        # Gas
            'PETROL': 8.887,    # Petróleo/Gasolina
            'BIODIESEL': 9.45,  # Biodiesel
            'DEFAULT': 8.887    # Valor por defecto
        }
        
        # Factores de conversión adicionales
        self.factor_combustion_completa = 0.99  # 99% de combustión completa
        self.factor_correccion_altitud = 1.0    # Ajuste por altitud (Lima está a nivel del mar)
        
    def normalizar_tipo_combustible(self, tipo):
        """Normaliza el tipo de combustible para búsqueda en factores"""
        if pd.isna(tipo):
            return 'DEFAULT'
        
        tipo_upper = str(tipo).upper()
        
        # Mapeo de variaciones comunes
        mapeo = {
            'GASOLINA': 'GASOLINE',
            'GASOLINE': 'GASOLINE',
            'PETROL': 'GASOLINE',
            'DIESEL': 'DIESEL',
            'PETRÓLEO': 'DIESEL',
            'GLP': 'GLP',
            'GAS': 'GLP',
            'BIODIESEL': 'BIODIESEL'
        }
        
        for key, value in mapeo.items():
            if key in tipo_upper:
                return value
        
        return 'DEFAULT'
    
    def calcular_emisiones_registro(self, galones, tipo_combustible):
        """Calcula las emisiones de CO2 para un registro individual"""
        try:
            if pd.isna(galones) or galones <= 0:
                return 0
            
            tipo_normalizado = self.normalizar_tipo_combustible(tipo_combustible)
            factor_emision = self.factores_emision.get(tipo_normalizado, self.factores_emision['DEFAULT'])
            
            # Cálculo básico: galones × factor de emisión
            emisiones_base = galones * factor_emision
            
            # Aplicar factores de corrección
            emisiones_total = (emisiones_base * 
                             self.factor_combustion_completa * 
                             self.factor_correccion_altitud)
            
            return round(emisiones_total, 3)
            
        except Exception as e:
            print(f"Error calculando emisiones: {e}")
            return 0
    
    def calcular_emisiones_dataframe(self, df):
        """Calcula las emisiones para todo el DataFrame"""
        df_emisiones = df.copy()
        
        try:
            # Calcular emisiones por registro
            df_emisiones['EMISIONES_CO2_KG'] = df_emisiones.apply(
                lambda row: self.calcular_emisiones_registro(
                    row.get('CANTIDAD_GALONES', 0),
                    row.get('TIPO_COMBUSTIBLE', 'DEFAULT')
                ), axis=1
            )
            
            # Calcular emisiones por kilómetro
            df_emisiones['EMISIONES_POR_KM'] = np.where(
                df_emisiones['KM_RECORRIDO'] > 0,
                df_emisiones['EMISIONES_CO2_KG'] / df_emisiones['KM_RECORRIDO'],
                0
            )
            
            # Clasificar nivel de emisiones
            df_emisiones['NIVEL_EMISIONES'] = pd.cut(
                df_emisiones['EMISIONES_POR_KM'],
                bins=[0, 0.5, 1.0, 2.0, float('inf')],
                labels=['Bajo', 'Moderado', 'Alto', 'Muy Alto'],
                include_lowest=True
            )
            
        except Exception as e:
            print(f"Error calculando emisiones del DataFrame: {e}")
        
        return df_emisiones
    
    def generar_estadisticas_emisiones(self, df):
        """Genera estadísticas detalladas de emisiones"""
        try:
            df_emisiones = self.calcular_emisiones_dataframe(df)
            
            estadisticas = {
                'total_emisiones_kg': df_emisiones['EMISIONES_CO2_KG'].sum(),
                'total_emisiones_toneladas': df_emisiones['EMISIONES_CO2_KG'].sum() / 1000,
                'promedio_emisiones_por_viaje': df_emisiones['EMISIONES_CO2_KG'].mean(),
                'promedio_emisiones_por_km': df_emisiones['EMISIONES_POR_KM'].mean(),
                'max_emisiones_registro': df_emisiones['EMISIONES_CO2_KG'].max(),
                'min_emisiones_registro': df_emisiones['EMISIONES_CO2_KG'].min()
            }
            
            # Estadísticas por tipo de combustible
            emisiones_por_combustible = df_emisiones.groupby('TIPO_COMBUSTIBLE').agg({
                'EMISIONES_CO2_KG': ['sum', 'mean', 'count'],
                'CANTIDAD_GALONES': 'sum'
            }).round(3)
            
            estadisticas['por_tipo_combustible'] = emisiones_por_combustible.to_dict()
            
            # Estadísticas por dependencia
            if 'UNIDAD_ORGANICA' in df_emisiones.columns:
                emisiones_por_dependencia = df_emisiones.groupby('UNIDAD_ORGANICA').agg({
                    'EMISIONES_CO2_KG': ['sum', 'mean'],
                    'CANTIDAD_GALONES': 'sum'
                }).round(3)
                
                estadisticas['por_dependencia'] = emisiones_por_dependencia.to_dict()
            
            # Estadísticas por vehículo (top 10)
            if 'PLACA' in df_emisiones.columns:
                top_vehiculos_emisiones = df_emisiones.groupby('PLACA')['EMISIONES_CO2_KG'].sum().sort_values(ascending=False).head(10)
                estadisticas['top_vehiculos_emisiones'] = top_vehiculos_emisiones.to_dict()
            
            # Distribución por nivel de emisiones
            if 'NIVEL_EMISIONES' in df_emisiones.columns:
                distribucion_niveles = df_emisiones['NIVEL_EMISIONES'].value_counts()
                estadisticas['distribucion_niveles'] = distribucion_niveles.to_dict()
            
            return estadisticas
            
        except Exception as e:
            print(f"Error generando estadísticas de emisiones: {e}")
            return {}
    
    def crear_graficos_emisiones(self, df, dependencia=None, mes=None):
        """Crea gráficos relacionados con emisiones"""
        graficos = {}
        df_emisiones = self.calcular_emisiones_dataframe(df)
        
        # Crear directorio temporal
        temp_dir = 'temp_graficos_emisiones'
        os.makedirs(temp_dir, exist_ok=True)
        
        plt.style.use('seaborn-v0_8')
        
        try:
            # 1. Gráfico de emisiones por tipo de combustible
            plt.figure(figsize=(10, 6))
            emisiones_combustible = df_emisiones.groupby('TIPO_COMBUSTIBLE')['EMISIONES_CO2_KG'].sum()
            
            bars = plt.bar(emisiones_combustible.index, emisiones_combustible.values, 
                          color='lightgreen', alpha=0.8, edgecolor='darkgreen')
            plt.xlabel('Tipo de Combustible')
            plt.ylabel('Emisiones de CO₂ (kg)')
            plt.title('Emisiones de CO₂ por Tipo de Combustible')
            plt.xticks(rotation=45)
            
            # Agregar valores en las barras
            for bar, valor in zip(bars, emisiones_combustible.values):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(emisiones_combustible.values)*0.01, 
                        f'{valor:.1f} kg', ha='center', va='bottom')
            
            plt.grid(True, alpha=0.3)
            grafico_path = os.path.join(temp_dir, 'emisiones_por_combustible.png')
            plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
            plt.close()
            graficos['emisiones_combustible'] = grafico_path
            
            # 2. Gráfico de emisiones vs eficiencia
            if 'EFICIENCIA' in df_emisiones.columns:
                plt.figure(figsize=(10, 6))
                plt.scatter(df_emisiones['EFICIENCIA'], df_emisiones['EMISIONES_POR_KM'], 
                           alpha=0.6, color='red', s=50)
                plt.xlabel('Eficiencia (km/gal)')
                plt.ylabel('Emisiones por km (kg CO₂/km)')
                plt.title('Relación entre Eficiencia y Emisiones por Kilómetro')
                
                # Línea de tendencia
                z = np.polyfit(df_emisiones['EFICIENCIA'].dropna(), 
                              df_emisiones['EMISIONES_POR_KM'].dropna(), 1)
                p = np.poly1d(z)
                plt.plot(df_emisiones['EFICIENCIA'].dropna(), 
                        p(df_emisiones['EFICIENCIA'].dropna()), "r--", alpha=0.8)
                
                plt.grid(True, alpha=0.3)
                grafico_path = os.path.join(temp_dir, 'emisiones_vs_eficiencia.png')
                plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
                plt.close()
                graficos['emisiones_eficiencia'] = grafico_path
            
            # 3. Top 10 vehículos con mayores emisiones
            if 'PLACA' in df_emisiones.columns:
                plt.figure(figsize=(12, 8))
                top_vehiculos = df_emisiones.groupby('PLACA')['EMISIONES_CO2_KG'].sum().sort_values(ascending=False).head(10)
                
                bars = plt.barh(range(len(top_vehiculos)), top_vehiculos.values, color='orange', alpha=0.8)
                plt.yticks(range(len(top_vehiculos)), top_vehiculos.index)
                plt.xlabel('Emisiones de CO₂ (kg)')
                plt.title('Top 10 Vehículos con Mayores Emisiones de CO₂')
                plt.gca().invert_yaxis()
                
                # Agregar valores
                for i, (bar, valor) in enumerate(zip(bars, top_vehiculos.values)):
                    plt.text(bar.get_width() + max(top_vehiculos.values)*0.01, 
                            bar.get_y() + bar.get_height()/2, 
                            f'{valor:.1f} kg', va='center')
                
                plt.grid(True, alpha=0.3)
                grafico_path = os.path.join(temp_dir, 'top_vehiculos_emisiones.png')
                plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
                plt.close()
                graficos['top_vehiculos_emisiones'] = grafico_path
            
            # 4. Distribución de niveles de emisiones
            if 'NIVEL_EMISIONES' in df_emisiones.columns:
                plt.figure(figsize=(8, 8))
                distribucion = df_emisiones['NIVEL_EMISIONES'].value_counts()
                
                colors = ['#90EE90', '#FFD700', '#FFA500', '#FF6347']  # Verde, amarillo, naranja, rojo
                wedges, texts, autotexts = plt.pie(distribucion.values, labels=distribucion.index, 
                                                  autopct='%1.1f%%', colors=colors, startangle=90)
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                plt.title('Distribución de Vehículos por Nivel de Emisiones', fontweight='bold')
                grafico_path = os.path.join(temp_dir, 'distribucion_niveles_emisiones.png')
                plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
                plt.close()
                graficos['distribucion_emisiones'] = grafico_path
            
        except Exception as e:
            print(f"Error creando gráficos de emisiones: {e}")
        
        return graficos
    
    def generar_reporte_emisiones_pdf(self, df, mes, dependencia):
        """Genera un reporte PDF específico de emisiones"""
        try:
            df_emisiones = self.calcular_emisiones_dataframe(df)
            estadisticas = self.generar_estadisticas_emisiones(df)
            graficos = self.crear_graficos_emisiones(df_emisiones, dependencia, mes)
            
            # Crear PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Página 1: Portada
            pdf.add_page()
            pdf.set_font('Arial', 'B', 20)
            pdf.cell(0, 20, 'REPORTE DE EMISIONES DE CO₂', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Dependencia: {dependencia}', 0, 1)
            pdf.cell(0, 10, f'Mes: {mes}', 0, 1)
            pdf.cell(0, 10, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}', 0, 1)
            pdf.ln(10)
            
            # Resumen ejecutivo de emisiones
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'RESUMEN DE EMISIONES', 0, 1)
            pdf.ln(5)
            
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 8, f'• Total de emisiones: {estadisticas.get("total_emisiones_kg", 0):.2f} kg de CO₂', 0, 1)
            pdf.cell(0, 8, f'• Equivalente en toneladas: {estadisticas.get("total_emisiones_toneladas", 0):.3f} ton de CO₂', 0, 1)
            pdf.cell(0, 8, f'• Promedio por viaje: {estadisticas.get("promedio_emisiones_por_viaje", 0):.2f} kg de CO₂', 0, 1)
            pdf.cell(0, 8, f'• Promedio por kilómetro: {estadisticas.get("promedio_emisiones_por_km", 0):.3f} kg CO₂/km', 0, 1)
            
            # Equivalencias ambientales
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'EQUIVALENCIAS AMBIENTALES', 0, 1)
            pdf.set_font('Arial', '', 11)
            
            total_co2 = estadisticas.get("total_emisiones_kg", 0)
            arboles_necesarios = total_co2 / 22  # Un árbol absorbe ~22 kg CO2/año
            km_auto_particular = total_co2 / 0.2  # Auto particular ~0.2 kg CO2/km
            
            pdf.cell(0, 6, f'• Árboles necesarios para compensar: {arboles_necesarios:.0f} árboles/año', 0, 1)
            pdf.cell(0, 6, f'• Equivale a recorrer en auto particular: {km_auto_particular:.0f} km', 0, 1)
            pdf.cell(0, 6, f'• Impacto ambiental: {"ALTO" if total_co2 > 1000 else "MEDIO" if total_co2 > 500 else "BAJO"}', 0, 1)
            
            # Insertar gráficos
            if 'emisiones_combustible' in graficos:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, 'EMISIONES POR TIPO DE COMBUSTIBLE', 0, 1)
                pdf.image(graficos['emisiones_combustible'], x=10, y=30, w=190)
            
            if 'top_vehiculos_emisiones' in graficos:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, 'VEHÍCULOS CON MAYORES EMISIONES', 0, 1)
                pdf.image(graficos['top_vehiculos_emisiones'], x=10, y=30, w=190)
            
            # Recomendaciones
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'RECOMENDACIONES AMBIENTALES', 0, 1)
            pdf.ln(5)
            
            pdf.set_font('Arial', '', 11)
            recomendaciones = [
                '• Implementar programa de mantenimiento preventivo para mejorar eficiencia',
                '• Considerar renovación de vehículos con altas emisiones por kilómetro',
                '• Optimizar rutas para reducir kilómetros innecesarios',
                '• Capacitar conductores en técnicas de conducción eco-eficiente',
                '• Evaluar uso de combustibles alternativos o vehículos híbridos',
                '• Implementar sistema de monitoreo continuo de emisiones',
                '• Compensar huella de carbono mediante programas de reforestación'
            ]
            
            for rec in recomendaciones:
                pdf.cell(0, 6, rec, 0, 1)
            
            # Guardar archivo
            os.makedirs('uploads', exist_ok=True)
            nombre_archivo = f"reporte_emisiones_{dependencia}_mes{mes}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            nombre_archivo = nombre_archivo.replace(' ', '_').replace('/', '_')
            ruta_completa = os.path.join('uploads', nombre_archivo)
            pdf.output(ruta_completa)
            
            # Limpiar archivos temporales
            for grafico_path in graficos.values():
                if os.path.exists(grafico_path):
                    os.remove(grafico_path)
            
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
            return nombre_archivo
            
        except Exception as e:
            print(f"Error generando reporte de emisiones: {e}")
            return None
    
    def calcular_huella_carbono_flota(self, df):
        """Calcula la huella de carbono total de la flota"""
        try:
            df_emisiones = self.calcular_emisiones_dataframe(df)
            
            huella_carbono = {
                'total_co2_kg': df_emisiones['EMISIONES_CO2_KG'].sum(),
                'total_co2_toneladas': df_emisiones['EMISIONES_CO2_KG'].sum() / 1000,
                'promedio_mensual_kg': df_emisiones['EMISIONES_CO2_KG'].sum() / 12,  # Estimado anual
                'vehiculos_analizados': df_emisiones['PLACA'].nunique(),
                'eficiencia_promedio_flota': df_emisiones['EFICIENCIA'].mean() if 'EFICIENCIA' in df_emisiones.columns else 0,
                'emisiones_por_km_flota': df_emisiones['EMISIONES_POR_KM'].mean(),
                'fecha_calculo': datetime.now().isoformat()
            }
            
            return huella_carbono
            
        except Exception as e:
            print(f"Error calculando huella de carbono: {e}")
            return {}
