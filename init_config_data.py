"""
Script para inicializar datos de configuración
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.configuracion import Configuracion

def init_config_data():
    """Inserta la configuración por defecto si no existe"""
    with app.app_context():
        config_defaults = [
            # General
            ('nombre_municipio', 'Villa Cutupú', 'string', 'general'),
            ('siglas', 'JDVC', 'string', 'general'),
            ('direccion', 'Calle Principal #123, Villa Cutupú', 'string', 'general'),
            ('telefono', '(809) 000-0000', 'string', 'general'),
            ('email_institucional', 'info@villacutupu.gob.do', 'string', 'general'),
            ('sitio_web', 'https://villacutupu.gob.do', 'string', 'general'),
            ('zona_horaria', 'America/Santo_Domingo', 'string', 'general'),
            ('formato_fecha', 'DD/MM/YYYY', 'string', 'general'),
            ('idioma', 'es', 'string', 'general'),
            
            # Seguridad
            ('pass_min_length', '8', 'int', 'seguridad'),
            ('max_intentos_fallidos', '5', 'int', 'seguridad'),
            ('pass_expiry_dias', '90', 'int', 'seguridad'),
            ('lockout_minutos', '15', 'int', 'seguridad'),
            ('session_duracion_horas', '8', 'int', 'seguridad'),
            ('inactividad_minutos', '30', 'int', 'seguridad'),
            ('require_mayusculas', 'true', 'bool', 'seguridad'),
            ('require_numeros', 'true', 'bool', 'seguridad'),
            ('require_especiales', 'false', 'bool', 'seguridad'),
            ('single_session', 'false', 'bool', 'seguridad'),
            ('log_intentos_acceso', 'true', 'bool', 'seguridad'),
            ('two_factor_auth', 'false', 'bool', 'seguridad'),
            
            # Sistema
            ('debug_mode', 'true', 'bool', 'sistema'),
            ('maintenance_mode', 'false', 'bool', 'sistema'),
            ('audit_log', 'true', 'bool', 'sistema'),
            ('file_logging', 'true', 'bool', 'sistema'),
            ('cache_sessions_segundos', '3600', 'int', 'sistema'),
            ('cache_static_dias', '7', 'int', 'sistema'),
            
            # Servicios
            ('max_solicitudes_mes', '10', 'int', 'servicios'),
            ('max_denuncias_mes', '5', 'int', 'servicios'),
            ('max_file_size_mb', '5', 'int', 'servicios'),
            ('tipos_archivo_permitidos', 'pdf,jpg,png,doc,docx', 'string', 'servicios'),
            
            # Apariencia
            ('color_primario', '#2d6a4f', 'string', 'apariencia'),
            ('color_acento', '#e9c46a', 'string', 'apariencia'),
            ('color_sidebar', '#1b4332', 'string', 'apariencia'),
            ('sidebar_colapsado', 'false', 'bool', 'apariencia'),
            ('mostrar_breadcrumbs', 'true', 'bool', 'apariencia'),
            ('animaciones', 'true', 'bool', 'apariencia'),
            
            # Notificaciones
            ('notif_nueva_solicitud', 'true', 'bool', 'notificaciones'),
            ('notif_nueva_denuncia', 'true', 'bool', 'notificaciones'),
            ('notif_nuevo_usuario', 'true', 'bool', 'notificaciones'),
            ('notif_cambio_estado', 'true', 'bool', 'notificaciones'),
            ('notif_resumen_diario', 'false', 'bool', 'notificaciones'),
            
            # Tiempos de respuesta por servicio (JSON)
            ('tiempos_respuesta', '{"funeraria":5,"uso-suelo":10,"oaim":7,"planeamiento":15,"ornato":5,"catastro":10,"aseo-comercial":8}', 'json', 'servicios'),
            ('servicios_activos', '{"funeraria":true,"uso-suelo":true,"oaim":true,"planeamiento":true,"ornato":true,"catastro":true,"aseo-comercial":true}', 'json', 'servicios'),
        ]
        
        insertados = 0
        for clave, valor, tipo, seccion in config_defaults:
            exists = Configuracion.query.filter_by(clave=clave).first()
            if not exists:
                config = Configuracion(clave=clave, valor=valor, tipo=tipo, seccion=seccion)
                db.session.add(config)
                insertados += 1
                print(f"✅ Insertado: {clave} = {valor}")
        
        db.session.commit()
        print(f"\n✅ Total de configuraciones insertadas: {insertados}")
        
        # Mostrar resumen
        total = Configuracion.query.count()
        print(f"📊 Total de configuraciones en la tabla: {total}")

if __name__ == '__main__':
    init_config_data()