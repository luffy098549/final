# models/reportes.py
from .solicitud import Solicitud
from .denuncia import Denuncia
from .usuario import Usuario
from collections import defaultdict
from datetime import datetime, timedelta

class Reportes:
    """Clase para generar reportes y estadísticas"""
    
    @staticmethod
    def obtener_estadisticas_generales():
        """Obtiene estadísticas generales del sistema"""
        try:
            solicitudes = Solicitud.cargar_todos()
            denuncias = Denuncia.cargar_todos()
            usuarios = Usuario.query.all()
            
            # Estadísticas de solicitudes
            total_solicitudes = len(solicitudes)
            solicitudes_pendientes = len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']])
            solicitudes_completadas = len([s for s in solicitudes if s.estado == 'completado'])
            
            # Estadísticas de denuncias
            total_denuncias = len(denuncias)
            denuncias_pendientes = len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
            denuncias_resueltas = len([d for d in denuncias if d.estado == 'resuelto'])
            
            # Estadísticas de usuarios
            total_usuarios = len(usuarios)
            admins = len([u for u in usuarios if u.rol in ['super_admin', 'admin'] or u.tipo == 'admin'])
            ciudadanos = total_usuarios - admins
            
            return {
                'solicitudes': {
                    'total': total_solicitudes,
                    'pendientes': solicitudes_pendientes,
                    'completadas': solicitudes_completadas,
                    'tasa_resolucion': round((solicitudes_completadas / total_solicitudes * 100) if total_solicitudes > 0 else 0, 1)
                },
                'denuncias': {
                    'total': total_denuncias,
                    'pendientes': denuncias_pendientes,
                    'resueltas': denuncias_resueltas,
                    'tasa_resolucion': round((denuncias_resueltas / total_denuncias * 100) if total_denuncias > 0 else 0, 1)
                },
                'usuarios': {
                    'total': total_usuarios,
                    'administradores': admins,
                    'ciudadanos': ciudadanos
                }
            }
        except Exception as e:
            print(f"Error en estadísticas: {e}")
            return {}
    
    @staticmethod
    def obtener_solicitudes_por_servicio():
        """Obtiene el conteo de solicitudes por servicio"""
        try:
            solicitudes = Solicitud.cargar_todos()
            por_servicio = defaultdict(int)
            for s in solicitudes:
                servicio_id = str(s.servicio_id)
                por_servicio[servicio_id] += 1
            return dict(por_servicio)
        except Exception as e:
            print(f"Error en solicitudes por servicio: {e}")
            return {}
    
    @staticmethod
    def obtener_denuncias_por_tipo():
        """Obtiene el conteo de denuncias por tipo"""
        try:
            denuncias = Denuncia.cargar_todos()
            por_tipo = defaultdict(int)
            for d in denuncias:
                por_tipo[d.tipo] += 1
            return dict(por_tipo)
        except Exception as e:
            print(f"Error en denuncias por tipo: {e}")
            return {}
    
    @staticmethod
    def obtener_solicitudes_por_mes(meses=6):
        """Obtiene solicitudes agrupadas por mes"""
        try:
            solicitudes = Solicitud.cargar_todos()
            por_mes = {}
            hoy = datetime.now()
            
            for i in range(meses):
                fecha = hoy - timedelta(days=30*i)
                mes = fecha.strftime("%Y-%m")
                count = 0
                for s in solicitudes:
                    if s.fecha_creacion.startswith(mes):
                        count += 1
                por_mes[mes] = count
            
            return por_mes
        except Exception as e:
            print(f"Error en solicitudes por mes: {e}")
            return {}
    
    @staticmethod
    def obtener_actividad_reciente(dias=7):
        """Obtiene actividad de los últimos días"""
        try:
            solicitudes = Solicitud.cargar_todos()
            denuncias = Denuncia.cargar_todos()
            
            fecha_limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
            
            solicitudes_recientes = [s for s in solicitudes if s.fecha_creacion >= fecha_limite]
            denuncias_recientes = [d for d in denuncias if d.fecha_creacion >= fecha_limite]
            
            return {
                'solicitudes': len(solicitudes_recientes),
                'denuncias': len(denuncias_recientes),
                'total': len(solicitudes_recientes) + len(denuncias_recientes)
            }
        except Exception as e:
            print(f"Error en actividad reciente: {e}")
            return {'solicitudes': 0, 'denuncias': 0, 'total': 0}