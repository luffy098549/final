"""
Modelos del sistema municipal de Villa Cutupú
"""
from .solicitud import Solicitud
from .denuncia import Denuncia
from .usuario import Usuario
from .reportes import Reportes
from .cita import Cita
from .encuesta import Encuesta
from .plantilla import Plantilla

__all__ = [
    'Solicitud', 
    'Denuncia', 
    'Usuario', 
    'Reportes', 
    'Cita', 
    'Encuesta', 
    'Plantilla'
]