"""
admin_config_routes.py
Rutas Flask para el módulo de Configuración del panel admin.
Agregar estas rutas dentro de tu admin Blueprint (admin.py).
"""

from flask import Blueprint, render_template, request, jsonify, session, send_file, redirect, url_for, flash
from functools import wraps
import os
from pathlib import Path

# Importar nuestro manager
import config_manager as cfg

# ── Si lo agregas directamente en admin.py, borra estas líneas
#    y usa tu admin_bp existente ──────────────────────────────
# admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ================================================================
# RUTA PRINCIPAL — renderiza configuracion.html
# ================================================================

@admin_bp.route('/configuracion')
@admin_required
def configuracion():
    config_actual = cfg.cargar_config()
    return render_template('admin/configuracion.html',
                           config=config_actual)


# ================================================================
# API — Guardar sección
# ================================================================

@admin_bp.route('/api/config/guardar', methods=['POST'])
@admin_required
def api_config_guardar():
    try:
        data    = request.get_json()
        seccion = data.get('seccion')
        datos   = data.get('datos', {})

        if not seccion:
            return jsonify({'ok': False, 'msg': 'Sección requerida'}), 400

        secciones_validas = ['general', 'seguridad', 'notificaciones',
                             'servicios', 'apariencia', 'sistema']
        if seccion not in secciones_validas:
            return jsonify({'ok': False, 'msg': 'Sección no válida'}), 400

        exito = cfg.guardar_seccion(seccion, datos)
        if exito:
            return jsonify({'ok': True, 'msg': f'Configuración de "{seccion}" guardada'})
        else:
            return jsonify({'ok': False, 'msg': 'Error al escribir config.json'}), 500

    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Obtener configuración actual (para precargar el form)
# ================================================================

@admin_bp.route('/api/config/cargar', methods=['GET'])
@admin_required
def api_config_cargar():
    try:
        seccion = request.args.get('seccion')
        if seccion:
            datos = cfg.obtener_seccion(seccion)
        else:
            datos = cfg.cargar_config()
        return jsonify({'ok': True, 'datos': datos})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Test SMTP
# ================================================================

@admin_bp.route('/api/config/test-smtp', methods=['POST'])
@admin_required
def api_test_smtp():
    try:
        data = request.get_json()
        exito, mensaje = cfg.test_smtp(
            host          = data.get('smtp_host', ''),
            port          = data.get('smtp_port', 587),
            user          = data.get('smtp_user', ''),
            password      = data.get('smtp_pass', ''),
            nombre        = data.get('smtp_name', 'Villa Cutupú'),
            email_destino = data.get('email_destino', '')
        )
        return jsonify({'ok': exito, 'msg': mensaje})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Subir imagen (logo / favicon / banner)
# ================================================================

@admin_bp.route('/api/config/subir-imagen', methods=['POST'])
@admin_required
def api_subir_imagen():
    try:
        tipo    = request.form.get('tipo')  # logo | favicon | banner
        archivo = request.files.get('archivo')

        if not tipo or not archivo or archivo.filename == '':
            return jsonify({'ok': False, 'msg': 'Tipo y archivo requeridos'}), 400

        exito, resultado = cfg.guardar_imagen_config(archivo, tipo)
        if exito:
            return jsonify({'ok': True, 'ruta': resultado,
                            'msg': f'{tipo.capitalize()} guardado correctamente'})
        else:
            return jsonify({'ok': False, 'msg': resultado}), 400

    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Exportar datos (ZIP)
# ================================================================

@admin_bp.route('/api/config/exportar', methods=['GET'])
@admin_required
def api_exportar_datos():
    try:
        exito, ruta = cfg.exportar_datos_zip()
        if exito:
            cfg.limpiar_exports_viejos(max_archivos=5)
            return send_file(
                ruta,
                as_attachment=True,
                download_name=Path(ruta).name,
                mimetype='application/zip'
            )
        else:
            return jsonify({'ok': False, 'msg': ruta}), 500
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Limpiar caché de sesiones Flask
# ================================================================

@admin_bp.route('/api/config/limpiar-cache', methods=['POST'])
@admin_required
def api_limpiar_cache():
    try:
        import glob
        # Limpiar archivos de sesión del filesystem si existen
        session_dir = Path('flask_session')
        eliminados  = 0
        if session_dir.exists():
            for f in session_dir.glob('*'):
                try:
                    f.unlink()
                    eliminados += 1
                except:
                    pass
        return jsonify({'ok': True, 'msg': f'Caché limpiado ({eliminados} sesiones eliminadas)'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Verificar estado del sistema
# ================================================================

@admin_bp.route('/api/config/sistema-info', methods=['GET'])
@admin_required
def api_sistema_info():
    import sys
    import flask
    try:
        info = {
            'python':  sys.version.split()[0],
            'flask':   flask.__version__,
            'storage': 'JSON Local',
            'version': 'v2.0.0',
            'debug':   cfg.get('sistema', 'debug', True),
            'maintenance': cfg.get('sistema', 'maintenance', False)
        }
        return jsonify({'ok': True, 'datos': info})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# API — Modo mantenimiento (toggle en tiempo real)
# ================================================================

@admin_bp.route('/api/config/mantenimiento', methods=['POST'])
@admin_required
def api_mantenimiento():
    try:
        data   = request.get_json()
        activo = data.get('activo', False)
        cfg.guardar_seccion('sistema', {'maintenance': activo})
        estado = 'activado' if activo else 'desactivado'
        return jsonify({'ok': True, 'msg': f'Modo mantenimiento {estado}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ================================================================
# MIDDLEWARE — Modo mantenimiento
# Agregar esto en app.py con @app.before_request
# ================================================================

# @app.before_request
# def check_maintenance():
#     """Bloquea el acceso público si el modo mantenimiento está activo."""
#     import config_manager as cfg
#     from flask import request, render_template
#
#     if cfg.get('sistema', 'maintenance', False):
#         # Permitir acceso a admins y a la ruta de login
#         rutas_permitidas = ['auth.login', 'auth.logout', 'static']
#         if request.endpoint in rutas_permitidas:
#             return
#         if session.get('is_admin'):
#             return
#         return render_template('mantenimiento.html'), 503