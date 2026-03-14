"""
Decoradores personalizados para permisos y roles
"""
from functools import wraps
from flask import session, flash, redirect, url_for
from rol import tiene_permiso, PERMISOS_POR_ROL  # Cambiado de models.rol a rol
import json
import os

# Cargar usuarios
USERS_FILE = "data/usuarios.json"

def _cargar_usuarios():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def permiso_requerido(permiso):
    """Decorador para verificar si el usuario tiene un permiso específico"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                flash("Por favor inicia sesión.", "error")
                return redirect(url_for("auth.login"))
            
            user_email = session.get("user")
            usuarios = _cargar_usuarios()
            usuario = usuarios.get(user_email, {})
            user_rol = usuario.get("rol")
            
            # Si no tiene rol, verificar el tipo tradicional
            if not user_rol:
                if usuario.get("tipo") == "admin":
                    user_rol = "admin"
                else:
                    flash("No tienes permisos para esta acción.", "error")
                    return redirect(url_for("index"))
            
            if not tiene_permiso(user_rol, permiso):
                flash(f"No tienes permiso para realizar esta acción.", "error")
                return redirect(url_for("admin.dashboard"))
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def solo_super_admin(f):
    """Decorador para funciones exclusivas de super admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Por favor inicia sesión.", "error")
            return redirect(url_for("auth.login"))
        
        user_email = session.get("user")
        usuarios = _cargar_usuarios()
        usuario = usuarios.get(user_email, {})
        user_rol = usuario.get("rol")
        
        if user_rol != "super_admin":
            flash("Solo el Super Administrador puede realizar esta acción.", "error")
            return redirect(url_for("admin.dashboard"))
            
        return f(*args, **kwargs)
    return decorated

def admin_o_super(f):
    """Decorador para funciones que pueden hacer admin y super admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Por favor inicia sesión.", "error")
            return redirect(url_for("auth.login"))
        
        user_email = session.get("user")
        usuarios = _cargar_usuarios()
        usuario = usuarios.get(user_email, {})
        user_rol = usuario.get("rol")
        
        if user_rol not in ["super_admin", "admin"]:
            flash("Acción permitida solo para administradores.", "error")
            return redirect(url_for("admin.dashboard"))
            
        return f(*args, **kwargs)
    return decorated

def moderador_o_superior(f):
    """Decorador para moderadores y superiores"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Por favor inicia sesión.", "error")
            return redirect(url_for("auth.login"))
        
        user_email = session.get("user")
        usuarios = _cargar_usuarios()
        usuario = usuarios.get(user_email, {})
        user_rol = usuario.get("rol")
        
        if user_rol not in ["super_admin", "admin", "moderador"]:
            flash("Acción no permitida para tu rol.", "error")
            return redirect(url_for("index"))
            
        return f(*args, **kwargs)
    return decorated