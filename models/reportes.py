"""
Modelo para generar reportes y estadísticas
"""
from datetime import datetime, timedelta
from collections import defaultdict
from .solicitud import Solicitud
from .denuncia import Denuncia
from .cita import Cita
from .encuesta import Encuesta

class Reportes:
    """Clase estática para generar reportes"""
    
    @staticmethod
    def obtener_estadisticas_generales():
        """Obtiene estadísticas generales del sistema"""
        solicitudes = Solicitud.cargar_todos()
        denuncias = Denuncia.cargar_todos()
        
        return {
            'solicitudes': {
                'total': len(solicitudes),
                'pendientes': len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']]),
                'completadas': len([s for s in solicitudes if s.estado == 'completado'])
            },
            'denuncias': {
                'total': len(denuncias),
                'pendientes': len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']]),
                'resueltas': len([d for d in denuncias if d.estado == 'resuelto']),
                'geolocalizadas': len([d for d in denuncias if d.geolocalizada])
            }
        }
    
    @staticmethod
    def obtener_solicitudes_por_servicio():
        """Obtiene conteo de solicitudes por servicio"""
        solicitudes = Solicitud.cargar_todos()
        resultado = defaultdict(int)
        for s in solicitudes:
            resultado[s.servicio_id] += 1
        return dict(resultado)
    
    @staticmethod
    def obtener_denuncias_por_tipo():
        """Obtiene conteo de denuncias por tipo"""
        denuncias = Denuncia.cargar_todos()
        resultado = defaultdict(int)
        for d in denuncias:
            resultado[d.tipo] += 1
        return dict(resultado)
    
    @staticmethod
    def obtener_actividad_por_mes(meses=6):
        """Obtiene actividad de los últimos meses"""
        solicitudes = Solicitud.cargar_todos()
        resultado = {}
        
        for i in range(meses):
            fecha = datetime.now() - timedelta(days=30*i)
            mes = fecha.strftime("%Y-%m")
            count = 0
            for s in solicitudes:
                if s.fecha_creacion.startswith(mes):
                    count += 1
            resultado[mes] = count
        
        return resultado
    
    @staticmethod
    def obtener_satisfaccion():
        """Obtiene estadísticas de satisfacción"""
        return Encuesta.obtener_estadisticas()