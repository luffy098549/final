# models/__init__.py

from .usuario import Usuario
from .solicitud import Solicitud
from .denuncia import Denuncia
from .cita import Cita
from .encuesta import Encuesta
from .plantilla import Plantilla
from .configuracion import Configuracion

# ================================================================
# 🔥 NUEVOS MODELOS DE CONTENIDO
# ================================================================

from .contenido import Contenido
from .transparencia import Transparencia
from .menu_item import MenuItem

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

# 🔥 IMPORTAR NOTIFICACIONES
from .notificacion import Notificacion

# 🔥 IMPORTAR MENSAJES
from .mensaje import Mensaje

# ================================================================
# 🔥 MODELOS DE NOTICIAS Y COMENTARIOS
# ================================================================

from .noticia import CategoriaNoticia, Noticia
from .like_noticia import LikeNoticia
from .comentario_noticia import ComentarioNoticia

# ================================================================
# 🔥 LOGS DE ACTIVIDAD
# ================================================================

from .log_actividad import LogActividad, registrar_log