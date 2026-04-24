# rol.py
from enum import Enum
from functools import wraps
from flask import session, flash, redirect, url_for, request

# ================================================================
# PERMISOS DISPONIBLES
# ================================================================

class Permiso(Enum):
    # Usuarios
    VER_USUARIOS = "ver_usuarios"
    EDITAR_USUARIOS = "editar_usuarios"
    CREAR_ADMINS = "crear_admins"
    ELIMINAR_USUARIOS = "eliminar_usuarios"
    
    # Solicitudes
    VER_SOLICITUDES = "ver_solicitudes"
    EDITAR_SOLICITUDES = "editar_solicitudes"
    ELIMINAR_SOLICITUDES = "eliminar_solicitudes"
    
    # Denuncias
    VER_DENUNCIAS = "ver_denuncias"
    EDITAR_DENUNCIAS = "editar_denuncias"
    ELIMINAR_DENUNCIAS = "eliminar_denuncias"
    
    # Configuración
    VER_CONFIG = "ver_config"
    EDITAR_CONFIG = "editar_config"
    
    # Sistema
    VER_BITACORA = "ver_bitacora"
    EXPORTAR_DATOS = "exportar_datos"
    MANTENIMIENTO = "mantenimiento"


# ================================================================
# PERMISOS POR ROL
# ================================================================

PERMISOS_POR_ROL = {
    'super_admin': list(Permiso),  # 🔥 TODOS los permisos

    'admin': [
        Permiso.VER_USUARIOS,
        Permiso.EDITAR_USUARIOS,
        Permiso.CREAR_ADMINS,
        Permiso.ELIMINAR_USUARIOS,
        Permiso.VER_SOLICITUDES,
        Permiso.EDITAR_SOLICITUDES,
        Permiso.ELIMINAR_SOLICITUDES,
        Permiso.VER_DENUNCIAS,
        Permiso.EDITAR_DENUNCIAS,
        Permiso.ELIMINAR_DENUNCIAS,
        Permiso.VER_CONFIG,
        Permiso.EDITAR_CONFIG,
        Permiso.VER_BITACORA,
        Permiso.EXPORTAR_DATOS,
    ],

    'moderador': [
        Permiso.VER_SOLICITUDES,
        Permiso.EDITAR_SOLICITUDES,
        Permiso.VER_DENUNCIAS,
        Permiso.EDITAR_DENUNCIAS,
    ],
}


# ================================================================
# FUNCIONES DE PERMISOS
# ================================================================

def tiene_permiso(rol, permiso):
    """Verifica si un rol tiene un permiso específico"""
    if not rol:
        return False
    return permiso in PERMISOS_POR_ROL.get(rol, [])


def tiene_permisos(rol, permisos, require_all=False):
    """Verifica si un rol tiene múltiples permisos"""
    if not rol:
        return False
    if require_all:
        return all(tiene_permiso(rol, p) for p in permisos)
    return any(tiene_permiso(rol, p) for p in permisos)


def obtener_permisos_rol(rol):
    """Obtiene todos los permisos de un rol"""
    return PERMISOS_POR_ROL.get(rol, [])


def obtener_roles():
    """Devuelve la lista de roles disponibles"""
    return ['super_admin', 'admin', 'moderador']


def obtener_nombre_rol(rol):
    """Devuelve el nombre legible de un rol"""
    nombres = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'moderador': 'Moderador',
        None: 'Ciudadano'
    }
    return nombres.get(rol, 'Ciudadano')


# ================================================================
# DECORADORES DE PERMISOS
# ================================================================

def permiso_requerido(permiso):
    """Decorador para verificar un permiso específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash("🔐 Necesitas iniciar sesión.", "error")
                return redirect(url_for("auth.login"))
            
            user_rol = session.get('user_rol')
            
            if not tiene_permiso(user_rol, permiso):
                nombre_permiso = permiso.value.replace('_', ' ').title() if hasattr(permiso, 'value') else str(permiso).replace('_', ' ').title()
                flash(f"⛔ No tienes permiso: {nombre_permiso}", "error")
                return redirect(request.referrer or url_for("admin.dashboard"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def solo_super_admin(f):
    """Decorador para rutas que solo puede ver Super Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("🔐 Necesitas iniciar sesión.", "error")
            return redirect(url_for("auth.login"))
        
        user_rol = session.get('user_rol')
        
        if user_rol != 'super_admin':
            flash("⛔ Solo disponible para Super Administradores.", "error")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def admin_o_super(f):
    """Decorador para rutas que pueden ver Admin y Super Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("🔐 Necesitas iniciar sesión.", "error")
            return redirect(url_for("auth.login"))
        
        user_rol = session.get('user_rol')
        if user_rol not in ['super_admin', 'admin']:
            flash("⛔ Acceso restringido a administradores.", "error")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def moderador_o_superior(f):
    """Decorador para rutas que pueden ver Moderador, Admin y Super Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("🔐 Necesitas iniciar sesión.", "error")
            return redirect(url_for("auth.login"))
        
        user_rol = session.get('user_rol')
        if user_rol not in ['super_admin', 'admin', 'moderador']:
            flash("⛔ No tienes permisos suficientes.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function