"""
Blueprint de administración profesional.
Maneja todas las funciones exclusivas de administradores.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from functools import wraps
from datetime import datetime
from pathlib import Path
import json
import os
import sys
from collections import defaultdict

# Importar modelos
from models import Solicitud, Denuncia, Usuario, Reportes

# Importar roles desde rol.py (ya no desde models.rol)
from rol import tiene_permiso, Permiso, obtener_roles

# Para acceder a USUARIOS de auth.py
from auth import _cargar_usuarios, _guardar_usuarios

# Decoradores personalizados
from decorators import permiso_requerido, solo_super_admin, admin_o_super, moderador_o_superior

# Módulo de configuración persistente
import config_manager as cfg

# Intentar importar nombres desde app.py
try:
    from app import NOMBRES_SERVICIOS, NOMBRES_DENUNCIAS
except ImportError:
    # Valores por defecto
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

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ================================================================
# DECORADOR ESPECÍFICO PARA ADMIN
# ================================================================

def admin_required(f):
    """Verifica que el usuario sea administrador (cualquier rol admin)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Acceso restringido a administradores.", "error")
            return redirect(url_for("auth.login"))
        
        user_email = session.get("user")
        usuarios = _cargar_usuarios()
        usuario = usuarios.get(user_email, {})
        user_rol = usuario.get("rol")
        
        # Verificar si tiene algún rol administrativo
        if user_rol not in ["super_admin", "admin", "moderador"] and usuario.get("tipo") != "admin":
            flash("Acceso restringido a administradores.", "error")
            return redirect(url_for("index"))
            
        # Guardar rol en sesión para uso en templates
        session["user_rol"] = user_rol
        return f(*args, **kwargs)
    return decorated


# ================================================================
# DASHBOARD PRINCIPAL - CORREGIDO PARA CONTAR PENDIENTES
# ================================================================

@admin_bp.route("/")
@admin_required
@moderador_o_superior
def dashboard():
    """Dashboard principal con estadísticas y resumen."""

    try:
        # Cargar todos los datos
        solicitudes = Solicitud.cargar_todos()
        denuncias = Denuncia.cargar_todos()
        usuarios_data = _cargar_usuarios()
        
        # Contar usuarios
        total_usuarios = len(usuarios_data)
        admins = 0
        for u in usuarios_data.values():
            if u.get('tipo') == 'admin' or u.get('rol') in ['super_admin', 'admin', 'moderador']:
                admins += 1
        ciudadanos = total_usuarios - admins
        
        # Contar solicitudes por estado
        total_solicitudes = len(solicitudes)
        solicitudes_pendientes = len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']])
        solicitudes_completadas = len([s for s in solicitudes if s.estado == 'completado'])
        solicitudes_por_servicio = defaultdict(int)
        for s in solicitudes:
            servicio_id = str(s.servicio_id)
            solicitudes_por_servicio[servicio_id] += 1
        
        # Contar denuncias por estado
        total_denuncias = len(denuncias)
        denuncias_pendientes = len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
        denuncias_resueltas = len([d for d in denuncias if d.estado == 'resuelto'])
        denuncias_por_tipo = defaultdict(int)
        for d in denuncias:
            tipo = d.tipo
            denuncias_por_tipo[tipo] += 1
        
        # Actividad hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        solicitudes_hoy = len([s for s in solicitudes if s.fecha_creacion.startswith(hoy)])
        denuncias_hoy = len([d for d in denuncias if d.fecha_creacion.startswith(hoy)])
        
        # Solicitudes por mes (últimos 6 meses)
        from datetime import timedelta
        solicitudes_por_mes = {}
        for i in range(5, -1, -1):
            fecha = datetime.now() - timedelta(days=30*i)
            mes = fecha.strftime("%Y-%m")
            count = 0
            for s in solicitudes:
                if s.fecha_creacion.startswith(mes):
                    count += 1
            solicitudes_por_mes[mes] = count
        
        # Estadísticas completas
        stats = {
            'usuarios': {
                'total': total_usuarios,
                'admins': admins,
                'ciudadanos': ciudadanos
            },
            'solicitudes': {
                'total': total_solicitudes,
                'pendientes': solicitudes_pendientes,
                'completadas': solicitudes_completadas,
                'por_servicio': dict(solicitudes_por_servicio),
                'por_mes': solicitudes_por_mes
            },
            'denuncias': {
                'total': total_denuncias,
                'pendientes': denuncias_pendientes,
                'resueltas': denuncias_resueltas,
                'por_tipo': dict(denuncias_por_tipo)
            },
            'actividad_hoy': {
                'total': solicitudes_hoy + denuncias_hoy,
                'solicitudes': solicitudes_hoy,
                'denuncias': denuncias_hoy
            }
        }

        # Últimas solicitudes (5 más recientes)
        ultimas_solicitudes = sorted(solicitudes,
                                     key=lambda x: x.fecha_creacion,
                                     reverse=True)[:5]

        # Últimas denuncias (5 más recientes)
        ultimas_denuncias = sorted(denuncias,
                                   key=lambda x: x.fecha_creacion,
                                   reverse=True)[:5]

    except Exception as e:
        print(f"Error en dashboard: {e}")
        stats = {
            'usuarios': {'total': 0, 'admins': 0, 'ciudadanos': 0},
            'solicitudes': {'total': 0, 'pendientes': 0, 'completadas': 0, 'por_servicio': {}, 'por_mes': {}},
            'denuncias': {'total': 0, 'pendientes': 0, 'resueltas': 0, 'por_tipo': {}},
            'actividad_hoy': {'total': 0, 'solicitudes': 0, 'denuncias': 0}
        }
        ultimas_solicitudes = []
        ultimas_denuncias = []

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        ultimas_solicitudes=ultimas_solicitudes,
        ultimas_denuncias=ultimas_denuncias,
        servicios=NOMBRES_SERVICIOS,
        tipos_denuncia=NOMBRES_DENUNCIAS,
        now=datetime.now()
    )


# ================================================================
# GESTIÓN DE SOLICITUDES - CORREGIDO CON STATS Y JSON
# ================================================================

@admin_bp.route("/solicitudes")
@admin_required
@permiso_requerido(Permiso.VER_SOLICITUDES)
def listar_solicitudes():
    estado   = request.args.get('estado', '')
    servicio = request.args.get('servicio', '')
    busqueda = request.args.get('q', '')

    try:
        solicitudes = Solicitud.cargar_todos()
    except:
        solicitudes = []

    # Calcular estadísticas para el template
    total_solicitudes = len(solicitudes)
    pendientes = len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']])
    completadas = len([s for s in solicitudes if s.estado == 'completado'])
    
    stats = {
        'solicitudes': total_solicitudes,
        'denuncias': 0,
        'pendientes': pendientes,
        'completados': completadas,
        'en_proceso': len([s for s in solicitudes if s.estado == 'en_proceso'])
    }

    if estado:
        solicitudes = [s for s in solicitudes if s.estado == estado]
    if servicio:
        solicitudes = [s for s in solicitudes if str(s.servicio_id) == servicio]
    if busqueda:
        b = busqueda.lower()
        solicitudes = [s for s in solicitudes if
                       b in s.folio.lower() or
                       b in s.usuario_nombre.lower() or
                       b in s.usuario_email.lower()]

    solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)

    # Convertir solicitudes a diccionarios serializables para JSON
    solicitudes_lista = []
    for s in solicitudes:
        solicitud_dict = {
            'id': s.id,
            'folio': s.folio,
            'tipo': 'solicitud',
            'servicio_id': s.servicio_id,
            'servicio_nombre': NOMBRES_SERVICIOS.get(str(s.servicio_id), f"Servicio {s.servicio_id}"),
            'descripcion': s.descripcion,
            'estado': s.estado,
            'fecha_creacion': s.fecha_creacion,
            'usuario_nombre': s.usuario_nombre,
            'usuario_email': s.usuario_email,
            'anonimo': getattr(s, 'anonimo', False),
            'comentarios_admin': getattr(s, 'comentarios_admin', [])
        }
        solicitudes_lista.append(solicitud_dict)

    return render_template(
        "admin/solicitudes.html",
        solicitudes=solicitudes,
        solicitudes_json=json.dumps(solicitudes_lista, ensure_ascii=False, default=str),
        estados=Solicitud.ESTADOS,
        servicios=NOMBRES_SERVICIOS,
        filtros={'estado': estado, 'servicio': servicio, 'q': busqueda},
        stats=stats
    )


@admin_bp.route("/solicitudes/<int:solicitud_id>")
@admin_required
@permiso_requerido(Permiso.VER_SOLICITUDES)
def detalle_solicitud(solicitud_id):
    solicitud = Solicitud.buscar_por_id(solicitud_id)
    if not solicitud:
        flash("Solicitud no encontrada.", "error")
        return redirect(url_for("admin.listar_solicitudes"))

    return render_template(
        "admin/solicitud_detalle.html",
        solicitud=solicitud,
        servicios=NOMBRES_SERVICIOS,
        estados=Solicitud.ESTADOS
    )


@admin_bp.route("/solicitudes/<int:solicitud_id>/actualizar", methods=["POST"])
@admin_required
def actualizar_solicitud(solicitud_id):
    solicitud = Solicitud.buscar_por_id(solicitud_id)
    if not solicitud:
        flash("Solicitud no encontrada.", "error")
        return redirect(url_for("admin.listar_solicitudes"))

    accion      = request.form.get('accion', '')
    admin_email = session.get('user')

    try:
        if accion == 'cambiar_estado':
            # Verificar permiso
            if not tiene_permiso(session.get("user_rol"), Permiso.EDITAR_SOLICITUDES):
                flash("No tienes permiso para cambiar estados.", "error")
                return redirect(url_for("admin.detalle_solicitud", solicitud_id=solicitud_id))
                
            nuevo_estado = request.form.get('estado')
            comentario   = request.form.get('comentario', '')
            if nuevo_estado in Solicitud.ESTADOS:
                solicitud.actualizar_estado(nuevo_estado, comentario, admin_email)
                flash(f"Solicitud actualizada a: {nuevo_estado}", "success")
                registrar_accion('cambiar_estado', f"Solicitud {solicitud.folio} cambiada a {nuevo_estado}")
            else:
                flash("Estado no válido.", "error")

        elif accion == 'asignar':
            if not tiene_permiso(session.get("user_rol"), Permiso.ASIGNAR):
                flash("No tienes permiso para asignar solicitudes.", "error")
                return redirect(url_for("admin.detalle_solicitud", solicitud_id=solicitud_id))
                
            solicitud.asignar(admin_email)
            flash("Solicitud asignada correctamente.", "success")
            registrar_accion('asignar', f"Solicitud {solicitud.folio} asignada a {admin_email}")

        elif accion == 'comentar':
            if not tiene_permiso(session.get("user_rol"), Permiso.COMENTAR):
                flash("No tienes permiso para comentar.", "error")
                return redirect(url_for("admin.detalle_solicitud", solicitud_id=solicitud_id))
                
            comentario = request.form.get('comentario')
            if comentario:
                solicitud.agregar_comentario(comentario, admin_email)
                flash("Comentario agregado.", "success")
                registrar_accion('comentar', f"Comentario agregado a solicitud {solicitud.folio}")

    except Exception as e:
        flash(f"Error al actualizar: {str(e)}", "error")

    return redirect(url_for("admin.detalle_solicitud", solicitud_id=solicitud_id))


@admin_bp.route("/solicitudes/<int:solicitud_id>/eliminar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.ELIMINAR_SOLICITUDES)
def eliminar_solicitud(solicitud_id):
    solicitud = Solicitud.buscar_por_id(solicitud_id)
    if solicitud:
        folio = solicitud.folio
        try:
            solicitudes = Solicitud.cargar_todos()
            solicitudes = [s for s in solicitudes if s.id != solicitud_id]
            Solicitud.guardar_todos(solicitudes)
            flash(f"Solicitud {folio} eliminada correctamente.", "success")
            registrar_accion('eliminar', f"Solicitud {folio} eliminada")
        except Exception as e:
            flash(f"Error al eliminar: {str(e)}", "error")
    else:
        flash("Solicitud no encontrada.", "error")

    return redirect(url_for("admin.listar_solicitudes"))


# ================================================================
# GESTIÓN DE DENUNCIAS - CORREGIDO CON STATS Y JSON
# ================================================================

@admin_bp.route("/denuncias")
@admin_required
@permiso_requerido(Permiso.VER_DENUNCIAS)
def listar_denuncias():
    estado   = request.args.get('estado', '')
    tipo     = request.args.get('tipo', '')
    busqueda = request.args.get('q', '')

    try:
        denuncias = Denuncia.cargar_todos()
    except:
        denuncias = []

    # Calcular estadísticas para el template
    total_denuncias = len(denuncias)
    pendientes = len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
    resueltas = len([d for d in denuncias if d.estado == 'resuelto'])
    en_investigacion = len([d for d in denuncias if d.estado == 'en_investigacion'])
    
    stats = {
        'solicitudes': 0,
        'denuncias': total_denuncias,
        'pendientes': pendientes,
        'completados': resueltas,
        'en_investigacion': en_investigacion
    }

    if estado:
        denuncias = [d for d in denuncias if d.estado == estado]
    if tipo:
        denuncias = [d for d in denuncias if d.tipo == tipo]
    if busqueda:
        b = busqueda.lower()
        denuncias = [d for d in denuncias if
                     b in d.folio.lower() or
                     b in d.descripcion.lower() or
                     b in d.direccion.lower()]

    denuncias.sort(key=lambda x: x.fecha_creacion, reverse=True)

    # Convertir denuncias a diccionarios serializables para JSON
    denuncias_lista = []
    for d in denuncias:
        denuncia_dict = {
            'id': d.id,
            'folio': d.folio,
            'tipo': 'denuncia',
            'tipo_id': d.tipo,
            'tipo_nombre': NOMBRES_DENUNCIAS.get(str(d.tipo), f"Tipo {d.tipo}"),
            'descripcion': d.descripcion,
            'direccion': getattr(d, 'direccion', ''),
            'estado': d.estado,
            'fecha_creacion': d.fecha_creacion,
            'usuario_nombre': d.usuario_nombre,
            'usuario_email': d.usuario_email,
            'anonimo': getattr(d, 'anonimo', False),
            'comentarios_admin': getattr(d, 'comentarios_admin', [])
        }
        denuncias_lista.append(denuncia_dict)

    return render_template(
        "admin/denuncias.html",
        denuncias=denuncias,
        denuncias_json=json.dumps(denuncias_lista, ensure_ascii=False, default=str),
        estados=Denuncia.ESTADOS,
        tipos=NOMBRES_DENUNCIAS,
        filtros={'estado': estado, 'tipo': tipo, 'q': busqueda},
        stats=stats
    )


@admin_bp.route("/denuncias/<int:denuncia_id>")
@admin_required
@permiso_requerido(Permiso.VER_DENUNCIAS)
def detalle_denuncia(denuncia_id):
    denuncia = Denuncia.buscar_por_id(denuncia_id)
    if not denuncia:
        flash("Denuncia no encontrada.", "error")
        return redirect(url_for("admin.listar_denuncias"))

    return render_template(
        "admin/denuncia_detalle.html",
        denuncia=denuncia,
        tipos=NOMBRES_DENUNCIAS,
        estados=Denuncia.ESTADOS
    )


@admin_bp.route("/denuncias/<int:denuncia_id>/actualizar", methods=["POST"])
@admin_required
def actualizar_denuncia(denuncia_id):
    denuncia = Denuncia.buscar_por_id(denuncia_id)
    if not denuncia:
        flash("Denuncia no encontrada.", "error")
        return redirect(url_for("admin.listar_denuncias"))

    accion      = request.form.get('accion', '')
    admin_email = session.get('user')

    try:
        if accion == 'cambiar_estado':
            if not tiene_permiso(session.get("user_rol"), Permiso.EDITAR_DENUNCIAS):
                flash("No tienes permiso para cambiar estados.", "error")
                return redirect(url_for("admin.detalle_denuncia", denuncia_id=denuncia_id))
                
            nuevo_estado = request.form.get('estado')
            comentario = request.form.get('comentario', '')
            if nuevo_estado in Denuncia.ESTADOS:
                denuncia.estado = nuevo_estado
                denuncia.fecha_actualizacion = datetime.now().isoformat()
                
                # Agregar al historial
                if 'historial' not in denuncia.__dict__:
                    denuncia.historial = []
                denuncia.historial.append({
                    'fecha': datetime.now().isoformat(),
                    'tipo': 'estado_cambiado',
                    'descripcion': f"Estado cambiado a {nuevo_estado}",
                    'usuario': admin_email
                })
                
                # Agregar comentario si existe
                if comentario:
                    if 'comentarios_admin' not in denuncia.__dict__:
                        denuncia.comentarios_admin = []
                    denuncia.comentarios_admin.append({
                        'fecha': datetime.now().isoformat(),
                        'admin': admin_email,
                        'comentario': comentario
                    })
                
                # Guardar cambios
                denuncias = Denuncia.cargar_todos()
                for i, d in enumerate(denuncias):
                    if d.id == denuncia_id:
                        denuncias[i] = denuncia
                        break
                Denuncia.guardar_todos(denuncias)
                
                flash(f"Denuncia actualizada a: {nuevo_estado}", "success")
                registrar_accion('cambiar_estado', f"Denuncia {denuncia.folio} cambiada a {nuevo_estado}")

        elif accion == 'comentar':
            if not tiene_permiso(session.get("user_rol"), Permiso.COMENTAR):
                flash("No tienes permiso para comentar.", "error")
                return redirect(url_for("admin.detalle_denuncia", denuncia_id=denuncia_id))
                
            comentario = request.form.get('comentario')
            if comentario:
                if 'comentarios_admin' not in denuncia.__dict__:
                    denuncia.comentarios_admin = []
                denuncia.comentarios_admin.append({
                    'fecha': datetime.now().isoformat(),
                    'admin': admin_email,
                    'comentario': comentario
                })
                denuncias = Denuncia.cargar_todos()
                for i, d in enumerate(denuncias):
                    if d.id == denuncia_id:
                        denuncias[i] = denuncia
                        break
                Denuncia.guardar_todos(denuncias)
                flash("Comentario agregado.", "success")
                registrar_accion('comentar', f"Comentario agregado a denuncia {denuncia.folio}")

    except Exception as e:
        flash(f"Error al actualizar: {str(e)}", "error")

    return redirect(url_for("admin.detalle_denuncia", denuncia_id=denuncia_id))


@admin_bp.route("/denuncias/<int:denuncia_id>/eliminar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.ELIMINAR_DENUNCIAS)
def eliminar_denuncia(denuncia_id):
    denuncia = Denuncia.buscar_por_id(denuncia_id)
    if denuncia:
        folio = denuncia.folio
        try:
            denuncias = Denuncia.cargar_todos()
            denuncias = [d for d in denuncias if d.id != denuncia_id]
            Denuncia.guardar_todos(denuncias)
            flash(f"Denuncia {folio} eliminada correctamente.", "success")
            registrar_accion('eliminar', f"Denuncia {folio} eliminada")
        except Exception as e:
            flash(f"Error al eliminar: {str(e)}", "error")
    else:
        flash("Denuncia no encontrada.", "error")

    return redirect(url_for("admin.listar_denuncias"))


# ================================================================
# GESTIÓN DE USUARIOS - CON ROLES
# ================================================================

@admin_bp.route("/usuarios")
@admin_required
@permiso_requerido(Permiso.VER_USUARIOS)
def listar_usuarios():
    busqueda = request.args.get('q', '')
    tipo     = request.args.get('tipo', '')
    rol      = request.args.get('rol', '')

    usuarios = _cargar_usuarios()
    usuarios_lista = []
    
    for email, datos in usuarios.items():
        usuarios_lista.append({
            "email": email,
            "nombre": datos.get("nombre", ""),
            "apellidos": datos.get("apellidos", ""),
            "telefono": datos.get("telefono", ""),
            "tipo": datos.get("tipo", "ciudadano"),
            "rol": datos.get("rol", None),
            "activo": datos.get("activo", True),
            "fecha_registro": datos.get("fecha_registro", ""),
            "ultimo_acceso": datos.get("ultimo_acceso", None),
            "notas_admin": datos.get("notas_admin", "")
        })

    # Aplicar filtros
    if tipo:
        usuarios_lista = [u for u in usuarios_lista if u["tipo"] == tipo]
    
    if rol:
        usuarios_lista = [u for u in usuarios_lista if u["rol"] == rol]
    
    if busqueda:
        b = busqueda.lower()
        usuarios_lista = [
            u for u in usuarios_lista 
            if b in u["email"].lower() or b in u["nombre"].lower()
        ]

    return render_template(
        "admin/usuarios.html",
        usuarios=usuarios_lista,
        roles=obtener_roles(),
        filtros={'q': busqueda, 'tipo': tipo, 'rol': rol}
    )


@admin_bp.route("/usuarios/<path:email>")
@admin_required
@permiso_requerido(Permiso.VER_USUARIOS)
def detalle_usuario(email):
    usuarios = _cargar_usuarios()
    
    if email not in usuarios:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    datos = usuarios[email]
    
    usuario_dict = {
        "email": email,
        "nombre": datos.get("nombre", ""),
        "apellidos": datos.get("apellidos", ""),
        "telefono": datos.get("telefono", ""),
        "tipo": datos.get("tipo", "ciudadano"),
        "rol": datos.get("rol", None),
        "activo": datos.get("activo", True),
        "fecha_registro": datos.get("fecha_registro", ""),
        "ultimo_acceso": datos.get("ultimo_acceso", None),
        "notas_admin": datos.get("notas_admin", "")
    }

    try:
        solicitudes = Solicitud.buscar_por_usuario(email)
    except:
        solicitudes = []

    try:
        denuncias = [d for d in Denuncia.cargar_todos() if d.usuario_email == email]
    except:
        denuncias = []

    return render_template(
        "admin/usuario_detalle.html",
        usuario=usuario_dict,
        roles=obtener_roles(),
        solicitudes=solicitudes,
        denuncias=denuncias
    )


@admin_bp.route("/usuarios/<path:email>/editar", methods=["GET", "POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_USUARIOS)
def editar_usuario(email):
    usuarios = _cargar_usuarios()
    
    if email not in usuarios:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    if request.method == "POST":
        # Actualizar datos básicos
        usuarios[email]['nombre'] = request.form.get('nombre', '')
        usuarios[email]['apellidos'] = request.form.get('apellidos', '')
        usuarios[email]['telefono'] = request.form.get('telefono', '')
        usuarios[email]['tipo'] = request.form.get('tipo', 'ciudadano')
        usuarios[email]['activo'] = request.form.get('activo') == 'on'
        usuarios[email]['notas_admin'] = request.form.get('notas_admin', '')
        
        # Actualizar rol (solo super_admin puede cambiar roles)
        if session.get("user_rol") == "super_admin":
            nuevo_rol = request.form.get('rol')
            if nuevo_rol in ["super_admin", "admin", "moderador", ""]:
                usuarios[email]['rol'] = nuevo_rol if nuevo_rol else None

        _guardar_usuarios(usuarios)
        flash(f"Usuario {email} actualizado correctamente.", "success")
        registrar_accion('editar_usuario', f"Usuario {email} actualizado")
        return redirect(url_for("admin.detalle_usuario", email=email))

    # GET: mostrar formulario
    datos = usuarios[email]
    
    usuario_dict = {
        "email": email,
        "nombre": datos.get("nombre", ""),
        "apellidos": datos.get("apellidos", ""),
        "telefono": datos.get("telefono", ""),
        "tipo": datos.get("tipo", "ciudadano"),
        "rol": datos.get("rol", None),
        "activo": datos.get("activo", True),
        "fecha_registro": datos.get("fecha_registro", ""),
        "notas_admin": datos.get("notas_admin", "")
    }

    return render_template(
        "admin/usuario_editar.html", 
        usuario=usuario_dict,
        roles=obtener_roles()
    )


@admin_bp.route("/usuarios/<path:email>/cambiar-password", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_USUARIOS)
def cambiar_password_usuario(email):
    usuarios = _cargar_usuarios()
    
    if email not in usuarios:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    nueva_password = request.form.get('nueva_password')
    confirmar      = request.form.get('confirmar_password')

    if not nueva_password or len(nueva_password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("admin.detalle_usuario", email=email))

    if nueva_password != confirmar:
        flash("Las contraseñas no coinciden.", "error")
        return redirect(url_for("admin.detalle_usuario", email=email))

    usuarios[email]['password'] = nueva_password
    _guardar_usuarios(usuarios)
    
    flash(f"Contraseña de {email} actualizada correctamente.", "success")
    registrar_accion('cambiar_password', f"Contraseña cambiada para {email}")
    return redirect(url_for("admin.detalle_usuario", email=email))


@admin_bp.route("/usuarios/crear-admin", methods=["GET", "POST"])
@admin_required
@permiso_requerido(Permiso.CREAR_ADMINS)
def crear_admin():
    if request.method == "POST":
        nombre   = request.form.get('nombre', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirmar= request.form.get('confirmar_password', '')
        telefono = request.form.get('telefono', '')
        rol      = request.form.get('rol', 'moderador')  # Por defecto moderador

        errores = []
        if not nombre or not email or not password:
            errores.append("Todos los campos son obligatorios.")
        if password != confirmar:
            errores.append("Las contraseñas no coinciden.")
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        
        usuarios = _cargar_usuarios()
        if email in usuarios:
            errores.append("Este correo ya está registrado.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "admin/crear_admin.html",
                roles=obtener_roles()
            )

        # Crear nuevo administrador/moderador
        usuarios[email] = {
            "password":       password,
            "nombre":         nombre,
            "apellidos":      "",
            "nombre_completo": nombre,
            "email":          email,
            "tipo":           "admin",
            "rol":            rol,
            "telefono":       telefono,
            "fecha_registro": datetime.now().strftime("%d/%m/%Y"),
            "activo":         True,
            "ultimo_acceso":  None,
            "notas_admin":    f"Creado por {session.get('user_name', session.get('user', 'desconocido'))}"
        }

        _guardar_usuarios(usuarios)

        rol_nombre = {
            "super_admin": "Super Administrador",
            "admin": "Administrador",
            "moderador": "Moderador"
        }.get(rol, rol)

        flash(f"{rol_nombre} {email} creado exitosamente.", "success")
        registrar_accion('crear_admin', f"{rol_nombre} {email} creado")
        return redirect(url_for("admin.listar_usuarios"))

    # GET: mostrar formulario
    return render_template(
        "admin/crear_admin.html",
        roles=obtener_roles()
    )


@admin_bp.route("/usuarios/<path:email>/toggle-activo", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_USUARIOS)
def toggle_usuario_activo(email):
    usuarios = _cargar_usuarios()
    
    if email not in usuarios:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    if email == session.get('user'):
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("admin.detalle_usuario", email=email))

    estado_actual = usuarios[email].get('activo', True)
    usuarios[email]['activo'] = not estado_actual
    _guardar_usuarios(usuarios)
    
    nuevo_estado = "activado" if not estado_actual else "desactivado"
    flash(f"Usuario {email} {nuevo_estado}.", "success")
    registrar_accion('toggle_activo', f"Usuario {email} {nuevo_estado}")
    return redirect(url_for("admin.detalle_usuario", email=email))


# ================================================================
# REPORTES Y ESTADÍSTICAS
# ================================================================

@admin_bp.route("/reportes")
@admin_required
@permiso_requerido(Permiso.VER_BITACORA)
def reportes():
    try:
        stats                    = Reportes.obtener_estadisticas_generales()
        solicitudes_por_servicio = Reportes.obtener_solicitudes_por_servicio()
        denuncias_por_tipo       = Reportes.obtener_denuncias_por_tipo()
    except:
        stats = {}
        solicitudes_por_servicio = {}
        denuncias_por_tipo       = {}

    return render_template(
        "admin/reportes.html",
        stats=stats,
        solicitudes_por_servicio=solicitudes_por_servicio,
        denuncias_por_tipo=denuncias_por_tipo,
        servicios=NOMBRES_SERVICIOS,
        tipos_denuncia=NOMBRES_DENUNCIAS
    )


@admin_bp.route("/api/estadisticas")
@admin_required
@permiso_requerido(Permiso.VER_BITACORA)
def api_estadisticas():
    try:
        stats = Reportes.obtener_estadisticas_generales()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# ================================================================
# CONFIGURACIÓN DEL SISTEMA
# ================================================================

@admin_bp.route("/configuracion")
@admin_required
@permiso_requerido(Permiso.VER_CONFIG)
def configuracion():
    """Página de configuración completa."""
    config_actual = cfg.cargar_config()
    return render_template("admin/configuracion.html", config=config_actual)


@admin_bp.route("/api/config/guardar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def api_config_guardar():
    """Guarda una sección de configuración en config.json."""
    try:
        data    = request.get_json()
        seccion = data.get('seccion')
        datos   = data.get('datos', {})

        secciones_validas = ['general', 'seguridad', 'notificaciones',
                             'servicios', 'apariencia', 'sistema']
        if not seccion or seccion not in secciones_validas:
            return jsonify({'ok': False, 'msg': 'Sección no válida'}), 400

        exito = cfg.guardar_seccion(seccion, datos)
        if exito:
            registrar_accion('config_guardar', f"Sección '{seccion}' actualizada")
            return jsonify({'ok': True, 'msg': f'Sección "{seccion}" guardada correctamente'})
        else:
            return jsonify({'ok': False, 'msg': 'Error al escribir config.json'}), 500

    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@admin_bp.route("/api/config/cargar", methods=["GET"])
@admin_required
@permiso_requerido(Permiso.VER_CONFIG)
def api_config_cargar():
    """Devuelve la configuración actual (toda o una sección)."""
    try:
        seccion = request.args.get('seccion')
        datos   = cfg.obtener_seccion(seccion) if seccion else cfg.cargar_config()
        return jsonify({'ok': True, 'datos': datos})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@admin_bp.route("/api/config/test-smtp", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def api_test_smtp():
    """Prueba la conexión SMTP real."""
    try:
        data  = request.get_json()
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


@admin_bp.route("/api/config/subir-imagen", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def api_subir_imagen():
    """Guarda logo, favicon o banner en static/uploads/config/."""
    try:
        tipo    = request.form.get('tipo')
        archivo = request.files.get('archivo')

        if not tipo or not archivo or archivo.filename == '':
            return jsonify({'ok': False, 'msg': 'Tipo y archivo requeridos'}), 400

        exito, resultado = cfg.guardar_imagen_config(archivo, tipo)
        if exito:
            registrar_accion('subir_imagen', f"Imagen '{tipo}' actualizada")
            return jsonify({'ok': True, 'ruta': resultado,
                            'msg': f'{tipo.capitalize()} guardado correctamente'})
        else:
            return jsonify({'ok': False, 'msg': resultado}), 400

    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@admin_bp.route("/api/config/exportar", methods=["GET"])
@admin_required
@permiso_requerido(Permiso.EXPORTAR_DATOS)
def api_exportar_datos():
    """Exporta todos los datos del sistema como ZIP."""
    try:
        exito, ruta = cfg.exportar_datos_zip()
        if exito:
            cfg.limpiar_exports_viejos(max_archivos=5)
            registrar_accion('exportar_datos', "Exportación ZIP generada")
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


@admin_bp.route("/api/config/limpiar-cache", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.MANTENIMIENTO)
def api_limpiar_cache():
    """Limpia archivos de sesión del filesystem."""
    try:
        session_dir = Path('flask_session')
        eliminados  = 0
        if session_dir.exists():
            for f in session_dir.glob('*'):
                try:
                    f.unlink()
                    eliminados += 1
                except:
                    pass
        registrar_accion('limpiar_cache', f"Caché limpiado ({eliminados} sesiones)")
        return jsonify({'ok': True, 'msg': f'Caché limpiado ({eliminados} sesiones eliminadas)'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@admin_bp.route("/api/config/sistema-info", methods=["GET"])
@admin_required
@permiso_requerido(Permiso.VER_CONFIG)
def api_sistema_info():
    """Devuelve información del entorno del servidor."""
    try:
        import flask
        info = {
            'python':      sys.version.split()[0],
            'flask':       flask.__version__,
            'storage':     'JSON Local',
            'version':     'v2.0.0',
            'debug':       cfg.get('sistema', 'debug', True),
            'maintenance': cfg.get('sistema', 'maintenance', False)
        }
        return jsonify({'ok': True, 'datos': info})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@admin_bp.route("/api/config/mantenimiento", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.MANTENIMIENTO)
def api_mantenimiento():
    """Activa o desactiva el modo mantenimiento en tiempo real."""
    try:
        data   = request.get_json()
        activo = data.get('activo', False)
        cfg.guardar_seccion('sistema', {'maintenance': activo})
        estado = 'activado' if activo else 'desactivado'
        registrar_accion('mantenimiento', f"Modo mantenimiento {estado}")
        return jsonify({'ok': True, 'msg': f'Modo mantenimiento {estado}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    

# ================================================================
# BITÁCORA DE ACTIVIDADES
# ================================================================

@admin_bp.route("/bitacora")
@admin_required
@permiso_requerido(Permiso.VER_BITACORA)
def bitacora():
    acciones_file = "data/admin_actions.json"
    acciones = []

    if os.path.exists(acciones_file):
        try:
            with open(acciones_file, 'r', encoding='utf-8') as f:
                acciones = json.load(f)
        except:
            acciones = []

    acciones.sort(key=lambda x: x.get('fecha', ''), reverse=True)

    pagina     = int(request.args.get('pagina', 1))
    por_pagina = 50
    inicio     = (pagina - 1) * por_pagina
    fin        = inicio + por_pagina
    total_pags = (len(acciones) + por_pagina - 1) // por_pagina

    return render_template(
        "admin/bitacora.html",
        acciones=acciones[inicio:fin],
        pagina=pagina,
        total_paginas=total_pags
    )


@admin_bp.route("/solicitudes/<int:solicitud_id>/responder", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_SOLICITUDES)
def responder_solicitud_api(solicitud_id):
    """API para responder a una solicitud desde el panel"""
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        respuesta = data.get('respuesta')
        admin_email = session.get('user')
        
        solicitud = Solicitud.buscar_por_id(solicitud_id)
        if not solicitud:
            return jsonify({'success': False, 'message': 'Solicitud no encontrada'}), 404
        
        # Actualizar estado
        solicitud.actualizar_estado(nuevo_estado, respuesta, admin_email)
        
        # Agregar comentario
        solicitud.agregar_comentario(respuesta, admin_email)
        
        registrar_accion('responder_solicitud', f"Solicitud {solicitud.folio} respondida")
        
        return jsonify({'success': True, 'message': 'Respuesta enviada'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route("/solicitudes/exportar/excel")
@admin_required
@permiso_requerido(Permiso.EXPORTAR_DATOS)
def exportar_solicitudes_excel():
    """Exportar solicitudes a Excel"""
    flash("Función de exportación próximamente", "info")
    return redirect(url_for("admin.listar_solicitudes"))


@admin_bp.route("/solicitudes/exportar/pdf")
@admin_required
@permiso_requerido(Permiso.EXPORTAR_DATOS)
def exportar_solicitudes_pdf():
    """Exportar solicitudes a PDF"""
    flash("Función de exportación próximamente", "info")
    return redirect(url_for("admin.listar_solicitudes"))


# ================================================================
# API PARA MENSAJES DE ADMIN EN TRÁMITES (NUEVA FUNCIONALIDAD)
# ================================================================

@admin_bp.route("/api/tramite/<folio>/mensaje", methods=["POST"])
@admin_required
def api_admin_mensaje(folio):
    """
    Admin envía un mensaje en el hilo de un trámite.
    El ciudadano lo verá en 'Mis Trámites' dentro del historial.
    """
    try:
        data  = request.get_json()
        texto = (data.get("texto") or "").strip()

        if not texto or len(texto) < 3:
            return jsonify({"error": "El mensaje no puede estar vacío."}), 400
        if len(texto) > 500:
            return jsonify({"error": "Máximo 500 caracteres."}), 400

        admin_email  = session.get("user")
        admin_nombre = session.get("user_name", admin_email)
        ahora        = datetime.now().isoformat()

        evento = {
            "fecha":       ahora,
            "tipo":        "mensaje_admin",
            "descripcion": texto,
            "usuario":     admin_email,
            "nombre":      admin_nombre
        }

        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio:
                if not isinstance(getattr(s, 'historial', None), list):
                    s.historial = []
                s.historial.append(evento)
                s.fecha_actualizacion = ahora
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                registrar_accion("mensaje_admin", f"Mensaje enviado en trámite {folio}")
                return jsonify({"success": True, "mensaje": evento})

        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio:
                if not isinstance(getattr(d, 'historial', None), list):
                    d.historial = []
                d.historial.append(evento)
                d.fecha_actualizacion = ahora
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                registrar_accion("mensaje_admin", f"Mensaje enviado en trámite {folio}")
                return jsonify({"success": True, "mensaje": evento})

        return jsonify({"error": "Trámite no encontrado."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# HELPER — Registrar acción en bitácora
# ================================================================

def registrar_accion(tipo: str, descripcion: str, admin: str = None):
    """Registra una acción administrativa en data/admin_actions.json."""
    acciones_file = "data/admin_actions.json"
    acciones = []

    if os.path.exists(acciones_file):
        try:
            with open(acciones_file, 'r', encoding='utf-8') as f:
                acciones = json.load(f)
        except:
            acciones = []

    acciones.append({
        'fecha':       datetime.now().isoformat(),
        'tipo':        tipo,
        'descripcion': descripcion,
        'admin':       admin or session.get('user', 'desconocido')
    })

    if len(acciones) > 1000:
        acciones = acciones[-1000:]

    os.makedirs('data', exist_ok=True)
    try:
        with open(acciones_file, 'w', encoding='utf-8') as f:
            json.dump(acciones, f, ensure_ascii=False, indent=2)
    except:
        pass


# ================================================================
# CONTEXTO PARA PLANTILLAS ADMIN
# ================================================================

@admin_bp.context_processor
def inject_admin_variables():
    return dict(ahora=datetime.now())