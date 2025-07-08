"""
Sistema de alertas configurables para el consumo de combustible
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models import db
from flask_sqlalchemy import SQLAlchemy
import json

class SistemaAlertas:
    def __init__(self):
        self.alertas_activas = []
        self.configuraciones = {
            'exceso_consumo': {
                'habilitado': True,
                'umbral_porcentaje': 20,  # % sobre el promedio
                'periodo_analisis': 30  # días
            },
            'mantenimiento_requerido': {
                'habilitado': True,
                'umbral_km': 5000,  # km para mantenimiento
                'umbral_eficiencia': 8  # km/gal mínimo
            },
            'anomalias_frecuentes': {
                'habilitado': True,
                'max_anomalias_mes': 5,
                'periodo': 30  # días
            },
            'consumo_fin_semana': {
                'habilitado': True,
                'umbral_porcentaje': 30  # % del consumo total
            }
        }
    
    def configurar_alerta(self, tipo_alerta, configuracion):
        """Configura los parámetros de una alerta específica"""
        if tipo_alerta in self.configuraciones:
            self.configuraciones[tipo_alerta].update(configuracion)
            return True
        return False
    
    def verificar_exceso_consumo(self, df, vehiculo=None):
        """Verifica si hay exceso de consumo comparado con el promedio"""
        alertas = []
        
        if not self.configuraciones['exceso_consumo']['habilitado']:
            return alertas
            
        try:
            # Filtrar últimos días según configuración
            dias_analisis = self.configuraciones['exceso_consumo']['periodo_analisis']
            fecha_limite = datetime.now() - timedelta(days=dias_analisis)
            
            df['fecha'] = pd.to_datetime(df['FECHA_INGRESO_VALE'])
            df_reciente = df[df['fecha'] >= fecha_limite]
            
            if df_reciente.empty:
                return alertas
            
            # Analizar por vehículo o general
            if vehiculo:
                df_vehiculo = df_reciente[df_reciente['PLACA'] == vehiculo]
                if not df_vehiculo.empty:
                    consumo_actual = df_vehiculo['TOTAL_CONSUMO'].sum()
                    consumo_promedio = df[df['PLACA'] == vehiculo]['TOTAL_CONSUMO'].mean() * len(df_vehiculo)
                    
                    if consumo_actual > consumo_promedio * (1 + self.configuraciones['exceso_consumo']['umbral_porcentaje'] / 100):
                        alertas.append({
                            'tipo': 'exceso_consumo',
                            'nivel': 'alto',
                            'vehiculo': vehiculo,
                            'mensaje': f'Vehículo {vehiculo} ha excedido el consumo promedio en {((consumo_actual/consumo_promedio - 1) * 100):.1f}%',
                            'valor_actual': consumo_actual,
                            'valor_esperado': consumo_promedio,
                            'fecha': datetime.now().isoformat()
                        })
            else:
                # Analizar todos los vehículos
                for placa in df_reciente['PLACA'].unique():
                    df_vehiculo = df_reciente[df_reciente['PLACA'] == placa]
                    if len(df_vehiculo) >= 3:  # Mínimo 3 registros
                        consumo_actual = df_vehiculo['TOTAL_CONSUMO'].sum()
                        df_historico = df[df['PLACA'] == placa]
                        consumo_promedio = df_historico['TOTAL_CONSUMO'].mean() * len(df_vehiculo)
                        
                        if consumo_actual > consumo_promedio * (1 + self.configuraciones['exceso_consumo']['umbral_porcentaje'] / 100):
                            exceso_porcentaje = ((consumo_actual/consumo_promedio - 1) * 100)
                            nivel = 'critico' if exceso_porcentaje > 50 else 'alto' if exceso_porcentaje > 30 else 'medio'
                            
                            alertas.append({
                                'tipo': 'exceso_consumo',
                                'nivel': nivel,
                                'vehiculo': placa,
                                'mensaje': f'Vehículo {placa} ha excedido el consumo promedio en {exceso_porcentaje:.1f}%',
                                'valor_actual': consumo_actual,
                                'valor_esperado': consumo_promedio,
                                'fecha': datetime.now().isoformat()
                            })
        
        except Exception as e:
            print(f"Error verificando exceso de consumo: {e}")
        
        return alertas
    
    def verificar_mantenimiento_requerido(self, df):
        """Verifica si algún vehículo requiere mantenimiento"""
        alertas = []
        
        if not self.configuraciones['mantenimiento_requerido']['habilitado']:
            return alertas
            
        try:
            umbral_km = self.configuraciones['mantenimiento_requerido']['umbral_km']
            umbral_eficiencia = self.configuraciones['mantenimiento_requerido']['umbral_eficiencia']
            
            # Analizar por vehículo
            for placa in df['PLACA'].unique():
                df_vehiculo = df[df['PLACA'] == placa]
                
                # Verificar kilómetros acumulados
                km_total = df_vehiculo['KM_RECORRIDO'].sum()
                
                # Verificar eficiencia promedio
                eficiencia_promedio = df_vehiculo['EFICIENCIA'].mean()
                
                # Alertas por alto kilometraje
                if km_total >= umbral_km:
                    alertas.append({
                        'tipo': 'mantenimiento_km',
                        'nivel': 'medio',
                        'vehiculo': placa,
                        'mensaje': f'Vehículo {placa} ha alcanzado {km_total:,.0f} km, se recomienda mantenimiento',
                        'km_acumulados': km_total,
                        'fecha': datetime.now().isoformat()
                    })
                
                # Alertas por baja eficiencia
                if not pd.isna(eficiencia_promedio) and eficiencia_promedio < umbral_eficiencia:
                    alertas.append({
                        'tipo': 'mantenimiento_eficiencia',
                        'nivel': 'alto',
                        'vehiculo': placa,
                        'mensaje': f'Vehículo {placa} tiene baja eficiencia ({eficiencia_promedio:.2f} km/gal), revisar motor',
                        'eficiencia_actual': eficiencia_promedio,
                        'eficiencia_minima': umbral_eficiencia,
                        'fecha': datetime.now().isoformat()
                    })
        
        except Exception as e:
            print(f"Error verificando mantenimiento: {e}")
        
        return alertas
    
    def verificar_anomalias_frecuentes(self, df):
        """Verifica si hay vehículos con anomalías frecuentes"""
        alertas = []
        
        if not self.configuraciones['anomalias_frecuentes']['habilitado']:
            return alertas
            
        try:
            if 'ANOMALIA' not in df.columns:
                return alertas
                
            max_anomalias = self.configuraciones['anomalias_frecuentes']['max_anomalias_mes']
            periodo = self.configuraciones['anomalias_frecuentes']['periodo']
            
            fecha_limite = datetime.now() - timedelta(days=periodo)
            df['fecha'] = pd.to_datetime(df['FECHA_INGRESO_VALE'])
            df_reciente = df[df['fecha'] >= fecha_limite]
            
            # Contar anomalías por vehículo
            anomalias_por_vehiculo = df_reciente.groupby('PLACA')['ANOMALIA'].sum()
            
            for placa, cantidad_anomalias in anomalias_por_vehiculo.items():
                if cantidad_anomalias >= max_anomalias:
                    nivel = 'critico' if cantidad_anomalias >= max_anomalias * 2 else 'alto'
                    alertas.append({
                        'tipo': 'anomalias_frecuentes',
                        'nivel': nivel,
                        'vehiculo': placa,
                        'mensaje': f'Vehículo {placa} tiene {cantidad_anomalias} anomalías en {periodo} días',
                        'cantidad_anomalias': int(cantidad_anomalias),
                        'periodo_dias': periodo,
                        'fecha': datetime.now().isoformat()
                    })
        
        except Exception as e:
            print(f"Error verificando anomalías frecuentes: {e}")
        
        return alertas
    
    def verificar_consumo_fin_semana(self, df):
        """Verifica el consumo en fines de semana"""
        alertas = []
        
        if not self.configuraciones['consumo_fin_semana']['habilitado']:
            return alertas
            
        try:
            if 'DIA_SEMANA' not in df.columns:
                return alertas
                
            umbral_porcentaje = self.configuraciones['consumo_fin_semana']['umbral_porcentaje']
            
            # Consumo total
            consumo_total = df['TOTAL_CONSUMO'].sum()
            
            # Consumo en fines de semana (sábado=5, domingo=6)
            consumo_fds = df[df['DIA_SEMANA'].isin([5, 6])]['TOTAL_CONSUMO'].sum()
            
            porcentaje_fds = (consumo_fds / consumo_total * 100) if consumo_total > 0 else 0
            
            if porcentaje_fds > umbral_porcentaje:
                nivel = 'alto' if porcentaje_fds > umbral_porcentaje * 1.5 else 'medio'
                alertas.append({
                    'tipo': 'consumo_fin_semana',
                    'nivel': nivel,
                    'mensaje': f'El {porcentaje_fds:.1f}% del consumo ocurre en fines de semana (límite: {umbral_porcentaje}%)',
                    'porcentaje_fds': porcentaje_fds,
                    'consumo_fds': consumo_fds,
                    'umbral': umbral_porcentaje,
                    'fecha': datetime.now().isoformat()
                })
        
        except Exception as e:
            print(f"Error verificando consumo fin de semana: {e}")
        
        return alertas
    
    def ejecutar_todas_las_verificaciones(self, df):
        """Ejecuta todas las verificaciones de alertas"""
        todas_alertas = []
        
        try:
            # Verificar exceso de consumo
            todas_alertas.extend(self.verificar_exceso_consumo(df))
            
            # Verificar mantenimiento requerido
            todas_alertas.extend(self.verificar_mantenimiento_requerido(df))
            
            # Verificar anomalías frecuentes
            todas_alertas.extend(self.verificar_anomalias_frecuentes(df))
            
            # Verificar consumo fin de semana
            todas_alertas.extend(self.verificar_consumo_fin_semana(df))
            
            # Ordenar por nivel de prioridad
            prioridad = {'critico': 0, 'alto': 1, 'medio': 2, 'bajo': 3}
            todas_alertas.sort(key=lambda x: prioridad.get(x['nivel'], 3))
            
            self.alertas_activas = todas_alertas
            
        except Exception as e:
            print(f"Error ejecutando verificaciones: {e}")
        
        return todas_alertas
    
    def obtener_alertas_por_nivel(self, nivel):
        """Obtiene alertas filtradas por nivel"""
        return [alerta for alerta in self.alertas_activas if alerta.get('nivel') == nivel]
    
    def obtener_alertas_por_vehiculo(self, placa):
        """Obtiene alertas filtradas por vehículo"""
        return [alerta for alerta in self.alertas_activas if alerta.get('vehiculo') == placa]
    
    def obtener_configuraciones(self):
        """Obtiene las configuraciones actuales de las alertas"""
        return self.configuraciones
    
    def actualizar_configuraciones(self, nuevas_configuraciones):
        """Actualiza las configuraciones de las alertas"""
        try:
            for tipo_alerta, config in nuevas_configuraciones.items():
                if tipo_alerta in self.configuraciones:
                    self.configuraciones[tipo_alerta].update(config)
            return True
        except Exception as e:
            print(f"Error actualizando configuraciones: {e}")
            return False
    
    def generar_resumen_alertas(self):
        """Genera un resumen de las alertas activas"""
        if not self.alertas_activas:
            return {
                'total': 0,
                'por_nivel': {},
                'por_tipo': {},
                'mensaje': 'No hay alertas activas'
            }
        
        total = len(self.alertas_activas)
        
        # Contar por nivel
        por_nivel = {}
        for alerta in self.alertas_activas:
            nivel = alerta.get('nivel', 'desconocido')
            por_nivel[nivel] = por_nivel.get(nivel, 0) + 1
        
        # Contar por tipo
        por_tipo = {}
        for alerta in self.alertas_activas:
            tipo = alerta.get('tipo', 'desconocido')
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        
        return {
            'total': total,
            'por_nivel': por_nivel,
            'por_tipo': por_tipo,
            'alertas_criticas': len([a for a in self.alertas_activas if a.get('nivel') == 'critico']),
            'ultima_actualizacion': datetime.now().isoformat()
        }
