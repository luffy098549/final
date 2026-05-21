# ================================================================
# models/__init__.py
# MODELOS DE LA BASE DE DATOS - VERSIÓN COMPLETA
# ================================================================

# ================================================================
# 🔥 MODELOS BASE
# ================================================================
from .usuario import Usuario
from .solicitud import Solicitud
from .denuncia import Denuncia
from .cita import Cita
from .encuesta import Encuesta
from .plantilla import Plantilla
from .configuracion import Configuracion

# ================================================================
# 🔥 SISTEMA DE ROLES Y PERMISOS (NUEVO)
# ================================================================
from .rol import Rol
from .permiso import Permiso
from .rol_permiso import RolPermiso

# ================================================================
# 🔥 MODELOS DE CONTENIDO
# ================================================================
from .contenido import Contenido
from .transparencia import Transparencia
from .menu_item import MenuItem

# ================================================================
# 🔥 REPORTES (CON SEGURIDAD)
# ================================================================
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

# ================================================================
# 🔥 NOTIFICACIONES Y MENSAJES
# ================================================================
from .notificacion import Notificacion
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

# ================================================================
# 🔥 EXPORTAR TODOS LOS MODELOS
# ================================================================
__all__ = [
    # Base
    'Usuario',
    'Solicitud',
    'Denuncia',
    'Cita',
    'Encuesta',
    'Plantilla',
    'Configuracion',
    
    # Roles y Permisos
    'Rol',
    'Permiso',
    'RolPermiso',
    
    # Contenido
    'Contenido',
    'Transparencia',
    'MenuItem',
    
    # Reportes
    'Reportes',
    
    # Notificaciones
    'Notificacion',
    'Mensaje',
    
    # Noticias
    'CategoriaNoticia',
    'Noticia',
    'LikeNoticia',
    'ComentarioNoticia',
    
    # Logs
    'LogActividad',
    'registrar_log'
]

# ================================================================
# 🔥 FUNCIÓN DE INICIALIZACIÓN (OPCIONAL)
# ================================================================
def init_db():
    """
    Inicializa la base de datos con datos por defecto.
    Ejecutar desde Flask shell:
    
    >>> from app import app
    >>> from models import init_db
    >>> with app.app_context():
    ...     init_db()
    """
    from flask import current_app
    from extensions import db
    
    # Crear todas las tablas si no existen
    db.create_all()
    
    # Inicializar roles y permisos
    from .rol import Rol
    from .permiso import Permiso
    from .rol_permiso import RolPermiso
    
    # Crear roles por defecto
    Rol.crear_roles_defecto()
    
    # Crear permisos por defecto
    Permiso.crear_permisos_defecto()
    
    # Obtener referencias
    roles = {r.nombre: r for r in Rol.query.all()}
    permisos = {p.codigo: p for p in Permiso.query.all()}
    
    # Asignar permisos a Super Admin (todos)
    if 'super_admin' in roles:
        for permiso in permisos.values():
            existe = RolPermiso.query.filter_by(
                rol_id=roles['super_admin'].id,
                permiso_id=permiso.id
            ).first()
            if not existe:
                db.session.add(RolPermiso(
                    rol_id=roles['super_admin'].id,
                    permiso_id=permiso.id
                ))
    
    # Asignar permisos a Admin
    if 'admin' in roles:
        admin_permisos = [
            'ver_usuarios', 'editar_usuarios', 'crear_usuarios',
            'ver_solicitudes', 'editar_solicitudes', 'eliminar_solicitudes',
            'ver_denuncias', 'editar_denuncias', 'eliminar_denuncias',
            'editar_contenido', 'editar_menu', 'editar_transparencia',
            'crear_noticias', 'editar_noticias', 'eliminar_noticias', 'moderar_comentarios',
            'ver_configuracion', 'exportar_datos'
        ]
        for codigo in admin_permisos:
            if codigo in permisos:
                existe = RolPermiso.query.filter_by(
                    rol_id=roles['admin'].id,
                    permiso_id=permisos[codigo].id
                ).first()
                if not existe:
                    db.session.add(RolPermiso(
                        rol_id=roles['admin'].id,
                        permiso_id=permisos[codigo].id
                    ))
    
    # Asignar permisos a Moderador
    if 'moderador' in roles:
        mod_permisos = [
            'ver_solicitudes', 'ver_denuncias', 'moderar_comentarios',
            'editar_contenido', 'ver_configuracion'
        ]
        for codigo in mod_permisos:
            if codigo in permisos:
                existe = RolPermiso.query.filter_by(
                    rol_id=roles['moderador'].id,
                    permiso_id=permisos[codigo].id
                ).first()
                if not existe:
                    db.session.add(RolPermiso(
                        rol_id=roles['moderador'].id,
                        permiso_id=permisos[codigo].id
                    ))
    
    db.session.commit()
    
    # Migrar usuarios existentes (que tengan rol string pero no rol_id)
    from .usuario import Usuario
    for usuario in Usuario.query.all():
        if usuario.rol and not usuario.rol_id:
            rol_obj = Rol.query.filter_by(nombre=usuario.rol).first()
            if rol_obj:
                usuario.rol_id = rol_obj.id
                usuarios_migrados += 1
    
    db.session.commit()
    
    print(f"✅ Base de datos inicializada: {len(roles)} roles, {len(permisos)} permisos, {usuarios_migrados} usuarios migrados")
    
    return True