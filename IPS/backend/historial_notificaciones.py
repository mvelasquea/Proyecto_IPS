"""
Módulo de historial de búsqueda y notificaciones
"""
import json
import os
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from models import db
import hashlib

class HistorialBusqueda(db.Model):
    """Modelo para guardar el historial de búsquedas"""
    __tablename__ = 'historial_busquedas'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    filtros_aplicados = db.Column(db.Text, nullable=False)  # JSON string
    resultados_encontrados = db.Column(db.Integer, default=0)
    anomalias_detectadas = db.Column(db.Integer, default=0)
    consumo_total_analizado = db.Column(db.Float, default=0.0)
    fecha_busqueda = db.Column(db.DateTime, default=datetime.utcnow)
    nombre_archivo = db.Column(db.String(255))
    hash_dataset = db.Column(db.String(64))  # Hash del dataset para detectar cambios
    
    user = db.relationship('User', backref='busquedas')

class NotificacionSistema(db.Model):
    """Modelo para notificaciones del sistema"""
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # 'dataset_actualizado', 'alerta', 'reporte'
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    metadata_extra = db.Column(db.Text)  # JSON adicional
    
    user = db.relationship('User', backref='notificaciones')

class GestorHistorialNotificaciones:
    def __init__(self):
        self.archivo_dataset_hash = 'dataset_hash.json'
        
    def calcular_hash_dataset(self, df):
        """Calcula un hash del dataset para detectar cambios"""
        try:
            # Crear un string representativo del dataset
            dataset_str = f"{len(df)}_{df.columns.tolist()}_{df.dtypes.to_dict()}"
            if not df.empty:
                dataset_str += f"_{df.iloc[0].to_dict()}_{df.iloc[-1].to_dict()}"
            
            return hashlib.md5(dataset_str.encode()).hexdigest()
        except Exception as e:
            print(f"Error calculando hash: {e}")
            return "unknown"
    
    def guardar_busqueda(self, user_id, filtros, resultados_df, nombre_archivo=None):
        """Guarda una búsqueda en el historial"""
        try:
            # Calcular estadísticas de los resultados
            total_registros = len(resultados_df) if not resultados_df.empty else 0
            anomalias = resultados_df['ANOMALIA'].sum() if 'ANOMALIA' in resultados_df.columns else 0
            consumo_total = resultados_df['TOTAL_CONSUMO'].sum() if 'TOTAL_CONSUMO' in resultados_df.columns else 0
            hash_dataset = self.calcular_hash_dataset(resultados_df)
            
            # Crear registro de historial
            busqueda = HistorialBusqueda(
                user_id=user_id,
                filtros_aplicados=json.dumps(filtros),
                resultados_encontrados=total_registros,
                anomalias_detectadas=int(anomalias),
                consumo_total_analizado=float(consumo_total),
                nombre_archivo=nombre_archivo,
                hash_dataset=hash_dataset
            )
            
            db.session.add(busqueda)
            db.session.commit()
            
            return busqueda.id
            
        except Exception as e:
            print(f"Error guardando búsqueda: {e}")
            db.session.rollback()
            return None
    
    def obtener_historial_usuario(self, user_id, limite=20):
        """Obtiene el historial de búsquedas de un usuario"""
        try:
            busquedas = HistorialBusqueda.query.filter_by(user_id=user_id)\
                                               .order_by(HistorialBusqueda.fecha_busqueda.desc())\
                                               .limit(limite).all()
            
            historial = []
            for busqueda in busquedas:
                try:
                    filtros = json.loads(busqueda.filtros_aplicados)
                except:
                    filtros = {}
                
                historial.append({
                    'id': busqueda.id,
                    'filtros': filtros,
                    'resultados_encontrados': busqueda.resultados_encontrados,
                    'anomalias_detectadas': busqueda.anomalias_detectadas,
                    'consumo_total_analizado': busqueda.consumo_total_analizado,
                    'fecha_busqueda': busqueda.fecha_busqueda.isoformat(),
                    'nombre_archivo': busqueda.nombre_archivo
                })
            
            return historial
            
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            return []
    
    def obtener_busquedas_frecuentes(self, user_id, limite=10):
        """Obtiene las búsquedas más frecuentes de un usuario"""
        try:
            # Obtener todas las búsquedas del usuario
            busquedas = HistorialBusqueda.query.filter_by(user_id=user_id).all()
            
            # Contar frecuencia de filtros similares
            filtros_frecuencia = {}
            for busqueda in busquedas:
                try:
                    filtros = json.loads(busqueda.filtros_aplicados)
                    # Crear una clave única para filtros similares
                    clave_filtros = f"{filtros.get('mes', 'N/A')}_{filtros.get('dependencia', 'N/A')}"
                    
                    if clave_filtros not in filtros_frecuencia:
                        filtros_frecuencia[clave_filtros] = {
                            'filtros': filtros,
                            'frecuencia': 0,
                            'ultima_vez': busqueda.fecha_busqueda,
                            'promedio_anomalias': 0,
                            'promedio_consumo': 0
                        }
                    
                    filtros_frecuencia[clave_filtros]['frecuencia'] += 1
                    filtros_frecuencia[clave_filtros]['promedio_anomalias'] += busqueda.anomalias_detectadas
                    filtros_frecuencia[clave_filtros]['promedio_consumo'] += busqueda.consumo_total_analizado
                    
                    if busqueda.fecha_busqueda > filtros_frecuencia[clave_filtros]['ultima_vez']:
                        filtros_frecuencia[clave_filtros]['ultima_vez'] = busqueda.fecha_busqueda
                
                except:
                    continue
            
            # Calcular promedios y ordenar por frecuencia
            for clave in filtros_frecuencia:
                freq = filtros_frecuencia[clave]['frecuencia']
                filtros_frecuencia[clave]['promedio_anomalias'] /= freq
                filtros_frecuencia[clave]['promedio_consumo'] /= freq
            
            # Convertir a lista y ordenar
            busquedas_frecuentes = list(filtros_frecuencia.values())
            busquedas_frecuentes.sort(key=lambda x: x['frecuencia'], reverse=True)
            
            return busquedas_frecuentes[:limite]
            
        except Exception as e:
            print(f"Error obteniendo búsquedas frecuentes: {e}")
            return []
    
    def verificar_cambios_dataset(self, df_actual, nombre_archivo=None):
        """Verifica si el dataset ha cambiado y genera notificaciones"""
        try:
            hash_actual = self.calcular_hash_dataset(df_actual)
            
            # Cargar hash anterior
            hash_anterior = None
            if os.path.exists(self.archivo_dataset_hash):
                with open(self.archivo_dataset_hash, 'r') as f:
                    data = json.load(f)
                    hash_anterior = data.get('hash')
            
            # Si el hash cambió, generar notificaciones
            if hash_anterior and hash_anterior != hash_actual:
                self.crear_notificacion_global(
                    tipo='dataset_actualizado',
                    titulo='Dataset Actualizado',
                    mensaje=f'El dataset {nombre_archivo or "principal"} ha sido actualizado. '
                           f'Se recomienda revisar los análisis anteriores.',
                    metadata={'hash_anterior': hash_anterior, 'hash_nuevo': hash_actual}
                )
            
            # Guardar nuevo hash
            with open(self.archivo_dataset_hash, 'w') as f:
                json.dump({
                    'hash': hash_actual,
                    'fecha_actualizacion': datetime.now().isoformat(),
                    'nombre_archivo': nombre_archivo
                }, f)
            
            return hash_anterior != hash_actual
            
        except Exception as e:
            print(f"Error verificando cambios dataset: {e}")
            return False
    
    def crear_notificacion(self, user_id, tipo, titulo, mensaje, metadata=None):
        """Crea una notificación para un usuario específico"""
        try:
            notificacion = NotificacionSistema(
                user_id=user_id,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                metadata_extra=json.dumps(metadata) if metadata else None
            )
            
            db.session.add(notificacion)
            db.session.commit()
            
            return notificacion.id
            
        except Exception as e:
            print(f"Error creando notificación: {e}")
            db.session.rollback()
            return None
    
    def crear_notificacion_global(self, tipo, titulo, mensaje, metadata=None):
        """Crea una notificación para todos los usuarios"""
        try:
            from models import User
            usuarios = User.query.all()
            
            notificaciones_creadas = 0
            for usuario in usuarios:
                if self.crear_notificacion(usuario.id, tipo, titulo, mensaje, metadata):
                    notificaciones_creadas += 1
            
            return notificaciones_creadas
            
        except Exception as e:
            print(f"Error creando notificaciones globales: {e}")
            return 0
    
    def obtener_notificaciones_usuario(self, user_id, solo_no_leidas=False, limite=50):
        """Obtiene las notificaciones de un usuario"""
        try:
            query = NotificacionSistema.query.filter_by(user_id=user_id)
            
            if solo_no_leidas:
                query = query.filter_by(leida=False)
            
            notificaciones = query.order_by(NotificacionSistema.fecha_creacion.desc())\
                                  .limit(limite).all()
            
            resultado = []
            for notif in notificaciones:
                metadata = None
                try:
                    if notif.metadata_extra:
                        metadata = json.loads(notif.metadata_extra)
                except:
                    pass
                
                resultado.append({
                    'id': notif.id,
                    'tipo': notif.tipo,
                    'titulo': notif.titulo,
                    'mensaje': notif.mensaje,
                    'leida': notif.leida,
                    'fecha_creacion': notif.fecha_creacion.isoformat(),
                    'metadata': metadata
                })
            
            return resultado
            
        except Exception as e:
            print(f"Error obteniendo notificaciones: {e}")
            return []
    
    def marcar_notificacion_leida(self, notificacion_id, user_id):
        """Marca una notificación como leída"""
        try:
            notificacion = NotificacionSistema.query.filter_by(
                id=notificacion_id, 
                user_id=user_id
            ).first()
            
            if notificacion:
                notificacion.leida = True
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error marcando notificación como leída: {e}")
            db.session.rollback()
            return False
    
    def marcar_todas_leidas(self, user_id):
        """Marca todas las notificaciones de un usuario como leídas"""
        try:
            NotificacionSistema.query.filter_by(user_id=user_id, leida=False)\
                                     .update({'leida': True})
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error marcando todas como leídas: {e}")
            db.session.rollback()
            return False
    
    def contar_notificaciones_no_leidas(self, user_id):
        """Cuenta las notificaciones no leídas de un usuario"""
        try:
            return NotificacionSistema.query.filter_by(user_id=user_id, leida=False).count()
        except Exception as e:
            print(f"Error contando notificaciones no leídas: {e}")
            return 0
    
    def limpiar_historial_antiguo(self, dias=90):
        """Limpia el historial de búsquedas antiguo"""
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            # Eliminar búsquedas antiguas
            HistorialBusqueda.query.filter(
                HistorialBusqueda.fecha_busqueda < fecha_limite
            ).delete()
            
            # Eliminar notificaciones leídas antiguas
            NotificacionSistema.query.filter(
                NotificacionSistema.fecha_creacion < fecha_limite,
                NotificacionSistema.leida == True
            ).delete()
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error limpiando historial antiguo: {e}")
            db.session.rollback()
            return False
    
    def generar_estadisticas_uso(self, user_id):
        """Genera estadísticas de uso para un usuario"""
        try:
            busquedas = HistorialBusqueda.query.filter_by(user_id=user_id).all()
            
            if not busquedas:
                return {
                    'total_busquedas': 0,
                    'total_anomalias_encontradas': 0,
                    'consumo_total_analizado': 0,
                    'promedio_anomalias_por_busqueda': 0,
                    'dependencia_mas_analizada': 'N/A',
                    'mes_mas_analizado': 'N/A'
                }
            
            total_busquedas = len(busquedas)
            total_anomalias = sum(b.anomalias_detectadas for b in busquedas)
            consumo_total = sum(b.consumo_total_analizado for b in busquedas)
            
            # Analizar dependencias y meses más consultados
            dependencias = {}
            meses = {}
            
            for busqueda in busquedas:
                try:
                    filtros = json.loads(busqueda.filtros_aplicados)
                    dep = filtros.get('dependencia', 'N/A')
                    mes = filtros.get('mes', 'N/A')
                    
                    dependencias[dep] = dependencias.get(dep, 0) + 1
                    meses[mes] = meses.get(mes, 0) + 1
                except:
                    continue
            
            dependencia_mas_analizada = max(dependencias.items(), key=lambda x: x[1])[0] if dependencias else 'N/A'
            mes_mas_analizado = max(meses.items(), key=lambda x: x[1])[0] if meses else 'N/A'
            
            return {
                'total_busquedas': total_busquedas,
                'total_anomalias_encontradas': total_anomalias,
                'consumo_total_analizado': consumo_total,
                'promedio_anomalias_por_busqueda': total_anomalias / total_busquedas,
                'dependencia_mas_analizada': dependencia_mas_analizada,
                'mes_mas_analizado': mes_mas_analizado
            }
            
        except Exception as e:
            print(f"Error generando estadísticas: {e}")
            return {}
