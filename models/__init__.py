# models/__init__.py

from .usuario import Usuario
from .solicitud import Solicitud
from .denuncia import Denuncia
from .cita import Cita
from .encuesta import Encuesta
from .plantilla import Plantilla
from .configuracion import Configuracion 

# 🔥 IMPORTAR REPORTES CON SEGURIDAD
try:
    from .reportes import Reportes
except ImportError:
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

# 🔥 IMPORTAR NOTIFICACIONES (DEBE EXISTIR)
from .notificacion import Notificacion

# 🔥 IMPORTAR MENSAJES (DEBE EXISTIR)
from .mensaje import Mensaje