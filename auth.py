# ================================================================
# auth.py - DEFINITIVO CON GOOGLE OAUTH CORREGIDO
# Google OAuth + Login Normal + Registro con Verificación por Correo
# ================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
from datetime import datetime, timedelta
from models.usuario import Usuario
from extensions import db
import os
import secrets
import re
from werkzeug.utils import secure_filename
from flask_mail import Message

auth = Blueprint('auth', __name__)

# ================================================================
# GOOGLE OAUTH - VERSIÓN CORREGIDA
# ================================================================
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized

IS_PRODUCTION = bool(os.environ.get('RENDER'))

# 🔥 CAMBIO IMPORTANTE: Usar redirect_to en lugar de redirigir a /login/google/authorized
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    scope=[
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ],
    redirect_to='auth.post_google_login'  # ← Redirige a tu ruta, no al authorized
)


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
        flash('Tu cuenta de Gmail no está verificada por Google.', 'error')
        return False

    usuario = Usuario.query.filter_by(email=google_email).first()

    # Usuario nuevo → guardar datos en sesión y redirigir a completar registro
    if not usuario:
        session['google_registro_data'] = {
            'email': google_email,
            'nombre': google_nombre,
            'apellidos': google_apellido,
            'google_id': google_id,
            'foto': google_foto
        }
        return False  # Flask-Dance redirigirá a redirect_to

    # Usuario existente desactivado
    if not usuario.activo:
        flash('❌ Tu cuenta está desactivada. Contacta al administrador.', 'error')
        return False

    # Actualizar datos de Google
    if google_foto:
        usuario.foto_perfil = google_foto
        usuario.foto_perfil_url = google_foto
    if not usuario.google_id:
        usuario.google_id = google_id

    # Si existía pero no tenía email verificado (registro manual previo), verificarlo ahora
    if not usuario.email_verificado:
        usuario.email_verificado = True

    usuario.ultimo_acceso = datetime.now()
    db.session.commit()

    # Actualizar sesión - NO usar session.clear()
    nombre_usuario = usuario.nombre_completo or usuario.nombre
    session['user'] = usuario.email
    session['user_name'] = nombre_usuario
    session['is_admin'] = usuario.tipo == 'admin' or usuario.rol in ['super_admin', 'admin', 'moderador']
    session['user_tipo'] = usuario.tipo
    session['user_rol'] = usuario.rol or ''
    session['foto_perfil'] = usuario.foto_perfil or ''
    
    flash(f'✅ ¡Bienvenido, {nombre_usuario}!', 'success')
    return False  # Flask-Dance redirigirá a redirect_to


# 🔥 NUEVA RUTA: Post login handler (reemplaza a google_authorized_redirect)
@auth.route("/post-google-login")
def post_google_login():
    print("=" * 50)
    print("POST-GOOGLE-LOGIN - Session:", dict(session))
    print("=" * 50)
    
    # Verificar si es registro nuevo
    if 'google_registro_data' in session:
        print("→ Nuevo usuario, redirigiendo a registro_completo")
        return redirect(url_for('auth.registro_completo'))
    
    # Usuario ya existe y está logueado
    if 'user' in session:
        print(f"→ Usuario logueado: {session.get('user_name')}")
        if session.get('is_admin'):
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('index'))
    
    # Algo salió mal
    print("→ Sesión vacía, error en login")
    flash('Error al iniciar sesión con Google.', 'error')
    return redirect(url_for('auth.login'))


# ⚠️ RUTA ELIMINADA - Ya no se usa (comentada para referencia)
# @auth.route("/login/google/authorized")
# def google_authorized_redirect():
#     pass


# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def esta_logueado():
    return "user" in session

def es_admin():
    return session.get("is_admin", False)

def get_user_rol():
    if "user" in session:
        usuario = Usuario.query.filter_by(email=session["user"]).first()
        return usuario.rol if usuario else None
    return None

def validar_password(password):
    errores = []
    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r'[A-Z]', password):
        errores.append("La contraseña debe tener al menos una letra mayúscula")
    if not re.search(r'[0-9]', password):
        errores.append("La contraseña debe tener al menos un número")
    if not re.search(r'[^a-zA-Z0-9]', password):
        errores.append("La contraseña debe tener al menos un símbolo (!@#$%...)")
    return errores


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
# LOGIN NORMAL
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
        flash("❌ Tu cuenta ha sido desactivada. Contacta al administrador.", "error")
        return render_template("login.html", next=next_url)

    # Bloquear si no verificó el correo
    if not usuario.email_verificado:
        flash("⚠️ Debes verificar tu correo antes de iniciar sesión. Revisa tu bandeja de entrada.", "warning")
        return render_template("login.html", next=next_url)

    usuario.ultimo_acceso = datetime.now()
    db.session.commit()

    # Para login normal SÍ podemos usar clear porque no hay estado OAuth
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
# REGISTRO NORMAL (con verificación por correo)
# ================================================================
@auth.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        if esta_logueado():
            return redirect(url_for("index"))
        return render_template("registro.html")

    nombre = request.form.get("nombre", "").strip()
    apellidos = request.form.get("apellidos", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    password = request.form.get("password", "")
    confirmar_password = request.form.get("confirmar_password", "")

    errores = []
    if not nombre:
        errores.append("El nombre es obligatorio")
    if not apellidos:
        errores.append("Los apellidos son obligatorios")
    if not email or '@' not in email:
        errores.append("Email inválido")
    if Usuario.query.filter_by(email=email).first():
        errores.append("Este email ya está registrado")
    errores.extend(validar_password(password))
    if password != confirmar_password:
        errores.append("Las contraseñas no coinciden")

    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return render_template("registro.html", nombre=nombre, apellidos=apellidos, email=email, telefono=telefono)

    token = secrets.token_urlsafe(32)
    expiracion = datetime.now() + timedelta(hours=24)

    usuario = Usuario(
        nombre=nombre,
        apellidos=apellidos,
        nombre_completo=f"{nombre} {apellidos}".strip(),
        email=email,
        telefono=telefono,
        password=password,
        tipo='ciudadano',
        activo=False,
        email_verificado=False,
        token_verificacion=token,
        token_expiracion=expiracion,
        fecha_registro=datetime.now()
    )
    db.session.add(usuario)
    db.session.commit()

    try:
        from app import mail
        link = url_for('auth.verificar_email', token=token, _external=True)
        msg = Message(
            subject="✅ Verifica tu correo — Villa Cutupú",
            recipients=[email],
            html=f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:30px;
                        border:1px solid #e0e0e0;border-radius:10px;">
                <h2 style="color:#2d6a4f;">¡Bienvenido, {nombre}!</h2>
                <p>Gracias por registrarte en el portal de <strong>Villa Cutupú</strong>.</p>
                <p>Para activar tu cuenta haz clic en el botón:</p>
                <a href="{link}" style="display:inline-block;background:#2d6a4f;color:white;
                   padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0;">
                    Verificar mi correo
                </a>
                <p style="color:#888;font-size:13px;">Este enlace expira en 24 horas.</p>
                <p style="color:#888;font-size:13px;">Si no creaste esta cuenta, ignora este mensaje.</p>
            </div>
            """
        )
        mail.send(msg)
        flash(f"✅ Te enviamos un correo a {email}. Revisa tu bandeja y confirma tu cuenta.", "success")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
        flash("⚠️ Cuenta creada pero no se pudo enviar el correo. Contacta al administrador.", "warning")

    return redirect(url_for("auth.login"))


# ================================================================
# VERIFICACIÓN DE EMAIL
# ================================================================
@auth.route("/verificar-email/<token>")
def verificar_email(token):
    usuario = Usuario.query.filter_by(token_verificacion=token).first()

    if not usuario:
        flash("❌ Enlace de verificación inválido.", "error")
        return redirect(url_for("auth.login"))

    if usuario.token_expiracion and datetime.now() > usuario.token_expiracion:
        flash("❌ El enlace expiró. Regístrate nuevamente.", "error")
        db.session.delete(usuario)
        db.session.commit()
        return redirect(url_for("auth.registro"))

    usuario.activo = True
    usuario.email_verificado = True
    usuario.token_verificacion = None
    usuario.token_expiracion = None
    db.session.commit()

    flash(f"✅ ¡Correo verificado! Ya puedes iniciar sesión, {usuario.nombre}.", "success")
    return redirect(url_for("auth.login"))


# ================================================================
# REGISTRO COMPLETO CON GOOGLE (sin verificación adicional)
# ================================================================
@auth.route("/registro-completo", methods=["GET", "POST"])
def registro_completo():
    google_data = session.get('google_registro_data')
    if not google_data:
        flash("⚠️ Por favor, inicia sesión con Google primero.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("registro_completo.html",
                               email=google_data.get('email'),
                               nombre=google_data.get('nombre'),
                               apellidos=google_data.get('apellidos'))

    telefono = request.form.get("telefono", "").strip()

    if Usuario.query.filter_by(email=google_data['email']).first():
        flash("❌ Este email ya está registrado.", "error")
        return redirect(url_for("auth.login"))

    # Google ya verificó el email → activar directamente, sin token
    usuario = Usuario(
        nombre=google_data.get('nombre', ''),
        apellidos=google_data.get('apellidos', ''),
        nombre_completo=f"{google_data.get('nombre', '')} {google_data.get('apellidos', '')}".strip(),
        email=google_data.get('email'),
        telefono=telefono,
        password='',
        google_id=google_data.get('google_id'),
        foto_perfil=google_data.get('foto', ''),
        foto_perfil_url=google_data.get('foto', ''),
        tipo='ciudadano',
        activo=True,
        email_verificado=True,
        token_verificacion=None,
        token_expiracion=None,
        fecha_registro=datetime.now()
    )
    db.session.add(usuario)
    db.session.commit()

    # Limpiar datos temporales e iniciar sesión directamente
    session.pop('google_registro_data', None)
    session['user'] = usuario.email
    session['user_name'] = usuario.nombre_completo
    session['user_tipo'] = usuario.tipo
    session['user_rol'] = usuario.rol or ''
    session['is_admin'] = False
    session['foto_perfil'] = usuario.foto_perfil or ''

    flash(f"✅ ¡Bienvenido, {usuario.nombre}! Tu cuenta fue creada exitosamente.", "success")
    return redirect(url_for('index'))


# ================================================================
# LOGOUT
# ================================================================
@auth.route("/logout")
def logout():
    if esta_logueado():
        nombre = session.get("user_name", "Usuario")
        session.clear()
        flash(f"✅ ¡Hasta pronto, {nombre}!", "success")
    return redirect(url_for("index"))


# ================================================================
# RECUPERAR CONTRASEÑA
# ================================================================
@auth.route("/recuperar-password", methods=["GET", "POST"])
def recuperar_password():
    if request.method == "GET":
        if esta_logueado():
            return redirect(url_for("mi_cuenta"))
        return render_template("recuperar.html")

    email = request.form.get("email", "").strip().lower()
    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and usuario.email_verificado:
        token = secrets.token_urlsafe(32)
        usuario.token_verificacion = token
        usuario.token_expiracion = datetime.now() + timedelta(hours=1)
        db.session.commit()

        try:
            from app import mail
            link = url_for('auth.reset_password', token=token, _external=True)
            msg = Message(
                subject="🔑 Recuperar contraseña — Villa Cutupú",
                recipients=[email],
                html=f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:30px;
                            border:1px solid #e0e0e0;border-radius:10px;">
                    <h2 style="color:#2d6a4f;">Recuperar contraseña</h2>
                    <p>Haz clic para crear una nueva contraseña:</p>
                    <a href="{link}" style="display:inline-block;background:#2d6a4f;color:white;
                       padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0;">
                        Cambiar contraseña
                    </a>
                    <p style="color:#888;font-size:13px;">Este enlace expira en 1 hora.</p>
                    <p style="color:#888;font-size:13px;">Si no solicitaste esto, ignora este mensaje.</p>
                </div>
                """
            )
            mail.send(msg)
        except Exception as e:
            print(f"❌ Error enviando correo de recuperación: {e}")

    flash("✅ Si el correo existe, recibirás instrucciones para recuperar tu contraseña.", "success")
    return redirect(url_for("auth.login"))


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    usuario = Usuario.query.filter_by(token_verificacion=token).first()

    if not usuario or (usuario.token_expiracion and datetime.now() > usuario.token_expiracion):
        flash("❌ El enlace es inválido o expiró.", "error")
        return redirect(url_for("auth.recuperar_password"))

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    password_nueva = request.form.get("password_nueva", "")
    password_confirmar = request.form.get("password_confirmar", "")

    errores = validar_password(password_nueva)
    if password_nueva != password_confirmar:
        errores.append("Las contraseñas no coinciden")

    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return render_template("reset_password.html", token=token)

    usuario.password = password_nueva
    usuario.token_verificacion = None
    usuario.token_expiracion = None
    db.session.commit()

    flash("✅ Contraseña actualizada. Ya puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))


# ================================================================
# CAMBIAR CONTRASEÑA (desde mi cuenta)
# ================================================================
@auth.route("/cambiar-password", methods=["POST"])
def cambiar_password():
    if not esta_logueado():
        return redirect(url_for("auth.login"))

    password_actual = request.form.get("password_actual", "")
    password_nueva = request.form.get("password_nueva", "")
    password_confirmar = request.form.get("password_confirmar", "")
    email = session["user"]

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario.password and usuario.password != password_actual:
        flash("❌ La contraseña actual es incorrecta.", "error")
        return redirect(request.referrer or url_for("mi_cuenta"))

    errores = validar_password(password_nueva)
    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return redirect(request.referrer or url_for("mi_cuenta"))

    if password_nueva != password_confirmar:
        flash("❌ Las contraseñas no coinciden.", "error")
        return redirect(request.referrer or url_for("mi_cuenta"))

    usuario.password = password_nueva
    db.session.commit()
    flash("✅ ¡Contraseña actualizada!", "success")
    return redirect(request.referrer or url_for("mi_cuenta"))


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
# FOTO DE PERFIL
# ================================================================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth.route('/subir-foto-perfil', methods=['POST'])
@login_required
def subir_foto_perfil():
    if 'foto_perfil' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(request.referrer or url_for('mi_cuenta'))

    file = request.files['foto_perfil']

    if file.filename == '':
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(request.referrer or url_for('mi_cuenta'))

    if file and allowed_file(file.filename):
        email = session['user']
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(
            f"{email.replace('@', '_').replace('.', '_')}_{int(datetime.now().timestamp())}.{extension}"
        )

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'perfiles')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            if usuario.foto_perfil and '/static/uploads/perfiles/' in usuario.foto_perfil:
                old_file = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except:
                        pass

            foto_url = f'/static/uploads/perfiles/{filename}'
            usuario.foto_perfil = foto_url
            usuario.foto_perfil_url = foto_url
            db.session.commit()
            session['foto_perfil'] = foto_url
            flash('✅ Foto de perfil actualizada correctamente', 'success')
        else:
            flash('❌ Error al actualizar la foto', 'error')
    else:
        flash('❌ Formato no permitido. Use PNG, JPG, JPEG, WEBP o GIF', 'error')

    return redirect(request.referrer or url_for('mi_cuenta'))


@auth.route('/eliminar-foto-perfil', methods=['POST'])
@login_required
def eliminar_foto_perfil():
    email = session['user']
    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and usuario.foto_perfil:
        if '/static/uploads/perfiles/' in usuario.foto_perfil:
            file_path = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        usuario.foto_perfil = None
        usuario.foto_perfil_url = None
        db.session.commit()
        session['foto_perfil'] = None
        flash('✅ Foto de perfil eliminada correctamente', 'success')
    else:
        flash('❌ No hay foto de perfil para eliminar', 'error')

    return redirect(request.referrer or url_for('mi_cuenta'))


# ================================================================
# EDITAR PERFIL
# ================================================================
@auth.route('/editar-perfil', methods=['POST'])
@login_required
def editar_perfil():
    email = session['user']
    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario:
        flash('❌ Usuario no encontrado', 'error')
        return redirect(url_for('mi_cuenta'))

    usuario.nombre = request.form.get('nombre', usuario.nombre)
    usuario.apellidos = request.form.get('apellidos', usuario.apellidos)
    usuario.telefono = request.form.get('telefono', usuario.telefono)
    usuario.direccion = request.form.get('direccion', usuario.direccion)

    if usuario.nombre and usuario.apellidos:
        usuario.nombre_completo = f"{usuario.nombre} {usuario.apellidos}".strip()
    elif usuario.nombre:
        usuario.nombre_completo = usuario.nombre
    else:
        usuario.nombre_completo = usuario.email.split('@')[0]

    db.session.commit()
    session['user_name'] = usuario.nombre_completo
    flash('✅ Perfil actualizado correctamente', 'success')
    return redirect(url_for('mi_cuenta'))


# ================================================================
# USUARIOS POR DEFECTO
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
            "activo": True,
            "email_verificado": True
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
            "activo": True,
            "email_verificado": True
        },
        {
            "email": "ciudadano@email.com",
            "password": "Ciudadano1*",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "nombre_completo": "Juan Pérez",
            "cedula": "001-1234567-8",
            "tipo": "ciudadano",
            "rol": None,
            "activo": True,
            "email_verificado": True
        }
    ]

    for datos in usuarios_por_defecto:
        existe = Usuario.query.filter_by(email=datos["email"]).first()
        if not existe:
            usuario = Usuario(**datos)
            db.session.add(usuario)
            print(f"✅ Usuario creado: {datos['email']}")
        else:
            if not existe.email_verificado:
                existe.email_verificado = True
                print(f"✅ Email verificado actualizado: {datos['email']}")

    db.session.commit()
    print("✅ Usuarios por defecto verificados")


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


print("🔑 GOOGLE_CLIENT_ID:", os.environ.get('GOOGLE_CLIENT_ID', 'NO ENCONTRADO'))
print("🔑 GOOGLE_CLIENT_SECRET:", os.environ.get('GOOGLE_CLIENT_SECRET', 'NO ENCONTRADO')[:10] if os.environ.get('GOOGLE_CLIENT_SECRET') else 'NO ENCONTRADO')