# admin.py
"""
Blueprint de administración profesional.
Maneja todas las funciones exclusivas de administradores.
"""
from models.usuario import Usuario
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from functools import wraps
from datetime import datetime
from pathlib import Path
import json
import os
import sys
import flask
from collections import defaultdict

# Importar modelos
from models import Solicitud, Denuncia, Usuario
from models.reportes import Reportes
from extensions import db

# Importar roles desde rol.py
from rol import tiene_permiso, Permiso, obtener_roles, permiso_requerido, solo_super_admin, admin_o_super, moderador_o_superior

# Módulo de configuración persistente
import config_manager as cfg

# Intentar importar nombres desde app.py
try:
    from app import NOMBRES_SERVICIOS, NOMBRES_DENUNCIAS, SERVICIOS_CITAS, cache, REDIS_AVAILABLE
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
    
    SERVICIOS_CITAS = {
        "asesoria-legal": "Asesoría Legal Municipal",
        "licencias": "Licencias de Funcionamiento",
        "catastro": "Trámites de Catastro",
        "registro-civil": "Registro Civil",
        "atencion-vecinal": "Atención Vecinal",
        "otro": "Otro trámite"
    }
    
    # Valores por defecto para cache y redis
    cache = None
    REDIS_AVAILABLE = False

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ================================================================
# FUNCIONES DE NOTIFICACIONES
# ================================================================

from models.notificacion import Notificacion

def enviar_notificacion_solicitud(solicitud, estado_anterior, comentario=None):
    """Envía notificación al usuario cuando su solicitud es actualizada"""
    titulo = f"Actualización de tu solicitud {solicitud.folio}"
    
    if estado_anterior != solicitud.estado:
        mensaje = f"Tu solicitud ha cambiado de estado: **{estado_anterior}** → **{solicitud.estado}**"
    elif comentario:
        mensaje = f"El administrador ha respondido a tu solicitud: {comentario[:200]}"
    else:
        mensaje = f"Tu solicitud ha sido actualizada. Nuevo estado: {solicitud.estado}"
    
    datos_extra = {
        'folio': solicitud.folio,
        'tipo': 'solicitud',
        'estado': solicitud.estado,
        'url': url_for('mis_tramites')
    }
    
    Notificacion.crear_notificacion(
        usuario_email=solicitud.usuario_email,
        tipo='solicitud',
        titulo=titulo,
        mensaje=mensaje,
        datos_extra=datos_extra
    )


def enviar_notificacion_denuncia(denuncia, estado_anterior, comentario=None):
    """Envía notificación al usuario cuando su denuncia es actualizada"""
    titulo = f"Actualización de tu denuncia {denuncia.folio}"
    
    if estado_anterior != denuncia.estado:
        mensaje = f"Tu denuncia ha cambiado de estado: **{estado_anterior}** → **{denuncia.estado}**"
    elif comentario:
        mensaje = f"El administrador ha respondido a tu denuncia: {comentario[:200]}"
    else:
        mensaje = f"Tu denuncia ha sido actualizada. Nuevo estado: {denuncia.estado}"
    
    datos_extra = {
        'folio': denuncia.folio,
        'tipo': 'denuncia',
        'estado': denuncia.estado,
        'url': url_for('mis_tramites')
    }
    
    Notificacion.crear_notificacion(
        usuario_email=denuncia.usuario_email if not getattr(denuncia, 'anonimo', False) else None,
        tipo='denuncia',
        titulo=titulo,
        mensaje=mensaje,
        datos_extra=datos_extra
    )


def enviar_notificacion_cita(cita, estado_anterior, notas=None):
    """Envía notificación al usuario cuando su cita es actualizada"""
    titulo = f"Actualización de tu cita {cita.folio}"
    
    if estado_anterior != cita.estado:
        mensaje = f"Tu cita ha cambiado de estado: **{estado_anterior}** → **{cita.estado}**"
    elif notas:
        mensaje = f"El administrador ha agregado notas a tu cita: {notas[:200]}"
    else:
        mensaje = f"Tu cita ha sido actualizada. Nuevo estado: {cita.estado}"
    
    datos_extra = {
        'folio': cita.folio,
        'tipo': 'cita',
        'estado': cita.estado,
        'url': url_for('mis_citas')
    }
    
    Notificacion.crear_notificacion(
        usuario_email=cita.usuario_email,
        tipo='cita',
        titulo=titulo,
        mensaje=mensaje,
        datos_extra=datos_extra
    )


# ================================================================
# FUNCIONES AUXILIARES
# ================================================================

def _cargar_usuarios_dict():
    """Carga usuarios desde la base de datos y los convierte a diccionario (compatibilidad)"""
    usuarios = Usuario.query.all()
    usuarios_dict = {}
    for u in usuarios:
        usuarios_dict[u.email] = {
            "password": u.password,
            "nombre": u.nombre or "",
            "apellidos": u.apellidos or "",
            "nombre_completo": u.nombre_completo or "",
            "email": u.email,
            "tipo": u.tipo,
            "rol": u.rol,
            "telefono": u.telefono or "",
            "cedula": u.cedula or "",
            "fecha_nacimiento": u.fecha_nacimiento or "",
            "direccion": u.direccion or "",
            "foto_perfil": u.foto_perfil or "",
            "activo": u.activo,
            "fecha_registro": u.fecha_registro.strftime("%d/%m/%Y") if u.fecha_registro else "",
            "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
            "notas_admin": u.notas_admin or ""
        }
    return usuarios_dict


def _guardar_usuarios_db(usuarios_dict):
    """Guarda usuarios desde diccionario a la base de datos (para compatibilidad)"""
    for email, datos in usuarios_dict.items():
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            usuario.nombre = datos.get("nombre", "")
            usuario.apellidos = datos.get("apellidos", "")
            usuario.nombre_completo = datos.get("nombre_completo", "")
            usuario.tipo = datos.get("tipo", "ciudadano")
            usuario.rol = datos.get("rol")
            usuario.telefono = datos.get("telefono", "")
            usuario.cedula = datos.get("cedula", "")
            usuario.direccion = datos.get("direccion", "")
            usuario.foto_perfil = datos.get("foto_perfil", "")
            usuario.activo = datos.get("activo", True)
            usuario.notas_admin = datos.get("notas_admin", "")
            if datos.get("password"):
                usuario.password = datos["password"]
        else:
            nuevo = Usuario(
                email=email,
                password=datos.get("password", ""),
                nombre=datos.get("nombre", ""),
                apellidos=datos.get("apellidos", ""),
                nombre_completo=datos.get("nombre_completo", ""),
                tipo=datos.get("tipo", "ciudadano"),
                rol=datos.get("rol"),
                telefono=datos.get("telefono", ""),
                cedula=datos.get("cedula", ""),
                direccion=datos.get("direccion", ""),
                foto_perfil=datos.get("foto_perfil", ""),
                activo=datos.get("activo", True),
                notas_admin=datos.get("notas_admin", "")
            )
            db.session.add(nuevo)
    db.session.commit()


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
        usuario = Usuario.query.filter_by(email=user_email).first()
        
        if not usuario:
            flash("Usuario no encontrado.", "error")
            return redirect(url_for("auth.login"))
        
        user_rol = usuario.rol
        
        if user_rol not in ["super_admin", "admin", "moderador"] and usuario.tipo != "admin":
            flash("Acceso restringido a administradores.", "error")
            return redirect(url_for("index"))
            
        session["user_rol"] = user_rol
        return f(*args, **kwargs)
    return decorated


# ================================================================
# DASHBOARD PRINCIPAL
# ================================================================

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
@moderador_o_superior
def dashboard():
    """Dashboard principal con estadísticas y resumen."""
    try:
        solicitudes = Solicitud.cargar_todos()
        denuncias = Denuncia.cargar_todos()
        usuarios = Usuario.query.all()
        
        total_usuarios = len(usuarios)
        admins = 0
        for u in usuarios:
            if u.tipo == 'admin' or u.rol in ['super_admin', 'admin', 'moderador']:
                admins += 1
        ciudadanos = total_usuarios - admins
        
        total_solicitudes = len(solicitudes)
        solicitudes_pendientes = len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']])
        solicitudes_completadas = len([s for s in solicitudes if s.estado == 'completado'])
        solicitudes_por_servicio = defaultdict(int)
        for s in solicitudes:
            servicio_id = str(s.servicio_id)
            solicitudes_por_servicio[servicio_id] += 1
        
        total_denuncias = len(denuncias)
        denuncias_pendientes = len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
        denuncias_resueltas = len([d for d in denuncias if d.estado == 'resuelto'])
        denuncias_por_tipo = defaultdict(int)
        for d in denuncias:
            tipo = d.tipo
            denuncias_por_tipo[tipo] += 1
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        solicitudes_hoy = len([s for s in solicitudes if s.fecha_creacion.startswith(hoy)])
        denuncias_hoy = len([d for d in denuncias if d.fecha_creacion.startswith(hoy)])
        
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

        ultimas_solicitudes = sorted(solicitudes, key=lambda x: x.fecha_creacion, reverse=True)[:5]
        ultimas_denuncias = sorted(denuncias, key=lambda x: x.fecha_creacion, reverse=True)[:5]

        try:
            from models.cita import Cita
            citas = Cita.cargar_todos()
            citas_pendientes = len([c for c in citas if c.estado == 'pendiente'])
        except:
            citas_pendientes = 0

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
        citas_pendientes = 0

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        ultimas_solicitudes=ultimas_solicitudes,
        ultimas_denuncias=ultimas_denuncias,
        servicios=NOMBRES_SERVICIOS,
        tipos_denuncia=NOMBRES_DENUNCIAS,
        citas_pendientes=citas_pendientes,
        now=datetime.now()
    )


# ================================================================
# GESTIÓN DE SOLICITUDES (COMPLETO)
# ================================================================

@admin_bp.route("/solicitudes")
@admin_required
@permiso_requerido(Permiso.VER_SOLICITUDES)
def listar_solicitudes():
    """Lista todas las solicitudes"""
    try:
        solicitudes = Solicitud.cargar_todos()
    except:
        solicitudes = []
    
    total = len(solicitudes)
    pendientes = len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']])
    completadas = len([s for s in solicitudes if s.estado == 'completado'])
    
    stats = {
        'solicitudes': total,
        'pendientes': pendientes,
        'completados': completadas,
        'en_proceso': len([s for s in solicitudes if s.estado == 'en_proceso'])
    }
    
    solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)
    
    return render_template(
        "admin/solicitudes.html",
        solicitudes=solicitudes,
        stats=stats,
        estados=Solicitud.ESTADOS,
        servicios=NOMBRES_SERVICIOS
    )


@admin_bp.route("/solicitudes/<string:solicitud_id>")
@admin_required
@permiso_requerido(Permiso.VER_SOLICITUDES)
def detalle_solicitud(solicitud_id):
    """Ver detalle de una solicitud específica"""
    try:
        solicitud = Solicitud.buscar_por_id(solicitud_id)
        if not solicitud:
            flash("Solicitud no encontrada.", "error")
            return redirect(url_for("admin.listar_solicitudes"))
        
        # Definir categorias para plantillas
        categorias = {
            'solicitud': 'Solicitudes',
            'denuncia': 'Denuncias',
            'cita': 'Citas',
            'general': 'General'
        }
        
        # Cargar plantillas disponibles
        try:
            from models.plantilla import Plantilla
            plantillas_disponibles = Plantilla.buscar_por_categoria('solicitud')
        except:
            plantillas_disponibles = []
        
        return render_template(
            "admin/solicitud_detalle.html",
            solicitud=solicitud,
            servicios=NOMBRES_SERVICIOS,
            estados=Solicitud.ESTADOS,
            categorias=categorias,
            plantillas=plantillas_disponibles,
            now=datetime.now()
        )
    except Exception as e:
        flash(f"Error al cargar solicitud: {str(e)}", "error")
        return redirect(url_for("admin.listar_solicitudes"))


@admin_bp.route("/solicitudes/<string:solicitud_id>/actualizar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_SOLICITUDES)
def actualizar_solicitud(solicitud_id):
    """Actualizar estado de una solicitud"""
    try:
        solicitud = Solicitud.buscar_por_id(solicitud_id)
        if not solicitud:
            flash("Solicitud no encontrada.", "error")
            return redirect(url_for("admin.listar_solicitudes"))
        
        estado_anterior = solicitud.estado
        nuevo_estado = request.form.get('estado')
        comentario = request.form.get('comentario', '')
        admin_email = session.get('user')
        
        if nuevo_estado in Solicitud.ESTADOS:
            solicitud.actualizar_estado(nuevo_estado, comentario, admin_email)
            flash(f"Solicitud actualizada a: {nuevo_estado}", "success")
            registrar_accion('actualizar_solicitud', f"Solicitud {solicitud.folio} actualizada a {nuevo_estado}")
            
            # Enviar notificación al usuario
            enviar_notificacion_solicitud(solicitud, estado_anterior, comentario)
        else:
            flash("Estado no válido.", "error")
        
        return redirect(url_for("admin.detalle_solicitud", solicitud_id=solicitud_id))
    except Exception as e:
        flash(f"Error al actualizar: {str(e)}", "error")
        return redirect(url_for("admin.listar_solicitudes"))


@admin_bp.route("/solicitudes/<string:solicitud_id>/eliminar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.ELIMINAR_SOLICITUDES)
def eliminar_solicitud(solicitud_id):
    """Eliminar una solicitud"""
    try:
        solicitud = Solicitud.buscar_por_id(solicitud_id)
        if solicitud:
            folio = solicitud.folio
            solicitudes = Solicitud.cargar_todos()
            solicitudes = [s for s in solicitudes if s.id != solicitud_id]
            Solicitud.guardar_todos(solicitudes)
            flash(f"Solicitud {folio} eliminada correctamente.", "success")
            registrar_accion('eliminar_solicitud', f"Solicitud {folio} eliminada")
        else:
            flash("Solicitud no encontrada.", "error")
    except Exception as e:
        flash(f"Error al eliminar: {str(e)}", "error")
    
    return redirect(url_for("admin.listar_solicitudes"))


# ================================================================
# GESTIÓN DE DENUNCIAS (COMPLETO - CORREGIDO)
# ================================================================

@admin_bp.route("/denuncias")
@admin_required
@permiso_requerido(Permiso.VER_DENUNCIAS)
def listar_denuncias():
    """Lista todas las denuncias"""
    try:
        denuncias = Denuncia.cargar_todos()
    except:
        denuncias = []
    
    total = len(denuncias)
    pendientes = len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
    resueltas = len([d for d in denuncias if d.estado == 'resuelto'])
    
    stats = {
        'denuncias': total,
        'pendientes': pendientes,
        'resueltas': resueltas,
        'en_investigacion': len([d for d in denuncias if d.estado == 'en_investigacion'])
    }
    
    denuncias.sort(key=lambda x: x.fecha_creacion, reverse=True)
    
    # Obtener filtros de la URL para mantenerlos en la plantilla
    filtros = {
        'estado': request.args.get('estado', ''),
        'tipo': request.args.get('tipo', ''),
        'fecha_inicio': request.args.get('fecha_inicio', ''),
        'fecha_fin': request.args.get('fecha_fin', ''),
        'busqueda': request.args.get('busqueda', '')
    }
    
    return render_template(
        "admin/denuncias.html",
        denuncias=denuncias,
        stats=stats,
        estados=Denuncia.ESTADOS,
        tipos=NOMBRES_DENUNCIAS,
        filtros=filtros  # CORREGIDO: Se pasa la variable filtros
    )


@admin_bp.route("/denuncias/<string:denuncia_id>")
@admin_required
@permiso_requerido(Permiso.VER_DENUNCIAS)
def detalle_denuncia(denuncia_id):
    """Ver detalle de una denuncia específica"""
    try:
        denuncia = Denuncia.buscar_por_id(denuncia_id)
        if not denuncia:
            flash("Denuncia no encontrada.", "error")
            return redirect(url_for("admin.listar_denuncias"))
        
        # Definir categorias para plantillas
        categorias = {
            'solicitud': 'Solicitudes',
            'denuncia': 'Denuncias',
            'cita': 'Citas',
            'general': 'General'
        }
        
        # Cargar plantillas disponibles
        try:
            from models.plantilla import Plantilla
            plantillas_disponibles = Plantilla.buscar_por_categoria('denuncia')
        except:
            plantillas_disponibles = []
        
        return render_template(
            "admin/denuncia_detalle.html",
            denuncia=denuncia,
            tipos=NOMBRES_DENUNCIAS,
            estados=Denuncia.ESTADOS,
            categorias=categorias,
            plantillas=plantillas_disponibles,
            now=datetime.now()
        )
    except Exception as e:
        flash(f"Error al cargar denuncia: {str(e)}", "error")
        return redirect(url_for("admin.listar_denuncias"))


@admin_bp.route("/denuncias/<string:denuncia_id>/actualizar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_DENUNCIAS)
def actualizar_denuncia(denuncia_id):
    """Actualizar estado de una denuncia"""
    try:
        denuncia = Denuncia.buscar_por_id(denuncia_id)
        if not denuncia:
            flash("Denuncia no encontrada.", "error")
            return redirect(url_for("admin.listar_denuncias"))
        
        estado_anterior = denuncia.estado
        nuevo_estado = request.form.get('estado')
        comentario = request.form.get('comentario', '')
        admin_email = session.get('user')
        
        if nuevo_estado in Denuncia.ESTADOS:
            denuncia.estado = nuevo_estado
            denuncia.fecha_actualizacion = datetime.now().isoformat()
            
            if comentario:
                if not hasattr(denuncia, 'comentarios_admin'):
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
            
            flash(f"Denuncia actualizada a: {nuevo_estado}", "success")
            registrar_accion('actualizar_denuncia', f"Denuncia {denuncia.folio} actualizada a {nuevo_estado}")
            
            # Enviar notificación al usuario (si no es anónimo)
            if not getattr(denuncia, 'anonimo', False):
                enviar_notificacion_denuncia(denuncia, estado_anterior, comentario)
        else:
            flash("Estado no válido.", "error")
        
        return redirect(url_for("admin.detalle_denuncia", denuncia_id=denuncia_id))
    except Exception as e:
        flash(f"Error al actualizar: {str(e)}", "error")
        return redirect(url_for("admin.listar_denuncias"))


@admin_bp.route("/denuncias/<string:denuncia_id>/eliminar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.ELIMINAR_DENUNCIAS)
def eliminar_denuncia(denuncia_id):
    """Eliminar una denuncia"""
    try:
        denuncia = Denuncia.buscar_por_id(denuncia_id)
        if denuncia:
            folio = denuncia.folio
            denuncias = Denuncia.cargar_todos()
            denuncias = [d for d in denuncias if d.id != denuncia_id]
            Denuncia.guardar_todos(denuncias)
            flash(f"Denuncia {folio} eliminada correctamente.", "success")
            registrar_accion('eliminar_denuncia', f"Denuncia {folio} eliminada")
        else:
            flash("Denuncia no encontrada.", "error")
    except Exception as e:
        flash(f"Error al eliminar: {str(e)}", "error")
    
    return redirect(url_for("admin.listar_denuncias"))


# ================================================================
# GESTIÓN DE USUARIOS
# ================================================================

@admin_bp.route("/usuarios")
@admin_required
@permiso_requerido(Permiso.VER_USUARIOS)
def listar_usuarios():
    busqueda = request.args.get('q', '')
    tipo = request.args.get('tipo', '')
    rol = request.args.get('rol', '')

    query = Usuario.query
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    if rol:
        query = query.filter_by(rol=rol)
    if busqueda:
        b = busqueda.lower()
        query = query.filter(
            db.or_(
                Usuario.email.ilike(f'%{b}%'),
                Usuario.nombre.ilike(f'%{b}%')
            )
        )
    
    usuarios = query.all()
    
    usuarios_lista = []
    for u in usuarios:
        usuarios_lista.append({
            "email": u.email,
            "nombre": u.nombre or "",
            "apellidos": u.apellidos or "",
            "telefono": u.telefono or "",
            "tipo": u.tipo,
            "rol": u.rol,
            "activo": u.activo,
            "fecha_registro": u.fecha_registro.strftime("%d/%m/%Y") if u.fecha_registro else "",
            "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
            "notas_admin": u.notas_admin or ""
        })

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
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    usuario_dict = {
        "email": usuario.email,
        "nombre": usuario.nombre or "",
        "apellidos": usuario.apellidos or "",
        "telefono": usuario.telefono or "",
        "tipo": usuario.tipo,
        "rol": usuario.rol,
        "activo": usuario.activo,
        "fecha_registro": usuario.fecha_registro.strftime("%d/%m/%Y") if usuario.fecha_registro else "",
        "ultimo_acceso": usuario.ultimo_acceso.isoformat() if usuario.ultimo_acceso else None,
        "notas_admin": usuario.notas_admin or ""
    }

    try:
        solicitudes = Solicitud.buscar_por_usuario(email)
        denuncias = [d for d in Denuncia.cargar_todos() if d.usuario_email == email]
    except:
        solicitudes = []
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
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    if request.method == "POST":
        usuario.nombre = request.form.get('nombre', '')
        usuario.apellidos = request.form.get('apellidos', '')
        usuario.telefono = request.form.get('telefono', '')
        usuario.tipo = request.form.get('tipo', 'ciudadano')
        usuario.activo = request.form.get('activo') == 'on'
        usuario.notas_admin = request.form.get('notas_admin', '')
        
        if session.get("user_rol") == "super_admin":
            nuevo_rol = request.form.get('rol')
            if nuevo_rol in ["super_admin", "admin", "moderador", ""]:
                usuario.rol = nuevo_rol if nuevo_rol else None

        db.session.commit()
        
        flash(f"Usuario {email} actualizado correctamente.", "success")
        registrar_accion('editar_usuario', f"Usuario {email} actualizado")
        return redirect(url_for("admin.detalle_usuario", email=email))

    usuario_dict = {
        "email": usuario.email,
        "nombre": usuario.nombre or "",
        "apellidos": usuario.apellidos or "",
        "telefono": usuario.telefono or "",
        "tipo": usuario.tipo,
        "rol": usuario.rol,
        "activo": usuario.activo,
        "fecha_registro": usuario.fecha_registro.strftime("%d/%m/%Y") if usuario.fecha_registro else "",
        "notas_admin": usuario.notas_admin or ""
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
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    nueva_password = request.form.get('nueva_password')
    confirmar = request.form.get('confirmar_password')

    if not nueva_password or len(nueva_password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("admin.detalle_usuario", email=email))

    if nueva_password != confirmar:
        flash("Las contraseñas no coinciden.", "error")
        return redirect(url_for("admin.detalle_usuario", email=email))

    usuario.password = nueva_password
    db.session.commit()
    
    flash(f"Contraseña de {email} actualizada correctamente.", "success")
    registrar_accion('cambiar_password', f"Contraseña cambiada para {email}")
    return redirect(url_for("admin.detalle_usuario", email=email))


# ================================================================
# CREAR ADMIN - CORREGIDO CON @solo_super_admin
# ================================================================

@admin_bp.route("/usuarios/crear-admin", methods=["GET", "POST"])
@admin_required
@solo_super_admin
def crear_admin():
    if request.method == "POST":
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirmar = request.form.get('confirmar_password', '')
        telefono = request.form.get('telefono', '')
        rol = request.form.get('rol', 'moderador')

        errores = []
        if not nombre or not email or not password:
            errores.append("Todos los campos son obligatorios.")
        if password != confirmar:
            errores.append("Las contraseñas no coinciden.")
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        
        existe = Usuario.query.filter_by(email=email).first()
        if existe:
            errores.append("Este correo ya está registrado.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("admin/crear_admin.html", roles=obtener_roles())

        nuevo_usuario = Usuario(
            email=email,
            password=password,
            nombre=nombre,
            apellidos="",
            nombre_completo=nombre,
            tipo="admin",
            rol=rol,
            telefono=telefono,
            activo=True,
            notas_admin=f"Creado por {session.get('user_name', session.get('user', 'desconocido'))}"
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        rol_nombre = {
            "super_admin": "Super Administrador",
            "admin": "Administrador",
            "moderador": "Moderador"
        }.get(rol, rol)

        flash(f"{rol_nombre} {email} creado exitosamente.", "success")
        registrar_accion('crear_admin', f"{rol_nombre} {email} creado")
        return redirect(url_for("admin.listar_usuarios"))

    return render_template("admin/crear_admin.html", roles=obtener_roles())


@admin_bp.route("/usuarios/<path:email>/toggle-activo", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_USUARIOS)
def toggle_usuario_activo(email):
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.listar_usuarios"))

    if email == session.get('user'):
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("admin.detalle_usuario", email=email))

    estado_actual = usuario.activo
    usuario.activo = not estado_actual
    db.session.commit()
    
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
        stats = Reportes.obtener_estadisticas_generales()
        solicitudes_por_servicio = Reportes.obtener_solicitudes_por_servicio()
        denuncias_por_tipo = Reportes.obtener_denuncias_por_tipo()
    except:
        stats = {}
        solicitudes_por_servicio = {}
        denuncias_por_tipo = {}

    return render_template(
        "admin/reportes.html",
        stats=stats,
        solicitudes_por_servicio=solicitudes_por_servicio,
        denuncias_por_tipo=denuncias_por_tipo,
        servicios=NOMBRES_SERVICIOS,
        tipos_denuncia=NOMBRES_DENUNCIAS
    )


# ================================================================
# CITAS
# ================================================================

@admin_bp.route("/citas")
@admin_required
def admin_citas():
    try:
        from models.cita import Cita
        citas = Cita.cargar_todos()
        citas.sort(key=lambda x: x.fecha + ' ' + x.hora)
        
        from datetime import datetime
        hoy = datetime.now().strftime('%Y-%m-%d')
        stats = {
            'total': len(citas),
            'pendientes': len([c for c in citas if c.estado == 'pendiente']),
            'confirmadas': len([c for c in citas if c.estado == 'confirmada']),
            'hoy': len([c for c in citas if c.fecha == hoy])
        }
        
        return render_template("admin/citas.html", citas=citas, stats=stats, servicios=SERVICIOS_CITAS)
    except Exception as e:
        flash(f"Error al cargar citas: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


@admin_bp.route("/citas/<cita_id>/estado", methods=["POST"])
@admin_required
def admin_cambiar_estado_cita(cita_id):
    try:
        from models.cita import Cita
        cita = Cita.buscar_por_id(cita_id)
        if not cita:
            flash("❌ Cita no encontrada.", "error")
            return redirect(url_for('admin.admin_citas'))
        
        estado_anterior = cita.estado
        nuevo_estado = request.form.get("estado")
        notas = request.form.get("notas", "")
        
        if nuevo_estado not in Cita.ESTADOS:
            flash("❌ Estado no válido.", "error")
            return redirect(url_for('admin.admin_citas'))
        
        cita.estado = nuevo_estado
        if notas:
            cita.notas_admin = notas
        
        citas = Cita.cargar_todos()
        for i, c in enumerate(citas):
            if c.id == cita_id:
                citas[i] = cita
                break
        Cita.guardar_todos(citas)
        
        flash(f"✅ Estado de cita actualizado a: {nuevo_estado}", "success")
        
        # Enviar notificación al usuario
        enviar_notificacion_cita(cita, estado_anterior, notas)
        
        return redirect(url_for('admin.admin_citas'))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


# ================================================================
# PLANTILLAS
# ================================================================

@admin_bp.route("/plantillas")
@admin_required
def admin_plantillas():
    try:
        from models.plantilla import Plantilla
        plantillas = Plantilla.cargar_todos()
        
        por_categoria = {}
        for p in plantillas:
            if p.categoria not in por_categoria:
                por_categoria[p.categoria] = []
            por_categoria[p.categoria].append(p)
        
        return render_template("admin/plantillas.html", plantillas=plantillas, por_categoria=por_categoria, categorias=Plantilla.CATEGORIAS)
    except Exception as e:
        flash(f"Error al cargar plantillas: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


@admin_bp.route("/plantillas/crear", methods=["POST"])
@admin_required
def admin_crear_plantilla():
    try:
        from models.plantilla import Plantilla
        nombre = request.form.get("nombre")
        categoria = request.form.get("categoria")
        contenido = request.form.get("contenido")
        variables = request.form.getlist("variables") or ['folio', 'nombre', 'fecha']
        
        if not nombre or not contenido:
            flash("❌ Nombre y contenido son obligatorios.", "error")
            return redirect(url_for('admin.admin_plantillas'))
        
        plantillas = Plantilla.cargar_todos()
        nueva = Plantilla(
            nombre=nombre,
            categoria=categoria,
            contenido=contenido,
            variables=variables,
            creada_por=session.get("user_name", session["user"])
        )
        plantillas.append(nueva)
        Plantilla.guardar_todos(plantillas)
        
        flash(f"✅ Plantilla '{nombre}' creada correctamente.", "success")
        return redirect(url_for('admin.admin_plantillas'))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


@admin_bp.route("/plantillas/<plantilla_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_plantilla(plantilla_id):
    try:
        from models.plantilla import Plantilla
        plantilla = Plantilla.buscar_por_id(plantilla_id)
        if not plantilla:
            flash("❌ Plantilla no encontrada.", "error")
            return redirect(url_for('admin.admin_plantillas'))
        
        plantilla.activa = not plantilla.activa
        
        plantillas = Plantilla.cargar_todos()
        for i, p in enumerate(plantillas):
            if p.id == plantilla_id:
                plantillas[i] = plantilla
                break
        Plantilla.guardar_todos(plantillas)
        
        estado = "activada" if plantilla.activa else "desactivada"
        flash(f"✅ Plantilla '{plantilla.nombre}' {estado}.", "success")
        return redirect(url_for('admin.admin_plantillas'))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


@admin_bp.route("/plantillas/<plantilla_id>/eliminar", methods=["POST"])
@admin_required
def admin_eliminar_plantilla(plantilla_id):
    try:
        from models.plantilla import Plantilla
        plantillas = Plantilla.cargar_todos()
        plantillas = [p for p in plantillas if p.id != plantilla_id]
        Plantilla.guardar_todos(plantillas)
        
        flash("✅ Plantilla eliminada.", "success")
        return redirect(url_for('admin.admin_plantillas'))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


# ================================================================
# MAPA DE INCIDENCIAS
# ================================================================

@admin_bp.route("/mapa")
@admin_required
def admin_mapa_incidencias():
    try:
        denuncias = Denuncia.cargar_todos()
        denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
        
        return render_template(
            "admin/mapa_admin.html",
            denuncias=denuncias_geo,
            tipos=NOMBRES_DENUNCIAS,
            stats={
                'total': len(denuncias),
                'geolocalizadas': len(denuncias_geo),
                'pendientes': len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
            }
        )
    except Exception as e:
        flash(f"Error al cargar mapa: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


# ================================================================
# ENCUESTAS
# ================================================================

@admin_bp.route("/encuestas")
@admin_required
def admin_encuestas():
    try:
        from models.encuesta import Encuesta
        stats = Encuesta.obtener_estadisticas()
        return render_template("admin/encuestas.html", stats=stats)
    except Exception as e:
        flash(f"Error al cargar encuestas: {str(e)}", "error")
        return redirect(url_for('admin.dashboard'))


# ================================================================
# BITÁCORA (CORREGIDA Y COMPLETA)
# ================================================================

@admin_bp.route("/bitacora")
@admin_required
@permiso_requerido(Permiso.VER_BITACORA)
def bitacora():
    """Muestra el registro de acciones de los administradores"""
    acciones_file = "data/admin_actions.json"
    acciones = []

    if os.path.exists(acciones_file):
        try:
            with open(acciones_file, 'r', encoding='utf-8') as f:
                acciones = json.load(f)
        except Exception as e:
            print(f"Error cargando bitácora: {e}")
            acciones = []

    # Ordenar por fecha (más reciente primero)
    acciones.sort(key=lambda x: x.get('fecha', ''), reverse=True)

    # Paginación
    pagina = int(request.args.get('pagina', 1))
    por_pagina = 50
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    total_pags = (len(acciones) + por_pagina - 1) // por_pagina if acciones else 1

    return render_template(
        "admin/bitacora.html",
        acciones=acciones[inicio:fin],
        pagina=pagina,
        total_paginas=total_pags,
        total_acciones=len(acciones)
    )


# ================================================================
# GESTIÓN DE MENSAJES EN TRÁMITES
# ================================================================

from models.mensaje import Mensaje

@admin_bp.route("/api/tramite/<folio>/mensajes", methods=["GET"])
@admin_required
def api_obtener_mensajes_tramite(folio):
    """Obtiene todos los mensajes de un trámite"""
    try:
        tramite_tipo = request.args.get('tipo', 'solicitud')
        mensajes = Mensaje.obtener_mensajes_tramite(folio, tramite_tipo)
        
        # Marcar como leídos los mensajes del usuario
        for m in mensajes:
            if not m.es_admin and not m.leido:
                m.marcar_leido()
        
        return jsonify({
            'success': True,
            'mensajes': [m.to_dict() for m in mensajes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route("/api/tramite/<folio>/responder", methods=["POST"])
@admin_required
def api_responder_mensaje_admin(folio):
    """Admin responde a un trámite"""
    try:
        data = request.get_json()
        mensaje_texto = data.get('mensaje', '').strip()
        tramite_tipo = data.get('tipo', 'solicitud')
        
        if not mensaje_texto:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'}), 400
        
        if len(mensaje_texto) > 1000:
            return jsonify({'success': False, 'error': 'El mensaje es demasiado largo'}), 400
        
        # Obtener información del trámite
        usuario_email = None
        nombre_tramite = ''
        
        if tramite_tipo == 'solicitud':
            solicitud = Solicitud.buscar_por_folio(folio)
            if solicitud:
                usuario_email = solicitud.usuario_email
                nombre_tramite = NOMBRES_SERVICIOS.get(solicitud.servicio_id, solicitud.servicio_id)
        elif tramite_tipo == 'denuncia':
            denuncias = Denuncia.cargar_todos()
            for d in denuncias:
                if d.folio == folio:
                    usuario_email = d.usuario_email
                    nombre_tramite = NOMBRES_DENUNCIAS.get(d.tipo, d.tipo)
                    break
        elif tramite_tipo == 'cita':
            from models.cita import Cita
            cita = Cita.buscar_por_folio(folio)
            if cita:
                usuario_email = cita.usuario_email
                nombre_tramite = SERVICIOS_CITAS.get(cita.servicio, cita.servicio)
        
        if not usuario_email:
            return jsonify({'success': False, 'error': 'Trámite no encontrado'}), 404
        
        admin_email = session.get('user')
        admin_nombre = session.get('user_name', 'Administrador')
        
        # Crear mensaje
        Mensaje.crear_mensaje(
            tramite_folio=folio,
            tramite_tipo=tramite_tipo,
            usuario_email=usuario_email,
            autor_email=admin_email,
            autor_nombre=admin_nombre,
            mensaje=mensaje_texto,
            es_admin=True
        )
        
        # También enviar una notificación al usuario
        try:
            titulo = f"Nuevo mensaje en tu {nombre_tramite}"
            descripcion = f"El administrador ha respondido a tu trámite {folio}"
            
            Notificacion.crear_notificacion(
                usuario_email=usuario_email,
                tipo='mensaje',
                titulo=titulo,
                mensaje=descripcion,
                datos_extra={
                    'folio': folio,
                    'tipo': tramite_tipo,
                    'url': url_for('mis_tramites')
                }
            )
        except:
            pass
        
        registrar_accion('responder_tramite', f"Admin respondió en {tramite_tipo} {folio}")
        
        return jsonify({'success': True, 'mensaje': 'Respuesta enviada correctamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ================================================================
# CONFIGURACIÓN
# ================================================================

@admin_bp.route("/configuracion", methods=["GET"])
@admin_required
@permiso_requerido(Permiso.VER_CONFIG)
def configuracion():
    """Muestra la página de configuración"""
    config_actual = cfg.cargar_config()
    return render_template("admin/configuracion.html", config=config_actual)


@admin_bp.route("/configuracion/guardar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def guardar_configuracion():
    """Guarda la configuración enviada desde el formulario (método POST tradicional)"""
    from models.configuracion import Configuracion
    
    # Guardar cada configuración
    for clave, valor in request.form.items():
        Configuracion.set(clave, valor)
    
    # Limpiar caché global
    Configuracion.clear_cache()
    
    flash('✅ Configuración actualizada correctamente', 'success')
    return redirect(url_for('admin.configuracion'))


# ================================================================
# API DE CONFIGURACIÓN (CORREGIDA - USA MODELO CONFIGURACION)
# ================================================================

@admin_bp.route("/api/config/sistema-info", methods=["GET"])
@admin_required
@permiso_requerido(Permiso.VER_CONFIG)
def api_sistema_info():
    """Devuelve información del sistema para la página de configuración"""
    try:
        info = {
            'version': '2.0.0',
            'python_version': sys.version.split()[0],
            'flask_version': flask.__version__,
            'database': 'PostgreSQL',
            'debug': True,
            'redis_available': REDIS_AVAILABLE,
            'cloudinary_configured': True,
            'total_usuarios': Usuario.query.count(),
            'total_solicitudes': len(Solicitud.cargar_todos()),
            'total_denuncias': len(Denuncia.cargar_todos()),
            'ultimo_backup': None,
            'mantenimiento': cfg.get('sistema', 'maintenance', False)
        }
        return jsonify({"ok": True, "datos": info})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/config/guardar", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def api_guardar_config():
    """Guarda la configuración del sistema en la base de datos usando modelo Configuracion"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"ok": False, "error": "No se recibieron datos"}), 400
        
        seccion = data.get('seccion')
        valores = data.get('datos', {})
        
        if not valores:
            return jsonify({"ok": False, "error": "No se recibieron valores para guardar"}), 400
        
        # Importar modelo de configuración
        from models.configuracion import Configuracion
        
        contador = 0
        if seccion:
            # Guardar sección completa
            for clave, valor in valores.items():
                # Detectar tipo automáticamente
                tipo = 'string'
                if isinstance(valor, bool):
                    tipo = 'bool'
                elif isinstance(valor, int):
                    tipo = 'int'
                elif isinstance(valor, float):
                    tipo = 'float'
                elif isinstance(valor, (dict, list)):
                    tipo = 'json'
                
                Configuracion.set(clave, valor, tipo, seccion)
                contador += 1
        else:
            # Guardar config general
            for clave, valor in valores.items():
                tipo = 'string'
                if isinstance(valor, bool):
                    tipo = 'bool'
                elif isinstance(valor, int):
                    tipo = 'int'
                elif isinstance(valor, float):
                    tipo = 'float'
                elif isinstance(valor, (dict, list)):
                    tipo = 'json'
                Configuracion.set(clave, valor, tipo, 'general')
                contador += 1
        
        # Confirmar transacción
        db.session.commit()
        
        # Registrar acción en bitácora
        registrar_accion(
            'guardar_configuracion', 
            f"Configuración actualizada - Sección: {seccion or 'general'} - {contador} valores guardados"
        )
        
        return jsonify({
            "ok": True, 
            "mensaje": f"✅ Configuración guardada correctamente ({contador} valores actualizados)",
            "guardados": contador
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error guardando configuración: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/config/test-smtp", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def api_test_smtp():
    """Prueba la conexión SMTP"""
    try:
        data = request.get_json()
        exito, mensaje = cfg.test_smtp(
            host=data.get('smtp_host', ''),
            port=data.get('smtp_port', 587),
            user=data.get('smtp_user', ''),
            password=data.get('smtp_pass', ''),
            nombre=data.get('smtp_name', 'Villa Cutupú'),
            email_destino=data.get('email_destino', '')
        )
        return jsonify({"ok": exito, "msg": mensaje})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@admin_bp.route("/api/config/subir-imagen", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.EDITAR_CONFIG)
def api_subir_imagen():
    """Sube imágenes de configuración (logo, favicon, banner)"""
    try:
        tipo = request.form.get('tipo')
        archivo = request.files.get('archivo')
        
        if not tipo or not archivo or archivo.filename == '':
            return jsonify({"ok": False, "msg": "Tipo y archivo requeridos"}), 400
        
        exito, resultado = cfg.guardar_imagen_config(archivo, tipo)
        
        if exito:
            registrar_accion('subir_imagen', f"Imagen '{tipo}' actualizada")
            return jsonify({"ok": True, "ruta": resultado, "msg": f"{tipo.capitalize()} guardado correctamente"})
        else:
            return jsonify({"ok": False, "msg": resultado}), 400
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@admin_bp.route("/api/config/exportar", methods=["GET"])
@admin_required
@permiso_requerido(Permiso.EXPORTAR_DATOS)
def api_exportar_datos():
    """Exporta los datos del sistema como ZIP"""
    try:
        exito, ruta = cfg.exportar_datos_zip()
        if exito:
            registrar_accion('exportar_datos', "Exportación ZIP generada")
            return send_file(
                ruta,
                as_attachment=True,
                download_name=Path(ruta).name,
                mimetype='application/zip'
            )
        else:
            return jsonify({"ok": False, "msg": ruta}), 500
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@admin_bp.route("/api/config/limpiar-cache", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.MANTENIMIENTO)
def api_limpiar_cache():
    """Limpia la caché del sistema"""
    try:
        if cache:
            cache.clear()
        registrar_accion('limpiar_cache', "Caché del sistema limpiada")
        return jsonify({"ok": True, "msg": "✅ Caché limpiada correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@admin_bp.route("/api/config/mantenimiento", methods=["POST"])
@admin_required
@permiso_requerido(Permiso.MANTENIMIENTO)
def api_mantenimiento():
    """Activa o desactiva el modo mantenimiento"""
    try:
        data = request.get_json()
        activo = data.get('activo', False)
        cfg.guardar_seccion('sistema', {'maintenance': activo})
        estado = 'activado' if activo else 'desactivado'
        registrar_accion('mantenimiento', f"Modo mantenimiento {estado}")
        return jsonify({"ok": True, "msg": f"Modo mantenimiento {estado}"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


# ================================================================
# API PARA ADMIN (ENDPOINTS SIN @admin_required PARA AJAX)
# ================================================================

@admin_bp.route("/api/citas-pendientes")
def api_citas_pendientes():
    if "user" not in session:
        return jsonify({"count": 0}), 401
    try:
        from models.cita import Cita
        citas = Cita.cargar_todos()
        print(f"[DEBUG] Total citas cargadas: {len(citas)}")
        pendientes = len([c for c in citas if c.estado == 'pendiente'])
        print(f"[DEBUG] Citas pendientes: {pendientes}")
        return jsonify({"count": pendientes})
    except Exception as e:
        print(f"[ERROR] api_citas_pendientes: {str(e)}")
        return jsonify({"count": 0, "error": str(e)}), 500


@admin_bp.route("/api/solicitudes-pendientes")
def api_solicitudes_pendientes():
    if "user" not in session:
        return jsonify({"count": 0}), 401
    try:
        solicitudes = Solicitud.cargar_todos()
        print(f"[DEBUG] Total solicitudes cargadas: {len(solicitudes)}")
        for s in solicitudes:
            print(f"[DEBUG] Solicitud: {s.folio} - estado: {s.estado}")
        pendientes = len([s for s in solicitudes if s.estado in ['pendiente', 'en_proceso']])
        print(f"[DEBUG] Solicitudes pendientes: {pendientes}")
        return jsonify({"count": pendientes})
    except Exception as e:
        print(f"[ERROR] api_solicitudes_pendientes: {str(e)}")
        return jsonify({"count": 0, "error": str(e)}), 500


@admin_bp.route("/api/denuncias-pendientes")
def api_denuncias_pendientes():
    if "user" not in session:
        return jsonify({"count": 0}), 401
    try:
        denuncias = Denuncia.cargar_todos()
        print(f"[DEBUG] Total denuncias cargadas: {len(denuncias)}")
        for d in denuncias:
            print(f"[DEBUG] Denuncia: {d.folio} - estado: {d.estado}")
        pendientes = len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
        print(f"[DEBUG] Denuncias pendientes: {pendientes}")
        return jsonify({"count": pendientes})
    except Exception as e:
        print(f"[ERROR] api_denuncias_pendientes: {str(e)}")
        return jsonify({"count": 0, "error": str(e)}), 500


# ================================================================
# API PARA DENUNCIAS EN MAPA (GEOJSON)
# ================================================================

@admin_bp.route("/api/denuncias/geojson")
@admin_required
def api_denuncias_geojson():
    """Devuelve las denuncias en formato GeoJSON para el mapa de incidencias"""
    try:
        denuncias = Denuncia.cargar_todos()
        
        # Filtrar solo denuncias con coordenadas
        features = []
        for d in denuncias:
            # Verificar si tiene coordenadas
            lat = None
            lng = None
            
            # Intentar obtener coordenadas de diferentes formas
            if hasattr(d, 'lat') and d.lat and hasattr(d, 'lng') and d.lng:
                try:
                    lat = float(d.lat)
                    lng = float(d.lng)
                except (ValueError, TypeError):
                    pass
            elif hasattr(d, 'latitud') and d.latitud and hasattr(d, 'longitud') and d.longitud:
                try:
                    lat = float(d.latitud)
                    lng = float(d.longitud)
                except (ValueError, TypeError):
                    pass
            elif hasattr(d, 'geolocalizada') and d.geolocalizada and hasattr(d, 'coordenadas') and d.coordenadas:
                # Si tiene coordenadas como string "lat,lng"
                if isinstance(d.coordenadas, str) and ',' in d.coordenadas:
                    parts = d.coordenadas.split(',')
                    if len(parts) == 2:
                        try:
                            lat = float(parts[0].strip())
                            lng = float(parts[1].strip())
                        except (ValueError, TypeError):
                            pass
            elif hasattr(d, 'ubicacion') and d.ubicacion:
                # Si tiene ubicación como string "lat,lng"
                if isinstance(d.ubicacion, str) and ',' in d.ubicacion:
                    parts = d.ubicacion.split(',')
                    if len(parts) == 2:
                        try:
                            lat = float(parts[0].strip())
                            lng = float(parts[1].strip())
                        except (ValueError, TypeError):
                            pass
            
            if lat and lng:
                # Obtener nombre del tipo de denuncia
                tipo_nombre = NOMBRES_DENUNCIAS.get(d.tipo, d.tipo)
                
                # Obtener color según estado
                color = "#ffc107"  # amarillo por defecto
                if d.estado == 'pendiente':
                    color = "#ffc107"  # amarillo
                elif d.estado == 'en_investigacion':
                    color = "#17a2b8"  # azul
                elif d.estado == 'resuelto':
                    color = "#28a745"  # verde
                elif d.estado == 'rechazado':
                    color = "#dc3545"  # rojo
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]  # GeoJSON usa [longitud, latitud]
                    },
                    "properties": {
                        "id": d.id,
                        "folio": d.folio,
                        "tipo": d.tipo,
                        "tipo_nombre": tipo_nombre,
                        "estado": d.estado,
                        "estado_label": d.estado.replace('_', ' ').title(),
                        "color": color,
                        "descripcion": d.descripcion[:200] if hasattr(d, 'descripcion') and d.descripcion else "",
                        "direccion": getattr(d, 'direccion', ''),
                        "fecha": d.fecha_creacion,
                        "fecha_formateada": datetime.strptime(d.fecha_creacion, "%Y-%m-%d").strftime("%d/%m/%Y") if d.fecha_creacion else "",
                        "url": url_for('admin.detalle_denuncia', denuncia_id=d.id)
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "total": len(features),
            "total_denuncias": len(denuncias)
        }
        
        return jsonify(geojson)
        
    except Exception as e:
        print(f"Error generando GeoJSON para mapa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "type": "FeatureCollection",
            "features": [],
            "error": str(e),
            "total": 0
        }), 500


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
# HELPER - Registrar acción en bitácora
# ================================================================

def registrar_accion(tipo: str, descripcion: str, admin: str = None):
    """Registra una acción en la bitácora de administración"""
    acciones_file = "data/admin_actions.json"
    acciones = []

    if os.path.exists(acciones_file):
        try:
            with open(acciones_file, 'r', encoding='utf-8') as f:
                acciones = json.load(f)
        except:
            acciones = []

    acciones.append({
        'fecha': datetime.now().isoformat(),
        'tipo': tipo,
        'descripcion': descripcion,
        'admin': admin or session.get('user', 'desconocido')
    })

    # Mantener solo las últimas 1000 acciones
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
    foto_perfil = session.get('foto_perfil', '')
    user_name = session.get('user_name', 'Administrador')
    user_rol = session.get('user_rol', 'admin')
    user_email = session.get('user', '')
    
    return dict(
        ahora=datetime.now(),
        NOMBRES_SERVICIOS=NOMBRES_SERVICIOS,
        NOMBRES_DENUNCIAS=NOMBRES_DENUNCIAS,
        foto_perfil=foto_perfil,
        user_name=user_name,
        user_rol=user_rol,
        user_email=user_email
    )