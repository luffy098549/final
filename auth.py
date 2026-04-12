# ================================================================
# auth.py - VERSIÓN CON SQLALCHEMY (POSTGRESQL/MYSQL/SQLITE)
# ================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
from models.usuario import Usuario
from extensions import db

auth = Blueprint('auth', __name__)


# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def esta_logueado():
    return "user" in session

def es_admin():
    return session.get("is_admin", False)

def get_user_rol():
    """Obtiene el rol del usuario actual"""
    if "user" in session:
        email = session["user"]
        usuario = Usuario.query.filter_by(email=email).first()
        return usuario.rol if usuario else None
    return None


# ================================================================
# CONTEXTO GLOBAL
# ================================================================
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


# ================================================================
# RUTAS
# ================================================================
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

        # 🔥 DEBUG - VERIFICAR QUÉ LLEGA
        print("=" * 50)
        print("🔍 DEBUG LOGIN")
        print("EMAIL ESCRITO:", email)
        print("PASSWORD LENGTH:", len(password) if password else 0)

        # 🔥 DEBUG - VER USUARIOS EN BD
        usuarios = Usuario.query.all()
        print(f"📊 Total usuarios en BD: {len(usuarios)}")
        for u in usuarios:
            print(f"   - {u.email} (rol: {u.rol}, activo: {u.activo})")
        print("=" * 50)

        if not email or not password:
            flash("❌ Por favor, completa todos los campos.", "error")
            return render_template("login.html")

        # 🔥 BUSCAR USUARIO EN BASE DE DATOS
        usuario = Usuario.query.filter_by(email=email).first()

        # 🔥 DEBUG - RESULTADO DE BÚSQUEDA
        if usuario:
            print(f"✅ Usuario encontrado: {usuario.email}")
            print(f"   Password en BD: {usuario.password}")
            print(f"   Password ingresado: {password}")
            print(f"   ¿Coinciden? {usuario.password == password}")
        else:
            print(f"❌ Usuario NO encontrado: {email}")

        # 🔥 VALIDACIÓN DE CREDENCIALES
        if not usuario or usuario.password != password:
            flash("❌ Credenciales incorrectas.", "error")
            return render_template("login.html")

        if not usuario.activo:
            flash("❌ Tu cuenta ha sido desactivada.", "error")
            return render_template("login.html")

        # Registrar último acceso
        usuario.ultimo_acceso = datetime.now()
        db.session.commit()

        # 🔥 GUARDAR EN SESIÓN
        session["user"] = usuario.email
        session["user_name"] = usuario.nombre_completo
        session["user_tipo"] = usuario.tipo
        session["user_rol"] = usuario.rol
        session["is_admin"] = usuario.es_admin()
        session["user_telefono"] = usuario.telefono or ""

        rol_nombre = {
            "super_admin": "Super Administrador",
            "admin": "Administrador",
            "moderador": "Moderador"
        }.get(usuario.rol, "Usuario")

        print(f"✅ Login exitoso: {usuario.email} -> {rol_nombre}")
        flash(f"✅ ¡Bienvenido, {session['user_name']}! ({rol_nombre})", "success")

        # Redirigir según rol
        if usuario.rol in ["super_admin", "admin", "moderador"] or usuario.tipo == "admin":
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

        print("=" * 50)
        print("🔍 DEBUG REGISTRO")
        print("EMAIL:", email)
        print("NOMBRE:", nombre)
        print("=" * 50)

        # Validaciones
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

        # Verificar si ya existe
        existe = Usuario.query.filter_by(email=email).first()
        if existe:
            flash("❌ Este correo electrónico ya está registrado.", "error")
            return render_template("registro.html")

        # 🔥 CREAR USUARIO EN BASE DE DATOS
        nombre_completo = f"{nombre} {apellidos}"
        nuevo_usuario = Usuario(
            nombre=nombre,
            apellidos=apellidos,
            nombre_completo=nombre_completo,
            email=email,
            password=password,
            telefono=telefono,
            cedula=cedula if cedula else None,
            fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
            direccion=direccion if direccion else None,
            tipo="ciudadano",
            rol=None,
            activo=True
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        print(f"✅ Usuario creado: {email}")
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
        print(f"🔍 Recuperación de password para: {email}")
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            flash(f"✅ Se ha enviado un enlace de recuperación a {email}", "success")
        else:
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

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario:
        flash("❌ Usuario no encontrado.", "error")
        return redirect(url_for("index"))

    if usuario.password != password_actual:
        flash("❌ La contraseña actual es incorrecta.", "error")
        return redirect(url_for("mi_cuenta"))

    if len(password_nueva) < 6:
        flash("❌ La nueva contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("mi_cuenta"))

    if password_nueva != password_confirmar:
        flash("❌ Las contraseñas nuevas no coinciden.", "error")
        return redirect(url_for("mi_cuenta"))

    usuario.password = password_nueva
    db.session.commit()
    
    flash("✅ ¡Contraseña actualizada correctamente!", "success")
    return redirect(url_for("mi_cuenta"))


# ================================================================
# FUNCIÓN PARA CREAR USUARIOS POR DEFECTO EN LA BD
# ================================================================
def crear_usuarios_por_defecto():
    """Crea usuarios por defecto si no existen en la base de datos"""
    
    usuarios_por_defecto = [
        {
            "email": "superadmin@cutupu.gob.do",
            "password": "Super2024*",
            "nombre": "Super",
            "apellidos": "Administrador",
            "nombre_completo": "Super Administrador",
            "tipo": "admin",
            "rol": "super_admin",
            "telefono": "+18096917111",
            "activo": True
        },
        {
            "email": "admin@cutupu.gob.do",
            "password": "Admin2024*",
            "nombre": "Carlos",
            "apellidos": "Rodríguez",
            "nombre_completo": "Carlos Rodríguez",
            "tipo": "admin",
            "rol": "admin",
            "telefono": "+18095551001",
            "activo": True
        },
        {
            "email": "moderador@cutupu.gob.do",
            "password": "Moderador2024*",
            "nombre": "Ana",
            "apellidos": "Martínez",
            "nombre_completo": "Ana Martínez",
            "tipo": "ciudadano",
            "rol": "moderador",
            "telefono": "+18095551002",
            "activo": True
        },
        {
            "email": "ciudadano@email.com",
            "password": "123456",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "nombre_completo": "Juan Pérez",
            "tipo": "ciudadano",
            "rol": None,
            "telefono": "+18095551234",
            "activo": True
        }
    ]
    
    for datos in usuarios_por_defecto:
        existe = Usuario.query.filter_by(email=datos["email"]).first()
        if not existe:
            usuario = Usuario(**datos)
            db.session.add(usuario)
    
    db.session.commit()
    print("✅ Usuarios por defecto creados/verificados en la base de datos")


# ================================================================
# DECORADORES
# ================================================================
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
            flash("⛔ No tienes permisos de administrador.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function