from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from pydantic import BaseModel
from enum import Enum

class TipoAlerta(str, Enum):
    CONSUMO_EXCESIVO = "consumo_excesivo"
    MANTENIMIENTO = "mantenimiento"
    FRECUENCIA_ALTA = "frecuencia_alta"
    RENDIMIENTO_BAJO = "rendimiento_bajo"
    PREDICCION_ANOMALA = "prediccion_anomala"

class NivelAlerta(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class ConfiguracionAlerta(BaseModel):
    id: Optional[int] = None
    usuario_email: str
    tipo_alerta: TipoAlerta
    nivel: NivelAlerta
    umbral_valor: float
    activa: bool = True
    vehiculos_especificos: Optional[List[str]] = None
    horario_notificacion: str = "08:00-18:00"
    
class Alerta(BaseModel):
    id: Optional[int] = None
    tipo_alerta: TipoAlerta
    nivel: NivelAlerta
    vehiculo: str
    mensaje: str
    valor_actual: float
    umbral_configurado: float
    fecha_deteccion: datetime
    notificada: bool = False
    resuelta: bool = False

class SistemaAlertas:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        """Inicializa la base de datos de alertas"""
        conn = sqlite3.connect('alertas.db')
        cursor = conn.cursor()
        
        # Tabla de configuraciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuraciones_alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                tipo_alerta TEXT NOT NULL,
                nivel TEXT NOT NULL,
                umbral_valor REAL NOT NULL,
                activa BOOLEAN DEFAULT TRUE,
                vehiculos_especificos TEXT,
                horario_notificacion TEXT DEFAULT "08:00-18:00",
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de alertas generadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_alerta TEXT NOT NULL,
                nivel TEXT NOT NULL,
                vehiculo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                valor_actual REAL NOT NULL,
                umbral_configurado REAL NOT NULL,
                fecha_deteccion TIMESTAMP NOT NULL,
                notificada BOOLEAN DEFAULT FALSE,
                resuelta BOOLEAN DEFAULT FALSE,
                usuario_email TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def crear_configuracion_alerta(self, config: ConfiguracionAlerta) -> int:
        """Crea una nueva configuración de alerta"""
        conn = sqlite3.connect('alertas.db')
        cursor = conn.cursor()
        
        vehiculos_str = ','.join(config.vehiculos_especificos) if config.vehiculos_especificos else None
        
        cursor.execute('''
            INSERT INTO configuraciones_alertas 
            (usuario_email, tipo_alerta, nivel, umbral_valor, activa, vehiculos_especificos, horario_notificacion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            config.usuario_email,
            config.tipo_alerta.value,
            config.nivel.value,
            config.umbral_valor,
            config.activa,
            vehiculos_str,
            config.horario_notificacion
        ))
        
        config_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return config_id
    
    def obtener_configuraciones_usuario(self, usuario_email: str) -> List[ConfiguracionAlerta]:
        """Obtiene todas las configuraciones de un usuario"""
        conn = sqlite3.connect('alertas.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, usuario_email, tipo_alerta, nivel, umbral_valor, activa, 
                   vehiculos_especificos, horario_notificacion
            FROM configuraciones_alertas 
            WHERE usuario_email = ?
        ''', (usuario_email,))
        
        configs = []
        for row in cursor.fetchall():
            vehiculos = row[6].split(',') if row[6] else None
            configs.append(ConfiguracionAlerta(
                id=row[0],
                usuario_email=row[1],
                tipo_alerta=TipoAlerta(row[2]),
                nivel=NivelAlerta(row[3]),
                umbral_valor=row[4],
                activa=bool(row[5]),
                vehiculos_especificos=vehiculos,
                horario_notificacion=row[7]
            ))
        
        conn.close()
        return configs
    
    def evaluar_alertas(self, df_datos, df_anomalias) -> List[Alerta]:
        """Evalúa los datos y genera alertas según las configuraciones"""
        alertas_generadas = []
        
        # Obtener todas las configuraciones activas
        conn = sqlite3.connect('alertas.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT usuario_email, tipo_alerta, nivel, umbral_valor, vehiculos_especificos
            FROM configuraciones_alertas 
            WHERE activa = TRUE
        ''')
        
        configuraciones = cursor.fetchall()
        conn.close()
        
        for config in configuraciones:
            usuario_email, tipo_alerta, nivel, umbral_valor, vehiculos_especificos = config
            
            # Filtrar vehículos si está especificado
            if vehiculos_especificos:
                vehiculos_filtro = vehiculos_especificos.split(',')
                df_filtrado = df_datos[df_datos['placa'].isin(vehiculos_filtro)]
            else:
                df_filtrado = df_datos
            
            # Evaluar según el tipo de alerta
            if tipo_alerta == TipoAlerta.CONSUMO_EXCESIVO.value:
                alertas_generadas.extend(
                    self._evaluar_consumo_excesivo(df_filtrado, umbral_valor, nivel, usuario_email)
                )
            
            elif tipo_alerta == TipoAlerta.FRECUENCIA_ALTA.value:
                alertas_generadas.extend(
                    self._evaluar_frecuencia_alta(df_filtrado, umbral_valor, nivel, usuario_email)
                )
            
            elif tipo_alerta == TipoAlerta.RENDIMIENTO_BAJO.value:
                alertas_generadas.extend(
                    self._evaluar_rendimiento_bajo(df_filtrado, umbral_valor, nivel, usuario_email)
                )
        
        # Guardar alertas en la base de datos
        self._guardar_alertas(alertas_generadas)
        
        return alertas_generadas
    
    def _evaluar_consumo_excesivo(self, df, umbral_valor, nivel, usuario_email) -> List[Alerta]:
        """Evalúa alertas por consumo excesivo"""
        alertas = []
        
        for _, row in df.iterrows():
            if row['galones'] > umbral_valor:
                alerta = Alerta(
                    tipo_alerta=TipoAlerta.CONSUMO_EXCESIVO,
                    nivel=NivelAlerta(nivel),
                    vehiculo=row['placa'],
                    mensaje=f"Vehículo {row['placa']} consumió {row['galones']:.2f} galones, excediendo el umbral de {umbral_valor:.2f}",
                    valor_actual=row['galones'],
                    umbral_configurado=umbral_valor,
                    fecha_deteccion=datetime.now()
                )
                alertas.append(alerta)
        
        return alertas
    
    def _evaluar_frecuencia_alta(self, df, umbral_valor, nivel, usuario_email) -> List[Alerta]:
        """Evalúa alertas por frecuencia alta de repostaje"""
        alertas = []
        
        # Calcular frecuencia por vehículo
        frecuencias = df.groupby('placa')['fecha'].apply(
            lambda x: len(x) / ((x.max() - x.min()).days + 1) if len(x) > 1 else 0
        )
        
        for placa, frecuencia in frecuencias.items():
            if frecuencia > umbral_valor:
                alerta = Alerta(
                    tipo_alerta=TipoAlerta.FRECUENCIA_ALTA,
                    nivel=NivelAlerta(nivel),
                    vehiculo=placa,
                    mensaje=f"Vehículo {placa} tiene una frecuencia de repostaje alta: {frecuencia:.2f} veces/día",
                    valor_actual=frecuencia,
                    umbral_configurado=umbral_valor,
                    fecha_deteccion=datetime.now()
                )
                alertas.append(alerta)
        
        return alertas
    
    def _evaluar_rendimiento_bajo(self, df, umbral_valor, nivel, usuario_email) -> List[Alerta]:
        """Evalúa alertas por rendimiento bajo"""
        alertas = []
        
        if 'rendimiento' in df.columns:
            for _, row in df.iterrows():
                if row['rendimiento'] < umbral_valor and row['rendimiento'] > 0:
                    alerta = Alerta(
                        tipo_alerta=TipoAlerta.RENDIMIENTO_BAJO,
                        nivel=NivelAlerta(nivel),
                        vehiculo=row['placa'],
                        mensaje=f"Vehículo {row['placa']} tiene bajo rendimiento: {row['rendimiento']:.2f} km/gal",
                        valor_actual=row['rendimiento'],
                        umbral_configurado=umbral_valor,
                        fecha_deteccion=datetime.now()
                    )
                    alertas.append(alerta)
        
        return alertas
    
    def _guardar_alertas(self, alertas: List[Alerta]):
        """Guarda las alertas en la base de datos"""
        if not alertas:
            return
        
        conn = sqlite3.connect('alertas.db')
        cursor = conn.cursor()
        
        for alerta in alertas:
            cursor.execute('''
                INSERT INTO alertas 
                (tipo_alerta, nivel, vehiculo, mensaje, valor_actual, umbral_configurado, 
                 fecha_deteccion, notificada, resuelta, usuario_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alerta.tipo_alerta.value,
                alerta.nivel.value,
                alerta.vehiculo,
                alerta.mensaje,
                alerta.valor_actual,
                alerta.umbral_configurado,
                alerta.fecha_deteccion,
                alerta.notificada,
                alerta.resuelta,
                'admin@sistema.com'  # Por defecto, se puede mejorar
            ))
        
        conn.commit()
        conn.close()
    
    def obtener_alertas_usuario(self, usuario_email: str, solo_activas: bool = True) -> List[Dict]:
        """Obtiene las alertas de un usuario"""
        conn = sqlite3.connect('alertas.db')
        cursor = conn.cursor()
        
        query = '''
            SELECT id, tipo_alerta, nivel, vehiculo, mensaje, valor_actual, 
                   umbral_configurado, fecha_deteccion, notificada, resuelta
            FROM alertas 
            WHERE usuario_email = ?
        '''
        
        params = [usuario_email]
        
        if solo_activas:
            query += ' AND resuelta = FALSE'
        
        query += ' ORDER BY fecha_deteccion DESC'
        
        cursor.execute(query, params)
        
        alertas = []
        for row in cursor.fetchall():
            alertas.append({
                'id': row[0],
                'tipo_alerta': row[1],
                'nivel': row[2],
                'vehiculo': row[3],
                'mensaje': row[4],
                'valor_actual': row[5],
                'umbral_configurado': row[6],
                'fecha_deteccion': row[7],
                'notificada': bool(row[8]),
                'resuelta': bool(row[9])
            })
        
        conn.close()
        return alertas

# Instancia global del sistema de alertas
sistema_alertas = SistemaAlertas()