"""
config_manager.py
Gestión de configuración persistente del sistema sin base de datos.
Lee y escribe en config.json en la raíz del proyecto.
"""

import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

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
        "cache_static": 30
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
        # Mezclar con defaults para no perder claves nuevas
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


# ── Subida de archivos (logo, favicon, banner) ─────────────────

UPLOAD_FOLDER = Path(__file__).parent / 'static' / 'uploads' / 'config'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'ico', 'webp'}


def guardar_imagen_config(archivo, tipo: str) -> tuple[bool, str]:
    """
    Guarda logo, favicon o banner en static/uploads/config/.
    Devuelve (éxito, ruta_relativa_o_error).
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

        # Guardar ruta en config
        config = cargar_config()
        config.setdefault('archivos', {})[tipo] = ruta_relativa
        guardar_config(config)

        return True, ruta_relativa
    except Exception as e:
        return False, str(e)


# ── Test SMTP real ─────────────────────────────────────────────

def test_smtp(host: str, port: int, user: str, password: str,
              nombre: str, email_destino: str) -> tuple[bool, str]:
    """
    Intenta conectarse al servidor SMTP y enviar un email de prueba.
    Devuelve (éxito, mensaje).
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not all([host, user, password, email_destino]):
        return False, "Faltan datos requeridos: host, usuario, contraseña y email destino"

    try:
        msg = MIMEMultipart()
        msg['From']    = f"{nombre} <{user}>"
        msg['To']      = email_destino
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


# ── Exportar datos como ZIP ────────────────────────────────────

DATA_FOLDER = Path(__file__).parent / 'data'


def exportar_datos_zip() -> tuple[bool, str]:
    """
    Crea un ZIP con todos los JSON de datos + config.json.
    Devuelve (éxito, ruta_del_zip).
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_nombre = f"backup_villacutupu_{timestamp}.zip"
    zip_ruta = Path(__file__).parent / 'static' / 'exports' / zip_nombre

    zip_ruta.parent.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_ruta, 'w', zipfile.ZIP_DEFLATED) as zf:
            # config.json
            if CONFIG_PATH.exists():
                zf.write(CONFIG_PATH, 'config.json')

            # Todos los JSON en /data
            if DATA_FOLDER.exists():
                for archivo in DATA_FOLDER.rglob('*.json'):
                    nombre_en_zip = f"data/{archivo.name}"
                    zf.write(archivo, nombre_en_zip)

            # Imágenes de config subidas
            if UPLOAD_FOLDER.exists():
                for archivo in UPLOAD_FOLDER.iterdir():
                    zf.write(archivo, f"uploads/config/{archivo.name}")

        return True, str(zip_ruta)
    except Exception as e:
        return False, str(e)


# ── Limpiar exportaciones viejas ───────────────────────────────

def limpiar_exports_viejos(max_archivos: int = 5):
    """Mantiene solo los últimos N ZIPs de exportación."""
    exports_dir = Path(__file__).parent / 'static' / 'exports'
    if not exports_dir.exists():
        return

    zips = sorted(exports_dir.glob('backup_*.zip'), key=os.path.getmtime)
    while len(zips) > max_archivos:
        zips.pop(0).unlink()