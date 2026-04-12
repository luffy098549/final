# models/__init__.py
from .usuario import Usuario
from .solicitud import Solicitud
from .denuncia import Denuncia
from .cita import Cita
from .encuesta import Encuesta
from .plantilla import Plantilla

# Importar Reportes desde donde corresponda
try:
    from .reportes import Reportes
except ImportError:
    # Si no existe reportes.py, creamos una clase temporal
    class Reportes:
        @staticmethod
        def obtener_estadisticas_generales():
            return {}
        
        @staticmethod
        def obtener_solicitudes_por_servicio():
            return {}
        
        @staticmethod
        def obtener_denuncias_por_tipo():
            return {}