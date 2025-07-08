"""
Módulo de filtros avanzados para búsqueda organizada y sencilla
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

class FiltrosAvanzados:
    def __init__(self):
        self.filtros_disponibles = {
            'temporal': ['fecha_inicio', 'fecha_fin', 'mes', 'dia_semana', 'trimestre'],
            'geografico': ['zona', 'region', 'dependencia'],
            'vehicular': ['placa', 'tipo_vehiculo', 'modelo', 'año'],
            'consumo': ['consumo_min', 'consumo_max', 'eficiencia_min', 'eficiencia_max'],
            'combustible': ['tipo_combustible', 'precio_min', 'precio_max'],
            'anomalias': ['con_anomalias', 'nivel_riesgo', 'score_anomalia_min']
        }
    
    def aplicar_filtro_temporal(self, df, **kwargs):
        """Aplica filtros temporales"""
        df_filtrado = df.copy()
        
        try:
            # Asegurar que la fecha esté en formato datetime
            if 'FECHA_INGRESO_VALE' in df_filtrado.columns:
                df_filtrado['FECHA_INGRESO_VALE'] = pd.to_datetime(df_filtrado['FECHA_INGRESO_VALE'])
            
            # Filtro por rango de fechas
            if kwargs.get('fecha_inicio'):
                fecha_inicio = pd.to_datetime(kwargs['fecha_inicio'])
                df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'] >= fecha_inicio]
            
            if kwargs.get('fecha_fin'):
                fecha_fin = pd.to_datetime(kwargs['fecha_fin'])
                df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'] <= fecha_fin]
            
            # Filtro por mes específico
            if kwargs.get('mes'):
                mes = int(kwargs['mes'])
                if 'MES' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['MES'] == mes]
                else:
                    df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'].dt.month == mes]
            
            # Filtro por día de la semana
            if kwargs.get('dia_semana') is not None:
                dia_semana = int(kwargs['dia_semana'])
                if 'DIA_SEMANA' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['DIA_SEMANA'] == dia_semana]
                else:
                    df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'].dt.dayofweek == dia_semana]
            
            # Filtro por trimestre
            if kwargs.get('trimestre'):
                trimestre = int(kwargs['trimestre'])
                df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'].dt.quarter == trimestre]
            
            # Filtros de período relativo
            if kwargs.get('ultimos_dias'):
                dias = int(kwargs['ultimos_dias'])
                fecha_limite = datetime.now() - timedelta(days=dias)
                df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'] >= fecha_limite]
            
            if kwargs.get('ultimo_mes'):
                fecha_limite = datetime.now() - timedelta(days=30)
                df_filtrado = df_filtrado[df_filtrado['FECHA_INGRESO_VALE'] >= fecha_limite]
            
        except Exception as e:
            print(f"Error aplicando filtros temporales: {e}")
        
        return df_filtrado
    
    def aplicar_filtro_geografico(self, df, **kwargs):
        """Aplica filtros geográficos y de dependencias"""
        df_filtrado = df.copy()
        
        try:
            # Filtro por dependencia/unidad orgánica
            if kwargs.get('dependencia'):
                dependencia = kwargs['dependencia']
                if isinstance(dependencia, list):
                    df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'].isin(dependencia)]
                else:
                    df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'] == dependencia]
            
            # Filtro por zona (basado en el nombre de la dependencia)
            if kwargs.get('zona'):
                zona = kwargs['zona'].upper()
                df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'].str.contains(zona, na=False, case=False)]
            
            # Filtro por palabras clave en dependencia
            if kwargs.get('buscar_en_dependencia'):
                termino = kwargs['buscar_en_dependencia']
                df_filtrado = df_filtrado[df_filtrado['UNIDAD_ORGANICA'].str.contains(termino, na=False, case=False)]
        
        except Exception as e:
            print(f"Error aplicando filtros geográficos: {e}")
        
        return df_filtrado
    
    def aplicar_filtro_vehicular(self, df, **kwargs):
        """Aplica filtros relacionados con vehículos"""
        df_filtrado = df.copy()
        
        try:
            # Filtro por placa específica
            if kwargs.get('placa'):
                placa = kwargs['placa']
                if isinstance(placa, list):
                    df_filtrado = df_filtrado[df_filtrado['PLACA'].isin(placa)]
                else:
                    df_filtrado = df_filtrado[df_filtrado['PLACA'] == placa]
            
            # Filtro por patrón de placa
            if kwargs.get('patron_placa'):
                patron = kwargs['patron_placa']
                df_filtrado = df_filtrado[df_filtrado['PLACA'].str.contains(patron, na=False, case=False)]
            
            # Filtro por tipo de vehículo (si existe la columna)
            if kwargs.get('tipo_vehiculo') and 'TIPO_VEHICULO' in df_filtrado.columns:
                tipo = kwargs['tipo_vehiculo']
                df_filtrado = df_filtrado[df_filtrado['TIPO_VEHICULO'] == tipo]
            
            # Filtro por rango de kilometraje
            if kwargs.get('km_min'):
                km_min = float(kwargs['km_min'])
                df_filtrado = df_filtrado[df_filtrado['KM_RECORRIDO'] >= km_min]
            
            if kwargs.get('km_max'):
                km_max = float(kwargs['km_max'])
                df_filtrado = df_filtrado[df_filtrado['KM_RECORRIDO'] <= km_max]
        
        except Exception as e:
            print(f"Error aplicando filtros vehiculares: {e}")
        
        return df_filtrado
    
    def aplicar_filtro_consumo(self, df, **kwargs):
        """Aplica filtros relacionados con consumo y eficiencia"""
        df_filtrado = df.copy()
        
        try:
            # Filtros de consumo total
            if kwargs.get('consumo_min'):
                consumo_min = float(kwargs['consumo_min'])
                df_filtrado = df_filtrado[df_filtrado['TOTAL_CONSUMO'] >= consumo_min]
            
            if kwargs.get('consumo_max'):
                consumo_max = float(kwargs['consumo_max'])
                df_filtrado = df_filtrado[df_filtrado['TOTAL_CONSUMO'] <= consumo_max]
            
            # Filtros de eficiencia
            if kwargs.get('eficiencia_min') and 'EFICIENCIA' in df_filtrado.columns:
                eficiencia_min = float(kwargs['eficiencia_min'])
                df_filtrado = df_filtrado[df_filtrado['EFICIENCIA'] >= eficiencia_min]
            
            if kwargs.get('eficiencia_max') and 'EFICIENCIA' in df_filtrado.columns:
                eficiencia_max = float(kwargs['eficiencia_max'])
                df_filtrado = df_filtrado[df_filtrado['EFICIENCIA'] <= eficiencia_max]
            
            # Filtros de galones
            if kwargs.get('galones_min'):
                galones_min = float(kwargs['galones_min'])
                df_filtrado = df_filtrado[df_filtrado['CANTIDAD_GALONES'] >= galones_min]
            
            if kwargs.get('galones_max'):
                galones_max = float(kwargs['galones_max'])
                df_filtrado = df_filtrado[df_filtrado['CANTIDAD_GALONES'] <= galones_max]
            
            # Filtro por consumo atípico (valores extremos)
            if kwargs.get('excluir_atipicos'):
                # Eliminar valores extremos usando IQR
                Q1 = df_filtrado['TOTAL_CONSUMO'].quantile(0.25)
                Q3 = df_filtrado['TOTAL_CONSUMO'].quantile(0.75)
                IQR = Q3 - Q1
                limite_inferior = Q1 - 1.5 * IQR
                limite_superior = Q3 + 1.5 * IQR
                df_filtrado = df_filtrado[
                    (df_filtrado['TOTAL_CONSUMO'] >= limite_inferior) & 
                    (df_filtrado['TOTAL_CONSUMO'] <= limite_superior)
                ]
        
        except Exception as e:
            print(f"Error aplicando filtros de consumo: {e}")
        
        return df_filtrado
    
    def aplicar_filtro_combustible(self, df, **kwargs):
        """Aplica filtros relacionados con combustible"""
        df_filtrado = df.copy()
        
        try:
            # Filtro por tipo de combustible
            if kwargs.get('tipo_combustible'):
                tipo = kwargs['tipo_combustible']
                if isinstance(tipo, list):
                    df_filtrado = df_filtrado[df_filtrado['TIPO_COMBUSTIBLE'].isin(tipo)]
                else:
                    df_filtrado = df_filtrado[df_filtrado['TIPO_COMBUSTIBLE'] == tipo]
            
            # Filtros de precio
            if kwargs.get('precio_min'):
                precio_min = float(kwargs['precio_min'])
                df_filtrado = df_filtrado[df_filtrado['PRECIO'] >= precio_min]
            
            if kwargs.get('precio_max'):
                precio_max = float(kwargs['precio_max'])
                df_filtrado = df_filtrado[df_filtrado['PRECIO'] <= precio_max]
        
        except Exception as e:
            print(f"Error aplicando filtros de combustible: {e}")
        
        return df_filtrado
    
    def aplicar_filtro_anomalias(self, df, **kwargs):
        """Aplica filtros relacionados con anomalías"""
        df_filtrado = df.copy()
        
        try:
            # Filtro para mostrar solo registros con anomalías
            if kwargs.get('solo_anomalias') and 'ANOMALIA' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['ANOMALIA'] == 1]
            
            # Filtro para excluir anomalías
            if kwargs.get('sin_anomalias') and 'ANOMALIA' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['ANOMALIA'] == 0]
            
            # Filtro por nivel de riesgo
            if kwargs.get('nivel_riesgo') and 'NIVEL_RIESGO' in df_filtrado.columns:
                nivel = kwargs['nivel_riesgo']
                if isinstance(nivel, list):
                    df_filtrado = df_filtrado[df_filtrado['NIVEL_RIESGO'].isin(nivel)]
                else:
                    df_filtrado = df_filtrado[df_filtrado['NIVEL_RIESGO'] == nivel]
            
            # Filtro por score de anomalía
            if kwargs.get('score_anomalia_min') and 'SCORE_ANOMALIA' in df_filtrado.columns:
                score_min = float(kwargs['score_anomalia_min'])
                df_filtrado = df_filtrado[df_filtrado['SCORE_ANOMALIA'] >= score_min]
        
        except Exception as e:
            print(f"Error aplicando filtros de anomalías: {e}")
        
        return df_filtrado
    
    def aplicar_filtros_combinados(self, df, filtros):
        """Aplica múltiples filtros de forma combinada"""
        df_resultado = df.copy()
        
        try:
            # Aplicar filtros temporales
            df_resultado = self.aplicar_filtro_temporal(df_resultado, **filtros)
            
            # Aplicar filtros geográficos
            df_resultado = self.aplicar_filtro_geografico(df_resultado, **filtros)
            
            # Aplicar filtros vehiculares
            df_resultado = self.aplicar_filtro_vehicular(df_resultado, **filtros)
            
            # Aplicar filtros de consumo
            df_resultado = self.aplicar_filtro_consumo(df_resultado, **filtros)
            
            # Aplicar filtros de combustible
            df_resultado = self.aplicar_filtro_combustible(df_resultado, **filtros)
            
            # Aplicar filtros de anomalías
            df_resultado = self.aplicar_filtro_anomalias(df_resultado, **filtros)
            
        except Exception as e:
            print(f"Error aplicando filtros combinados: {e}")
        
        return df_resultado
    
    def obtener_opciones_filtro(self, df):
        """Obtiene las opciones disponibles para cada tipo de filtro"""
        opciones = {}
        
        try:
            # Opciones temporales
            if 'FECHA_INGRESO_VALE' in df.columns:
                df['fecha_temp'] = pd.to_datetime(df['FECHA_INGRESO_VALE'])
                opciones['fechas'] = {
                    'min': df['fecha_temp'].min().strftime('%Y-%m-%d') if not df['fecha_temp'].isna().all() else None,
                    'max': df['fecha_temp'].max().strftime('%Y-%m-%d') if not df['fecha_temp'].isna().all() else None
                }
                opciones['meses'] = sorted(df['fecha_temp'].dt.month.dropna().unique().tolist())
                opciones['años'] = sorted(df['fecha_temp'].dt.year.dropna().unique().tolist())
            
            # Opciones geográficas
            if 'UNIDAD_ORGANICA' in df.columns:
                opciones['dependencias'] = sorted(df['UNIDAD_ORGANICA'].dropna().unique().tolist())
            
            # Opciones vehiculares
            if 'PLACA' in df.columns:
                opciones['placas'] = sorted(df['PLACA'].dropna().unique().tolist())
            
            if 'TIPO_VEHICULO' in df.columns:
                opciones['tipos_vehiculo'] = sorted(df['TIPO_VEHICULO'].dropna().unique().tolist())
            
            # Opciones de combustible
            if 'TIPO_COMBUSTIBLE' in df.columns:
                opciones['tipos_combustible'] = sorted(df['TIPO_COMBUSTIBLE'].dropna().unique().tolist())
            
            # Rangos de valores numéricos
            columnas_numericas = ['TOTAL_CONSUMO', 'KM_RECORRIDO', 'CANTIDAD_GALONES', 'PRECIO', 'EFICIENCIA']
            for col in columnas_numericas:
                if col in df.columns:
                    valores = df[col].dropna()
                    if not valores.empty:
                        opciones[f'rango_{col.lower()}'] = {
                            'min': float(valores.min()),
                            'max': float(valores.max()),
                            'promedio': float(valores.mean())
                        }
            
            # Opciones de anomalías
            if 'NIVEL_RIESGO' in df.columns:
                opciones['niveles_riesgo'] = sorted(df['NIVEL_RIESGO'].dropna().unique().tolist())
        
        except Exception as e:
            print(f"Error obteniendo opciones de filtro: {e}")
        
        return opciones
    
    def crear_filtro_rapido(self, nombre, parametros):
        """Crea un filtro rápido predefinido"""
        filtros_rapidos = {
            'anomalias_criticas': {'solo_anomalias': True, 'nivel_riesgo': 'Critico'},
            'alto_consumo': {'consumo_min': 100, 'solo_anomalias': True},
            'baja_eficiencia': {'eficiencia_max': 8, 'excluir_atipicos': True},
            'ultimo_mes': {'ultimo_mes': True},
            'fines_semana': {'dia_semana': [5, 6]},
            'gerencias': {'buscar_en_dependencia': 'GERENCIA'},
            'vehiculos_problema': {'solo_anomalias': True, 'eficiencia_max': 6}
        }
        
        if nombre in filtros_rapidos:
            return filtros_rapidos[nombre]
        
        return parametros
    
    def generar_resumen_filtro(self, df_original, df_filtrado, filtros_aplicados):
        """Genera un resumen de los resultados del filtro"""
        try:
            total_original = len(df_original)
            total_filtrado = len(df_filtrado)
            porcentaje_filtrado = (total_filtrado / total_original * 100) if total_original > 0 else 0
            
            # Calcular estadísticas básicas
            consumo_total = df_filtrado['TOTAL_CONSUMO'].sum() if 'TOTAL_CONSUMO' in df_filtrado.columns else 0
            anomalias = df_filtrado['ANOMALIA'].sum() if 'ANOMALIA' in df_filtrado.columns else 0
            
            resumen = {
                'registros_originales': total_original,
                'registros_filtrados': total_filtrado,
                'porcentaje_datos': round(porcentaje_filtrado, 2),
                'consumo_total_filtrado': round(consumo_total, 2),
                'anomalias_encontradas': int(anomalias),
                'filtros_aplicados': filtros_aplicados,
                'vehículos_unicos': df_filtrado['PLACA'].nunique() if 'PLACA' in df_filtrado.columns else 0,
                'dependencias_unicas': df_filtrado['UNIDAD_ORGANICA'].nunique() if 'UNIDAD_ORGANICA' in df_filtrado.columns else 0
            }
            
            return resumen
            
        except Exception as e:
            print(f"Error generando resumen: {e}")
            return {}
