# ================================================================
# APP.PY - VILLA CUTUPÚ MUNICIPAL SYSTEM (VERSIÓN COMPLETA - CORREGIDA PARA RENDER)
# ================================================================

# ================================================================
# 1. IMPORTS PRINCIPALES
# ================================================================
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, send_from_directory, abort
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
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ================================================================
# 2. IMPORTS ADICIONALES
# ================================================================
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import hashlib

# ================================================================
# 3. CONFIGURACIÓN DE EXTENSIONES
# ================================================================
from config_manager import get_flask_config, init_production_config, is_production
from extensions import db, login_manager, migrate

# ================================================================
# 4. IMPORTS PARA CLOUDINARY
# ================================================================
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ================================================================
# 5. CREACIÓN DE LA APLICACIÓN
# ================================================================
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Inicializar configuración de producción si aplica
init_production_config()

# 🔥🔥🔥 NUEVA FORMA DE CARGAR CONFIGURACIÓN (CORREGIDO PARA RENDER) 🔥🔥🔥
app.config.update(get_flask_config())

# 🔥🔥🔥 PRINT OBLIGATORIO PARA DIAGNÓSTICO 🔥🔥🔥
print("=" * 80)
print("🔥 DATABASE FINAL:", app.config.get('SQLALCHEMY_DATABASE_URI', 'NO CONFIGURADA'))
print("=" * 80)

# Imprimir diagnóstico (IMPORTANTE para debug)
print("=" * 60)
print("📊 DIAGNÓSTICO DE BASE DE DATOS:")
print(f"   Modo producción: {is_production()}")
print(f"   Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurada')[:80]}...")
print(f"   Es PostgreSQL: {'✅' if 'postgresql' in str(app.config.get('SQLALCHEMY_DATABASE_URI', '')) else '❌'}")
print(f"   SSL Mode: {'✅' if 'sslmode=require' in str(app.config.get('SQLALCHEMY_DATABASE_URI', '')) else '❌'}")
print(f"   localhost detectado: {'❌ CRÍTICO!' if 'localhost' in str(app.config.get('SQLALCHEMY_DATABASE_URI', '')) else '✅ OK'}")
print("=" * 60)

# ================================================================
# 6. CONFIGURAR CLOUDINARY (con prioridad a variables de entorno)
# ================================================================
cloudinary.config(
    cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key=app.config.get('CLOUDINARY_API_KEY', ''),
    api_secret=app.config.get('CLOUDINARY_API_SECRET', ''),
    secure=True
)

if app.config.get('CLOUDINARY_ENABLED'):
    print("✅ Cloudinary configurado correctamente")
else:
    print("⚠️ Cloudinary no configurado (faltan credenciales)")

# ================================================================
# 7. INICIALIZAR BASE DE DATOS Y LOGIN
# ================================================================
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)

@login_manager.user_loader
def load_user(user_id):
    from models.usuario import Usuario
    try:
        user_id_int = int(user_id) if user_id else None
        if user_id_int is None:
            return None
        return Usuario.query.get(user_id_int)
    except (ValueError, TypeError):
        return None

# ================================================================
# 8. CONFIGURACIÓN DE LA APLICACIÓN
# ================================================================
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
DOCS_FOLDER = os.path.join('static', 'uploads', 'documentos')
ALLOWED_DOC_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
DOCS_MAX_POR_TRAMITE = 5
DOCS_MAX_SIZE_MB = 10

# Registrar blueprints
app.register_blueprint(auth)
app.register_blueprint(admin_bp)

# ================================================================
# 9. DETECCIÓN DE REDIS
# ================================================================
REDIS_AVAILABLE = False
redis_client = None

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
# 10. CACHÉ
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

try:
    cache.clear()
    print("✅ Caché limpiado al iniciar")
except Exception as e:
    print(f"⚠️ No se pudo limpiar caché: {e}")

# ================================================================
# 11. RATE LIMITING
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
# 12. CONFIGURACIÓN POR DEFECTO
# ================================================================
def init_default_config():
    from models.configuracion import Configuracion
    
    config_defaults = {
        'nombre_municipio': ('Villa Cutupú', 'string', 'general'),
        'siglas': ('JDVC', 'string', 'general'),
        'direccion': ('Calle Principal #123, Villa Cutupú', 'string', 'general'),
        'telefono': ('(809) 000-0000', 'string', 'general'),
        'email_institucional': ('info@villacutupu.gob.do', 'string', 'general'),
        'sitio_web': ('https://villacutupu.gob.do', 'string', 'general'),
        'zona_horaria': ('America/Santo_Domingo', 'string', 'general'),
        'formato_fecha': ('DD/MM/YYYY', 'string', 'general'),
        'idioma': ('es', 'string', 'general'),
        'pass_min_length': (8, 'int', 'seguridad'),
        'max_intentos_fallidos': (5, 'int', 'seguridad'),
        'pass_expiry_dias': (90, 'int', 'seguridad'),
        'lockout_minutos': (15, 'int', 'seguridad'),
        'session_duracion_horas': (8, 'int', 'seguridad'),
        'inactividad_minutos': (30, 'int', 'seguridad'),
        'require_mayusculas': (True, 'bool', 'seguridad'),
        'require_numeros': (True, 'bool', 'seguridad'),
        'require_especiales': (False, 'bool', 'seguridad'),
        'single_session': (False, 'bool', 'seguridad'),
        'log_intentos_acceso': (True, 'bool', 'seguridad'),
        'two_factor_auth': (False, 'bool', 'seguridad'),
        'debug_mode': (app.debug, 'bool', 'sistema'),
        'maintenance_mode': (False, 'bool', 'sistema'),
        'audit_log': (True, 'bool', 'sistema'),
        'file_logging': (True, 'bool', 'sistema'),
        'cache_sessions_segundos': (3600, 'int', 'sistema'),
        'cache_static_dias': (7, 'int', 'sistema'),
        'max_solicitudes_mes': (10, 'int', 'servicios'),
        'max_denuncias_mes': (5, 'int', 'servicios'),
        'max_file_size_mb': (5, 'int', 'servicios'),
        'tipos_archivo_permitidos': ('pdf,jpg,png,doc,docx', 'string', 'servicios'),
        'color_primario': ('#2d6a4f', 'string', 'apariencia'),
        'color_acento': ('#e9c46a', 'string', 'apariencia'),
        'color_sidebar': ('#1b4332', 'string', 'apariencia'),
        'sidebar_colapsado': (False, 'bool', 'apariencia'),
        'mostrar_breadcrumbs': (True, 'bool', 'apariencia'),
        'animaciones': (True, 'bool', 'apariencia'),
        'notif_nueva_solicitud': (True, 'bool', 'notificaciones'),
        'notif_nueva_denuncia': (True, 'bool', 'notificaciones'),
        'notif_nuevo_usuario': (True, 'bool', 'notificaciones'),
        'notif_cambio_estado': (True, 'bool', 'notificaciones'),
        'notif_resumen_diario': (False, 'bool', 'notificaciones'),
    }
    
    for clave, (valor, tipo, seccion) in config_defaults.items():
        if Configuracion.get(clave) is None:
            Configuracion.set(clave, valor, tipo, seccion)
            print(f"✅ Configuración por defecto creada: {clave} = {valor}")

# ================================================================
# 13. CREAR TABLAS Y USUARIOS POR DEFECTO (CORREGIDO)
# ================================================================
from auth import crear_usuarios_por_defecto
from models.configuracion import Configuracion

with app.app_context():
    # En producción, usar migraciones; en desarrollo, crear tablas
    if not is_production():
        db.create_all()
        print("✅ Tablas de base de datos creadas/verificadas (modo desarrollo)")
    else:
        # En producción, intentar crear tablas si no existen (conexión segura)
        try:
            # Verificar si las tablas existen
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                print("⚠️ No se encontraron tablas en producción - creándolas...")
                db.create_all()
                print("✅ Tablas creadas exitosamente")
            else:
                print(f"✅ Modo producción - {len(existing_tables)} tablas existentes")
        except Exception as e:
            print(f"⚠️ Error verificando tablas: {e}")
            # Intentar crear igualmente
            try:
                db.create_all()
                print("✅ Tablas creadas después de error")
            except Exception as create_error:
                print(f"❌ Error crítico creando tablas: {create_error}")
    
    # Crear usuarios por defecto
    crear_usuarios_por_defecto()
    print("✅ Usuarios por defecto creados/verificados")
    
    # Inicializar configuración
    init_default_config()

# ================================================================
# 14. CABECERAS DE RENDIMIENTO Y SEGURIDAD
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
# 15. DECORADOR CACHÉ DE API
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
# 16. FUNCIONES AUXILIARES
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
# 17. FUNCIÓN PARA GUARDAR CONTACTOS
# ================================================================
def guardar_contacto_en_bd(nombre, email, telefono, asunto, mensaje):
    try:
        from models.mensaje import Mensaje
        
        folio = f"CTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        nuevo_contacto = Mensaje(
            tramite_folio=folio,
            tramite_tipo='consulta',
            usuario_email=email,
            autor_email=email,
            autor_nombre=nombre,
            mensaje=f"Asunto: {asunto}\nTeléfono: {telefono if telefono else 'No especificado'}\n\nMensaje: {mensaje}",
            es_admin=False
        )
        
        db.session.add(nuevo_contacto)
        db.session.commit()
        
        print(f"✅ Contacto guardado - Folio: {folio}")
        return True, folio
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error guardando contacto: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

# ================================================================
# 18. FUNCIONES DE CLOUDINARY
# ================================================================
def subir_foto_cloudinary(archivo, email, folder="fotos_perfil"):
    if not app.config.get('CLOUDINARY_ENABLED'):
        return {'success': False, 'error': 'Cloudinary no está configurado'}
    
    try:
        if email is None:
            email_str = "usuario"
        else:
            email_str = str(email)

        email_str = email_str.replace(' ', '_').replace('@', '_').replace('.', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        public_id = f"{folder}/{email_str}_{timestamp}"
        
        print(f"📤 Subiendo a Cloudinary con public_id: {public_id}")
        archivo.stream.seek(0)
        
        upload_result = cloudinary.uploader.upload(
            archivo.stream,
            public_id=public_id,
            folder=folder,
            overwrite=True,
            transformation=[
                {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                {"fetch_format": "auto", "quality": "auto"}
            ]
        )
        
        return {
            'success': True,
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id']
        }
    except Exception as e:
        print(f"❌ Error subiendo a Cloudinary: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def eliminar_foto_cloudinary(public_id):
    if not app.config.get('CLOUDINARY_ENABLED') or not public_id:
        return True
    
    try:
        if not public_id:
            return True
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"❌ Error eliminando foto: {e}")
        return False

# ================================================================
# 19. CATÁLOGOS
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
    "asesoria_legal": "Asesoría Legal Municipal",
    "licencias": "Licencias de Funcionamiento",
    "catastro": "Trámites de Catastro",
    "registro_civil": "Registro Civil",
    "atencion_ciudadana": "Atención Ciudadana",
    "tesoreria": "Tesorería Municipal",
    "planeamiento": "Planeamiento Urbano",
    "oaim": "Oficina de Acceso a la Información",
    "funeraria": "Servicios Funerarios",
}

# ================================================================
# 20. CONTEXTO GLOBAL DE TEMPLATES
# ================================================================
@app.context_processor
def inject_global_variables():
    from models.configuracion import Configuracion
    
    config = {
        'nombre_municipio': Configuracion.get('nombre_municipio', 'Villa Cutupú'),
        'siglas': Configuracion.get('siglas', 'JDVC'),
        'direccion': Configuracion.get('direccion', ''),
        'telefono': Configuracion.get('telefono', ''),
        'email_institucional': Configuracion.get('email_institucional', ''),
        'sitio_web': Configuracion.get('sitio_web', ''),
        'color_primario': Configuracion.get('color_primario', '#2d6a4f'),
        'color_acento': Configuracion.get('color_acento', '#e9c46a'),
        'color_sidebar': Configuracion.get('color_sidebar', '#1b4332'),
        'sidebar_colapsado': Configuracion.get('sidebar_colapsado', False),
        'zona_horaria': Configuracion.get('zona_horaria', 'America/Santo_Domingo'),
        'formato_fecha': Configuracion.get('formato_fecha', 'DD/MM/YYYY'),
        'maintenance_mode': Configuracion.get('maintenance_mode', False),
        'mostrar_breadcrumbs': Configuracion.get('mostrar_breadcrumbs', True),
        'animaciones': Configuracion.get('animaciones', True),
    }
    
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
        config=config
    )

# ================================================================
# 21. RUTAS PÚBLICAS
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

@app.route("/bitacora")
@cache_response(timeout=300)
def bitacora():
    return render_template("bitacora.html")

@app.route("/mapa")
@cache_response(timeout=60)
def mapa_incidencias():
    try:
        from models import Denuncia
        
        denuncias = Denuncia.cargar_todos()
        denuncias_geo = []
        for d in denuncias:
            lat = None
            lng = None
            
            if hasattr(d, 'lat') and d.lat and hasattr(d, 'lng') and d.lng:
                try:
                    lat = float(d.lat)
                    lng = float(d.lng)
                except:
                    pass
            elif hasattr(d, 'latitud') and d.latitud and hasattr(d, 'longitud') and d.longitud:
                try:
                    lat = float(d.latitud)
                    lng = float(d.longitud)
                except:
                    pass
            elif hasattr(d, 'coordenadas') and d.coordenadas and ',' in str(d.coordenadas):
                try:
                    parts = str(d.coordenadas).split(',')
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                except:
                    pass
            
            if lat and lng:
                denuncias_geo.append({
                    'id': d.id,
                    'folio': d.folio,
                    'tipo': d.tipo,
                    'tipo_nombre': NOMBRES_DENUNCIAS.get(d.tipo, d.tipo),
                    'estado': d.estado,
                    'descripcion': d.descripcion[:200] if hasattr(d, 'descripcion') and d.descripcion else '',
                    'lat': lat,
                    'lng': lng,
                    'fecha': d.fecha_creacion
                })
        
        return render_template(
            'mapa_publico.html',
            denuncias=denuncias_geo,
            tipos=NOMBRES_DENUNCIAS,
            stats={'total': len(denuncias), 'geolocalizadas': len(denuncias_geo)}
        )
    except Exception as e:
        print(f"Error en mapa público: {e}")
        import traceback
        traceback.print_exc()
        return render_template('mapa_publico.html', denuncias=[], tipos=NOMBRES_DENUNCIAS, stats={'total': 0, 'geolocalizadas': 0})

@app.route("/denuncia/<denuncia_id>")
def detalle_denuncia_publica(denuncia_id):
    try:
        from models import Denuncia
        denuncia = Denuncia.buscar_por_id(denuncia_id)
        if not denuncia:
            flash("Denuncia no encontrada", "error")
            return redirect(url_for('mapa_incidencias'))
        
        return render_template('denuncia_publica_detalle.html', denuncia=denuncia, tipos=NOMBRES_DENUNCIAS)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('mapa_incidencias'))

# ================================================================
# 22. TRANSPARENCIA - RUTAS
# ================================================================
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

def create_transparency_view(template_name):
    @cache_response(timeout=300)
    def view():
        return render_template(template_name)
    return view

for route_name, (url_path, template_name) in _TRANSPARENCIA.items():
    app.add_url_rule(url_path, route_name, create_transparency_view(template_name))

# ================================================================
# 23. NOTICIAS Y CONTACTO PÚBLICO (RUTAS COMPLETAS CORREGIDAS)
# ================================================================

# ================================================================
# 23.1 NOTICIAS - LISTADO PAGINADO
# ================================================================
@app.route("/noticias")
@cache_response(timeout=180)
def noticias():
    """Lista paginada de noticias"""
    from models.noticia import Noticia, CategoriaNoticia
    
    pagina = request.args.get('pagina', 1, type=int)
    categoria_slug = request.args.get('categoria', None)
    
    categorias = CategoriaNoticia.todas_activas()
    
    resultado = Noticia.listar_publicadas(
        pagina=pagina,
        por_pagina=9,
        categoria_slug=categoria_slug
    )
    
    categoria_actual = None
    if categoria_slug:
        categoria_actual = CategoriaNoticia.query.filter_by(slug=categoria_slug).first()
    
    return render_template(
        'noticias.html',
        noticias=resultado['items'],
        paginacion={
            'total': resultado['total'],
            'pagina': resultado['pagina'],
            'por_pagina': resultado['por_pagina'],
            'total_paginas': resultado['total_paginas'],
            'tiene_siguiente': resultado['tiene_siguiente'],
            'tiene_anterior': resultado['tiene_anterior']
        },
        categorias=categorias,
        categoria_actual=categoria_actual
    )

# ================================================================
# 23.2 NOTICIAS - DETALLE
# ================================================================
@app.route("/noticias/<slug>")
def detalle_noticia(slug):
    """Detalle de una noticia"""
    from models.noticia import Noticia
    from models.comentario_noticia import ComentarioNoticia
    from models.like_noticia import LikeNoticia
    
    noticia = Noticia.buscar_por_slug(slug)
    
    if not noticia or noticia.estado != 'publicado':
        abort(404)
    
    noticia.incrementar_vistas()
    
    comentarios = ComentarioNoticia.listar_por_noticia(noticia.id, solo_aprobados=True)
    
    cliente_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if cliente_ip and ',' in cliente_ip:
        cliente_ip = cliente_ip.split(',')[0].strip()
    
    ya_dio_like = LikeNoticia.ya_dio_like(noticia.id, cliente_ip) if cliente_ip else False
    
    return render_template(
        'detalle_noticia.html',
        noticia=noticia,
        comentarios=comentarios,
        ya_dio_like=ya_dio_like
    )

# ================================================================
# 23.3 API - LIKE/NOTICIA (TOGGLE)
# ================================================================
@app.route("/api/noticias/<slug>/like", methods=["POST"])
@limiter.limit("30 per minute")
def api_noticia_like(slug):
    """Toggle like en una noticia"""
    from models.noticia import Noticia
    from models.like_noticia import LikeNoticia
    from models.log_actividad import registrar_log
    
    try:
        noticia = Noticia.buscar_por_slug(slug)
        if not noticia or noticia.estado != 'publicado':
            return jsonify({'ok': False, 'mensaje': 'Noticia no encontrada'}), 404
        
        cliente_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if cliente_ip and ',' in cliente_ip:
            cliente_ip = cliente_ip.split(',')[0].strip()
        
        if not cliente_ip:
            return jsonify({'ok': False, 'mensaje': 'No se pudo identificar la IP'}), 400
        
        usuario_email = session.get('user') if session.get('user') else None
        
        liked, total_likes = LikeNoticia.dar_like(
            noticia_id=noticia.id,
            usuario_ip=cliente_ip,
            usuario_email=usuario_email
        )
        
        registrar_log(
            accion='like_noticia' if liked else 'unlike_noticia',
            modulo='noticias',
            descripcion=f"{'Like' if liked else 'Unlike'} en noticia {noticia.slug}",
            datos_extra={'noticia_id': noticia.id, 'noticia_slug': noticia.slug}
        )
        
        return jsonify({
            'ok': True,
            'liked': liked,
            'total': total_likes
        })
        
    except Exception as e:
        print(f"Error en like_noticia: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'mensaje': str(e)}), 500

# ================================================================
# 23.4 API - COMENTAR/NOTICIA
# ================================================================
@app.route("/api/noticias/<slug>/comentar", methods=["POST"])
@limiter.limit("10 per minute")
def api_noticia_comentar(slug):
    """Agregar un comentario a una noticia"""
    from models.noticia import Noticia
    from models.comentario_noticia import ComentarioNoticia
    from models.log_actividad import registrar_log
    
    try:
        noticia = Noticia.buscar_por_slug(slug)
        if not noticia or noticia.estado != 'publicado':
            return jsonify({'ok': False, 'mensaje': 'Noticia no encontrada'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'ok': False, 'mensaje': 'Datos inválidos'}), 400
        
        autor_nombre = data.get('autor_nombre', '').strip()
        contenido = data.get('contenido', '').strip()
        autor_email = data.get('autor_email', '').strip()
        
        if not autor_nombre:
            return jsonify({'ok': False, 'mensaje': 'El nombre es obligatorio'}), 400
        
        if not contenido:
            return jsonify({'ok': False, 'mensaje': 'El comentario no puede estar vacío'}), 400
        
        if len(contenido) > 5000:
            return jsonify({'ok': False, 'mensaje': 'El comentario es demasiado largo (máx 5000 caracteres)'}), 400
        
        cliente_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if cliente_ip and ',' in cliente_ip:
            cliente_ip = cliente_ip.split(',')[0].strip()
        
        comentario = ComentarioNoticia.crear(
            noticia_id=noticia.id,
            autor_nombre=autor_nombre,
            contenido=contenido,
            autor_email=autor_email if autor_email else None,
            ip_autor=cliente_ip
        )
        
        registrar_log(
            accion='comentar_noticia',
            modulo='noticias',
            descripcion=f"Nuevo comentario en noticia {noticia.slug} por {autor_nombre}",
            datos_extra={'noticia_id': noticia.id, 'comentario_id': comentario.id}
        )
        
        return jsonify({
            'ok': True,
            'mensaje': 'Comentario enviado correctamente. Será revisado por un administrador.',
            'comentario_id': comentario.id
        })
        
    except Exception as e:
        print(f"Error en comentar_noticia: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'mensaje': str(e)}), 500

# ================================================================
# 23.5 CONTACTO PÚBLICO
# ================================================================
@app.route("/contacto", methods=["GET"])
def contacto():
    return render_template("contacto.html")

@app.route("/enviar-contacto", methods=["POST"])
@limiter.limit("5 per minute")
def enviar_contacto():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    telefono = request.form.get("telefono", "").strip()
    asunto = request.form.get("asunto", "").strip()
    mensaje = request.form.get("mensaje", "").strip()
    
    if not all([nombre, email, asunto, mensaje]):
        flash("❌ Todos los campos obligatorios deben completarse.", "error")
        return redirect(url_for("contacto"))
    
    exito, resultado = guardar_contacto_en_bd(nombre, email, telefono, asunto, mensaje)
    
    if exito:
        flash(f"✅ Gracias {nombre}, tu mensaje fue enviado. Folio: {resultado}", "success")
    else:
        flash(f"❌ Error al guardar tu mensaje. Por favor intenta más tarde.", "error")
    
    return redirect(url_for("contacto"))

# ================================================================
# 23.6 ARCHIVOS SUBIDOS
# ================================================================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'uploads'), filename)

# ================================================================
# 24. MI CUENTA - RUTAS DE USUARIO
# ================================================================
@app.route("/perfil")
@login_required
def perfil():
    return redirect(url_for('mi_cuenta'))

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
    
    try:
        from models import Solicitud, Denuncia
        solicitudes = Solicitud.buscar_por_usuario(email)
        solicitudes_count = len(solicitudes)
        denuncias = [d for d in Denuncia.cargar_todos() if d.usuario_email == email]
        denuncias_count = len(denuncias)
    except:
        solicitudes_count = 0
        denuncias_count = 0
    
    foto_url = usuario.foto_perfil_url or usuario.foto_perfil or ""
    
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
        "foto_perfil": foto_url,
        "foto_perfil_public_id": usuario.foto_perfil_public_id or "",
        "cedula": usuario.cedula or "",
        "direccion": usuario.direccion or "",
        "solicitudes_count": solicitudes_count,
        "denuncias_count": denuncias_count
    }
    
    return render_template("usuarios/mi_cuenta.html", usuario=usuario_dict)

@app.route("/subir-foto-perfil", methods=["POST"])
@login_required
def subir_foto_perfil():
    from models.usuario import Usuario
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
    
    resultado = subir_foto_cloudinary(archivo, usuario.email)
    
    if not resultado['success']:
        flash(f"Error al subir la foto: {resultado['error']}", "error")
        return redirect(url_for("mi_cuenta"))
    
    if usuario.foto_perfil_public_id:
        eliminar_foto_cloudinary(usuario.foto_perfil_public_id)
    
    usuario.foto_perfil_url = resultado['url']
    usuario.foto_perfil_public_id = resultado['public_id']
    usuario.foto_perfil = resultado['url']
    db.session.commit()
    
    session["foto_perfil"] = resultado['url']
    flash("✅ Foto de perfil actualizada correctamente.", "success")
    return redirect(url_for("mi_cuenta"))

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
    
    if usuario.foto_perfil_public_id:
        eliminar_foto_cloudinary(usuario.foto_perfil_public_id)
        usuario.foto_perfil_url = None
        usuario.foto_perfil_public_id = None
        usuario.foto_perfil = None
        db.session.commit()
        session.pop("foto_perfil", None)
        flash("✅ Foto de perfil eliminada correctamente.", "success")
    else:
        flash("No tienes foto de perfil asignada.", "info")
    
    return redirect(url_for("mi_cuenta"))

@app.route("/editar-perfil", methods=["POST"])
@login_required
def editar_perfil():
    from models.usuario import Usuario
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    usuario.nombre = request.form.get("nombre", "")
    usuario.apellidos = request.form.get("apellidos", "")
    usuario.telefono = request.form.get("telefono", "")
    usuario.direccion = request.form.get("direccion", "")
    
    nombre_completo = f"{usuario.nombre} {usuario.apellidos}".strip()
    if nombre_completo:
        usuario.nombre_completo = nombre_completo
    
    db.session.commit()
    session["user_name"] = usuario.nombre_completo
    flash("✅ Perfil actualizado correctamente.", "success")
    return redirect(url_for("mi_cuenta"))

@app.route("/mi-cuenta/configuracion", methods=["GET", "POST"])
@login_required
def configuracion_cuenta():
    from models.usuario import Usuario
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        if hasattr(usuario, 'notificaciones_email'):
            usuario.notificaciones_email = request.form.get("notificaciones_email") == "on"
        if hasattr(usuario, 'notificaciones_whatsapp'):
            usuario.notificaciones_whatsapp = request.form.get("notificaciones_whatsapp") == "on"
        
        db.session.commit()
        flash("✅ Configuración actualizada correctamente.", "success")
        return redirect(url_for("mi_cuenta"))
    
    return render_template("usuarios/configuracion.html", usuario=usuario)

# ================================================================
# 25. MIS TRÁMITES - RUTAS DEL USUARIO
# ================================================================
@app.route("/mis-servicios")
@login_required
def mis_servicios():
    try:
        from models import Solicitud
        email = session.get("user")
        solicitudes = Solicitud.buscar_por_usuario(email)
        solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)
        return render_template("usuarios/mis_solicitudes.html", solicitudes=solicitudes)
    except Exception as e:
        print(f"Error cargando servicios: {e}")
        flash(f"Error al cargar servicios: {str(e)}", "error")
        return render_template("usuarios/mis_solicitudes.html", solicitudes=[])

@app.route("/mis-tramites")
@login_required
def mis_tramites():
    from models.usuario import Usuario
    from models import Solicitud, Denuncia
    from models.cita import Cita
    from datetime import datetime as dt
    
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    tramites = []
    
    # Solicitudes
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
    
    # Denuncias
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
    
    # Citas
    try:
        citas = Cita.buscar_por_usuario(email)
        for c in citas:
            fecha_cita = c.fecha_creacion
            if isinstance(fecha_cita, str):
                try:
                    fecha_cita = dt.strptime(fecha_cita, '%Y-%m-%d %H:%M:%S')
                except:
                    fecha_cita = dt.now()
            
            tramites.append({
                'tipo': 'cita',
                'folio': c.folio,
                'nombre': SERVICIOS_CITAS.get(c.servicio, c.servicio),
                'descripcion': f"Cita para {c.fecha} a las {c.hora}",
                'estado': c.estado,
                'fecha': fecha_cita,
                'url': '#'
            })
    except Exception as e:
        print(f"Error cargando citas: {e}")
    
    # Contactos/Mensajes del usuario
    try:
        from models.mensaje import Mensaje
        contactos_usuario = Mensaje.query.filter_by(
            usuario_email=email,
            tramite_tipo='consulta',
            es_admin=False
        ).order_by(Mensaje.fecha_creacion.desc()).all()
        
        for c in contactos_usuario:
            respuesta = Mensaje.query.filter_by(
                tramite_folio=c.tramite_folio,
                es_admin=True
            ).first()
            
            fecha_contacto = c.fecha_creacion
            if isinstance(fecha_contacto, str):
                try:
                    fecha_contacto = dt.strptime(fecha_contacto, '%Y-%m-%d %H:%M:%S')
                except:
                    fecha_contacto = dt.now()
            
            tramites.append({
                'tipo': 'contacto',
                'folio': c.tramite_folio,
                'nombre': 'Mensaje de contacto',
                'descripcion': c.mensaje[:100] + '...' if len(c.mensaje) > 100 else c.mensaje,
                'estado': 'respondido' if respuesta else 'pendiente',
                'fecha': fecha_contacto,
                'respuesta': respuesta.mensaje if respuesta else None,
                'fecha_creacion': fecha_contacto,
                'url': '#'
            })
    except Exception as e:
        print(f"Error cargando contactos: {e}")
        import traceback
        traceback.print_exc()
    
    # Función robusta para obtener la fecha como datetime
    def get_fecha_comparable(item):
        fecha = item.get('fecha')
        if fecha is None:
            return dt.min
        if isinstance(fecha, dt):
            return fecha
        if isinstance(fecha, str):
            try:
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y']:
                    try:
                        return dt.strptime(fecha, fmt)
                    except:
                        continue
                return dt.min
            except:
                return dt.min
        return dt.min
    
    # Normalizar fecha_creacion como string en todos los trámites
    for t in tramites:
        fecha = t.get('fecha')
        if fecha is None:
            t['fecha_creacion'] = ''
        elif isinstance(fecha, dt):
            t['fecha_creacion'] = fecha.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(fecha, str):
            t['fecha_creacion'] = fecha
        else:
            t['fecha_creacion'] = str(fecha)

    # Ordenar usando la función robusta
    tramites.sort(key=get_fecha_comparable, reverse=True)

    # Estadísticas
    stats = {
        'total': len(tramites),
        'solicitudes': len([t for t in tramites if t['tipo'] == 'solicitud']),
        'denuncias': len([t for t in tramites if t['tipo'] == 'denuncia']),
        'citas': len([t for t in tramites if t['tipo'] == 'cita']),
        'contactos': len([t for t in tramites if t['tipo'] == 'contacto']),
        'pendientes': len([t for t in tramites if t['estado'] in ['pendiente', 'en_proceso', 'en_investigacion']]),
        'completados': len([t for t in tramites if t['estado'] in ['completado', 'resuelto', 'completada', 'respondido']])
    }

    import json as _json

    def tramite_serializable(t):
        result = {}
        for k, v in t.items():
            if isinstance(v, dt):
                result[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                result[k] = v
        return result

    tramites_json = _json.dumps([tramite_serializable(t) for t in tramites], ensure_ascii=False)

    return render_template(
        "usuarios/mis_tramites.html",
        tramites=tramites,
        stats=stats,
        tramites_json=tramites_json
    )

@app.route("/mis-solicitudes")
@login_required
def mis_solicitudes():
    from models import Solicitud
    email = session.get("user")
    solicitudes = Solicitud.buscar_por_usuario(email)
    solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)
    return render_template("usuarios/mis_solicitudes.html", solicitudes=solicitudes)

@app.route("/cancelar-solicitud/<solicitud_id>", methods=["POST"])
@login_required
def cancelar_solicitud(solicitud_id):
    from models.solicitud import Solicitud
    email = session.get("user")
    
    solicitud = Solicitud.buscar_por_id(solicitud_id)
    
    if not solicitud:
        flash("Solicitud no encontrada.", "error")
        return redirect(url_for("mis_solicitudes"))
    
    if solicitud.usuario_email != email:
        flash("No tienes permiso para cancelar esta solicitud.", "error")
        return redirect(url_for("mis_solicitudes"))
    
    if solicitud.estado not in ['pendiente', 'en_proceso']:
        flash("Esta solicitud no se puede cancelar.", "error")
        return redirect(url_for("mis_solicitudes"))
    
    solicitud.actualizar_estado('cancelado', comentario='Cancelada por el usuario', admin_email=email)
    flash("✅ Solicitud cancelada correctamente.", "success")
    return redirect(url_for("mis_solicitudes"))

@app.route("/mis-denuncias")
@login_required
def mis_denuncias():
    from models import Denuncia
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    todas_denuncias = Denuncia.cargar_todos()
    denuncias_usuario = [d for d in todas_denuncias if d.usuario_email == email]
    denuncias_usuario.sort(key=lambda x: x.fecha_creacion, reverse=True)
    return render_template("usuarios/mis_denuncias.html", denuncias=denuncias_usuario)

@app.route("/mis-consultas")
@login_required
def mis_consultas():
    flash("⚠️ Funcionalidad en desarrollo. Próximamente disponible.", "warning")
    return redirect(url_for("mis_tramites"))

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
    return render_template("citas/mis_citas.html", citas=citas, servicios=SERVICIOS_CITAS)

# ================================================================
# 26. RUTAS DINÁMICAS PARA FORMULARIOS
# ================================================================
@app.route('/solicitar/<tipo>')
@login_required
def solicitar(tipo):
    if tipo not in NOMBRES_SERVICIOS:
        flash(f"❌ Servicio '{tipo}' no encontrado.", "error")
        return redirect(url_for('servicios'))
    
    return render_template('solicitudes/formulario.html', 
                         tipo=tipo,
                         nombre_servicio=NOMBRES_SERVICIOS[tipo],
                         servicios=NOMBRES_SERVICIOS)

@app.route('/denunciar/<tipo>')
@login_required
def denunciar(tipo):
    if tipo not in NOMBRES_DENUNCIAS:
        flash(f"❌ Tipo de denuncia '{tipo}' no encontrado.", "error")
        return redirect(url_for('servicios'))
    
    return render_template('denuncias/formulario.html', 
                         tipo=tipo,
                         nombre_denuncia=NOMBRES_DENUNCIAS[tipo])

@app.route('/consultar/<tipo>')
@login_required
def consultar(tipo):
    if tipo not in NOMBRES_CONSULTAS:
        flash(f"❌ Tipo de consulta '{tipo}' no encontrado.", "error")
        return redirect(url_for('servicios'))
    
    return render_template('consultas/formulario.html', 
                         tipo=tipo,
                         nombre_consulta=NOMBRES_CONSULTAS[tipo])

# ================================================================
# 27. PROCESAMIENTO DE FORMULARIOS
# ================================================================
@app.route("/procesar-solicitud", methods=["POST"])
@login_required
def procesar_solicitud():
    try:
        email = session.get('user')

        servicio_id = (
            request.form.get('servicio_id', '').strip() or
            request.form.get('servicio', '').strip() or
            request.form.get('tipo', '').strip()
        )

        descripcion = (
            request.form.get('descripcion', '').strip() or
            request.form.get('detalles_adicionales', '').strip()
        )

        nombre = request.form.get('nombre', '').strip()
        cedula = request.form.get('cedula', '').strip()

        if not nombre or not cedula:
            from models.usuario import Usuario
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario:
                nombre = nombre or usuario.nombre_completo or f"{usuario.nombre or ''} {usuario.apellidos or ''}".strip()
                cedula = cedula or usuario.cedula or ''

        if not servicio_id:
            flash("❌ No se pudo identificar el servicio.", "error")
            return redirect(request.referrer or url_for('servicios'))

        if not descripcion:
            flash("❌ La descripción es obligatoria.", "error")
            return redirect(request.referrer or url_for('servicios'))

        if not nombre:
            flash("❌ No se encontró el nombre del usuario. Actualiza tu perfil.", "error")
            return redirect(url_for('mi_cuenta'))

        servicio_nombre = NOMBRES_SERVICIOS.get(servicio_id, "Servicio Municipal")

        from models.solicitud import Solicitud
        solicitud = Solicitud.crear(
            usuario_email=email,
            usuario_nombre=nombre,
            usuario_cedula=cedula or 'N/A',
            servicio_id=servicio_id,
            servicio_nombre=servicio_nombre,
            descripcion=descripcion
        )

        flash(f"✅ ¡Solicitud creada! Tu folio es: {solicitud.folio}", "success")
        return redirect(url_for('mis_servicios'))

    except Exception as e:
        print(f"Error al procesar solicitud: {e}")
        import traceback
        traceback.print_exc()
        flash(f"❌ Error al procesar la solicitud: {str(e)}", "error")
        return redirect(url_for('servicios'))

@app.route('/procesar-denuncia', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def procesar_denuncia():
    from models import Denuncia
    from models.usuario import Usuario
    
    email = session.get("user")
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    tipo = request.form.get('tipo')
    ubicacion = request.form.get('ubicacion')
    descripcion = request.form.get('descripcion')
    evidencia = request.form.get('evidencia', '')
    
    lat_str = request.form.get('lat', '')
    lng_str = request.form.get('lng', '')
    lat = float(lat_str) if lat_str and lat_str.strip() else None
    lng = float(lng_str) if lng_str and lng_str.strip() else None
    
    if not tipo or not ubicacion or not descripcion:
        flash("❌ Todos los campos obligatorios deben completarse.", "error")
        return redirect(url_for('denunciar', tipo=tipo or 'otro'))
    
    try:
        nueva_denuncia = Denuncia(
            folio=Denuncia.generar_folio(),
            usuario_email=email,
            usuario_nombre=usuario.nombre_completo or f"{usuario.nombre} {usuario.apellidos}",
            tipo=tipo,
            tipo_nombre=NOMBRES_DENUNCIAS.get(tipo, tipo),
            ubicacion=ubicacion,
            descripcion=descripcion,
            evidencia=evidencia,
            estado='pendiente',
            fecha_creacion=datetime.now(),
            lat=lat,
            lng=lng,
            geolocalizada=bool(lat and lng)
        )
        
        db.session.add(nueva_denuncia)
        db.session.commit()
        
        if lat and lng:
            flash(f"✅ Denuncia #{nueva_denuncia.folio} registrada exitosamente con ubicación en el mapa.", "success")
        else:
            flash(f"✅ Denuncia #{nueva_denuncia.folio} registrada exitosamente.", "success")
        
        return redirect(url_for('mis_denuncias'))
    except Exception as e:
        db.session.rollback()
        print(f"Error al procesar denuncia: {e}")
        import traceback
        traceback.print_exc()
        flash("❌ Error al procesar la denuncia.", "error")
        return redirect(url_for('denunciar', tipo=tipo or 'otro'))

@app.route('/procesar-consulta', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def procesar_consulta():
    flash("⚠️ Funcionalidad de consultas en desarrollo. Próximamente disponible.", "warning")
    return redirect(url_for('servicios'))

@app.route("/solicitar-cita", methods=["GET", "POST"])
@login_required
def solicitar_cita():
    from models.cita import Cita
    from models.usuario import Usuario
    
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        try:
            servicio = request.form.get("servicio")
            fecha = request.form.get("fecha")
            hora = request.form.get("hora")
            motivo = request.form.get("motivo", "")
            
            if not all([servicio, fecha, hora]):
                flash("❌ Todos los campos obligatorios deben completarse.", "error")
                return render_template("citas/solicitar_cita.html", 
                                     usuario=usuario,
                                     servicios=SERVICIOS_CITAS,
                                     now=datetime.now())
            
            cita_existente = Cita.query.filter_by(
                servicio=servicio,
                fecha=fecha,
                hora=hora,
                estado="pendiente"
            ).first()
            
            if cita_existente:
                flash("❌ El horario seleccionado ya no está disponible.", "error")
                return render_template("citas/solicitar_cita.html",
                                     usuario=usuario,
                                     servicios=SERVICIOS_CITAS,
                                     now=datetime.now())
            
            nueva_cita = Cita(
                folio=Cita.generar_folio(),
                usuario_email=email,
                usuario_nombre=usuario.nombre_completo or f"{usuario.nombre} {usuario.apellidos}",
                servicio=servicio,
                servicio_nombre=SERVICIOS_CITAS.get(servicio, servicio),
                fecha=fecha,
                hora=hora,
                motivo=motivo,
                estado="pendiente"
            )
            
            db.session.add(nueva_cita)
            db.session.commit()
            
            flash(f"✅ Cita solicitada exitosamente. Tu folio es: {nueva_cita.folio}", "success")
            return redirect(url_for("mis_citas"))
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear cita: {e}")
            flash("❌ Error al procesar la solicitud.", "error")
    
    return render_template("citas/solicitar_cita.html", 
                         usuario=usuario,
                         servicios=SERVICIOS_CITAS,
                         now=datetime.now())

@app.route("/cancelar-cita/<int:cita_id>", methods=["POST"])
@login_required
def cancelar_cita(cita_id):
    from models.cita import Cita
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    cita = Cita.query.get(cita_id)
    
    if not cita:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("mis_citas"))
    
    if cita.usuario_email != email:
        flash("No tienes permiso para cancelar esta cita.", "error")
        return redirect(url_for("mis_citas"))
    
    if cita.estado not in ['pendiente', 'confirmada']:
        flash("Esta cita no se puede cancelar.", "error")
        return redirect(url_for("mis_citas"))
    
    cita.estado = "cancelada"
    db.session.commit()
    flash(f"✅ Cita {cita.folio} cancelada correctamente.", "success")
    return redirect(url_for("mis_citas"))

# ================================================================
# 28. APIs
# ================================================================
@app.route("/api/horarios-disponibles")
@login_required
def horarios_disponibles():
    from models.cita import Cita
    
    servicio = request.args.get("servicio")
    fecha = request.args.get("fecha")
    
    if not servicio or not fecha:
        return jsonify({"error": "Faltan parámetros"}), 400
    
    todos_horarios = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
    
    try:
        citas_ocupadas = Cita.query.filter_by(
            servicio=servicio,
            fecha=fecha,
            estado="pendiente"
        ).all()
        
        horarios_ocupados = [c.hora for c in citas_ocupadas]
        horarios_disponibles = [h for h in todos_horarios if h not in horarios_ocupados]
    except Exception as e:
        print(f"Error al obtener horarios: {e}")
        horarios_disponibles = todos_horarios
    
    return jsonify({
        "disponibles": horarios_disponibles,
        "servicio": servicio,
        "fecha": fecha
    })

@app.route("/api/configuracion")
def api_configuracion():
    from models.configuracion import Configuracion
    
    try:
        config = Configuracion.get_all()
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Error en API config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/configuracion/recargar", methods=["POST"])
@admin_required
def api_recargar_configuracion():
    from models.configuracion import Configuracion
    try:
        Configuracion.clear_cache()
        return jsonify({'success': True, 'message': 'Configuración recargada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/configuracion/actualizar", methods=["POST"])
@admin_required
def api_actualizar_configuracion():
    from models.configuracion import Configuracion
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se enviaron datos'}), 400
        
        actualizadas = []
        
        for clave, valor in data.items():
            if isinstance(valor, bool):
                tipo = 'bool'
            elif isinstance(valor, int):
                tipo = 'int'
            elif isinstance(valor, dict) or isinstance(valor, list):
                tipo = 'json'
            else:
                tipo = 'string'
                valor = str(valor)
            
            Configuracion.set(clave, valor, tipo)
            actualizadas.append(clave)
        
        Configuracion.clear_cache()
        try:
            cache.clear()
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': f'{len(actualizadas)} configuraciones actualizadas',
            'actualizadas': actualizadas
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/notificaciones")
@login_required
def api_notificaciones():
    try:
        from models.notificacion import Notificacion
        email = session.get("user")
        
        if not email:
            return jsonify({'error': 'Usuario no autenticado'}), 401
        
        no_leidas = Notificacion.obtener_no_leidas(email)
        todas = Notificacion.obtener_todas(email)
        
        return jsonify({
            'no_leidas': [n.to_dict() for n in no_leidas],
            'todas': [n.to_dict() for n in todas],
            'total_no_leidas': len(no_leidas)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/notificaciones/marcar-leida/<int:notificacion_id>", methods=["POST"])
@login_required
def api_marcar_notificacion_leida(notificacion_id):
    try:
        from models.notificacion import Notificacion
        email = session.get("user")
        
        if not email:
            return jsonify({'error': 'Usuario no autenticado'}), 401
        
        notif = Notificacion.query.get(notificacion_id)
        
        if not notif or notif.usuario_email != email:
            return jsonify({'error': 'Notificación no encontrada'}), 404
        
        notif.marcar_leido()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/notificaciones/marcar-todas", methods=["POST"])
@login_required
def api_marcar_todas_notificaciones():
    try:
        from models.notificacion import Notificacion
        email = session.get("user")
        
        if not email:
            return jsonify({'error': 'Usuario no autenticado'}), 401
        
        count = Notificacion.marcar_todas_como_leidas(email)
        return jsonify({'success': True, 'marcadas': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/notificaciones/crear", methods=["POST"])
@admin_required
def api_crear_notificacion():
    try:
        from models.notificacion import Notificacion
        
        data = request.get_json()
        usuario_email = data.get('usuario_email')
        tipo = data.get('tipo', 'info')
        titulo = data.get('titulo')
        mensaje = data.get('mensaje')
        datos_extra = data.get('datos_extra')
        
        if not all([usuario_email, titulo, mensaje]):
            return jsonify({'success': False, 'error': 'Faltan campos requeridos'}), 400
        
        notificacion = Notificacion.crear_notificacion(
            usuario_email=usuario_email,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_extra=datos_extra
        )
        
        return jsonify({'success': True, 'notificacion': notificacion.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/usuario/tramite/<folio>/mensajes", methods=["GET"])
@login_required
def api_usuario_obtener_mensajes(folio):
    try:
        from models.mensaje import Mensaje
        tramite_tipo = request.args.get('tipo', 'solicitud')
        email = session.get('user')
        
        pertenece = False
        if tramite_tipo == 'solicitud':
            from models import Solicitud
            solicitudes = Solicitud.buscar_por_usuario(email)
            for s in solicitudes:
                if s.folio == folio:
                    pertenece = True
                    break
        elif tramite_tipo == 'denuncia':
            from models import Denuncia
            denuncias = Denuncia.cargar_todos()
            for d in denuncias:
                if d.folio == folio and d.usuario_email == email:
                    pertenece = True
                    break
        elif tramite_tipo == 'cita':
            from models.cita import Cita
            citas = Cita.buscar_por_usuario(email)
            for c in citas:
                if c.folio == folio:
                    pertenece = True
                    break
        elif tramite_tipo == 'contacto':
            contactos = Mensaje.query.filter_by(
                usuario_email=email,
                tramite_folio=folio,
                tramite_tipo='consulta'
            ).first()
            if contactos:
                pertenece = True
        
        if not pertenece:
            return jsonify({'success': False, 'error': 'No tienes permiso'}), 403
        
        mensajes = Mensaje.obtener_mensajes_tramite(folio, tramite_tipo)
        
        for m in mensajes:
            if m.es_admin and not m.leido:
                m.marcar_leido()
        
        return jsonify({
            'success': True,
            'mensajes': [m.to_dict() for m in mensajes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/usuario/tramite/<folio>/responder", methods=["POST"])
@login_required
def api_usuario_responder_mensaje(folio):
    try:
        from models.mensaje import Mensaje
        data = request.get_json()
        mensaje_texto = data.get('mensaje', '').strip()
        tramite_tipo = data.get('tipo', 'solicitud')
        
        if not mensaje_texto:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'}), 400
        
        if len(mensaje_texto) > 1000:
            return jsonify({'success': False, 'error': 'El mensaje es demasiado largo'}), 400
        
        email = session.get('user')
        nombre = session.get('user_name', email)
        
        usuario_email = None
        if tramite_tipo == 'solicitud':
            from models import Solicitud
            solicitudes = Solicitud.buscar_por_usuario(email)
            for s in solicitudes:
                if s.folio == folio:
                    usuario_email = s.usuario_email
                    break
        elif tramite_tipo == 'denuncia':
            from models import Denuncia
            denuncias = Denuncia.cargar_todos()
            for d in denuncias:
                if d.folio == folio and d.usuario_email == email:
                    usuario_email = d.usuario_email
                    break
        elif tramite_tipo == 'cita':
            from models.cita import Cita
            citas = Cita.buscar_por_usuario(email)
            for c in citas:
                if c.folio == folio:
                    usuario_email = c.usuario_email
                    break
        elif tramite_tipo == 'contacto':
            contacto = Mensaje.query.filter_by(
                tramite_folio=folio,
                tramite_tipo='consulta'
            ).first()
            if contacto:
                usuario_email = contacto.usuario_email
        
        if not usuario_email:
            return jsonify({'success': False, 'error': 'Trámite no encontrado'}), 404
        
        Mensaje.crear_mensaje(
            tramite_folio=folio,
            tramite_tipo=tramite_tipo,
            usuario_email=usuario_email,
            autor_email=email,
            autor_nombre=nombre,
            mensaje=mensaje_texto,
            es_admin=False
        )
        
        return jsonify({'success': True, 'mensaje': 'Mensaje enviado correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# 29. ENCUESTAS
# ================================================================
@app.route("/tramite/<folio>/encuesta", methods=["GET", "POST"])
@login_required
def encuesta_tramite(folio):
    from models import Solicitud, Denuncia
    from models.cita import Cita
    from models.encuesta import Encuesta
    
    email = session.get("user")
    
    if not email:
        flash("No hay sesión activa.", "error")
        return redirect(url_for("auth.login"))
    
    tramite = None
    tipo_tramite = None
    
    solicitudes = Solicitud.buscar_por_usuario(email)
    for s in solicitudes:
        if s.folio == folio:
            tramite = s
            tipo_tramite = 'solicitud'
            break
    
    if not tramite:
        denuncias = Denuncia.cargar_todos()
        for d in denuncias:
            if d.usuario_email == email and d.folio == folio:
                tramite = d
                tipo_tramite = 'denuncia'
                break
    
    if not tramite:
        citas = Cita.buscar_por_usuario(email)
        for c in citas:
            if c.folio == folio:
                tramite = c
                tipo_tramite = 'cita'
                break
    
    if not tramite:
        flash("Trámite no encontrado.", "error")
        return redirect(url_for("mis_tramites"))
    
    estados_completados = ['completado', 'resuelto', 'completada', 'respondido']
    if tramite.estado not in estados_completados:
        flash("❌ Solo puedes evaluar trámites completados.", "error")
        return redirect(url_for("mis_tramites"))
    
    if Encuesta.buscar_por_tramite(folio):
        flash("✅ Ya has evaluado este trámite. ¡Gracias!", "info")
        return redirect(url_for("mis_tramites"))
    
    if request.method == "POST":
        calificacion = request.form.get("calificacion")
        comentario = request.form.get("comentario", "").strip()
        
        if not calificacion:
            flash("❌ Por favor selecciona una calificación.", "error")
            return redirect(url_for("encuesta_tramite", folio=folio))
        
        try:
            calif_int = int(calificacion)
            if calif_int < 1 or calif_int > 5:
                raise ValueError
        except:
            flash("❌ Calificación no válida.", "error")
            return redirect(url_for("encuesta_tramite", folio=folio))
        
        Encuesta.crear(
            folio_tramite=folio,
            tipo_tramite=tipo_tramite,
            usuario_email=email,
            usuario_nombre=session.get("user_name", "Ciudadano"),
            calificacion=calif_int,
            comentario=comentario
        )
        
        flash("✅ ¡Gracias por tu evaluación! Tu opinión nos ayuda a mejorar.", "success")
        return redirect(url_for("mis_tramites"))
    
    nombre_servicio = ""
    if hasattr(tramite, 'servicio_nombre'):
        nombre_servicio = tramite.servicio_nombre
    elif hasattr(tramite, 'tipo_nombre'):
        nombre_servicio = tramite.tipo_nombre
    elif hasattr(tramite, 'servicio'):
        nombre_servicio = SERVICIOS_CITAS.get(tramite.servicio, tramite.servicio)
    
    return render_template("encuestas/encuesta.html", 
                          tramite=tramite, 
                          tipo=tipo_tramite,
                          nombre_servicio=nombre_servicio,
                          folio=folio)

# ================================================================
# 30. ADMIN - ESTADÍSTICAS DE ENCUESTAS
# ================================================================
@app.route("/admin/encuestas")
@admin_required
def admin_encuestas():
    from models.encuesta import Encuesta
    stats = Encuesta.obtener_estadisticas()
    return render_template("admin/encuestas.html", stats=stats)

# ================================================================
# 31. ADMIN - GESTIÓN DE CONTACTOS
# ================================================================
@app.route("/admin/contactos")
@admin_required
def admin_contactos():
    from models.mensaje import Mensaje
    contactos = Mensaje.obtener_todos_contactos()
    return render_template("admin/contactos.html", contactos=contactos)

@app.route("/admin/responder-contacto", methods=["POST"])
@admin_required
def admin_responder_contacto():
    from models.mensaje import Mensaje
    
    contacto_id = request.form.get("contacto_id")
    respuesta = request.form.get("respuesta", "").strip()
    
    if not respuesta:
        flash("❌ La respuesta no puede estar vacía.", "error")
        return redirect(url_for("admin_contactos"))
    
    try:
        admin_email = session.get("user")
        admin_nombre = session.get("user_name", "Administrador")
        
        Mensaje.responder_contacto(contacto_id, admin_email, admin_nombre, respuesta)
        
        flash("✅ Respuesta enviada correctamente. El usuario recibirá una notificación.", "success")
    except Exception as e:
        flash(f"❌ Error al enviar respuesta: {str(e)}", "error")
    
    return redirect(url_for("admin_contactos"))

@app.route("/admin/contacto/<int:contacto_id>/detalle")
@admin_required
def admin_contacto_detalle(contacto_id):
    from models.mensaje import Mensaje
    
    conversacion = Mensaje.obtener_conversacion_contacto(contacto_id)
    
    if not conversacion:
        flash("Contacto no encontrado", "error")
        return redirect(url_for("admin_contactos"))
    
    return render_template("admin/contacto_detalle.html", conversacion=conversacion)

@app.route("/admin/contactos/pendientes")
@admin_required
def admin_contactos_pendientes():
    from models.mensaje import Mensaje
    contactos = Mensaje.obtener_contactos_pendientes()
    return render_template("admin/contactos_pendientes.html", contactos=contactos)

@app.route("/admin/api/contactos-pendientes")
@admin_required
def api_contactos_pendientes():
    from models.mensaje import Mensaje
    
    try:
        contactos_pendientes = Mensaje.obtener_contactos_pendientes()
        count = len(contactos_pendientes)
        return jsonify({'count': count})
    except Exception as e:
        print(f"Error al obtener contactos pendientes: {e}")
        return jsonify({'count': 0})

# ================================================================
# 32. ADMIN - OTRAS RUTAS
# ================================================================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard_redirect():
    return redirect(url_for("admin.dashboard"))

@app.route("/admin/mapa")
@admin_required
def admin_mapa_incidencias():
    from models import Denuncia
    denuncias = Denuncia.cargar_todos()
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    return render_template("admin/mapa_admin.html", denuncias=denuncias_geo, tipos=NOMBRES_DENUNCIAS)

@app.route("/admin/api/notificaciones")
@admin_required
def api_notificaciones_admin():
    try:
        from models import Solicitud, Denuncia
        sp = len([s for s in Solicitud.cargar_todos() if s.estado == 'pendiente'])
        dp = len([d for d in Denuncia.cargar_todos() if d.estado == 'pendiente'])
        return jsonify({'count': sp + dp, 'notifications': []})
    except:
        return jsonify({'count': 0, 'notifications': []})

# ================================================================
# 33. ERROR HANDLERS
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
        return jsonify({"error": "Rate limit exceeded"}), 429
    return redirect(request.referrer or url_for('index'))

# ================================================================
# 34. ARRANQUE
# ================================================================
if __name__ == "__main__":
    # Crear directorios necesarios
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DOCS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
    
    print("=" * 60)
    print("🚀 VILLA CUTUPÚ - SISTEMA MUNICIPAL")
    print("=" * 60)
    
    if is_production():
        print("🏭 MODO PRODUCCIÓN ACTIVADO")
        print(f"   Debug: {app.debug}")
        print(f"   Cloudinary: {'✅' if app.config.get('CLOUDINARY_ENABLED') else '❌'}")
        print(f"   Base de datos: {app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurada')[:80]}...")
        print(f"   SSL Mode: {'✅' if 'sslmode=require' in str(app.config.get('SQLALCHEMY_DATABASE_URI', '')) else '❌'}")
    else:
        print("💻 MODO DESARROLLO ACTIVADO")
        print("   Debug: True")
    
    print("=" * 60)
    print("✅ Cloudinary:", "Configurado" if app.config.get('CLOUDINARY_ENABLED') else "No configurado")
    print("✅ Base de datos: SQLAlchemy inicializada")
    print("✅ Usuarios por defecto creados/verificados")
    print("✅ Configuración global disponible en templates")
    print("✅ API de Configuración disponible")
    print("✅ API de Notificaciones disponible")
    print("✅ API de Mensajería disponible")
    print("✅ Gestión de Contactos en Admin")
    print("=" * 60)
    print("📌 RUTAS PRINCIPALES:")
    print("   /                 → Inicio")
    print("   /transparencia    → Transparencia")
    print("   /contacto         → Formulario de contacto")
    print("   /mis-servicios    → Mis servicios solicitados")
    print("   /mis-tramites     → Mis trámites (incluye contactos)")
    print("   /mis-solicitudes  → Solo solicitudes")
    print("   /mis-denuncias    → Solo denuncias")
    print("   /mis-citas        → Solo citas")
    print("   /solicitar-cita   → Solicitar cita")
    print("   /mi-cuenta        → Mi perfil")
    print("   /mapa             → Mapa de incidencias")
    print("   /noticias         → Noticias y novedades")
    print("=" * 60)
    print("📌 RUTAS ADMINISTRADOR:")
    print("   /admin/contactos           → Gestión de contactos")
    print("   /admin/contactos/pendientes→ Contactos pendientes")
    print("   /admin/encuestas           → Estadísticas de encuestas")
    print("   /admin/mapa                → Mapa de incidencias (admin)")
    print("   /admin/noticias            → Gestión de noticias")
    print("   /admin/logs                → Dashboard de logs")
    print("=" * 60)
    print("🌐 Servidor en: http://localhost:5000")
    print("=" * 60)
    
    # Obtener puerto desde variable de entorno (para producción)
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        debug=app.debug,
        host="0.0.0.0",
        port=port,
        use_reloader=app.debug
    )