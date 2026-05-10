# ================================================================
# auth.py - CON GOOGLE OAUTH + LOGIN NORMAL + REGISTRO CON CÉDULA
# ================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
from datetime import datetime
from models.usuario import Usuario
from extensions import db
import os
import re

auth = Blueprint('auth', __name__)

# ================================================================
# CONFIGURAR GOOGLE OAUTH
# ================================================================
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized

google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    scope=[
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
)

# ================================================================
# SIGNAL: cuando Google autoriza exitosamente
# ================================================================
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash('Error al iniciar sesión con Google.', 'error')
        return False

    resp = blueprint.session.get('/oauth2/v2/userinfo')
    if not resp.ok:
        flash('Error al obtener información de Google.', 'error')
        return False

    google_info = resp.json()
    google_email = google_info.get('email')
    google_nombre = google_info.get('given_name', '')
    google_apellido = google_info.get('family_name', '')
    google_foto = google_info.get('picture', '')
    google_id = str(google_info.get('id', ''))

    if not google_email:
        flash('No se pudo obtener el email de Google.', 'error')
        return False

    if not google_info.get('verified_email', False):
        flash('Tu cuenta de Gmail no está verificada.', 'error')
        return False

    # Buscar si el usuario YA existe en la BD
    usuario = Usuario.query.filter_by(email=google_email).first()

    if not usuario:
        # Si no existe, redirigir al registro con los datos de Google pre-cargados
        session['google_registro_data'] = {
            'email': google_email,
            'nombre': google_nombre,
            'apellidos': google_apellido,
            'google_id': google_id,
            'foto': google_foto
        }
        flash('📝 Completa tu registro con tu cédula para continuar.', 'info')
        return redirect(url_for('auth.registro_completo'))

    if not usuario.activo:
        flash('❌ Tu cuenta está desactivada. Contacta al administrador.', 'error')
        return False

    # ✅ Usuario existe — actualizar foto y google_id
    if google_foto:
        usuario.foto_perfil = google_foto
        usuario.foto_perfil_url = google_foto
    
    if not usuario.google_id:
        usuario.google_id = google_id

    usuario.ultimo_acceso = datetime.now()
    db.session.commit()

    session.clear()
    session['user'] = usuario.email
    session['user_name'] = usuario.nombre_completo or usuario.nombre
    session['is_admin'] = usuario.tipo == 'admin' or usuario.rol in ['super_admin', 'admin', 'moderador']
    session['user_tipo'] = usuario.tipo
    session['user_rol'] = usuario.rol or ''
    session['foto_perfil'] = usuario.foto_perfil or ''

    flash(f'✅ ¡Bienvenido de vuelta, {usuario.nombre}!', 'success')
    return False


# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def esta_logueado():
    return "user" in session

def es_admin():
    return session.get("is_admin", False)

def get_user_rol():
    if "user" in session:
        email = session["user"]
        usuario = Usuario.query.filter_by(email=email).first()
        return usuario.rol if usuario else None
    return None

def validar_cedula(cedula):
    """Validar formato de cédula dominicana (XXX-XXXXXXX-X)"""
    patron = r'^\d{3}-\d{7}-\d{1}$'
    return re.match(patron, cedula) is not None


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
    if request.method == "GET":
        if esta_logueado():
            next_url = request.args.get('next')
            if next_url and next_url != request.url:
                return redirect(next_url)
            if session.get("is_admin"):
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("index"))
        return render_template("login.html", next=request.args.get('next', ''))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    next_url = request.form.get("next") or request.args.get("next", "")

    if not email or not password:
        flash("❌ Por favor, completa todos los campos.", "error")
        return render_template("login.html", next=next_url)

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or usuario.password != password:
        flash("❌ Credenciales incorrectas.", "error")
        return render_template("login.html", next=next_url)

    if not usuario.activo:
        flash("❌ Tu cuenta ha sido desactivada.", "error")
        return render_template("login.html", next=next_url)

    usuario.ultimo_acceso = datetime.now()
    db.session.commit()

    session.clear()
    session["user"] = usuario.email
    session["user_name"] = usuario.nombre_completo or f"{usuario.nombre} {usuario.apellidos}".strip()
    session["user_tipo"] = usuario.tipo
    session["user_rol"] = usuario.rol
    session["is_admin"] = usuario.es_admin()
    session["foto_perfil"] = usuario.foto_perfil or ""

    flash(f"✅ ¡Bienvenido, {session['user_name']}!", "success")

    if next_url and next_url.startswith('/'):
        return redirect(next_url)

    if usuario.rol in ["super_admin", "admin", "moderador"] or usuario.tipo == "admin":
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("index"))


# ================================================================
# REGISTRO NORMAL CON CÉDULA
# ================================================================
@auth.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        if esta_logueado():
            return redirect(url_for("index"))
        return render_template("registro.html")
    
    # POST - Procesar registro
    cedula = request.form.get("cedula", "").strip()
    nombre = request.form.get("nombre", "").strip()
    apellidos = request.form.get("apellidos", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    password = request.form.get("password", "")
    confirmar_password = request.form.get("confirmar_password", "")
    
    # Validaciones
    errores = []
    
    if not cedula or not validar_cedula(cedula):
        errores.append("La cédula debe tener el formato XXX-XXXXXXX-X")
    
    if not nombre:
        errores.append("El nombre es obligatorio")
    
    if not apellidos:
        errores.append("Los apellidos son obligatorios")
    
    if not email or '@' not in email:
        errores.append("Email inválido")
    
    if Usuario.query.filter_by(email=email).first():
        errores.append("Este email ya está registrado")
    
    if Usuario.query.filter_by(cedula=cedula).first():
        errores.append("Esta cédula ya está registrada")
    
    if len(password) < 6:
        errores.append("La contraseña debe tener al menos 6 caracteres")
    
    if password != confirmar_password:
        errores.append("Las contraseñas no coinciden")
    
    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return render_template("registro.html", 
                             cedula=cedula, nombre=nombre, apellidos=apellidos,
                             email=email, telefono=telefono)
    
    # Crear usuario
    usuario = Usuario(
        cedula=cedula,
        nombre=nombre,
        apellidos=apellidos,
        nombre_completo=f"{nombre} {apellidos}".strip(),
        email=email,
        telefono=telefono,
        password=password,
        tipo='ciudadano',
        activo=True,
        fecha_registro=datetime.now()
    )
    
    db.session.add(usuario)
    db.session.commit()
    
    flash(f"✅ ¡Registro exitoso! Ahora puedes iniciar sesión, {nombre}.", "success")
    return redirect(url_for("auth.login"))


# ================================================================
# REGISTRO COMPLETO CON DATOS DE GOOGLE
# ================================================================
@auth.route("/registro-completo", methods=["GET", "POST"])
def registro_completo():
    # Verificar que hay datos de Google en sesión
    google_data = session.get('google_registro_data')
    if not google_data:
        flash("⚠️ Por favor, inicia sesión con Google primero.", "warning")
        return redirect(url_for("auth.login"))
    
    if request.method == "GET":
        return render_template("registro_completo.html", 
                             email=google_data.get('email'),
                             nombre=google_data.get('nombre'),
                             apellidos=google_data.get('apellidos'))
    
    # POST - Completar registro
    cedula = request.form.get("cedula", "").strip()
    telefono = request.form.get("telefono", "").strip()
    
    # Validaciones
    errores = []
    
    if not cedula or not validar_cedula(cedula):
        errores.append("La cédula debe tener el formato XXX-XXXXXXX-X")
    
    if Usuario.query.filter_by(cedula=cedula).first():
        errores.append("Esta cédula ya está registrada")
    
    if Usuario.query.filter_by(email=google_data['email']).first():
        errores.append("Este email ya está registrado")
    
    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return render_template("registro_completo.html",
                             email=google_data.get('email'),
                             nombre=google_data.get('nombre'),
                             apellidos=google_data.get('apellidos'),
                             cedula=cedula, telefono=telefono)
    
    # Crear usuario con datos de Google
    usuario = Usuario(
        cedula=cedula,
        nombre=google_data.get('nombre', ''),
        apellidos=google_data.get('apellidos', ''),
        nombre_completo=f"{google_data.get('nombre', '')} {google_data.get('apellidos', '')}".strip(),
        email=google_data.get('email'),
        telefono=telefono,
        password='',  # Sin contraseña porque usa Google
        google_id=google_data.get('google_id'),
        foto_perfil=google_data.get('foto', ''),
        foto_perfil_url=google_data.get('foto', ''),
        tipo='ciudadano',
        activo=True,
        fecha_registro=datetime.now()
    )
    
    db.session.add(usuario)
    db.session.commit()
    
    # Limpiar sesión de Google
    session.pop('google_registro_data', None)
    
    # Iniciar sesión automáticamente
    session.clear()
    session['user'] = usuario.email
    session['user_name'] = usuario.nombre_completo
    session['user_tipo'] = usuario.tipo
    session['user_rol'] = usuario.rol or ''
    session['is_admin'] = False
    session['foto_perfil'] = usuario.foto_perfil or ''
    
    flash(f"✅ ¡Bienvenido {usuario.nombre}! Tu cuenta ha sido creada exitosamente.", "success")
    return redirect(url_for("index"))


@auth.route("/logout")
def logout():
    if esta_logueado():
        nombre = session.get("user_name", "Usuario")
        session.clear()
        flash(f"✅ ¡Hasta pronto, {nombre}!", "success")
    return redirect(url_for("index"))


@auth.route("/recuperar-password", methods=["GET", "POST"])
def recuperar_password():
    if request.method == "GET":
        if esta_logueado():
            return redirect(url_for("mi_cuenta"))
        return render_template("recuperar.html")

    email = request.form.get("email", "").strip().lower()
    usuario = Usuario.query.filter_by(email=email).first()
    flash("✅ Si el correo existe, recibirás instrucciones.", "success")
    return redirect(url_for("auth.login"))


@auth.route("/cambiar-password", methods=["POST"])
def cambiar_password():
    if not esta_logueado():
        return redirect(url_for("auth.login"))

    password_actual = request.form.get("password_actual", "")
    password_nueva = request.form.get("password_nueva", "")
    password_confirmar = request.form.get("password_confirmar", "")
    email = session["user"]

    usuario = Usuario.query.filter_by(email=email).first()

    # Si el usuario no tiene contraseña (usa Google), permitir crear una
    if usuario.password:
        if not usuario or usuario.password != password_actual:
            flash("❌ La contraseña actual es incorrecta.", "error")
            return redirect(request.referrer or url_for("mi_cuenta"))
    else:
        # Usuario de Google, no necesita contraseña actual
        pass

    if len(password_nueva) < 6 or password_nueva != password_confirmar:
        flash("❌ La contraseña nueva no es válida o no coincide.", "error")
        return redirect(request.referrer or url_for("mi_cuenta"))

    usuario.password = password_nueva
    db.session.commit()
    flash("✅ ¡Contraseña actualizada! Ahora puedes iniciar sesión con tu contraseña.", "success")
    return redirect(url_for("mi_cuenta"))


# ================================================================
# CREAR USUARIOS POR DEFECTO (INCLUYE CÉDULA)
# ================================================================
def crear_usuarios_por_defecto():
    usuarios_por_defecto = [
        {
            "email": "superadmin@cutupu.gob.do",
            "password": "Super2024*",
            "nombre": "Super",
            "apellidos": "Administrador",
            "nombre_completo": "Super Administrador",
            "cedula": "001-0000001-0",
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
            "cedula": "001-0000002-0",
            "tipo": "admin",
            "rol": "admin",
            "activo": True
        },
        {
            "email": "ciudadano@email.com",
            "password": "123456",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "nombre_completo": "Juan Pérez",
            "cedula": "001-1234567-8",
            "tipo": "ciudadano",
            "rol": None,
            "activo": True
        }
    ]

    for datos in usuarios_por_defecto:
        existe = Usuario.query.filter_by(email=datos["email"]).first()
        if not existe:
            usuario = Usuario(**datos)
            db.session.add(usuario)
            print(f"✅ Usuario creado: {datos['email']} - Cédula: {datos['cedula']}")

    db.session.commit()
    print("✅ Usuarios por defecto verificados")


# ================================================================
# DECORADORES
# ================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not esta_logueado():
            flash("🔐 Necesitas iniciar sesión.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not esta_logueado():
            flash("🔐 Necesitas iniciar sesión.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if not es_admin():
            flash("⛔ No tienes permisos de administrador.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


# ================================================================
# RUTA DE PRUEBA
# ================================================================
@auth.route("/test-auth")
def test_auth():
    return {
        "logged": esta_logueado(),
        "is_admin": es_admin(),
        "user": session.get("user"),
        "message": "Auth funcionando correctamente"
    }