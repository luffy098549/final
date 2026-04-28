"""
config_manager.py
Gestión de configuración persistente del sistema sin base de datos.
Lee y escribe en config.json en la raíz del proyecto.
Soporte para variables de entorno en producción (Render, Railway, etc.)
"""

import json
import os
import smtplib
import zipfile
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_PATH = Path(__file__).parent / 'config.json'

# ── Configuración por defecto ──────────────────────────────────
DEFAULT_CONFIG = {
    "general": {
        "nombre_municipio": "Villa Cutupú",
        "siglas": "JDVC",
        "direccion": "Villa Cutupú, La Vega, Rep. Dom.",
        "telefono": "",
        "email": "",
        "web": "http://localhost:5000",
        "timezone": "America/Santo_Domingo",
        "date_format": "DD/MM/YYYY",
        "idioma": "es"
    },
    "seguridad": {
        "pass_min": 8,
        "max_intentos": 5,
        "pass_expiry": 90,
        "lockout_time": 15,
        "require_upper": True,
        "require_num": True,
        "require_special": False,
        "session_hours": 8,
        "inactivity": 30,
        "single_session": False,
        "log_access": True
    },
    "notificaciones": {
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_pass": "",
        "smtp_name": "Junta Distrital Villa Cutupú",
        "notif_solicitud": True,
        "notif_denuncia": True,
        "notif_usuario": True,
        "notif_estado": False
    },
    "servicios": {
        "tiempos": {
            "funeraria": 3,
            "uso-suelo": 5,
            "oaim": 7,
            "planeamiento": 10,
            "ornato": 5,
            "catastro": 7,
            "aseo-comercial": 3
        },
        "activos": {
            "funeraria": True,
            "uso-suelo": True,
            "oaim": True,
            "planeamiento": True,
            "ornato": True,
            "catastro": True,
            "aseo-comercial": True
        },
        "max_solicitudes": 10,
        "max_denuncias": 5,
        "max_file_size": 5,
        "file_types": "pdf,jpg,jpeg,png,doc,docx"
    },
    "apariencia": {
        "tema": "default",
        "color_primary": "#7E8F76",
        "color_accent": "#2B6A9E",
        "color_sidebar": "#1a2e1a",
        "sidebar_collapsed": False,
        "breadcrumbs": True,
        "animations": True
    },
    "sistema": {
        "debug": True,
        "maintenance": False,
        "audit_log": True,
        "file_log": False,
        "cache_sessions": 3600,
        "cache_static": 30,
        "secret_key": ""
    },
    "cloudinary": {
        "enabled": True,
        "cloud_name": "",
        "api_key": "",
        "api_secret": "",
        "upload_folder": "fotos_perfil",
        "transformation": {
            "width": 300,
            "height": 300,
            "crop": "fill",
            "gravity": "face",
            "quality": "auto",
            "fetch_format": "auto"
        }
    },
    "database": {
        "url": "postgresql://postgres:1234@localhost:5432/ayuntamiento"
    },
    "archivos": {
        "logo": "",
        "favicon": "",
        "banner": ""
    }
}


def cargar_config() -> dict:
    """Carga config.json. Si no existe, crea uno con valores por defecto."""
    if not CONFIG_PATH.exists():
        guardar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return _merge_defaults(data, DEFAULT_CONFIG)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def guardar_config(config: dict) -> bool:
    """Guarda el diccionario de config en config.json."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except IOError:
        return False


def guardar_seccion(seccion: str, datos: dict) -> bool:
    """Actualiza solo una sección de la configuración."""
    config = cargar_config()
    if seccion not in config:
        config[seccion] = {}
    config[seccion].update(datos)
    return guardar_config(config)


def obtener_seccion(seccion: str) -> dict:
    """Devuelve solo una sección de la configuración."""
    config = cargar_config()
    return config.get(seccion, {})


def get(seccion: str, clave: str, default=None):
    """Acceso rápido a un valor específico."""
    return obtener_seccion(seccion).get(clave, default)


def _merge_defaults(data: dict, defaults: dict) -> dict:
    """Mezcla recursiva: agrega claves faltantes del defaults."""
    result = defaults.copy()
    for key, value in data.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_defaults(value, result[key])
        else:
            result[key] = value
    return result


# ================================================================
# DETECCIÓN DE ENTORNO
# ================================================================

def is_production() -> bool:
    """Detecta si estamos en entorno de producción."""
    return bool(
        os.environ.get('RENDER') or
        os.environ.get('RAILWAY_ENVIRONMENT') or
        os.environ.get('PRODUCTION')
    )


# ================================================================
# FUNCIÓN CENTRAL: OBTENER DATABASE URL
# ================================================================

def get_database_url() -> str:
    """
    Obtiene la URL de la base de datos con esta prioridad:
    1. Variable de entorno DATABASE_URL  ← SIEMPRE primero
    2. config.json
    3. Default localhost (solo desarrollo)
    """
    # ── 1. Variable de entorno (Render, Railway, Heroku) ──────────
    database_url = os.environ.get('DATABASE_URL', '').strip()

    if database_url:
        # Render/Heroku usan 'postgres://' pero SQLAlchemy necesita 'postgresql://'
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        # Agregar sslmode=require si no está presente (requerido por Render)
        if 'postgresql' in database_url and 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url += f'{separator}sslmode=require'
        print(f"✅ DATABASE_URL cargada desde variable de entorno")
        return database_url

    # ── 2. config.json ─────────────────────────────────────────────
    json_url = get('database', 'url', '').strip()
    if json_url and 'localhost' not in json_url:
        print(f"✅ DATABASE_URL cargada desde config.json")
        return json_url

    # ── 3. Default desarrollo local ────────────────────────────────
    print("⚠️  Usando DATABASE_URL por defecto (localhost - solo desarrollo)")
    return "postgresql://postgres:1234@localhost:5432/ayuntamiento"


# ================================================================
# CLOUDINARY
# ================================================================

def get_cloudinary_config() -> dict:
    return obtener_seccion('cloudinary')


def is_cloudinary_enabled() -> bool:
    return get('cloudinary', 'enabled', True)


def get_cloudinary_credentials() -> dict:
    cloud_config = get_cloudinary_config()
    return {
        'cloud_name': cloud_config.get('cloud_name'),
        'api_key': cloud_config.get('api_key'),
        'api_secret': cloud_config.get('api_secret'),
        'upload_folder': cloud_config.get('upload_folder', 'fotos_perfil')
    }


# ================================================================
# SUBIDA DE ARCHIVOS DE CONFIGURACIÓN (logo, favicon, banner)
# ================================================================

UPLOAD_FOLDER = Path(__file__).parent / 'static' / 'uploads' / 'config'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'ico', 'webp'}


def guardar_imagen_config(archivo, tipo: str) -> tuple[bool, str]:
    """
    Guarda logo, favicon o banner en static/uploads/config/.
    tipo: 'logo' | 'favicon' | 'banner'
    """
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    extension = Path(archivo.filename).suffix.lower().lstrip('.')
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Extensión .{extension} no permitida"

    nombre_archivo = f"{tipo}.{extension}"
    ruta_destino = UPLOAD_FOLDER / nombre_archivo

    try:
        archivo.save(str(ruta_destino))
        ruta_relativa = f"uploads/config/{nombre_archivo}"
        config = cargar_config()
        config.setdefault('archivos', {})[tipo] = ruta_relativa
        guardar_config(config)
        return True, ruta_relativa
    except Exception as e:
        return False, str(e)


# ================================================================
# TEST SMTP
# ================================================================

def test_smtp(host: str, port: int, user: str, password: str,
              nombre: str, email_destino: str) -> tuple[bool, str]:
    if not all([host, user, password, email_destino]):
        return False, "Faltan datos requeridos: host, usuario, contraseña y email destino"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{nombre} <{user}>"
        msg['To'] = email_destino
        msg['Subject'] = "✅ Prueba de configuración SMTP - Villa Cutupú"

        cuerpo = f"""
        <html><body>
        <h2 style="color:#2d4a2d">Prueba de configuración SMTP</h2>
        <p>Este mensaje confirma que el servidor SMTP está configurado correctamente.</p>
        <hr>
        <small>Junta Distrital Villa Cutupú · {datetime.now().strftime('%d/%m/%Y %H:%M')}</small>
        </body></html>
        """
        msg.attach(MIMEText(cuerpo, 'html'))

        with smtplib.SMTP(host, int(port), timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, email_destino, msg.as_string())

        return True, f"Email enviado exitosamente a {email_destino}"
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación: usuario o contraseña incorrectos"
    except smtplib.SMTPConnectError:
        return False, f"No se pudo conectar a {host}:{port}"
    except TimeoutError:
        return False, f"Tiempo de espera agotado al conectar a {host}"
    except Exception as e:
        return False, f"Error: {str(e)}"


# ================================================================
# EXPORTAR DATOS COMO ZIP
# ================================================================

DATA_FOLDER = Path(__file__).parent / 'data'


def exportar_datos_zip() -> tuple[bool, str]:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_nombre = f"backup_villacutupu_{timestamp}.zip"
    zip_ruta = Path(__file__).parent / 'static' / 'exports' / zip_nombre
    zip_ruta.parent.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_ruta, 'w', zipfile.ZIP_DEFLATED) as zf:
            if CONFIG_PATH.exists():
                zf.write(CONFIG_PATH, 'config.json')
            if DATA_FOLDER.exists():
                for archivo in DATA_FOLDER.rglob('*.json'):
                    zf.write(archivo, f"data/{archivo.name}")
            if UPLOAD_FOLDER.exists():
                for archivo in UPLOAD_FOLDER.iterdir():
                    zf.write(archivo, f"uploads/config/{archivo.name}")
        return True, str(zip_ruta)
    except Exception as e:
        return False, str(e)


def limpiar_exports_viejos(max_archivos: int = 5):
    exports_dir = Path(__file__).parent / 'static' / 'exports'
    if not exports_dir.exists():
        return
    zips = sorted(exports_dir.glob('backup_*.zip'), key=os.path.getmtime)
    while len(zips) > max_archivos:
        zips.pop(0).unlink()


# ================================================================
# FLASK CONFIG — AHORA COMO DICCIONARIO DIRECTO
# ================================================================
# Se usa get_flask_config() en app.py en lugar de from_object()
# para garantizar que las env vars se lean en el momento correcto.

def get_flask_config() -> dict:
    """
    Devuelve un diccionario listo para app.config.update().
    Las variables de entorno siempre tienen prioridad sobre config.json.
    """
    # ── Base de datos ──────────────────────────────────────────────
    database_uri = get_database_url()

    # ── Secret key ────────────────────────────────────────────────
    secret_key = (
        os.environ.get('SECRET_KEY') or
        get('sistema', 'secret_key', '') or
        'clave_secreta_muy_segura_cambiar_en_produccion_123'
    )

    # ── Debug ─────────────────────────────────────────────────────
    debug = False if is_production() else get('sistema', 'debug', True)

    # ── Cloudinary ────────────────────────────────────────────────
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or get('cloudinary', 'cloud_name', '')
    api_key    = os.environ.get('CLOUDINARY_API_KEY')    or get('cloudinary', 'api_key', '')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET') or get('cloudinary', 'api_secret', '')
    cloudinary_enabled = bool(cloud_name and api_key) and get('cloudinary', 'enabled', True)

    # ── Max upload ────────────────────────────────────────────────
    max_file_mb = get('servicios', 'max_file_size', 5)

    # ── Sesión ────────────────────────────────────────────────────
    session_hours = get('seguridad', 'session_hours', 8)

    config = {
        # Base de datos
        'SQLALCHEMY_DATABASE_URI':        database_uri,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {'sslmode': 'require'} if is_production() else {},
        },

        # Seguridad
        'SECRET_KEY':               secret_key,
        'DEBUG':                    debug,
        'TEMPLATES_AUTO_RELOAD':    debug,
        'SESSION_COOKIE_SECURE':    not debug,
        'SESSION_COOKIE_HTTPONLY':  True,
        'SESSION_COOKIE_SAMESITE':  'Lax',
        'PERMANENT_SESSION_LIFETIME': session_hours * 3600,

        # Uploads
        'MAX_CONTENT_LENGTH': max_file_mb * 1024 * 1024,
        'UPLOAD_FOLDER': str(Path(__file__).parent / 'static' / 'uploads'),

        # Cloudinary
        'CLOUDINARY_CLOUD_NAME':    cloud_name,
        'CLOUDINARY_API_KEY':       api_key,
        'CLOUDINARY_API_SECRET':    api_secret,
        'CLOUDINARY_UPLOAD_FOLDER': get('cloudinary', 'upload_folder', 'fotos_perfil'),
        'CLOUDINARY_ENABLED':       cloudinary_enabled,
    }

    # ── Diagnóstico ───────────────────────────────────────────────
    print("=" * 60)
    print("📊 DIAGNÓSTICO DE CONFIGURACIÓN:")
    print(f"   Producción:       {is_production()}")
    print(f"   Debug:            {debug}")
    print(f"   DATABASE_URL env: {'✅ Presente' if os.environ.get('DATABASE_URL') else '❌ Ausente'}")
    print(f"   DB URI:           {database_uri[:80]}...")
    print(f"   localhost en URI: {'❌ CRÍTICO' if 'localhost' in database_uri else '✅ OK'}")
    print(f"   SSL Mode:         {'✅' if 'sslmode=require' in database_uri else '⚠️  Sin SSL'}")
    print(f"   Cloudinary:       {'✅' if cloudinary_enabled else '❌'}")
    print("=" * 60)

    return config


# ================================================================
# COMPATIBILIDAD — flask_config para imports existentes en app.py
# ================================================================
# Si en app.py usas: from config_manager import flask_config
# esto sigue funcionando, pero ahora es un dict-like wrapper.

class _FlaskConfigCompat:
    """
    Wrapper de compatibilidad para que el código existente que use
    flask_config.ALGO o app.config.from_object(flask_config) siga
    funcionando. Internamente delega a get_flask_config().
    """
    def __getattr__(self, key: str):
        return get_flask_config().get(key)

    def __getitem__(self, key: str):
        return get_flask_config().get(key)

    def __contains__(self, key: str):
        return key in get_flask_config()

    def items(self):
        return get_flask_config().items()


flask_config = _FlaskConfigCompat()


# ================================================================
# INICIALIZACIÓN EN PRODUCCIÓN
# ================================================================

def init_production_config():
    """Configuración específica para producción."""
    if is_production():
        config = cargar_config()
        if 'sistema' in config:
            config['sistema']['debug'] = False
            guardar_config(config)

        if not os.environ.get('SECRET_KEY'):
            print("⚠️  ADVERTENCIA: SECRET_KEY no configurada en variables de entorno")

        if not os.environ.get('DATABASE_URL'):
            print("❌ CRÍTICO: DATABASE_URL no configurada en variables de entorno")
        else:
            print("✅ DATABASE_URL detectada en variables de entorno")

        print("✅ Configuración de producción activada")