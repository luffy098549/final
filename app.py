# ================================================================
# IMPORTS PRINCIPALES
# ================================================================
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, send_from_directory
)
from auth import auth, login_required, admin_required
from admin import admin_bp
import os
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import sys
import flask

# ================================================================
# IMPORTS ADICIONALES PARA CACHÉ Y RATE LIMITING
# ================================================================
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import hashlib

# ================================================================
# CONFIGURACIÓN DE EXTENSIONES
# ================================================================
from config_manager import Config
from extensions import db, login_manager, migrate

# ================================================================
# CREACIÓN DE LA APLICACIÓN
# ================================================================
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Cargar configuración desde Config
app.config.from_object(Config)

# Inicializar base de datos
db.init_app(app)

# Inicializar login_manager
login_manager.init_app(app)
migrate.init_app(app, db)

# Configurar user_loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models.usuario import Usuario
    return Usuario.query.get(int(user_id))

# ================================================================
# MODO DESARROLLO ACTIVADO
# ================================================================
app.debug = True

# ── Corrige IPs reales detrás de proxy/nginx ─────────────────────
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ── Clave secreta (usar variable de entorno en producción) ────────
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "clave_secreta_muy_segura_cambiar_en_produccion_123"
)
app.config['SESSION_TYPE'] = 'filesystem'

# ── Uploads ───────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
DOCS_FOLDER = os.path.join('static', 'uploads', 'documentos')
ALLOWED_DOC_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
DOCS_MAX_POR_TRAMITE = 5
DOCS_MAX_SIZE_MB = 10

# ================================================================
# CONFIGURACIÓN PARA MODO DESARROLLO (SIN CACHÉ)
# ================================================================
app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    TEMPLATES_AUTO_RELOAD=True,
    JSON_SORT_KEYS=False,
    PROPAGATE_EXCEPTIONS=True,
)

# Registrar blueprints
app.register_blueprint(auth)
app.register_blueprint(admin_bp)

# ================================================================
# DETECCIÓN DE REDIS
# ================================================================
try:
    import redis
    redis_client = redis.Redis(
        host='localhost', port=6379, db=0, socket_connect_timeout=0.5
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis conectado")
except Exception:
    REDIS_AVAILABLE = False
    redis_client = None
    print("⚠️ Redis no disponible, usando caché en memoria")

# ================================================================
# CACHÉ
# ================================================================
_cache_cfg = {
    'CACHE_KEY_PREFIX': 'municipio_',
    'CACHE_DEFAULT_TIMEOUT': 300,
}
if REDIS_AVAILABLE:
    _cache_cfg.update({
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_HOST': 'localhost',
        'CACHE_REDIS_PORT': 6379,
        'CACHE_REDIS_DB': 0,
    })
else:
    _cache_cfg.update({
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_THRESHOLD': 1000,
    })

cache = Cache(app, config=_cache_cfg)

# ================================================================
# LIMPIAR CACHÉ AL INICIAR
# ================================================================
try:
    cache.clear()
    print("✅ Caché limpiado al iniciar")
except Exception as e:
    print(f"⚠️ No se pudo limpiar caché: {e}")

# ================================================================
# RATE LIMITING
# ================================================================
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379/0" if REDIS_AVAILABLE else "memory://",
    strategy="fixed-window",
)
print("✅ Caché y Rate Limiting configurados")

# ================================================================
# CREAR TABLAS Y USUARIOS POR DEFECTO
# ================================================================
from auth import crear_usuarios_por_defecto

with app.app_context():
    db.create_all()
    crear_usuarios_por_defecto()
    print("✅ Tablas de base de datos creadas/verificadas")
    print("✅ Usuarios por defecto creados/verificados")

# ================================================================
# CABECERAS DE RENDIMIENTO Y SEGURIDAD
# ================================================================
@app.after_request
def set_performance_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    elif response.content_type.startswith('text/html'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response

# ================================================================
# DECORADOR CACHÉ DE API
# ================================================================
def cache_response(timeout=300, key_prefix='api'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if app.debug:
                return f(*args, **kwargs)
            
            cache_key = (
                f"{key_prefix}_{f.__name__}_"
                f"{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            )
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response
        return decorated_function
    return decorator

# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _allowed_document(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

def _objeto_a_dict(obj):
    d = dict(obj) if isinstance(obj, dict) else (
        {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        if hasattr(obj, '__dict__') else {}
    )
    for k, v in d.items():
        if hasattr(v, '__dict__') or not isinstance(v, (str, int, float, bool, list, dict, type(None))):
            d[k] = str(v)
        elif isinstance(v, list):
            d[k] = [
                item if isinstance(item, (str, int, float, bool, dict, type(None))) else str(item)
                for item in v
            ]
    return d

def _icono_doc(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return {
        'pdf': 'fa-file-pdf', 'doc': 'fa-file-word', 'docx': 'fa-file-word',
        'jpg': 'fa-file-image', 'jpeg': 'fa-file-image', 'png': 'fa-file-image',
    }.get(ext, 'fa-file')

# ================================================================
# CATÁLOGOS
# ================================================================
NOMBRES_SERVICIOS = {
    "funeraria": "Funerarias Municipales",
    "uso-suelo": "Certificado de Uso de Suelo",
    "oaim": "Oficina de Acceso a la Información (OAI/M)",
    "planeamiento": "Planeamiento Urbano",
    "ornato": "Ornato y Préstamos de Áreas",
    "catastro": "Catastro Municipal",
    "aseo-comercial": "Gestión Comercial de Aseo",
}
NOMBRES_DENUNCIAS = {
    "policia": "Policía Municipal",
    "limpieza": "Limpieza y Cuidado de la Vía Pública",
    "basura": "Recogida de Basura",
    "alumbrado": "Alumbrado Público",
    "otro": "Otra denuncia",
}
NOMBRES_CONSULTAS = {"pot": "Plan de Ordenamiento Territorial"}
SERVICIOS_CITAS = {
    "asesoria-legal": "Asesoría Legal Municipal",
    "licencias": "Licencias de Funcionamiento",
    "catastro": "Trámites de Catastro",
    "registro-civil": "Registro Civil",
    "atencion-vecinal": "Atención Vecinal",
    "otro": "Otro trámite",
}

# ================================================================
# CONTEXTO GLOBAL DE TEMPLATES
# ================================================================
@app.context_processor
def inject_global_variables():
    return dict(
        now=datetime.now(),
        NOMBRES_SERVICIOS=NOMBRES_SERVICIOS,
        NOMBRES_DENUNCIAS=NOMBRES_DENUNCIAS,
        NOMBRES_CONSULTAS=NOMBRES_CONSULTAS,
        SERVICIOS_CITAS=SERVICIOS_CITAS,
        logged="user" in session,
        is_admin=session.get("is_admin", False),
        user_name=session.get("user_name", ""),
        user_email=session.get("user", ""),
        user_tipo=session.get("user_tipo", ""),
        foto_perfil=session.get("foto_perfil", ""),
        redis_available=REDIS_AVAILABLE,
        cache_enabled=True,
        debug_mode=app.debug,
    )

# ================================================================
# RUTAS PÚBLICAS
# ================================================================
@app.route("/")
@cache_response(timeout=60)
def index():
    return render_template("index.html")

@app.route("/municipio")
@cache_response(timeout=300)
def municipio():
    return render_template("municipio.html")

@app.route("/servicios")
@cache_response(timeout=300)
def servicios():
    return render_template("servicios.html")

# ── Transparencia ────────────────────────────────────────────────
_TRANSPARENCIA = {
    "transparencia": ("/transparencia", "transparencia.html"),
    "transparencia_estructura": ("/transparencia/estructura", "transparencia_estructura.html"),
    "transparencia_integrantes": ("/transparencia/integrantes", "transparencia_integrantes.html"),
    "transparencia_normativas": ("/transparencia/normativas", "transparencia_normativas.html"),
    "transparencia_proyectos": ("/transparencia/proyectos", "transparencia_proyectos.html"),
    "transparencia_informes": ("/transparencia/informes", "transparencia_informes.html"),
    "transparencia_datos": ("/transparencia/datos", "transparencia_datos.html"),
    "transparencia_atencion": ("/transparencia/atencion", "transparencia_atencion.html"),
    "transparencia_actas": ("/transparencia/actas", "transparencia_actas.html"),
    "transparencia_compras": ("/transparencia/compras", "transparencia_compras.html"),
}
for _name, (_url, _tmpl) in _TRANSPARENCIA.items():
    def _make_view(tmpl):
        @cache_response(timeout=300)
        def _view():
            return render_template(tmpl)
        return _view
    app.add_url_rule(_url, _name, _make_view(_tmpl))

@app.route("/noticias")
@cache_response(timeout=180)
def noticias():
    return render_template("noticias.html")

@app.route("/contacto", methods=["GET"])
def contacto():
    return render_template("contacto.html")

@app.route("/enviar-contacto", methods=["POST"])
@limiter.limit("5 per minute")
def enviar_contacto():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    asunto = request.form.get("asunto", "").strip()
    mensaje = request.form.get("mensaje", "").strip()
    if not all([nombre, email, asunto, mensaje]):
        flash("❌ Todos los campos obligatorios deben completarse.", "error")
        return redirect(url_for("contacto"))
    flash(f"✅ Gracias {nombre}, tu mensaje fue enviado. Te responderemos a la brevedad.", "success")
    return redirect(url_for("contacto"))

# ================================================================
# ARCHIVOS SUBIDOS
# ================================================================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'uploads'), filename)

# ================================================================
# MI CUENTA - CORREGIDO CON SQLALCHEMY
# ================================================================
@app.route("/mi-cuenta")
@login_required
def mi_cuenta():
    from models.usuario import Usuario
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    # Obtener estadísticas del usuario
    try:
        from models import Solicitud, Denuncia
        solicitudes = Solicitud.buscar_por_usuario(email)
        solicitudes_count = len(solicitudes)
        denuncias = [d for d in Denuncia.cargar_todos() if d.usuario_email == email]
        denuncias_count = len(denuncias)
    except:
        solicitudes_count = 0
        denuncias_count = 0
    
    usuario_dict = {
        "email": usuario.email,
        "nombre": usuario.nombre or "",
        "apellidos": usuario.apellidos or "",
        "nombre_completo": usuario.nombre_completo or f"{usuario.nombre or ''} {usuario.apellidos or ''}",
        "telefono": usuario.telefono or "",
        "tipo": usuario.tipo,
        "rol": usuario.rol,
        "activo": usuario.activo,
        "fecha_registro": usuario.fecha_registro.strftime("%d/%m/%Y") if usuario.fecha_registro else "",
        "ultimo_acceso": usuario.ultimo_acceso.strftime("%d/%m/%Y %H:%M") if usuario.ultimo_acceso else "",
        "foto_perfil": usuario.foto_perfil or "",
        "cedula": usuario.cedula or "",
        "direccion": usuario.direccion or "",
        "solicitudes_count": solicitudes_count,
        "denuncias_count": denuncias_count
    }
    
    return render_template("usuarios/mi_cuenta.html", usuario=usuario_dict)


# ================================================================
# SUBIR FOTO DE PERFIL
# ================================================================
@app.route("/subir-foto-perfil", methods=["POST"])
@login_required
def subir_foto_perfil():
    from models.usuario import Usuario
    import uuid
    
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    if 'foto_perfil' not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("mi_cuenta"))
    
    archivo = request.files['foto_perfil']
    
    if archivo.filename == '':
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("mi_cuenta"))
    
    if not _allowed_file(archivo.filename):
        flash("Formato no permitido. Usa PNG, JPG, GIF o WEBP.", "error")
        return redirect(url_for("mi_cuenta"))
    
    # Eliminar foto anterior si existe
    if usuario.foto_perfil:
        ruta_anterior = os.path.join(UPLOAD_FOLDER, usuario.foto_perfil)
        if os.path.exists(ruta_anterior):
            try:
                os.remove(ruta_anterior)
            except:
                pass
    
    # Guardar nueva foto
    ext = archivo.filename.rsplit('.', 1)[1].lower()
    nombre_archivo = f"avatar_{uuid.uuid4().hex[:12]}.{ext}"
    archivo.save(os.path.join(UPLOAD_FOLDER, nombre_archivo))
    
    usuario.foto_perfil = nombre_archivo
    db.session.commit()
    
    # Actualizar sesión
    session["foto_perfil"] = nombre_archivo
    
    flash("✅ Foto de perfil actualizada correctamente.", "success")
    return redirect(url_for("mi_cuenta"))


# ================================================================
# ELIMINAR FOTO DE PERFIL
# ================================================================
@app.route("/eliminar-foto-perfil", methods=["POST"])
@login_required
def eliminar_foto_perfil():
    from models.usuario import Usuario
    
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    if usuario.foto_perfil:
        ruta = os.path.join(UPLOAD_FOLDER, usuario.foto_perfil)
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
            except:
                pass
        
        usuario.foto_perfil = None
        db.session.commit()
        
        # Actualizar sesión
        session.pop("foto_perfil", None)
        
        flash("✅ Foto de perfil eliminada correctamente.", "success")
    else:
        flash("No tienes foto de perfil asignada.", "info")
    
    return redirect(url_for("mi_cuenta"))


# ================================================================
# MIS TRÁMITES - RUTA AGREGADA
# ================================================================
@app.route("/mis-tramites")
@login_required
def mis_tramites():
    from models.usuario import Usuario
    from models import Solicitud, Denuncia
    from models.cita import Cita
    
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    tramites = []
    
    # Obtener solicitudes del usuario
    try:
        solicitudes = Solicitud.buscar_por_usuario(email)
        for s in solicitudes:
            tramites.append({
                'tipo': 'solicitud',
                'folio': s.folio,
                'nombre': s.servicio_nombre,
                'descripcion': s.descripcion[:100] + "..." if len(s.descripcion) > 100 else s.descripcion,
                'estado': s.estado,
                'fecha': s.fecha_creacion,
                'url': url_for('admin.detalle_solicitud', solicitud_id=s.id) if session.get('is_admin') else '#'
            })
    except Exception as e:
        print(f"Error cargando solicitudes: {e}")
    
    # Obtener denuncias del usuario
    try:
        denuncias = Denuncia.cargar_todos()
        for d in denuncias:
            if d.usuario_email == email:
                tramites.append({
                    'tipo': 'denuncia',
                    'folio': d.folio,
                    'nombre': d.tipo_nombre,
                    'descripcion': d.descripcion[:100] + "..." if len(d.descripcion) > 100 else d.descripcion,
                    'estado': d.estado,
                    'fecha': d.fecha_creacion,
                    'url': url_for('admin.detalle_denuncia', denuncia_id=d.id) if session.get('is_admin') else '#'
                })
    except Exception as e:
        print(f"Error cargando denuncias: {e}")
    
    # Obtener citas del usuario
    try:
        citas = Cita.buscar_por_usuario(email)
        for c in citas:
            tramites.append({
                'tipo': 'cita',
                'folio': c.folio,
                'nombre': SERVICIOS_CITAS.get(c.servicio, c.servicio),
                'descripcion': f"Cita para {c.fecha} a las {c.hora}",
                'estado': c.estado,
                'fecha': c.fecha_creacion,
                'url': '#'
            })
    except Exception as e:
        print(f"Error cargando citas: {e}")
    
    # Ordenar por fecha (más recientes primero)
    tramites.sort(key=lambda x: x.get('fecha', ''), reverse=True)
    
    # Estadísticas
    stats = {
        'total': len(tramites),
        'solicitudes': len([t for t in tramites if t['tipo'] == 'solicitud']),
        'denuncias': len([t for t in tramites if t['tipo'] == 'denuncia']),
        'citas': len([t for t in tramites if t['tipo'] == 'cita']),
        'pendientes': len([t for t in tramites if t['estado'] in ['pendiente', 'en_proceso', 'en_investigacion']]),
        'completados': len([t for t in tramites if t['estado'] in ['completado', 'resuelto', 'completada']])
    }
    
    return render_template("usuarios/mis_tramites.html", tramites=tramites, stats=stats)


# ================================================================
# MIS SOLICITUDES
# ================================================================
@app.route("/mis-solicitudes")
@login_required
def mis_solicitudes():
    from models import Solicitud
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    solicitudes = Solicitud.buscar_por_usuario(email)
    solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)
    
    return render_template("usuarios/mis_solicitudes.html", solicitudes=solicitudes)


# ================================================================
# MIS DENUNCIAS
# ================================================================
@app.route("/mis-denuncias")
@login_required
def mis_denuncias():
    from models import Denuncia
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    denuncias = Denuncia.cargar_todos()
    denuncias_usuario = [d for d in denuncias if d.usuario_email == email]
    denuncias_usuario.sort(key=lambda x: x.fecha_creacion, reverse=True)
    
    return render_template("usuarios/mis_denuncias.html", denuncias=denuncias_usuario)


# ================================================================
# MIS CITAS
# ================================================================
@app.route("/mis-citas")
@login_required
def mis_citas():
    from models.cita import Cita
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    citas = Cita.buscar_por_usuario(email)
    citas.sort(key=lambda x: x.fecha + ' ' + x.hora, reverse=True)
    
    return render_template("usuarios/mis_citas.html", citas=citas, servicios=SERVICIOS_CITAS)


# ================================================================
# MANEJADORES DE ERRORES
# ================================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    flash("❌ Demasiadas solicitudes. Por favor espera un momento.", "error")
    if request.path.startswith('/api/'):
        return jsonify({"error": "Rate limit exceeded",
                        "message": "Has realizado demasiadas solicitudes. Intenta de nuevo más tarde.",
                        "retry_after": e.description}), 429
    return redirect(request.referrer or url_for('index'))

# ================================================================
# 🔥 ARRANQUE (MODO DESARROLLO)
# ================================================================
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DOCS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
    
    print("=" * 60)
    print("🚀 VILLA CUTUPÚ - MODO DESARROLLO ACTIVADO")
    print("=" * 60)
    print("✅ SEND_FILE_MAX_AGE_DEFAULT = 0 (sin caché)")
    print("✅ TEMPLATES_AUTO_RELOAD = True")
    print("✅ DEBUG = True")
    print("✅ Caché limpiado al iniciar")
    print("✅ Base de datos SQLAlchemy inicializada")
    print("✅ Usuarios por defecto creados")
    print("=" * 60)
    print("🌐 Servidor en: http://localhost:5000")
    print("=" * 60)
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=True
    )