# decorators.py
from functools import wraps
from flask import session, flash, redirect, url_for, request
from rol import tiene_permiso, Permiso

# ================================================================
# DECORADORES BÁSICOS
# ================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("🔐 Necesitas iniciar sesión para acceder a esta página.", "error")
            session['next_url'] = request.url
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("🔐 Necesitas iniciar sesión.", "error")
            session['next_url'] = request.url
            return redirect(url_for("auth.login"))
        
        user_rol = session.get('user_rol')
        if user_rol not in ['super_admin', 'admin']:
            flash("⛔ No tienes permisos de administrador.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


# ================================================================
# DECORADORES DE ROL (IMPORTADOS DE ROL.PY PARA FACILIDAD)
# ================================================================

from rol import solo_super_admin, admin_o_super, moderador_o_superior, permiso_requerido


# ================================================================
# DECORADOR DE PERMISOS MÚLTIPLES
# ================================================================

def permisos_requeridos(permisos, require_all=False):
    """Decorador para verificar múltiples permisos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash("🔐 Necesitas iniciar sesión.", "error")
                return redirect(url_for("auth.login"))
            
            user_rol = session.get('user_rol')
            permisos_valores = [p.value if hasattr(p, 'value') else p for p in permisos]
            
            if require_all:
                faltantes = []
                for p in permisos_valores:
                    if not tiene_permiso(user_rol, p):
                        faltantes.append(p.replace('_', ' ').title())
                if faltantes:
                    flash(f"⛔ Te faltan: {', '.join(faltantes)}", "error")
                    return redirect(request.referrer or url_for("admin.dashboard"))
            else:
                if not any(tiene_permiso(user_rol, p) for p in permisos_valores):
                    flash("⛔ No tienes suficientes permisos.", "error")
                    return redirect(request.referrer or url_for("admin.dashboard"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator