# ================================================================
# auth.py - CON GOOGLE OAUTH + LOGIN NORMAL + REGISTRO SIN CÉDULA
# ================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
from datetime import datetime
from models.usuario import Usuario
from extensions import db
import os
from werkzeug.utils import secure_filename

auth = Blueprint('auth', __name__)

# ================================================================
# CONFIGURAR GOOGLE OAUTH CON REDIRECT PERSONALIZADO
# ================================================================
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error

google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    scope=[
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ],
    redirect_url='/login/google/authorized-check'
)
# ================================================================
# SIGNAL: cuando Google autoriza exitosamente (solo guarda estado)
# ================================================================
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
        # Guardar datos para registro incompleto y bandera
        session['google_registro_data'] = {
            'email': google_email,
            'nombre': google_nombre,
            'apellidos': google_apellido,
            'google_id': google_id,
            'foto': google_foto
        }
        session['google_needs_register'] = True
        flash('📝 Completa tu registro para continuar.', 'info')
        return False   # Solo guardamos estado, sin redirect

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

    # Iniciar sesión (guardar en sesión de Flask)
    nombre_usuario = usuario.nombre_completo or usuario.nombre

    session.clear()
    session['user'] = usuario.email
    session['user_name'] = nombre_usuario
    session['is_admin'] = usuario.tipo == 'admin' or usuario.rol in ['super_admin', 'admin', 'moderador']
    session['user_tipo'] = usuario.tipo
    session['user_rol'] = usuario.rol or ''   # Ajustar si usas rol_id
    session['foto_perfil'] = usuario.foto_perfil or ''
    session['google_login_message'] = f'✅ ¡Bienvenido, {nombre_usuario}!'
    return False


# ================================================================
# ENDPOINT PERSONALIZADO DESPUÉS DE OAUTH
# ================================================================
@auth.route('/login/google/authorized-check')
def google_authorized_check():
    """
    Esta ruta recibe la redirección después de que Google completa el OAuth.
    Decide si el usuario debe ir a registro_completo o ya está logueado.
    """
    # Verificar si hay token (la sesión de OAuth debe existir)
    if not google_bp.session.authorized:
        flash('Error al autenticar con Google.', 'error')
        return redirect(url_for('auth.login'))

    # Si el usuario necesita completar registro
    if session.pop('google_needs_register', False):
        # Los datos ya están en session['google_registro_data']
        return redirect(url_for('auth.registro_completo'))

    # Si el usuario ya existe y el signal ya inició sesión
    if session.get('user'):
        return redirect(url_for('index'))
    else:
        # Fallback por si algo falló
        flash('No se pudo iniciar sesión correctamente.', 'error')
        return redirect(url_for('auth.login'))


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
# REGISTRO NORMAL (SIN CÉDULA)
# ================================================================
@auth.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        if esta_logueado():
            return redirect(url_for("index"))
        return render_template("registro.html")
    
    # POST - Procesar registro
    nombre = request.form.get("nombre", "").strip()
    apellidos = request.form.get("apellidos", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    password = request.form.get("password", "")
    confirmar_password = request.form.get("confirmar_password", "")
    
    # Validaciones
    errores = []
    
    if not nombre:
        errores.append("El nombre es obligatorio")
    
    if not apellidos:
        errores.append("Los apellidos son obligatorios")
    
    if not email or '@' not in email:
        errores.append("Email inválido")
    
    if Usuario.query.filter_by(email=email).first():
        errores.append("Este email ya está registrado")
    
    if len(password) < 6:
        errores.append("La contraseña debe tener al menos 6 caracteres")
    
    if password != confirmar_password:
        errores.append("Las contraseñas no coinciden")
    
    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return render_template("registro.html", 
                             nombre=nombre, apellidos=apellidos,
                             email=email, telefono=telefono)
    
    # Crear usuario (sin cédula)
    usuario = Usuario(
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
# REGISTRO COMPLETO CON DATOS DE GOOGLE (SIN CÉDULA)
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
    telefono = request.form.get("telefono", "").strip()
    
    # Validaciones
    errores = []
    
    if Usuario.query.filter_by(email=google_data['email']).first():
        errores.append("Este email ya está registrado")
    
    if errores:
        for error in errores:
            flash(f"❌ {error}", "error")
        return render_template("registro_completo.html",
                             email=google_data.get('email'),
                             nombre=google_data.get('nombre'),
                             apellidos=google_data.get('apellidos'),
                             telefono=telefono)
    
    # Crear usuario con datos de Google (sin cédula)
    usuario = Usuario(
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
    session.pop('google_needs_register', None)
    
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
# SUBIR FOTO DE PERFIL
# ================================================================

# Configuración para archivos
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
        # Crear nombre seguro
        email = session['user']
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{email.replace('@', '_').replace('.', '_')}_{int(datetime.now().timestamp())}.{extension}")
        
        # Crear directorio si no existe
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'perfiles')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Guardar archivo
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Actualizar usuario
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            # Eliminar foto anterior si existe
            if usuario.foto_perfil and '/static/uploads/perfiles/' in usuario.foto_perfil:
                old_file = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except:
                        pass
            
            # Guardar nueva foto
            foto_url = f'/static/uploads/perfiles/{filename}'
            usuario.foto_perfil = foto_url
            usuario.foto_perfil_url = foto_url
            db.session.commit()
            
            # Actualizar sesión
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
        # Eliminar archivo físico
        if usuario.foto_perfil and '/static/uploads/perfiles/' in usuario.foto_perfil:
            file_path = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        # Limpiar base de datos
        usuario.foto_perfil = None
        usuario.foto_perfil_url = None
        db.session.commit()
        
        # Limpiar sesión
        session['foto_perfil'] = None
        
        flash('✅ Foto de perfil eliminada correctamente', 'success')
    else:
        flash('❌ No hay foto de perfil para eliminar', 'error')
    
    return redirect(request.referrer or url_for('mi_cuenta'))


@auth.route('/editar-perfil', methods=['POST'])
@login_required
def editar_perfil():
    email = session['user']
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash('❌ Usuario no encontrado', 'error')
        return redirect(url_for('mi_cuenta'))
    
    # Actualizar campos
    usuario.nombre = request.form.get('nombre', usuario.nombre)
    usuario.apellidos = request.form.get('apellidos', usuario.apellidos)
    usuario.telefono = request.form.get('telefono', usuario.telefono)
    usuario.direccion = request.form.get('direccion', usuario.direccion)
    
    # Actualizar nombre completo
    if usuario.nombre and usuario.apellidos:
        usuario.nombre_completo = f"{usuario.nombre} {usuario.apellidos}".strip()
    elif usuario.nombre:
        usuario.nombre_completo = usuario.nombre
    else:
        usuario.nombre_completo = usuario.email.split('@')[0]
    
    db.session.commit()
    
    # Actualizar sesión
    session['user_name'] = usuario.nombre_completo
    
    flash('✅ Perfil actualizado correctamente', 'success')
    return redirect(url_for('mi_cuenta'))


# ================================================================
# CREAR USUARIOS POR DEFECTO (CON CÉDULA, PARA ADMINISTRACIÓN)
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