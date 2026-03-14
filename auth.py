from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
import json
import os

auth = Blueprint('auth', __name__)

# ========== CONFIGURACIÓN ==========
USERS_FILE = "data/usuarios.json"
os.makedirs("data", exist_ok=True)

# ========== FUNCIONES DE PERSISTENCIA ==========
def _cargar_usuarios():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _guardar_usuarios(usuarios):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)

# Cargar usuarios
USUARIOS = _cargar_usuarios()

# Usuarios por defecto con ROLES
if not USUARIOS:
    USUARIOS = {
        "superadmin@cutupu.gob.do": {
            "password": "Super2024*",
            "nombre": "Super",
            "apellidos": "Administrador",
            "nombre_completo": "Super Administrador",
            "email": "superadmin@cutupu.gob.do",
            "tipo": "admin",
            "rol": "super_admin",
            "telefono": "+18096917111",
            "fecha_registro": datetime.now().strftime("%d/%m/%Y"),
            "activo": True,
            "ultimo_acceso": None
        },
        "admin@cutupu.gob.do": {
            "password": "Admin2024*",
            "nombre": "Carlos",
            "apellidos": "Rodríguez",
            "nombre_completo": "Carlos Rodríguez",
            "email": "admin@cutupu.gob.do",
            "tipo": "admin",
            "rol": "admin",
            "telefono": "+18095551001",
            "fecha_registro": datetime.now().strftime("%d/%m/%Y"),
            "activo": True,
            "ultimo_acceso": None
        },
        "moderador@cutupu.gob.do": {
            "password": "Moderador2024*",
            "nombre": "Ana",
            "apellidos": "Martínez",
            "nombre_completo": "Ana Martínez",
            "email": "moderador@cutupu.gob.do",
            "tipo": "ciudadano",
            "rol": "moderador",
            "telefono": "+18095551002",
            "fecha_registro": datetime.now().strftime("%d/%m/%Y"),
            "activo": True,
            "ultimo_acceso": None
        },
        "ciudadano@email.com": {
            "password": "123456",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "nombre_completo": "Juan Pérez",
            "email": "ciudadano@email.com",
            "tipo": "ciudadano",
            "rol": None,
            "telefono": "+18095551234",
            "fecha_registro": "15/01/2026",
            "activo": True,
            "ultimo_acceso": None
        }
    }
    _guardar_usuarios(USUARIOS)

# ========== FUNCIONES AUXILIARES ==========
def esta_logueado():
    return "user" in session

def es_admin():
    return session.get("is_admin", False)

def get_user_rol():
    """Obtiene el rol del usuario actual"""
    if "user" in session:
        email = session["user"]
        usuarios = _cargar_usuarios()
        return usuarios.get(email, {}).get("rol")
    return None

# ========== CONTEXTO GLOBAL ==========
@auth.context_processor
def inject_auth_variables():
    return dict(
        logged=esta_logueado(),
        is_admin=es_admin(),
        user_email=session.get("user"),
        user_name=session.get("user_name"),
        user_tipo=session.get("user_tipo"),
        user_rol=session.get("user_rol"),
        now=datetime.now()
    )

# ========== RUTAS ==========
@auth.route("/login", methods=["GET", "POST"])
def login():
    """Página de inicio de sesión."""
    if esta_logueado():
        if session.get("is_admin"):
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("❌ Por favor, completa todos los campos.", "error")
            return render_template("login.html")

        usuarios_actualizados = _cargar_usuarios()
        USUARIOS.update(usuarios_actualizados)

        usuario = USUARIOS.get(email)

        if not usuario:
            flash("❌ Este correo electrónico no está registrado.", "error")
            return render_template("login.html")

        if usuario["password"] != password:
            flash("❌ Contraseña incorrecta.", "error")
            return render_template("login.html")

        if not usuario.get('activo', True):
            flash("❌ Tu cuenta ha sido desactivada.", "error")
            return render_template("login.html")

        # Registrar último acceso
        usuario["ultimo_acceso"] = datetime.now().isoformat()
        USUARIOS[email] = usuario
        _guardar_usuarios(USUARIOS)

        # Guardar en sesión
        session["user"] = email
        session["user_name"] = usuario.get("nombre_completo") or f"{usuario.get('nombre', '')} {usuario.get('apellidos', '')}".strip()
        session["user_tipo"] = usuario["tipo"]
        session["is_admin"] = (usuario["tipo"] == "admin" or usuario.get("rol") in ["super_admin", "admin", "moderador"])
        session["user_rol"] = usuario.get("rol")
        session["user_telefono"] = usuario.get("telefono", "")

        rol_nombre = {
            "super_admin": "Super Administrador",
            "admin": "Administrador",
            "moderador": "Moderador"
        }.get(usuario.get("rol"), "Usuario")

        flash(f"✅ ¡Bienvenido, {session['user_name']}! ({rol_nombre})", "success")

        # Redirigir según rol
        if usuario.get("rol") in ["super_admin", "admin", "moderador"] or usuario["tipo"] == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("index"))

    return render_template("login.html")

@auth.route("/registro", methods=["GET", "POST"])
def registro():
    """Página de registro de nuevos usuarios."""
    if esta_logueado():
        if session.get("is_admin"):
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("index"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        cedula = request.form.get("cedula", "").strip()
        fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
        direccion = request.form.get("direccion", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()
        password = request.form.get("password", "")
        confirmar_password = request.form.get("confirmar_password", "")
        terminos = request.form.get("terminos")

        if not nombre or not apellidos or not email or not password:
            flash("❌ Los campos nombre, apellidos, email y contraseña son obligatorios.", "error")
            return render_template("registro.html")

        if password != confirmar_password:
            flash("❌ Las contraseñas no coinciden.", "error")
            return render_template("registro.html")

        if len(password) < 6:
            flash("❌ La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("registro.html")

        if not terminos:
            flash("❌ Debes aceptar los términos y condiciones.", "error")
            return render_template("registro.html")

        usuarios_actualizados = _cargar_usuarios()
        USUARIOS.update(usuarios_actualizados)

        if email in USUARIOS:
            flash("❌ Este correo electrónico ya está registrado.", "error")
            return render_template("registro.html")

        nombre_completo = f"{nombre} {apellidos}"
        nuevo_usuario = {
            "password": password,
            "nombre": nombre,
            "apellidos": apellidos,
            "nombre_completo": nombre_completo,
            "cedula": cedula if cedula else "",
            "fecha_nacimiento": fecha_nacimiento if fecha_nacimiento else "",
            "direccion": direccion if direccion else "",
            "email": email,
            "telefono": telefono,
            "tipo": "ciudadano",
            "rol": None,
            "fecha_registro": datetime.now().strftime("%d/%m/%Y"),
            "activo": True,
            "ultimo_acceso": None
        }

        USUARIOS[email] = nuevo_usuario
        _guardar_usuarios(USUARIOS)

        flash("✅ ¡Registro exitoso! Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registro.html")

@auth.route("/logout")
def logout():
    """Cierra la sesión del usuario."""
    if esta_logueado():
        nombre = session.get("user_name", "Usuario")
        session.clear()
        flash(f"✅ ¡Hasta pronto, {nombre}! Has cerrado sesión.", "success")
    return redirect(url_for("index"))

@auth.route("/recuperar-password", methods=["GET", "POST"])
def recuperar_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        flash(f"✅ Si el correo existe, recibirás instrucciones.", "success")
        return redirect(url_for("auth.login"))
    return render_template("recuperar.html")

@auth.route("/cambiar-password", methods=["POST"])
def cambiar_password():
    if not esta_logueado():
        flash("❌ Debes iniciar sesión.", "error")
        return redirect(url_for("auth.login"))

    password_actual = request.form.get("password_actual", "")
    password_nueva = request.form.get("password_nueva", "")
    password_confirmar = request.form.get("password_confirmar", "")
    email = session["user"]

    usuarios_actualizados = _cargar_usuarios()
    USUARIOS.update(usuarios_actualizados)

    if email not in USUARIOS:
        flash("❌ Usuario no encontrado.", "error")
        return redirect(url_for("index"))

    if USUARIOS[email]["password"] != password_actual:
        flash("❌ La contraseña actual es incorrecta.", "error")
        return redirect(url_for("mi_cuenta"))

    if len(password_nueva) < 6:
        flash("❌ La nueva contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("mi_cuenta"))

    if password_nueva != password_confirmar:
        flash("❌ Las contraseñas nuevas no coinciden.", "error")
        return redirect(url_for("mi_cuenta"))

    USUARIOS[email]["password"] = password_nueva
    _guardar_usuarios(USUARIOS)
    flash("✅ ¡Contraseña actualizada correctamente!", "success")
    return redirect(url_for("mi_cuenta"))

# ========== DECORADORES ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not esta_logueado():
            flash("🔐 Necesitas iniciar sesión.", "login_required")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not esta_logueado():
            flash("🔐 Necesitas iniciar sesión.", "login_required")
            return redirect(url_for("auth.login"))
        if not es_admin():
            flash("⛔ No tienes permisos.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function