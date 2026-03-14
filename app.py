# ================================================================
# IMPORTS
# ================================================================
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from auth import auth, login_required, admin_required, _cargar_usuarios
from admin import admin_bp
import os
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

# ================================================================
# CONFIGURACIÓN INICIAL
# ================================================================
app = Flask(__name__)
app.secret_key = "clave_secreta_muy_segura_cambiar_en_produccion_123"
app.config['SESSION_TYPE'] = 'filesystem'

# Configuración para subida de archivos (fotos perfil)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB máx
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración para documentos de trámites
DOCS_FOLDER = os.path.join('static', 'uploads', 'documentos')
ALLOWED_DOC_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
DOCS_MAX_POR_TRAMITE = 5
DOCS_MAX_SIZE_MB = 10

app.static_folder = 'static'
app.static_url_path = '/static'

# Registrar blueprints
app.register_blueprint(auth)
app.register_blueprint(admin_bp)

# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _allowed_document(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

def _objeto_a_dict(obj):
    """Convierte un objeto o dict a dict limpio serializable."""
    if isinstance(obj, dict):
        d = dict(obj)
    elif hasattr(obj, '__dict__'):
        d = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    else:
        return {}

    # Convertir cualquier valor no serializable a string
    for k, v in d.items():
        if hasattr(v, '__dict__') or (not isinstance(v, (str, int, float, bool, list, dict, type(None)))):
            d[k] = str(v)
        elif isinstance(v, list):
            d[k] = [
                (item if isinstance(item, (str, int, float, bool, dict, type(None)))
                 else str(item))
                for item in v
            ]

    return d

def _icono_doc(filename):
    """Devuelve clase FontAwesome según extensión."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    iconos = {
        'pdf':  'fa-file-pdf',
        'doc':  'fa-file-word',
        'docx': 'fa-file-word',
        'jpg':  'fa-file-image',
        'jpeg': 'fa-file-image',
        'png':  'fa-file-image',
    }
    return iconos.get(ext, 'fa-file')

# ================================================================
# CATÁLOGO DE SERVICIOS
# ================================================================
NOMBRES_SERVICIOS = {
    "funeraria":     "Funerarias Municipales",
    "uso-suelo":     "Certificado de Uso de Suelo",
    "oaim":          "Oficina de Acceso a la Información (OAI/M)",
    "planeamiento":  "Planeamiento Urbano",
    "ornato":        "Ornato y Préstamos de Áreas",
    "catastro":      "Catastro Municipal",
    "aseo-comercial":"Gestión Comercial de Aseo",
}

NOMBRES_DENUNCIAS = {
    "policia":  "Policía Municipal",
    "limpieza": "Limpieza y Cuidado de la Vía Pública",
    "basura":   "Recogida de Basura",
    "alumbrado":"Alumbrado Público",
    "otro":     "Otra denuncia",
}

NOMBRES_CONSULTAS = {
    "pot": "Plan de Ordenamiento Territorial",
}

# ================================================================
# SERVICIOS PARA CITAS
# ================================================================
SERVICIOS_CITAS = {
    "asesoria-legal": "Asesoría Legal Municipal",
    "licencias": "Licencias de Funcionamiento",
    "catastro": "Trámites de Catastro",
    "registro-civil": "Registro Civil",
    "atencion-vecinal": "Atención Vecinal",
    "otro": "Otro trámite"
}

# ================================================================
# CONTEXTO GLOBAL
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
        foto_perfil=session.get("foto_perfil", "")
    )

# ================================================================
# RUTAS PÚBLICAS
# ================================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/municipio")
def municipio():
    return render_template("municipio.html")

@app.route("/servicios")
def servicios():
    return render_template("servicios.html")

@app.route("/transparencia")
def transparencia():
    return render_template("transparencia.html")

@app.route("/transparencia/estructura")
def transparencia_estructura():
    return render_template("transparencia_estructura.html")

@app.route("/transparencia/integrantes")
def transparencia_integrantes():
    return render_template("transparencia_integrantes.html")

@app.route("/transparencia/normativas")
def transparencia_normativas():
    return render_template("transparencia_normativas.html")

@app.route("/transparencia/proyectos")
def transparencia_proyectos():
    return render_template("transparencia_proyectos.html")

@app.route("/transparencia/informes")
def transparencia_informes():
    return render_template("transparencia_informes.html")

@app.route("/transparencia/datos")
def transparencia_datos():
    return render_template("transparencia_datos.html")

@app.route("/transparencia/atencion")
def transparencia_atencion():
    return render_template("transparencia_atencion.html")

@app.route("/transparencia/actas")
def transparencia_actas():
    return render_template("transparencia_actas.html")

@app.route("/transparencia/compras")
def transparencia_compras():
    return render_template("transparencia_compras.html")

@app.route("/noticias")
def noticias():
    return render_template("noticias.html")

@app.route("/contacto", methods=["GET"])
def contacto():
    return render_template("contacto.html")

@app.route("/enviar-contacto", methods=["POST"])
def enviar_contacto():
    nombre  = request.form.get("nombre", "").strip()
    email   = request.form.get("email", "").strip()
    asunto  = request.form.get("asunto", "").strip()
    mensaje = request.form.get("mensaje", "").strip()

    if not nombre or not email or not asunto or not mensaje:
        flash("❌ Todos los campos obligatorios deben completarse.", "error")
        return redirect(url_for("contacto"))

    flash(f"✅ Gracias {nombre}, tu mensaje fue enviado. Te responderemos a la brevedad.", "success")
    return redirect(url_for("contacto"))

# ================================================================
# SERVICIOS (PROTEGIDOS)
# ================================================================
@app.route("/solicitar/<servicio>", methods=["GET", "POST"])
@login_required
def solicitar_servicio(servicio):
    if servicio not in NOMBRES_SERVICIOS:
        flash("❌ El servicio solicitado no existe.", "error")
        return redirect(url_for("servicios"))

    nombre_servicio = NOMBRES_SERVICIOS[servicio]

    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        cedula      = request.form.get("cedula", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre or not cedula or not descripcion:
            flash("❌ Completa todos los campos obligatorios.", "error")
            return redirect(url_for("solicitar_servicio", servicio=servicio))

        try:
            from models import Solicitud
            solicitud = Solicitud.crear(
                usuario_email=session["user"],
                usuario_nombre=nombre,
                usuario_cedula=cedula,
                servicio_id=servicio,
                servicio_nombre=nombre_servicio,
                descripcion=descripcion
            )
            flash(
                f"✅ Tu solicitud de «{nombre_servicio}» fue enviada. "
                f"Tu folio es: **{solicitud.folio}**. Te contactaremos pronto.",
                "success"
            )
        except Exception as e:
            flash(f"❌ Error al procesar la solicitud: {str(e)}", "error")

        return redirect(url_for("servicios"))

    return render_template("solicitar.html",
                           servicio=servicio,
                           nombre_servicio=nombre_servicio,
                           tipo_formulario="solicitud")

@app.route("/consultar/<consulta>", methods=["GET", "POST"])
@login_required
def consultar_servicio(consulta):
    if consulta not in NOMBRES_CONSULTAS:
        flash("❌ La consulta solicitada no existe.", "error")
        return redirect(url_for("servicios"))

    nombre_consulta = NOMBRES_CONSULTAS[consulta]

    if request.method == "POST":
        nombre         = request.form.get("nombre", "").strip()
        consulta_texto = request.form.get("consulta", "").strip()

        if not nombre or not consulta_texto:
            flash("❌ Completa todos los campos obligatorios.", "error")
            return redirect(url_for("consultar_servicio", consulta=consulta))

        flash(
            f"✅ Tu consulta sobre «{nombre_consulta}» fue recibida. "
            f"Te responderemos en 3 días hábiles.",
            "success"
        )
        return redirect(url_for("servicios"))

    return render_template("consultar.html",
                           consulta=consulta,
                           nombre_consulta=nombre_consulta)

@app.route("/denunciar/<tipo>", methods=["GET", "POST"])
@login_required
def denunciar_servicio(tipo):
    if tipo not in NOMBRES_DENUNCIAS:
        flash("❌ El tipo de denuncia no es válido.", "error")
        return redirect(url_for("servicios"))

    nombre_servicio = NOMBRES_DENUNCIAS[tipo]

    # Calcular estadísticas para el template
    try:
        from models import Denuncia
        denuncias = Denuncia.cargar_todos()
        stats = {
            'denuncias': len(denuncias),
            'pendientes': len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']]),
            'resueltas': len([d for d in denuncias if d.estado == 'resuelto'])
        }
    except Exception as e:
        print(f"Error cargando estadísticas: {e}")
        stats = {
            'denuncias': 0,
            'pendientes': 0,
            'resueltas': 0
        }

    filtros = {
        'q': request.args.get('q', ''),
        'estado': request.args.get('estado', ''),
        'tipo': request.args.get('tipo', '')
    }

    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        direccion   = request.form.get("direccion", "").strip()
        anonimo     = request.form.get("anonimo") == "on"

        if not anonimo and not nombre:
            flash("❌ Proporciona tu nombre o marca la denuncia como anónima.", "error")
            return redirect(url_for("denunciar_servicio", tipo=tipo))

        if not descripcion or not direccion:
            flash("❌ La descripción y la dirección son campos obligatorios.", "error")
            return redirect(url_for("denunciar_servicio", tipo=tipo))

        try:
            from models import Denuncia
            denuncia = Denuncia.crear(
                usuario_email=session["user"] if not anonimo else None,
                usuario_nombre=nombre if not anonimo else "Anónimo",
                tipo=tipo,
                tipo_nombre=nombre_servicio,
                descripcion=descripcion,
                direccion=direccion,
                anonimo=anonimo
            )
            flash(
                f"✅ Tu denuncia sobre «{nombre_servicio}» fue registrada. "
                f"Folio: **{denuncia.folio}**. Daremos seguimiento en 48 horas.",
                "success"
            )
        except Exception as e:
            flash(f"❌ Error al registrar la denuncia: {str(e)}", "error")

        return redirect(url_for("servicios"))

    return render_template("denunciar.html",
                           servicio=tipo,
                           nombre_servicio=nombre_servicio,
                           tipo_formulario="denuncia",
                           stats=stats,
                           filtros=filtros,
                           tipos=NOMBRES_DENUNCIAS)

# ================================================================
# RUTAS DE ARCHIVOS SUBIDOS (FOTOS)
# ================================================================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'uploads'),
        filename
    )

# ================================================================
# RUTAS DE FOTO DE PERFIL
# ================================================================
@app.route("/mi-cuenta/foto", methods=["POST"])
@login_required
def subir_foto_perfil():
    if 'foto' not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("mi_cuenta"))

    archivo = request.files['foto']

    if archivo.filename == '':
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("mi_cuenta"))

    if not _allowed_file(archivo.filename):
        flash("Formato no permitido. Usa PNG, JPG, GIF o WEBP.", "error")
        return redirect(url_for("mi_cuenta"))

    email    = session["user"]
    usuarios = _cargar_usuarios()

    # Eliminar foto anterior si existe
    foto_anterior = usuarios.get(email, {}).get("foto_perfil", "")
    if foto_anterior:
        ruta_anterior = os.path.join(UPLOAD_FOLDER, foto_anterior)
        if os.path.exists(ruta_anterior):
            try:
                os.remove(ruta_anterior)
            except Exception:
                pass

    # Nombre único para el archivo
    ext            = archivo.filename.rsplit('.', 1)[1].lower()
    nombre_archivo = f"avatar_{uuid.uuid4().hex[:12]}.{ext}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    archivo.save(os.path.join(UPLOAD_FOLDER, nombre_archivo))

    # Guardar en usuarios.json
    usuarios[email]["foto_perfil"] = nombre_archivo
    from auth import _guardar_usuarios
    _guardar_usuarios(usuarios)
    session["foto_perfil"] = nombre_archivo

    flash("Foto de perfil actualizada correctamente.", "success")
    return redirect(url_for("mi_cuenta"))

@app.route("/mi-cuenta/foto/eliminar", methods=["POST"])
@login_required
def eliminar_foto_perfil():
    email    = session["user"]
    usuarios = _cargar_usuarios()

    foto = usuarios.get(email, {}).get("foto_perfil", "")
    if foto:
        ruta = os.path.join(UPLOAD_FOLDER, foto)
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
            except Exception:
                pass
        usuarios[email]["foto_perfil"] = ""
        from auth import _guardar_usuarios
        _guardar_usuarios(usuarios)
        session.pop("foto_perfil", None)
        flash("Foto de perfil eliminada.", "success")
    else:
        flash("No tienes foto de perfil asignada.", "info")

    return redirect(url_for("mi_cuenta"))

# ================================================================
# RUTAS DE USUARIO AUTENTICADO
# ================================================================
@app.route("/mi-cuenta")
@login_required
def mi_cuenta():
    email         = session["user"]
    usuarios      = _cargar_usuarios()
    datos_usuario = usuarios.get(email, {})

    usuario = {
        "nombre":           datos_usuario.get("nombre", ""),
        "apellidos":        datos_usuario.get("apellidos", ""),
        "nombre_completo":  datos_usuario.get("nombre_completo", ""),
        "email":            email,
        "tipo":             datos_usuario.get("tipo", "ciudadano"),
        "rol":              datos_usuario.get("rol", None),
        "telefono":         datos_usuario.get("telefono", "No registrado"),
        "cedula":           datos_usuario.get("cedula", ""),
        "fecha_nacimiento": datos_usuario.get("fecha_nacimiento", ""),
        "direccion":        datos_usuario.get("direccion", ""),
        "fecha_registro":   datos_usuario.get("fecha_registro", ""),
        "ultimo_acceso":    datos_usuario.get("ultimo_acceso", ""),
        "activo":           datos_usuario.get("activo", True),
        "notas_admin":      datos_usuario.get("notas_admin", ""),
        "foto_perfil":      datos_usuario.get("foto_perfil", "")
    }

    try:
        from models import Solicitud, Denuncia
        solicitudes       = Solicitud.buscar_por_usuario(email)
        solicitudes_count = len(solicitudes)

        todas_denuncias   = Denuncia.cargar_todos()
        denuncias_usuario = [d for d in todas_denuncias if d.usuario_email == email]
        denuncias_count   = len(denuncias_usuario)

        ultimas_actividades = []
        for s in sorted(solicitudes, key=lambda x: x.fecha_creacion, reverse=True)[:3]:
            ultimas_actividades.append({
                'tipo': 'solicitud', 'folio': s.folio,
                'descripcion': s.servicio_nombre,
                'estado': s.estado, 'fecha': s.fecha_creacion
            })
        for d in sorted(denuncias_usuario, key=lambda x: x.fecha_creacion, reverse=True)[:3]:
            ultimas_actividades.append({
                'tipo': 'denuncia', 'folio': d.folio,
                'descripcion': d.tipo_nombre,
                'estado': d.estado, 'fecha': d.fecha_creacion
            })
        ultimas_actividades.sort(key=lambda x: x['fecha'], reverse=True)

    except Exception as e:
        print(f"Error cargando actividades: {e}")
        solicitudes_count   = 0
        denuncias_count     = 0
        ultimas_actividades = []

    return render_template("mi_cuenta.html",
                           usuario=usuario,
                           solicitudes_count=solicitudes_count,
                           denuncias_count=denuncias_count,
                           ultimas_actividades=ultimas_actividades[:5])

@app.route("/mi-cuenta/editar", methods=["POST"])
@login_required
def editar_perfil():
    email    = session["user"]
    usuarios = _cargar_usuarios()

    if email in usuarios:
        usuarios[email]['nombre']    = request.form.get('nombre', '')
        usuarios[email]['apellidos'] = request.form.get('apellidos', '')
        usuarios[email]['telefono']  = request.form.get('telefono', '')
        usuarios[email]['direccion'] = request.form.get('direccion', '')

        from auth import _guardar_usuarios
        _guardar_usuarios(usuarios)
        session['user_name'] = f"{usuarios[email]['nombre']} {usuarios[email]['apellidos']}".strip()
        flash("✅ Perfil actualizado correctamente", "success")
    else:
        flash("❌ Error al actualizar el perfil", "error")

    return redirect(url_for("mi_cuenta"))

@app.route("/mis-solicitudes")
@login_required
def mis_solicitudes():
    try:
        from models import Solicitud
        solicitudes = Solicitud.buscar_por_usuario(session["user"])
        solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)
    except Exception as e:
        print(f"Error cargando solicitudes: {e}")
        solicitudes = []
    return render_template("mis_solicitudes.html", solicitudes=solicitudes)

@app.route("/mis-denuncias")
@login_required
def mis_denuncias():
    try:
        from models import Denuncia
        todas     = Denuncia.cargar_todos()
        denuncias = [d for d in todas if d.usuario_email == session["user"]]
        denuncias.sort(key=lambda x: x.fecha_creacion, reverse=True)
    except Exception as e:
        print(f"Error cargando denuncias: {e}")
        denuncias = []
    return render_template("mis_denuncias.html", denuncias=denuncias)

# ================================================================
# MIS TRÁMITES (solicitudes + denuncias unificadas)
# ================================================================
@app.route("/mis-tramites")
@login_required
def mis_tramites():
    """Página unificada: muestra solicitudes y denuncias del usuario."""
    email    = session["user"]
    tramites = []

    # Solicitudes
    try:
        from models import Solicitud
        for s in Solicitud.buscar_por_usuario(email):
            item = _objeto_a_dict(s)
            item['tipo'] = 'solicitud'
            item.setdefault('comentarios_admin', [])
            item.setdefault('servicio_nombre', '')
            item.setdefault('tipo_nombre', '')
            item.setdefault('descripcion', '')
            item.setdefault('estado', 'pendiente')
            item.setdefault('folio', '')
            item.setdefault('fecha_creacion', '')
            tramites.append(item)
    except Exception as e:
        print(f"[mis_tramites] Error cargando solicitudes: {e}")

    # Denuncias
    try:
        from models import Denuncia
        for d in Denuncia.cargar_todos():
            if d.usuario_email == email:
                item = _objeto_a_dict(d)
                item['tipo'] = 'denuncia'
                item.setdefault('comentarios_admin', [])
                item.setdefault('servicio_nombre', '')
                item.setdefault('tipo_nombre', '')
                item.setdefault('descripcion', '')
                item.setdefault('estado', 'pendiente')
                item.setdefault('folio', '')
                item.setdefault('fecha_creacion', '')
                item.setdefault('direccion', '')
                tramites.append(item)
    except Exception as e:
        print(f"[mis_tramites] Error cargando denuncias: {e}")

    # Ordenar más recientes primero
    tramites.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)

    # Stats
    estados_proceso    = {'pendiente', 'en_proceso', 'en_investigacion'}
    estados_completado = {'completado', 'resuelto'}
    stats = {
        'solicitudes': sum(1 for t in tramites if t['tipo'] == 'solicitud'),
        'denuncias':   sum(1 for t in tramites if t['tipo'] == 'denuncia'),
        'pendientes':  sum(1 for t in tramites if t.get('estado') in estados_proceso),
        'completados': sum(1 for t in tramites if t.get('estado') in estados_completado),
    }

    # Serializar de forma segura
    tramites_json = json.dumps(tramites, ensure_ascii=False, default=str)

    return render_template(
        "mis_tramites.html",
        tramites=tramites,
        tramites_json=tramites_json,
        stats=stats
    )

# ================================================================
# API DE MENSAJES EN TRÁMITES
# ================================================================
@app.route("/api/tramite/<folio>/mensaje", methods=["POST"])
@login_required
def api_enviar_mensaje_ciudadano(folio):
    try:
        data  = request.get_json()
        texto = (data.get("texto") or "").strip()

        if not texto or len(texto) < 3:
            return jsonify({"error": "El mensaje no puede estar vacío."}), 400
        if len(texto) > 500:
            return jsonify({"error": "Máximo 500 caracteres."}), 400

        email  = session["user"]
        nombre = session.get("user_name", email)
        ahora  = datetime.now().isoformat()

        from models import Solicitud, Denuncia

        evento = {
            "fecha":       ahora,
            "tipo":        "mensaje_ciudadano",
            "descripcion": texto,
            "usuario":     email,
            "nombre":      nombre
        }

        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == email:
                if not isinstance(getattr(s, 'historial', None), list):
                    s.historial = []
                s.historial.append(evento)
                s.fecha_actualizacion = ahora
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                return jsonify({"success": True, "mensaje": evento})

        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == email:
                if not isinstance(getattr(d, 'historial', None), list):
                    d.historial = []
                d.historial.append(evento)
                d.fecha_actualizacion = ahora
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                return jsonify({"success": True, "mensaje": evento})

        return jsonify({"error": "Trámite no encontrado."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================================
# API PARA DOCUMENTOS EN TRÁMITES
# ================================================================
@app.route("/api/tramite/<folio>/documentos", methods=["POST"])
@login_required
def api_subir_documento(folio):
    """
    Subir un documento a un trámite (solicitud o denuncia)
    """
    try:
        if 'archivo' not in request.files:
            return jsonify({"success": False, "error": "No se envió ningún archivo"}), 400
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            return jsonify({"success": False, "error": "Nombre de archivo vacío"}), 400
        
        if not _allowed_document(archivo.filename):
            return jsonify({"success": False, "error": "Tipo de archivo no permitido. Usa PDF, JPG, PNG, DOC, DOCX"}), 400
        
        # Verificar tamaño
        archivo.seek(0, os.SEEK_END)
        size = archivo.tell()
        archivo.seek(0)
        if size > DOCS_MAX_SIZE_MB * 1024 * 1024:
            return jsonify({"success": False, "error": f"El archivo excede el límite de {DOCS_MAX_SIZE_MB} MB"}), 400
        
        email = session["user"]
        from models import Solicitud, Denuncia
        
        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == email:
                # Verificar límite de documentos
                if not hasattr(s, 'documentos'):
                    s.documentos = []
                if len(s.documentos) >= DOCS_MAX_POR_TRAMITE:
                    return jsonify({"success": False, "error": f"Límite de {DOCS_MAX_POR_TRAMITE} documentos alcanzado"}), 400
                
                # Guardar archivo
                ext = archivo.filename.rsplit('.', 1)[1].lower()
                nombre_seguro = secure_filename(archivo.filename)
                nombre_unico = f"doc_{folio}_{uuid.uuid4().hex[:8]}.{ext}"
                
                os.makedirs(DOCS_FOLDER, exist_ok=True)
                ruta = os.path.join(DOCS_FOLDER, nombre_unico)
                archivo.save(ruta)
                
                # Crear registro del documento
                documento = {
                    "id": str(uuid.uuid4()),
                    "nombre": nombre_seguro,
                    "archivo": nombre_unico,
                    "extension": ext,
                    "tamaño": size,
                    "fecha": datetime.now().isoformat(),
                    "subido_por": email
                }
                
                s.documentos.append(documento)
                s.fecha_actualizacion = datetime.now().isoformat()
                
                # Agregar al historial
                if not hasattr(s, 'historial'):
                    s.historial = []
                s.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento",
                    "descripcion": f"Documento adjunto: {nombre_seguro}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                
                return jsonify({
                    "success": True,
                    "documento": documento,
                    "restantes": DOCS_MAX_POR_TRAMITE - len(s.documentos)
                })
        
        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == email:
                if not hasattr(d, 'documentos'):
                    d.documentos = []
                if len(d.documentos) >= DOCS_MAX_POR_TRAMITE:
                    return jsonify({"success": False, "error": f"Límite de {DOCS_MAX_POR_TRAMITE} documentos alcanzado"}), 400
                
                ext = archivo.filename.rsplit('.', 1)[1].lower()
                nombre_seguro = secure_filename(archivo.filename)
                nombre_unico = f"doc_{folio}_{uuid.uuid4().hex[:8]}.{ext}"
                
                os.makedirs(DOCS_FOLDER, exist_ok=True)
                ruta = os.path.join(DOCS_FOLDER, nombre_unico)
                archivo.save(ruta)
                
                documento = {
                    "id": str(uuid.uuid4()),
                    "nombre": nombre_seguro,
                    "archivo": nombre_unico,
                    "extension": ext,
                    "tamaño": size,
                    "fecha": datetime.now().isoformat(),
                    "subido_por": email
                }
                
                d.documentos.append(documento)
                d.fecha_actualizacion = datetime.now().isoformat()
                
                if not hasattr(d, 'historial'):
                    d.historial = []
                d.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento",
                    "descripcion": f"Documento adjunto: {nombre_seguro}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                
                return jsonify({
                    "success": True,
                    "documento": documento,
                    "restantes": DOCS_MAX_POR_TRAMITE - len(d.documentos)
                })
        
        return jsonify({"success": False, "error": "Trámite no encontrado"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tramite/<folio>/documentos/<doc_id>", methods=["DELETE"])
@login_required
def api_eliminar_documento(folio, doc_id):
    """
    Eliminar un documento de un trámite
    """
    try:
        email = session["user"]
        from models import Solicitud, Denuncia
        
        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == email:
                if not hasattr(s, 'documentos'):
                    return jsonify({"success": False, "error": "Sin documentos"}), 404
                
                # Buscar el documento
                documento = None
                for doc in s.documentos:
                    if doc.get('id') == doc_id:
                        documento = doc
                        break
                
                if not documento:
                    return jsonify({"success": False, "error": "Documento no encontrado"}), 404
                
                # Eliminar archivo físico
                ruta = os.path.join(DOCS_FOLDER, documento['archivo'])
                if os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                    except:
                        pass
                
                # Eliminar de la lista
                s.documentos = [d for d in s.documentos if d.get('id') != doc_id]
                s.fecha_actualizacion = datetime.now().isoformat()
                
                # Agregar al historial
                if not hasattr(s, 'historial'):
                    s.historial = []
                s.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento_eliminado",
                    "descripcion": f"Documento eliminado: {documento.get('nombre', '')}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                
                return jsonify({"success": True})
        
        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == email:
                if not hasattr(d, 'documentos'):
                    return jsonify({"success": False, "error": "Sin documentos"}), 404
                
                documento = None
                for doc in d.documentos:
                    if doc.get('id') == doc_id:
                        documento = doc
                        break
                
                if not documento:
                    return jsonify({"success": False, "error": "Documento no encontrado"}), 404
                
                ruta = os.path.join(DOCS_FOLDER, documento['archivo'])
                if os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                    except:
                        pass
                
                d.documentos = [doc for doc in d.documentos if doc.get('id') != doc_id]
                d.fecha_actualizacion = datetime.now().isoformat()
                
                if not hasattr(d, 'historial'):
                    d.historial = []
                d.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento_eliminado",
                    "descripcion": f"Documento eliminado: {documento.get('nombre', '')}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                
                return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Trámite no encontrado"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ================================================================
# API DE NOTIFICACIONES (para la campana)
# ================================================================
@app.route("/api/notificaciones")
@login_required
def api_notificaciones_usuario():
    """
    Obtiene las notificaciones del usuario (últimos eventos)
    """
    try:
        email = session["user"]
        from models import Solicitud, Denuncia, Cita
        
        notificaciones = []
        
        # Buscar en solicitudes
        solicitudes = Solicitud.buscar_por_usuario(email)
        for s in solicitudes:
            if hasattr(s, 'historial') and s.historial:
                # Tomar los últimos 3 eventos de cada trámite
                ultimos = sorted(s.historial, key=lambda x: x.get('fecha', ''), reverse=True)[:3]
                for ev in ultimos:
                    notificaciones.append({
                        "folio": s.folio,
                        "tipo": 'solicitud',
                        "servicio": s.servicio_nombre if hasattr(s, 'servicio_nombre') else 'Solicitud',
                        "fecha": ev.get('fecha', s.fecha_creacion),
                        "ultimo_tipo": ev.get('tipo', 'actividad'),
                        "descripcion": ev.get('descripcion', '')[:60],
                        "estado": s.estado
                    })
        
        # Buscar en denuncias
        todas_denuncias = Denuncia.cargar_todos()
        denuncias = [d for d in todas_denuncias if d.usuario_email == email]
        for d in denuncias:
            if hasattr(d, 'historial') and d.historial:
                ultimos = sorted(d.historial, key=lambda x: x.get('fecha', ''), reverse=True)[:3]
                for ev in ultimos:
                    notificaciones.append({
                        "folio": d.folio,
                        "tipo": 'denuncia',
                        "servicio": d.tipo_nombre if hasattr(d, 'tipo_nombre') else 'Denuncia',
                        "fecha": ev.get('fecha', d.fecha_creacion),
                        "ultimo_tipo": ev.get('tipo', 'actividad'),
                        "descripcion": ev.get('descripcion', '')[:60],
                        "estado": d.estado
                    })
        
        # Buscar en citas
        citas = Cita.buscar_por_usuario(email)
        for c in citas:
            # Agregar notificación para citas próximas
            if hasattr(c, 'fecha') and c.fecha:
                notificaciones.append({
                    "folio": c.folio,
                    "tipo": 'cita',
                    "servicio": SERVICIOS_CITAS.get(c.servicio, c.servicio),
                    "fecha": c.fecha_creacion if hasattr(c, 'fecha_creacion') else datetime.now().isoformat(),
                    "ultimo_tipo": 'cita_programada',
                    "descripcion": f"Cita para {c.fecha} a las {c.hora}",
                    "estado": c.estado
                })
        
        # Ordenar por fecha (más reciente primero)
        notificaciones.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        return jsonify({"items": notificaciones[:10]})  # Solo las 10 más recientes
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# SERVIDOR DE DOCUMENTOS
# ================================================================
@app.route('/uploads/documentos/<path:filename>')
@login_required
def uploaded_documento(filename):
    """
    Servir documentos (solo usuarios autenticados)
    """
    email = session["user"]
    
    # Verificar que el archivo pertenece al usuario
    from models import Solicitud, Denuncia
    autorizado = False

    for s in Solicitud.cargar_todos():
        if s.usuario_email == email:
            for doc in (getattr(s, 'documentos', []) or []):
                if doc.get('archivo') == filename:
                    autorizado = True
                    break

    if not autorizado:
        for d in Denuncia.cargar_todos():
            if d.usuario_email == email:
                for doc in (getattr(d, 'documentos', []) or []):
                    if doc.get('archivo') == filename:
                        autorizado = True
                        break

    # Admin puede ver todos
    if session.get('is_admin'):
        autorizado = True

    if not autorizado:
        flash("No tienes permiso para ver ese archivo.", "error")
        return redirect(url_for('mis_tramites'))

    return send_from_directory(
        os.path.join(app.root_path, DOCS_FOLDER),
        filename
    )

# ================================================================
# SISTEMA DE CITAS / TURNOS EN LÍNEA
# ================================================================
# Importar modelo de Cita
try:
    from models.cita import Cita
except ImportError:
    # Si el modelo no existe, definimos una clase temporal
    class Cita:
        ESTADOS = ['pendiente', 'confirmada', 'cancelada', 'completada']
        
        @staticmethod
        def crear(usuario_email, usuario_nombre, servicio, fecha, hora, motivo=""):
            from models import BaseModel
            cita = BaseModel.crear('cita', {
                'usuario_email': usuario_email,
                'usuario_nombre': usuario_nombre,
                'servicio': servicio,
                'fecha': fecha,
                'hora': hora,
                'motivo': motivo,
                'estado': 'pendiente',
                'notas_admin': ''
            })
            return cita
        
        @staticmethod
        def buscar_por_usuario(email):
            from models import BaseModel
            return BaseModel.buscar_por('cita', 'usuario_email', email)
        
        @staticmethod
        def buscar_por_id(cita_id):
            from models import BaseModel
            return BaseModel.buscar_por_id('cita', cita_id)
        
        @staticmethod
        def cargar_todos():
            from models import BaseModel
            return BaseModel.cargar_todos('cita')
        
        @staticmethod
        def guardar_todos(citas):
            from models import BaseModel
            return BaseModel.guardar_todos('cita', citas)
        
        @staticmethod
        def horarios_disponibles(servicio, fecha):
            # Horarios predeterminados (9 AM a 5 PM, cada hora)
            todos_horarios = [f"{h:02d}:00" for h in range(9, 18)]
            
            # Obtener citas existentes para esa fecha y servicio
            citas = Cita.cargar_todos()
            citas_ocupadas = [
                c.hora for c in citas 
                if c.servicio == servicio and c.fecha == fecha 
                and c.estado in ['pendiente', 'confirmada']
            ]
            
            # Filtrar horarios disponibles
            disponibles = [h for h in todos_horarios if h not in citas_ocupadas]
            return disponibles

@app.route("/citas/solicitar", methods=["GET", "POST"])
@login_required
def solicitar_cita():
    """Formulario para solicitar una cita"""
    if request.method == "POST":
        servicio = request.form.get("servicio")
        fecha = request.form.get("fecha")
        hora = request.form.get("hora")
        motivo = request.form.get("motivo", "").strip()
        
        if not servicio or not fecha or not hora:
            flash("❌ Completa todos los campos obligatorios.", "error")
            return redirect(url_for("solicitar_cita"))
        
        try:
            cita = Cita.crear(
                usuario_email=session["user"],
                usuario_nombre=session.get("user_name", "Ciudadano"),
                servicio=servicio,
                fecha=fecha,
                hora=hora,
                motivo=motivo
            )
            flash(
                f"✅ ¡Cita solicitada con éxito! Tu folio es: **{cita.folio}**. "
                f"Te confirmaremos por correo.",
                "success"
            )
            return redirect(url_for("mis_citas"))
        except Exception as e:
            flash(f"❌ Error al solicitar cita: {str(e)}", "error")
            return redirect(url_for("solicitar_cita"))
    
    # GET: mostrar formulario
    return render_template("citas/solicitar_cita.html", servicios=SERVICIOS_CITAS)

@app.route("/api/horarios-disponibles")
@login_required
def api_horarios_disponibles():
    """API para obtener horarios disponibles de una fecha"""
    servicio = request.args.get("servicio")
    fecha = request.args.get("fecha")
    
    if not servicio or not fecha:
        return jsonify({"error": "Faltan parámetros"}), 400
    
    try:
        disponibles = Cita.horarios_disponibles(servicio, fecha)
        return jsonify({"disponibles": disponibles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/mis-citas")
@login_required
def mis_citas():
    """Listado de citas del usuario"""
    citas = Cita.buscar_por_usuario(session["user"])
    # Ordenar por fecha (más recientes primero)
    citas.sort(key=lambda x: x.fecha + ' ' + x.hora, reverse=True)
    
    # Convertir a diccionario para el template
    citas_dict = []
    for c in citas:
        c_dict = _objeto_a_dict(c)
        c_dict['servicio_nombre'] = SERVICIOS_CITAS.get(c.servicio, c.servicio)
        citas_dict.append(c_dict)
    
    return render_template("citas/mis_citas.html", citas=citas_dict)

@app.route("/citas/<cita_id>/cancelar", methods=["POST"])
@login_required
def cancelar_cita(cita_id):
    """Cancelar una cita"""
    cita = Cita.buscar_por_id(cita_id)
    if not cita or cita.usuario_email != session["user"]:
        flash("❌ Cita no encontrada.", "error")
        return redirect(url_for("mis_citas"))
    
    cita.estado = 'cancelada'
    citas = Cita.cargar_todos()
    for i, c in enumerate(citas):
        if c.id == cita_id:
            citas[i] = cita
            break
    Cita.guardar_todos(citas)
    
    flash("✅ Cita cancelada correctamente.", "success")
    return redirect(url_for("mis_citas"))

# ================================================================
# MAPA DE INCIDENCIAS
# ================================================================
@app.route("/mapa")
@login_required
def mapa_incidencias():
    """Mapa público de denuncias (ciudadanos ven sus denuncias)"""
    from models import Denuncia
    
    # Si es admin, ve todas
    if session.get('is_admin'):
        denuncias = Denuncia.cargar_todos()
    else:
        # Ciudadano solo ve sus denuncias
        todas = Denuncia.cargar_todos()
        denuncias = [d for d in todas if d.usuario_email == session["user"]]
    
    # Filtrar solo las que tienen coordenadas
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    
    return render_template("mapa.html", 
                          denuncias=denuncias_geo,
                          tipos=NOMBRES_DENUNCIAS)

@app.route("/admin/mapa")
@admin_required
def admin_mapa_incidencias():
    """Mapa administrativo con todas las denuncias"""
    from models import Denuncia
    
    denuncias = Denuncia.cargar_todos()
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    
    return render_template("admin/mapa_admin.html", 
                          denuncias=denuncias_geo,
                          tipos=NOMBRES_DENUNCIAS,
                          stats={
                              'total': len(denuncias),
                              'geolocalizadas': len(denuncias_geo),
                              'pendientes': len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
                          })

@app.route("/api/denuncias/geojson")
@login_required
def api_denuncias_geojson():
    """API que devuelve las denuncias en formato GeoJSON para el mapa"""
    from models import Denuncia
    
    if session.get('is_admin'):
        denuncias = Denuncia.cargar_todos()
    else:
        todas = Denuncia.cargar_todos()
        denuncias = [d for d in todas if d.usuario_email == session["user"]]
    
    # Filtrar geolocalizadas
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    
    features = []
    for d in denuncias_geo:
        # Color según estado
        color = {
            'pendiente': '#f59e0b',
            'en_investigacion': '#3b82f6',
            'resuelto': '#10b981',
            'rechazado': '#ef4444'
        }.get(d.estado, '#6b7280')
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [d.longitud, d.latitud]
            },
            "properties": {
                "id": d.id,
                "folio": d.folio,
                "tipo": d.tipo,
                "tipo_nombre": NOMBRES_DENUNCIAS.get(d.tipo, d.tipo),
                "descripcion": d.descripcion[:100] + "..." if len(d.descripcion) > 100 else d.descripcion,
                "direccion": d.direccion,
                "fecha": d.fecha_creacion[:10],
                "estado": d.estado,
                "anonimo": getattr(d, 'anonimo', False),
                "usuario": "Anónimo" if getattr(d, 'anonimo', False) else d.usuario_nombre,
                "color": color,
                "url": url_for('admin.detalle_denuncia', denuncia_id=d.id) if session.get('is_admin') else "#"
            }
        })
    
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

# ================================================================
# API PARA GEOLOCALIZACIÓN (usando Nominatim/OpenStreetMap)
# ================================================================
@app.route("/api/geocodificar", methods=["POST"])
@admin_required
def api_geocodificar():
    """Convierte una dirección en coordenadas usando Nominatim"""
    try:
        data = request.get_json()
        direccion = data.get('direccion')
        denuncia_id = data.get('denuncia_id')
        
        if not direccion:
            return jsonify({"error": "Dirección requerida"}), 400
        
        import requests
        from urllib.parse import quote
        
        # Usar Nominatim de OpenStreetMap (gratuito)
        url = f"https://nominatim.openstreetmap.org/search?q={quote(direccion)}&format=json&limit=1"
        
        # IMPORTANTE: Agregar User-Agent con tu email
        headers = {
            'User-Agent': 'VillaCutupuApp/1.0 (contacto@cutupu.gob.do)'
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            
            # Si hay denuncia_id, actualizar la denuncia
            if denuncia_id:
                from models import Denuncia
                denuncias = Denuncia.cargar_todos()
                for i, d in enumerate(denuncias):
                    if str(d.id) == str(denuncia_id):
                        d.latitud = lat
                        d.longitud = lon
                        d.geolocalizada = True
                        denuncias[i] = d
                        break
                Denuncia.guardar_todos(denuncias)
            
            return jsonify({
                "success": True,
                "latitud": lat,
                "longitud": lon,
                "display_name": data[0].get('display_name', direccion)
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo encontrar la dirección"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================================
# PLANTILLAS DE RESPUESTA RÁPIDA
# ================================================================
from models.plantilla import Plantilla

@app.route("/admin/plantillas")
@admin_required
def admin_plantillas():
    """Gestión de plantillas de respuesta"""
    plantillas = Plantilla.cargar_todos()
    
    # Agrupar por categoría
    por_categoria = {}
    for p in plantillas:
        if p.categoria not in por_categoria:
            por_categoria[p.categoria] = []
        por_categoria[p.categoria].append(p)
    
    return render_template("admin/plantillas.html", 
                          plantillas=plantillas,
                          por_categoria=por_categoria,
                          categorias=Plantilla.CATEGORIAS)

@app.route("/admin/plantillas/crear", methods=["POST"])
@admin_required
def admin_crear_plantilla():
    """Crea una nueva plantilla"""
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    contenido = request.form.get("contenido")
    variables = request.form.getlist("variables") or ['folio', 'nombre', 'fecha']
    
    if not nombre or not contenido:
        flash("❌ Nombre y contenido son obligatorios.", "error")
        return redirect(url_for("admin_plantillas"))
    
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
    return redirect(url_for("admin_plantillas"))

@app.route("/admin/plantillas/<plantilla_id>/editar", methods=["POST"])
@admin_required
def admin_editar_plantilla(plantilla_id):
    """Edita una plantilla existente"""
    plantilla = Plantilla.buscar_por_id(plantilla_id)
    if not plantilla:
        flash("❌ Plantilla no encontrada.", "error")
        return redirect(url_for("admin_plantillas"))
    
    plantilla.nombre = request.form.get("nombre")
    plantilla.categoria = request.form.get("categoria")
    plantilla.contenido = request.form.get("contenido")
    plantilla.variables = request.form.getlist("variables") or ['folio', 'nombre', 'fecha']
    
    plantillas = Plantilla.cargar_todos()
    for i, p in enumerate(plantillas):
        if p.id == plantilla_id:
            plantillas[i] = plantilla
            break
    Plantilla.guardar_todos(plantillas)
    
    flash(f"✅ Plantilla '{plantilla.nombre}' actualizada.", "success")
    return redirect(url_for("admin_plantillas"))

@app.route("/admin/plantillas/<plantilla_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_plantilla(plantilla_id):
    """Activa/desactiva una plantilla"""
    plantilla = Plantilla.buscar_por_id(plantilla_id)
    if not plantilla:
        flash("❌ Plantilla no encontrada.", "error")
        return redirect(url_for("admin_plantillas"))
    
    plantilla.activa = not plantilla.activa
    
    plantillas = Plantilla.cargar_todos()
    for i, p in enumerate(plantillas):
        if p.id == plantilla_id:
            plantillas[i] = plantilla
            break
    Plantilla.guardar_todos(plantillas)
    
    estado = "activada" if plantilla.activa else "desactivada"
    flash(f"✅ Plantilla '{plantilla.nombre}' {estado}.", "success")
    return redirect(url_for("admin_plantillas"))

@app.route("/admin/plantillas/<plantilla_id>/eliminar", methods=["POST"])
@admin_required
def admin_eliminar_plantilla(plantilla_id):
    """Elimina una plantilla"""
    plantillas = Plantilla.cargar_todos()
    plantillas = [p for p in plantillas if p.id != plantilla_id]
    Plantilla.guardar_todos(plantillas)
    
    flash("✅ Plantilla eliminada.", "success")
    return redirect(url_for("admin_plantillas"))

@app.route("/api/plantillas/<categoria>")
@admin_required
def api_plantillas_por_categoria(categoria):
    """API para obtener plantillas por categoría"""
    plantillas = Plantilla.buscar_por_categoria(categoria)
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'contenido': p.contenido,
        'variables': p.variables
    } for p in plantillas])

@app.route("/api/plantillas/<plantilla_id>/procesar", methods=["POST"])
@admin_required
def api_procesar_plantilla(plantilla_id):
    """Procesa una plantilla con variables"""
    plantilla = Plantilla.buscar_por_id(plantilla_id)
    if not plantilla:
        return jsonify({"error": "Plantilla no encontrada"}), 404
    
    data = request.get_json()
    contenido = plantilla.procesar(**data)
    plantilla.incrementar_uso()
    
    return jsonify({"contenido": contenido})

# ================================================================
# ADMIN: GESTIÓN DE CITAS (ya está arriba, pero unificamos)
# ================================================================
# Las rutas de admin/citas ya están definidas arriba en la sección de citas

# ================================================================
# ENCUESTAS DE SATISFACCIÓN
# ================================================================
try:
    from models.encuesta import Encuesta
except ImportError:
    # Si el modelo no existe, definimos una clase temporal
    class Encuesta:
        @staticmethod
        def crear(folio_tramite, tipo_tramite, usuario_email, usuario_nombre, calificacion, comentario=""):
            from models import BaseModel
            encuesta = BaseModel.crear('encuesta', {
                'folio_tramite': folio_tramite,
                'tipo_tramite': tipo_tramite,
                'usuario_email': usuario_email,
                'usuario_nombre': usuario_nombre,
                'calificacion': calificacion,
                'comentario': comentario,
                'fecha': datetime.now().isoformat()
            })
            return encuesta
        
        @staticmethod
        def buscar_por_tramite(folio_tramite):
            from models import BaseModel
            return BaseModel.buscar_por('encuesta', 'folio_tramite', folio_tramite)
        
        @staticmethod
        def obtener_estadisticas():
            from models import BaseModel
            encuestas = BaseModel.cargar_todos('encuesta')
            
            if not encuestas:
                return {
                    'total': 0,
                    'promedio': 0,
                    'por_calificacion': {1:0, 2:0, 3:0, 4:0, 5:0},
                    'por_tipo': {'solicitud':0, 'denuncia':0, 'cita':0},
                    'ultimas': []
                }
            
            total = len(encuestas)
            suma = sum(e.calificacion for e in encuestas)
            
            # Calcular distribución por calificación
            por_calificacion = {1:0, 2:0, 3:0, 4:0, 5:0}
            for e in encuestas:
                if e.calificacion in por_calificacion:
                    por_calificacion[e.calificacion] += 1
            
            # Calcular por tipo de trámite
            por_tipo = {'solicitud':0, 'denuncia':0, 'cita':0}
            for e in encuestas:
                if e.tipo_tramite in por_tipo:
                    por_tipo[e.tipo_tramite] += 1
            
            # Últimas 10 encuestas
            ultimas = sorted(encuestas, key=lambda x: x.fecha, reverse=True)[:10]
            ultimas_dict = []
            for e in ultimas:
                e_dict = _objeto_a_dict(e)
                ultimas_dict.append(e_dict)
            
            return {
                'total': total,
                'promedio': round(suma / total, 1),
                'por_calificacion': por_calificacion,
                'por_tipo': por_tipo,
                'ultimas': ultimas_dict
            }

@app.route("/tramite/<folio>/encuesta", methods=["GET", "POST"])
@login_required
def encuesta_tramite(folio):
    """Formulario de encuesta para un trámite completado"""
    from models import Solicitud, Denuncia, Cita
    
    # Verificar que el trámite existe y pertenece al usuario
    tramite = None
    tipo = None
    
    # Buscar en solicitudes
    for s in Solicitud.buscar_por_usuario(session["user"]):
        if s.folio == folio:
            tramite = s
            tipo = 'solicitud'
            break
    
    # Buscar en denuncias
    if not tramite:
        for d in Denuncia.cargar_todos():
            if d.folio == folio and d.usuario_email == session["user"]:
                tramite = d
                tipo = 'denuncia'
                break
    
    # Buscar en citas
    if not tramite:
        for c in Cita.buscar_por_usuario(session["user"]):
            if c.folio == folio:
                tramite = c
                tipo = 'cita'
                break
    
    if not tramite:
        flash("❌ Trámite no encontrado.", "error")
        return redirect(url_for("mis_tramites"))
    
    # Verificar que el trámite está completado
    estados_completados = ['completado', 'resuelto', 'completada']
    if tramite.estado not in estados_completados:
        flash("❌ Solo puedes evaluar trámites completados.", "error")
        return redirect(url_for("mis_tramites"))
    
    # Verificar si ya respondió
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
            tipo_tramite=tipo,
            usuario_email=session["user"],
            usuario_nombre=session.get("user_name", "Ciudadano"),
            calificacion=calif_int,
            comentario=comentario
        )
        
        flash("✅ ¡Gracias por tu evaluación! Tu opinión nos ayuda a mejorar.", "success")
        return redirect(url_for("mis_tramites"))
    
    # GET: mostrar formulario
    nombre_servicio = ""
    if hasattr(tramite, 'servicio_nombre'):
        nombre_servicio = tramite.servicio_nombre
    elif hasattr(tramite, 'tipo_nombre'):
        nombre_servicio = tramite.tipo_nombre
    elif hasattr(tramite, 'servicio'):
        nombre_servicio = SERVICIOS_CITAS.get(tramite.servicio, tramite.servicio)
    
    return render_template("encuestas/encuesta.html", 
                          tramite=tramite, 
                          tipo=tipo,
                          nombre_servicio=nombre_servicio,
                          folio=folio)

# ================================================================
# ADMIN: ESTADÍSTICAS DE ENCUESTAS
# ================================================================
@app.route("/admin/encuestas")
@admin_required
def admin_encuestas():
    """Panel admin con estadísticas de satisfacción"""
    stats = Encuesta.obtener_estadisticas()
    return render_template("admin/encuestas.html", stats=stats)

# ================================================================
# API PARA ADMIN: CITAS PENDIENTES (para el badge)
# ================================================================
@app.route("/api/admin/citas-pendientes")
@admin_required
def api_admin_citas_pendientes():
    """API para obtener el número de citas pendientes"""
    try:
        from models import Cita
        citas = Cita.cargar_todos()
        pendientes = len([c for c in citas if c.estado == 'pendiente'])
        return jsonify({"count": pendientes})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)}), 500

# ================================================================
# APIs GENERALES
# ================================================================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard_redirect():
    return redirect(url_for("admin.dashboard"))

@app.route("/admin-panel")
@admin_required
def admin_panel():
    return redirect(url_for("admin.dashboard"))

@app.route("/api/tramite/<folio>")
@login_required
def api_tramite(folio):
    try:
        from models import Solicitud, Denuncia

        for s in Solicitud.cargar_todos():
            if s.folio == folio and s.usuario_email == session["user"]:
                tramite = s.to_dict() if hasattr(s, 'to_dict') else _objeto_a_dict(s)
                tramite['tipo'] = 'solicitud'
                return jsonify(tramite)

        for d in Denuncia.cargar_todos():
            if d.folio == folio and d.usuario_email == session["user"]:
                tramite = d.to_dict() if hasattr(d, 'to_dict') else _objeto_a_dict(d)
                tramite['tipo'] = 'denuncia'
                return jsonify(tramite)

        return jsonify({'error': 'Trámite no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/tramite/<folio>/responder", methods=["POST"])
@login_required
def api_responder_tramite(folio):
    try:
        data         = request.get_json()
        respuesta    = data.get('respuesta')
        nuevo_estado = data.get('estado')

        from models import Solicitud, Denuncia

        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == session["user"]:
                if not hasattr(s, 'historial'):
                    s.historial = []
                s.historial.append({
                    'fecha': datetime.now().isoformat(),
                    'usuario': session["user"],
                    'tipo': 'respuesta',
                    'descripcion': respuesta
                })
                s.estado              = nuevo_estado
                s.fecha_actualizacion = datetime.now().isoformat()
                solicitudes[i]        = s
                Solicitud.guardar_todos(solicitudes)
                return jsonify({'success': True, 'message': 'Respuesta enviada'})

        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == session["user"]:
                if not hasattr(d, 'historial'):
                    d.historial = []
                d.historial.append({
                    'fecha': datetime.now().isoformat(),
                    'usuario': session["user"],
                    'tipo': 'respuesta',
                    'descripcion': respuesta
                })
                d.estado              = nuevo_estado
                d.fecha_actualizacion = datetime.now().isoformat()
                denuncias[i]          = d
                Denuncia.guardar_todos(denuncias)
                return jsonify({'success': True, 'message': 'Respuesta enviada'})

        return jsonify({'error': 'Trámite no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/admin/api/notificaciones")
@admin_required
def api_notificaciones_admin():
    try:
        from models import Solicitud, Denuncia
        sp = len([s for s in Solicitud.cargar_todos() if s.estado == 'pendiente'])
        dp = len([d for d in Denuncia.cargar_todos()  if d.estado == 'pendiente'])
        return jsonify({
            'count': sp + dp,
            'notifications': [
                {'icon': 'fa-file-alt',            'message': f'{sp} solicitudes pendientes', 'time': 'Ahora', 'read': False},
                {'icon': 'fa-exclamation-triangle', 'message': f'{dp} denuncias pendientes',   'time': 'Ahora', 'read': False},
            ]
        })
    except:
        return jsonify({'count': 0, 'notifications': []})

# ================================================================
# ERROR HANDLERS
# ================================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

# ================================================================
# ARRANQUE
# ================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 SISTEMA MUNICIPAL VILLA CUTUPÚ")
    print("=" * 50)
    print("✅ Blueprint 'auth' registrado")
    print("✅ Blueprint 'admin' registrado")
    print("✅ Configuración de uploads lista")
    print("=" * 50)
    print("📌 Rutas principales:")
    print("   /                → index")
    print("   /login           → login")
    print("   /registro        → registro")
    print("   /admin           → panel admin")
    print("   /mi-cuenta       → perfil (con foto)")
    print("   /mis-tramites    → tramites unificados")
    print("   /citas/solicitar → solicitar cita")
    print("   /mis-citas       → mis citas")
    print("   /admin/citas     → admin citas")
    print("   /mapa            → mapa de incidencias (ciudadano)")
    print("   /admin/mapa      → mapa de incidencias (admin)")
    print("   /tramite/*/encuesta → encuesta satisfacción")
    print("   /admin/encuestas → estadísticas encuestas")
    print("   /admin/plantillas → plantillas de respuesta")
    print("=" * 50)
    
    # Crear carpetas de uploads si no existen
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DOCS_FOLDER, exist_ok=True)
    
    app.run(debug=True, host="0.0.0.0", port=5000)# ================================================================
# IMPORTS
# ================================================================
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from auth import auth, login_required, admin_required, _cargar_usuarios
from admin import admin_bp
import os
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

# ================================================================
# CONFIGURACIÓN INICIAL
# ================================================================
app = Flask(__name__)
app.secret_key = "clave_secreta_muy_segura_cambiar_en_produccion_123"
app.config['SESSION_TYPE'] = 'filesystem'

# Configuración para subida de archivos (fotos perfil)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB máx
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración para documentos de trámites
DOCS_FOLDER = os.path.join('static', 'uploads', 'documentos')
ALLOWED_DOC_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
DOCS_MAX_POR_TRAMITE = 5
DOCS_MAX_SIZE_MB = 10

app.static_folder = 'static'
app.static_url_path = '/static'

# Registrar blueprints
app.register_blueprint(auth)
app.register_blueprint(admin_bp)

# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _allowed_document(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

def _objeto_a_dict(obj):
    """Convierte un objeto o dict a dict limpio serializable."""
    if isinstance(obj, dict):
        d = dict(obj)
    elif hasattr(obj, '__dict__'):
        d = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    else:
        return {}

    # Convertir cualquier valor no serializable a string
    for k, v in d.items():
        if hasattr(v, '__dict__') or (not isinstance(v, (str, int, float, bool, list, dict, type(None)))):
            d[k] = str(v)
        elif isinstance(v, list):
            d[k] = [
                (item if isinstance(item, (str, int, float, bool, dict, type(None)))
                 else str(item))
                for item in v
            ]

    return d

def _icono_doc(filename):
    """Devuelve clase FontAwesome según extensión."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    iconos = {
        'pdf':  'fa-file-pdf',
        'doc':  'fa-file-word',
        'docx': 'fa-file-word',
        'jpg':  'fa-file-image',
        'jpeg': 'fa-file-image',
        'png':  'fa-file-image',
    }
    return iconos.get(ext, 'fa-file')

# ================================================================
# CATÁLOGO DE SERVICIOS
# ================================================================
NOMBRES_SERVICIOS = {
    "funeraria":     "Funerarias Municipales",
    "uso-suelo":     "Certificado de Uso de Suelo",
    "oaim":          "Oficina de Acceso a la Información (OAI/M)",
    "planeamiento":  "Planeamiento Urbano",
    "ornato":        "Ornato y Préstamos de Áreas",
    "catastro":      "Catastro Municipal",
    "aseo-comercial":"Gestión Comercial de Aseo",
}

NOMBRES_DENUNCIAS = {
    "policia":  "Policía Municipal",
    "limpieza": "Limpieza y Cuidado de la Vía Pública",
    "basura":   "Recogida de Basura",
    "alumbrado":"Alumbrado Público",
    "otro":     "Otra denuncia",
}

NOMBRES_CONSULTAS = {
    "pot": "Plan de Ordenamiento Territorial",
}

# ================================================================
# SERVICIOS PARA CITAS
# ================================================================
SERVICIOS_CITAS = {
    "asesoria-legal": "Asesoría Legal Municipal",
    "licencias": "Licencias de Funcionamiento",
    "catastro": "Trámites de Catastro",
    "registro-civil": "Registro Civil",
    "atencion-vecinal": "Atención Vecinal",
    "otro": "Otro trámite"
}

# ================================================================
# CONTEXTO GLOBAL
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
        foto_perfil=session.get("foto_perfil", "")
    )

# ================================================================
# RUTAS PÚBLICAS
# ================================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/municipio")
def municipio():
    return render_template("municipio.html")

@app.route("/servicios")
def servicios():
    return render_template("servicios.html")

@app.route("/transparencia")
def transparencia():
    return render_template("transparencia.html")

@app.route("/transparencia/estructura")
def transparencia_estructura():
    return render_template("transparencia_estructura.html")

@app.route("/transparencia/integrantes")
def transparencia_integrantes():
    return render_template("transparencia_integrantes.html")

@app.route("/transparencia/normativas")
def transparencia_normativas():
    return render_template("transparencia_normativas.html")

@app.route("/transparencia/proyectos")
def transparencia_proyectos():
    return render_template("transparencia_proyectos.html")

@app.route("/transparencia/informes")
def transparencia_informes():
    return render_template("transparencia_informes.html")

@app.route("/transparencia/datos")
def transparencia_datos():
    return render_template("transparencia_datos.html")

@app.route("/transparencia/atencion")
def transparencia_atencion():
    return render_template("transparencia_atencion.html")

@app.route("/transparencia/actas")
def transparencia_actas():
    return render_template("transparencia_actas.html")

@app.route("/transparencia/compras")
def transparencia_compras():
    return render_template("transparencia_compras.html")

@app.route("/noticias")
def noticias():
    return render_template("noticias.html")

@app.route("/contacto", methods=["GET"])
def contacto():
    return render_template("contacto.html")

@app.route("/enviar-contacto", methods=["POST"])
def enviar_contacto():
    nombre  = request.form.get("nombre", "").strip()
    email   = request.form.get("email", "").strip()
    asunto  = request.form.get("asunto", "").strip()
    mensaje = request.form.get("mensaje", "").strip()

    if not nombre or not email or not asunto or not mensaje:
        flash("❌ Todos los campos obligatorios deben completarse.", "error")
        return redirect(url_for("contacto"))

    flash(f"✅ Gracias {nombre}, tu mensaje fue enviado. Te responderemos a la brevedad.", "success")
    return redirect(url_for("contacto"))

# ================================================================
# SERVICIOS (PROTEGIDOS)
# ================================================================
@app.route("/solicitar/<servicio>", methods=["GET", "POST"])
@login_required
def solicitar_servicio(servicio):
    if servicio not in NOMBRES_SERVICIOS:
        flash("❌ El servicio solicitado no existe.", "error")
        return redirect(url_for("servicios"))

    nombre_servicio = NOMBRES_SERVICIOS[servicio]

    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        cedula      = request.form.get("cedula", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre or not cedula or not descripcion:
            flash("❌ Completa todos los campos obligatorios.", "error")
            return redirect(url_for("solicitar_servicio", servicio=servicio))

        try:
            from models import Solicitud
            solicitud = Solicitud.crear(
                usuario_email=session["user"],
                usuario_nombre=nombre,
                usuario_cedula=cedula,
                servicio_id=servicio,
                servicio_nombre=nombre_servicio,
                descripcion=descripcion
            )
            flash(
                f"✅ Tu solicitud de «{nombre_servicio}» fue enviada. "
                f"Tu folio es: **{solicitud.folio}**. Te contactaremos pronto.",
                "success"
            )
        except Exception as e:
            flash(f"❌ Error al procesar la solicitud: {str(e)}", "error")

        return redirect(url_for("servicios"))

    return render_template("solicitar.html",
                           servicio=servicio,
                           nombre_servicio=nombre_servicio,
                           tipo_formulario="solicitud")

@app.route("/consultar/<consulta>", methods=["GET", "POST"])
@login_required
def consultar_servicio(consulta):
    if consulta not in NOMBRES_CONSULTAS:
        flash("❌ La consulta solicitada no existe.", "error")
        return redirect(url_for("servicios"))

    nombre_consulta = NOMBRES_CONSULTAS[consulta]

    if request.method == "POST":
        nombre         = request.form.get("nombre", "").strip()
        consulta_texto = request.form.get("consulta", "").strip()

        if not nombre or not consulta_texto:
            flash("❌ Completa todos los campos obligatorios.", "error")
            return redirect(url_for("consultar_servicio", consulta=consulta))

        flash(
            f"✅ Tu consulta sobre «{nombre_consulta}» fue recibida. "
            f"Te responderemos en 3 días hábiles.",
            "success"
        )
        return redirect(url_for("servicios"))

    return render_template("consultar.html",
                           consulta=consulta,
                           nombre_consulta=nombre_consulta)

@app.route("/denunciar/<tipo>", methods=["GET", "POST"])
@login_required
def denunciar_servicio(tipo):
    if tipo not in NOMBRES_DENUNCIAS:
        flash("❌ El tipo de denuncia no es válido.", "error")
        return redirect(url_for("servicios"))

    nombre_servicio = NOMBRES_DENUNCIAS[tipo]

    # Calcular estadísticas para el template
    try:
        from models import Denuncia
        denuncias = Denuncia.cargar_todos()
        stats = {
            'denuncias': len(denuncias),
            'pendientes': len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']]),
            'resueltas': len([d for d in denuncias if d.estado == 'resuelto'])
        }
    except Exception as e:
        print(f"Error cargando estadísticas: {e}")
        stats = {
            'denuncias': 0,
            'pendientes': 0,
            'resueltas': 0
        }

    filtros = {
        'q': request.args.get('q', ''),
        'estado': request.args.get('estado', ''),
        'tipo': request.args.get('tipo', '')
    }

    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        direccion   = request.form.get("direccion", "").strip()
        anonimo     = request.form.get("anonimo") == "on"

        if not anonimo and not nombre:
            flash("❌ Proporciona tu nombre o marca la denuncia como anónima.", "error")
            return redirect(url_for("denunciar_servicio", tipo=tipo))

        if not descripcion or not direccion:
            flash("❌ La descripción y la dirección son campos obligatorios.", "error")
            return redirect(url_for("denunciar_servicio", tipo=tipo))

        try:
            from models import Denuncia
            denuncia = Denuncia.crear(
                usuario_email=session["user"] if not anonimo else None,
                usuario_nombre=nombre if not anonimo else "Anónimo",
                tipo=tipo,
                tipo_nombre=nombre_servicio,
                descripcion=descripcion,
                direccion=direccion,
                anonimo=anonimo
            )
            flash(
                f"✅ Tu denuncia sobre «{nombre_servicio}» fue registrada. "
                f"Folio: **{denuncia.folio}**. Daremos seguimiento en 48 horas.",
                "success"
            )
        except Exception as e:
            flash(f"❌ Error al registrar la denuncia: {str(e)}", "error")

        return redirect(url_for("servicios"))

    return render_template("denunciar.html",
                           servicio=tipo,
                           nombre_servicio=nombre_servicio,
                           tipo_formulario="denuncia",
                           stats=stats,
                           filtros=filtros,
                           tipos=NOMBRES_DENUNCIAS)

# ================================================================
# RUTAS DE ARCHIVOS SUBIDOS (FOTOS)
# ================================================================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'uploads'),
        filename
    )

# ================================================================
# RUTAS DE FOTO DE PERFIL
# ================================================================
@app.route("/mi-cuenta/foto", methods=["POST"])
@login_required
def subir_foto_perfil():
    if 'foto' not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("mi_cuenta"))

    archivo = request.files['foto']

    if archivo.filename == '':
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("mi_cuenta"))

    if not _allowed_file(archivo.filename):
        flash("Formato no permitido. Usa PNG, JPG, GIF o WEBP.", "error")
        return redirect(url_for("mi_cuenta"))

    email    = session["user"]
    usuarios = _cargar_usuarios()

    # Eliminar foto anterior si existe
    foto_anterior = usuarios.get(email, {}).get("foto_perfil", "")
    if foto_anterior:
        ruta_anterior = os.path.join(UPLOAD_FOLDER, foto_anterior)
        if os.path.exists(ruta_anterior):
            try:
                os.remove(ruta_anterior)
            except Exception:
                pass

    # Nombre único para el archivo
    ext            = archivo.filename.rsplit('.', 1)[1].lower()
    nombre_archivo = f"avatar_{uuid.uuid4().hex[:12]}.{ext}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    archivo.save(os.path.join(UPLOAD_FOLDER, nombre_archivo))

    # Guardar en usuarios.json
    usuarios[email]["foto_perfil"] = nombre_archivo
    from auth import _guardar_usuarios
    _guardar_usuarios(usuarios)
    session["foto_perfil"] = nombre_archivo

    flash("Foto de perfil actualizada correctamente.", "success")
    return redirect(url_for("mi_cuenta"))

@app.route("/mi-cuenta/foto/eliminar", methods=["POST"])
@login_required
def eliminar_foto_perfil():
    email    = session["user"]
    usuarios = _cargar_usuarios()

    foto = usuarios.get(email, {}).get("foto_perfil", "")
    if foto:
        ruta = os.path.join(UPLOAD_FOLDER, foto)
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
            except Exception:
                pass
        usuarios[email]["foto_perfil"] = ""
        from auth import _guardar_usuarios
        _guardar_usuarios(usuarios)
        session.pop("foto_perfil", None)
        flash("Foto de perfil eliminada.", "success")
    else:
        flash("No tienes foto de perfil asignada.", "info")

    return redirect(url_for("mi_cuenta"))

# ================================================================
# RUTAS DE USUARIO AUTENTICADO
# ================================================================
@app.route("/mi-cuenta")
@login_required
def mi_cuenta():
    email         = session["user"]
    usuarios      = _cargar_usuarios()
    datos_usuario = usuarios.get(email, {})

    usuario = {
        "nombre":           datos_usuario.get("nombre", ""),
        "apellidos":        datos_usuario.get("apellidos", ""),
        "nombre_completo":  datos_usuario.get("nombre_completo", ""),
        "email":            email,
        "tipo":             datos_usuario.get("tipo", "ciudadano"),
        "rol":              datos_usuario.get("rol", None),
        "telefono":         datos_usuario.get("telefono", "No registrado"),
        "cedula":           datos_usuario.get("cedula", ""),
        "fecha_nacimiento": datos_usuario.get("fecha_nacimiento", ""),
        "direccion":        datos_usuario.get("direccion", ""),
        "fecha_registro":   datos_usuario.get("fecha_registro", ""),
        "ultimo_acceso":    datos_usuario.get("ultimo_acceso", ""),
        "activo":           datos_usuario.get("activo", True),
        "notas_admin":      datos_usuario.get("notas_admin", ""),
        "foto_perfil":      datos_usuario.get("foto_perfil", "")
    }

    try:
        from models import Solicitud, Denuncia
        solicitudes       = Solicitud.buscar_por_usuario(email)
        solicitudes_count = len(solicitudes)

        todas_denuncias   = Denuncia.cargar_todos()
        denuncias_usuario = [d for d in todas_denuncias if d.usuario_email == email]
        denuncias_count   = len(denuncias_usuario)

        ultimas_actividades = []
        for s in sorted(solicitudes, key=lambda x: x.fecha_creacion, reverse=True)[:3]:
            ultimas_actividades.append({
                'tipo': 'solicitud', 'folio': s.folio,
                'descripcion': s.servicio_nombre,
                'estado': s.estado, 'fecha': s.fecha_creacion
            })
        for d in sorted(denuncias_usuario, key=lambda x: x.fecha_creacion, reverse=True)[:3]:
            ultimas_actividades.append({
                'tipo': 'denuncia', 'folio': d.folio,
                'descripcion': d.tipo_nombre,
                'estado': d.estado, 'fecha': d.fecha_creacion
            })
        ultimas_actividades.sort(key=lambda x: x['fecha'], reverse=True)

    except Exception as e:
        print(f"Error cargando actividades: {e}")
        solicitudes_count   = 0
        denuncias_count     = 0
        ultimas_actividades = []

    return render_template("mi_cuenta.html",
                           usuario=usuario,
                           solicitudes_count=solicitudes_count,
                           denuncias_count=denuncias_count,
                           ultimas_actividades=ultimas_actividades[:5])

@app.route("/mi-cuenta/editar", methods=["POST"])
@login_required
def editar_perfil():
    email    = session["user"]
    usuarios = _cargar_usuarios()

    if email in usuarios:
        usuarios[email]['nombre']    = request.form.get('nombre', '')
        usuarios[email]['apellidos'] = request.form.get('apellidos', '')
        usuarios[email]['telefono']  = request.form.get('telefono', '')
        usuarios[email]['direccion'] = request.form.get('direccion', '')

        from auth import _guardar_usuarios
        _guardar_usuarios(usuarios)
        session['user_name'] = f"{usuarios[email]['nombre']} {usuarios[email]['apellidos']}".strip()
        flash("✅ Perfil actualizado correctamente", "success")
    else:
        flash("❌ Error al actualizar el perfil", "error")

    return redirect(url_for("mi_cuenta"))

@app.route("/mis-solicitudes")
@login_required
def mis_solicitudes():
    try:
        from models import Solicitud
        solicitudes = Solicitud.buscar_por_usuario(session["user"])
        solicitudes.sort(key=lambda x: x.fecha_creacion, reverse=True)
    except Exception as e:
        print(f"Error cargando solicitudes: {e}")
        solicitudes = []
    return render_template("mis_solicitudes.html", solicitudes=solicitudes)

@app.route("/mis-denuncias")
@login_required
def mis_denuncias():
    try:
        from models import Denuncia
        todas     = Denuncia.cargar_todos()
        denuncias = [d for d in todas if d.usuario_email == session["user"]]
        denuncias.sort(key=lambda x: x.fecha_creacion, reverse=True)
    except Exception as e:
        print(f"Error cargando denuncias: {e}")
        denuncias = []
    return render_template("mis_denuncias.html", denuncias=denuncias)

# ================================================================
# MIS TRÁMITES (solicitudes + denuncias unificadas)
# ================================================================
@app.route("/mis-tramites")
@login_required
def mis_tramites():
    """Página unificada: muestra solicitudes y denuncias del usuario."""
    email    = session["user"]
    tramites = []

    # Solicitudes
    try:
        from models import Solicitud
        for s in Solicitud.buscar_por_usuario(email):
            item = _objeto_a_dict(s)
            item['tipo'] = 'solicitud'
            item.setdefault('comentarios_admin', [])
            item.setdefault('servicio_nombre', '')
            item.setdefault('tipo_nombre', '')
            item.setdefault('descripcion', '')
            item.setdefault('estado', 'pendiente')
            item.setdefault('folio', '')
            item.setdefault('fecha_creacion', '')
            tramites.append(item)
    except Exception as e:
        print(f"[mis_tramites] Error cargando solicitudes: {e}")

    # Denuncias
    try:
        from models import Denuncia
        for d in Denuncia.cargar_todos():
            if d.usuario_email == email:
                item = _objeto_a_dict(d)
                item['tipo'] = 'denuncia'
                item.setdefault('comentarios_admin', [])
                item.setdefault('servicio_nombre', '')
                item.setdefault('tipo_nombre', '')
                item.setdefault('descripcion', '')
                item.setdefault('estado', 'pendiente')
                item.setdefault('folio', '')
                item.setdefault('fecha_creacion', '')
                item.setdefault('direccion', '')
                tramites.append(item)
    except Exception as e:
        print(f"[mis_tramites] Error cargando denuncias: {e}")

    # Ordenar más recientes primero
    tramites.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)

    # Stats
    estados_proceso    = {'pendiente', 'en_proceso', 'en_investigacion'}
    estados_completado = {'completado', 'resuelto'}
    stats = {
        'solicitudes': sum(1 for t in tramites if t['tipo'] == 'solicitud'),
        'denuncias':   sum(1 for t in tramites if t['tipo'] == 'denuncia'),
        'pendientes':  sum(1 for t in tramites if t.get('estado') in estados_proceso),
        'completados': sum(1 for t in tramites if t.get('estado') in estados_completado),
    }

    # Serializar de forma segura
    tramites_json = json.dumps(tramites, ensure_ascii=False, default=str)

    return render_template(
        "mis_tramites.html",
        tramites=tramites,
        tramites_json=tramites_json,
        stats=stats
    )

# ================================================================
# API DE MENSAJES EN TRÁMITES
# ================================================================
@app.route("/api/tramite/<folio>/mensaje", methods=["POST"])
@login_required
def api_enviar_mensaje_ciudadano(folio):
    try:
        data  = request.get_json()
        texto = (data.get("texto") or "").strip()

        if not texto or len(texto) < 3:
            return jsonify({"error": "El mensaje no puede estar vacío."}), 400
        if len(texto) > 500:
            return jsonify({"error": "Máximo 500 caracteres."}), 400

        email  = session["user"]
        nombre = session.get("user_name", email)
        ahora  = datetime.now().isoformat()

        from models import Solicitud, Denuncia

        evento = {
            "fecha":       ahora,
            "tipo":        "mensaje_ciudadano",
            "descripcion": texto,
            "usuario":     email,
            "nombre":      nombre
        }

        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == email:
                if not isinstance(getattr(s, 'historial', None), list):
                    s.historial = []
                s.historial.append(evento)
                s.fecha_actualizacion = ahora
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                return jsonify({"success": True, "mensaje": evento})

        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == email:
                if not isinstance(getattr(d, 'historial', None), list):
                    d.historial = []
                d.historial.append(evento)
                d.fecha_actualizacion = ahora
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                return jsonify({"success": True, "mensaje": evento})

        return jsonify({"error": "Trámite no encontrado."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================================
# API PARA DOCUMENTOS EN TRÁMITES
# ================================================================
@app.route("/api/tramite/<folio>/documentos", methods=["POST"])
@login_required
def api_subir_documento(folio):
    """
    Subir un documento a un trámite (solicitud o denuncia)
    """
    try:
        if 'archivo' not in request.files:
            return jsonify({"success": False, "error": "No se envió ningún archivo"}), 400
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            return jsonify({"success": False, "error": "Nombre de archivo vacío"}), 400
        
        if not _allowed_document(archivo.filename):
            return jsonify({"success": False, "error": "Tipo de archivo no permitido. Usa PDF, JPG, PNG, DOC, DOCX"}), 400
        
        # Verificar tamaño
        archivo.seek(0, os.SEEK_END)
        size = archivo.tell()
        archivo.seek(0)
        if size > DOCS_MAX_SIZE_MB * 1024 * 1024:
            return jsonify({"success": False, "error": f"El archivo excede el límite de {DOCS_MAX_SIZE_MB} MB"}), 400
        
        email = session["user"]
        from models import Solicitud, Denuncia
        
        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == email:
                # Verificar límite de documentos
                if not hasattr(s, 'documentos'):
                    s.documentos = []
                if len(s.documentos) >= DOCS_MAX_POR_TRAMITE:
                    return jsonify({"success": False, "error": f"Límite de {DOCS_MAX_POR_TRAMITE} documentos alcanzado"}), 400
                
                # Guardar archivo
                ext = archivo.filename.rsplit('.', 1)[1].lower()
                nombre_seguro = secure_filename(archivo.filename)
                nombre_unico = f"doc_{folio}_{uuid.uuid4().hex[:8]}.{ext}"
                
                os.makedirs(DOCS_FOLDER, exist_ok=True)
                ruta = os.path.join(DOCS_FOLDER, nombre_unico)
                archivo.save(ruta)
                
                # Crear registro del documento
                documento = {
                    "id": str(uuid.uuid4()),
                    "nombre": nombre_seguro,
                    "archivo": nombre_unico,
                    "extension": ext,
                    "tamaño": size,
                    "fecha": datetime.now().isoformat(),
                    "subido_por": email
                }
                
                s.documentos.append(documento)
                s.fecha_actualizacion = datetime.now().isoformat()
                
                # Agregar al historial
                if not hasattr(s, 'historial'):
                    s.historial = []
                s.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento",
                    "descripcion": f"Documento adjunto: {nombre_seguro}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                
                return jsonify({
                    "success": True,
                    "documento": documento,
                    "restantes": DOCS_MAX_POR_TRAMITE - len(s.documentos)
                })
        
        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == email:
                if not hasattr(d, 'documentos'):
                    d.documentos = []
                if len(d.documentos) >= DOCS_MAX_POR_TRAMITE:
                    return jsonify({"success": False, "error": f"Límite de {DOCS_MAX_POR_TRAMITE} documentos alcanzado"}), 400
                
                ext = archivo.filename.rsplit('.', 1)[1].lower()
                nombre_seguro = secure_filename(archivo.filename)
                nombre_unico = f"doc_{folio}_{uuid.uuid4().hex[:8]}.{ext}"
                
                os.makedirs(DOCS_FOLDER, exist_ok=True)
                ruta = os.path.join(DOCS_FOLDER, nombre_unico)
                archivo.save(ruta)
                
                documento = {
                    "id": str(uuid.uuid4()),
                    "nombre": nombre_seguro,
                    "archivo": nombre_unico,
                    "extension": ext,
                    "tamaño": size,
                    "fecha": datetime.now().isoformat(),
                    "subido_por": email
                }
                
                d.documentos.append(documento)
                d.fecha_actualizacion = datetime.now().isoformat()
                
                if not hasattr(d, 'historial'):
                    d.historial = []
                d.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento",
                    "descripcion": f"Documento adjunto: {nombre_seguro}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                
                return jsonify({
                    "success": True,
                    "documento": documento,
                    "restantes": DOCS_MAX_POR_TRAMITE - len(d.documentos)
                })
        
        return jsonify({"success": False, "error": "Trámite no encontrado"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tramite/<folio>/documentos/<doc_id>", methods=["DELETE"])
@login_required
def api_eliminar_documento(folio, doc_id):
    """
    Eliminar un documento de un trámite
    """
    try:
        email = session["user"]
        from models import Solicitud, Denuncia
        
        # Buscar en solicitudes
        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == email:
                if not hasattr(s, 'documentos'):
                    return jsonify({"success": False, "error": "Sin documentos"}), 404
                
                # Buscar el documento
                documento = None
                for doc in s.documentos:
                    if doc.get('id') == doc_id:
                        documento = doc
                        break
                
                if not documento:
                    return jsonify({"success": False, "error": "Documento no encontrado"}), 404
                
                # Eliminar archivo físico
                ruta = os.path.join(DOCS_FOLDER, documento['archivo'])
                if os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                    except:
                        pass
                
                # Eliminar de la lista
                s.documentos = [d for d in s.documentos if d.get('id') != doc_id]
                s.fecha_actualizacion = datetime.now().isoformat()
                
                # Agregar al historial
                if not hasattr(s, 'historial'):
                    s.historial = []
                s.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento_eliminado",
                    "descripcion": f"Documento eliminado: {documento.get('nombre', '')}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                solicitudes[i] = s
                Solicitud.guardar_todos(solicitudes)
                
                return jsonify({"success": True})
        
        # Buscar en denuncias
        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == email:
                if not hasattr(d, 'documentos'):
                    return jsonify({"success": False, "error": "Sin documentos"}), 404
                
                documento = None
                for doc in d.documentos:
                    if doc.get('id') == doc_id:
                        documento = doc
                        break
                
                if not documento:
                    return jsonify({"success": False, "error": "Documento no encontrado"}), 404
                
                ruta = os.path.join(DOCS_FOLDER, documento['archivo'])
                if os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                    except:
                        pass
                
                d.documentos = [doc for doc in d.documentos if doc.get('id') != doc_id]
                d.fecha_actualizacion = datetime.now().isoformat()
                
                if not hasattr(d, 'historial'):
                    d.historial = []
                d.historial.append({
                    "fecha": datetime.now().isoformat(),
                    "tipo": "documento_eliminado",
                    "descripcion": f"Documento eliminado: {documento.get('nombre', '')}",
                    "usuario": email,
                    "nombre": session.get("user_name", email)
                })
                
                denuncias[i] = d
                Denuncia.guardar_todos(denuncias)
                
                return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Trámite no encontrado"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ================================================================
# API DE NOTIFICACIONES (para la campana)
# ================================================================
@app.route("/api/notificaciones")
@login_required
def api_notificaciones_usuario():
    """
    Obtiene las notificaciones del usuario (últimos eventos)
    """
    try:
        email = session["user"]
        from models import Solicitud, Denuncia, Cita
        
        notificaciones = []
        
        # Buscar en solicitudes
        solicitudes = Solicitud.buscar_por_usuario(email)
        for s in solicitudes:
            if hasattr(s, 'historial') and s.historial:
                # Tomar los últimos 3 eventos de cada trámite
                ultimos = sorted(s.historial, key=lambda x: x.get('fecha', ''), reverse=True)[:3]
                for ev in ultimos:
                    notificaciones.append({
                        "folio": s.folio,
                        "tipo": 'solicitud',
                        "servicio": s.servicio_nombre if hasattr(s, 'servicio_nombre') else 'Solicitud',
                        "fecha": ev.get('fecha', s.fecha_creacion),
                        "ultimo_tipo": ev.get('tipo', 'actividad'),
                        "descripcion": ev.get('descripcion', '')[:60],
                        "estado": s.estado
                    })
        
        # Buscar en denuncias
        todas_denuncias = Denuncia.cargar_todos()
        denuncias = [d for d in todas_denuncias if d.usuario_email == email]
        for d in denuncias:
            if hasattr(d, 'historial') and d.historial:
                ultimos = sorted(d.historial, key=lambda x: x.get('fecha', ''), reverse=True)[:3]
                for ev in ultimos:
                    notificaciones.append({
                        "folio": d.folio,
                        "tipo": 'denuncia',
                        "servicio": d.tipo_nombre if hasattr(d, 'tipo_nombre') else 'Denuncia',
                        "fecha": ev.get('fecha', d.fecha_creacion),
                        "ultimo_tipo": ev.get('tipo', 'actividad'),
                        "descripcion": ev.get('descripcion', '')[:60],
                        "estado": d.estado
                    })
        
        # Buscar en citas
        citas = Cita.buscar_por_usuario(email)
        for c in citas:
            # Agregar notificación para citas próximas
            if hasattr(c, 'fecha') and c.fecha:
                notificaciones.append({
                    "folio": c.folio,
                    "tipo": 'cita',
                    "servicio": SERVICIOS_CITAS.get(c.servicio, c.servicio),
                    "fecha": c.fecha_creacion if hasattr(c, 'fecha_creacion') else datetime.now().isoformat(),
                    "ultimo_tipo": 'cita_programada',
                    "descripcion": f"Cita para {c.fecha} a las {c.hora}",
                    "estado": c.estado
                })
        
        # Ordenar por fecha (más reciente primero)
        notificaciones.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        return jsonify({"items": notificaciones[:10]})  # Solo las 10 más recientes
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# SERVIDOR DE DOCUMENTOS
# ================================================================
@app.route('/uploads/documentos/<path:filename>')
@login_required
def uploaded_documento(filename):
    """
    Servir documentos (solo usuarios autenticados)
    """
    email = session["user"]
    
    # Verificar que el archivo pertenece al usuario
    from models import Solicitud, Denuncia
    autorizado = False

    for s in Solicitud.cargar_todos():
        if s.usuario_email == email:
            for doc in (getattr(s, 'documentos', []) or []):
                if doc.get('archivo') == filename:
                    autorizado = True
                    break

    if not autorizado:
        for d in Denuncia.cargar_todos():
            if d.usuario_email == email:
                for doc in (getattr(d, 'documentos', []) or []):
                    if doc.get('archivo') == filename:
                        autorizado = True
                        break

    # Admin puede ver todos
    if session.get('is_admin'):
        autorizado = True

    if not autorizado:
        flash("No tienes permiso para ver ese archivo.", "error")
        return redirect(url_for('mis_tramites'))

    return send_from_directory(
        os.path.join(app.root_path, DOCS_FOLDER),
        filename
    )

# ================================================================
# SISTEMA DE CITAS / TURNOS EN LÍNEA
# ================================================================
# Importar modelo de Cita
try:
    from models.cita import Cita
except ImportError:
    # Si el modelo no existe, definimos una clase temporal
    class Cita:
        ESTADOS = ['pendiente', 'confirmada', 'cancelada', 'completada']
        
        @staticmethod
        def crear(usuario_email, usuario_nombre, servicio, fecha, hora, motivo=""):
            from models import BaseModel
            cita = BaseModel.crear('cita', {
                'usuario_email': usuario_email,
                'usuario_nombre': usuario_nombre,
                'servicio': servicio,
                'fecha': fecha,
                'hora': hora,
                'motivo': motivo,
                'estado': 'pendiente',
                'notas_admin': ''
            })
            return cita
        
        @staticmethod
        def buscar_por_usuario(email):
            from models import BaseModel
            return BaseModel.buscar_por('cita', 'usuario_email', email)
        
        @staticmethod
        def buscar_por_id(cita_id):
            from models import BaseModel
            return BaseModel.buscar_por_id('cita', cita_id)
        
        @staticmethod
        def cargar_todos():
            from models import BaseModel
            return BaseModel.cargar_todos('cita')
        
        @staticmethod
        def guardar_todos(citas):
            from models import BaseModel
            return BaseModel.guardar_todos('cita', citas)
        
        @staticmethod
        def horarios_disponibles(servicio, fecha):
            # Horarios predeterminados (9 AM a 5 PM, cada hora)
            todos_horarios = [f"{h:02d}:00" for h in range(9, 18)]
            
            # Obtener citas existentes para esa fecha y servicio
            citas = Cita.cargar_todos()
            citas_ocupadas = [
                c.hora for c in citas 
                if c.servicio == servicio and c.fecha == fecha 
                and c.estado in ['pendiente', 'confirmada']
            ]
            
            # Filtrar horarios disponibles
            disponibles = [h for h in todos_horarios if h not in citas_ocupadas]
            return disponibles

@app.route("/citas/solicitar", methods=["GET", "POST"])
@login_required
def solicitar_cita():
    """Formulario para solicitar una cita"""
    if request.method == "POST":
        servicio = request.form.get("servicio")
        fecha = request.form.get("fecha")
        hora = request.form.get("hora")
        motivo = request.form.get("motivo", "").strip()
        
        if not servicio or not fecha or not hora:
            flash("❌ Completa todos los campos obligatorios.", "error")
            return redirect(url_for("solicitar_cita"))
        
        try:
            cita = Cita.crear(
                usuario_email=session["user"],
                usuario_nombre=session.get("user_name", "Ciudadano"),
                servicio=servicio,
                fecha=fecha,
                hora=hora,
                motivo=motivo
            )
            flash(
                f"✅ ¡Cita solicitada con éxito! Tu folio es: **{cita.folio}**. "
                f"Te confirmaremos por correo.",
                "success"
            )
            return redirect(url_for("mis_citas"))
        except Exception as e:
            flash(f"❌ Error al solicitar cita: {str(e)}", "error")
            return redirect(url_for("solicitar_cita"))
    
    # GET: mostrar formulario
    return render_template("citas/solicitar_cita.html", servicios=SERVICIOS_CITAS)

@app.route("/api/horarios-disponibles")
@login_required
def api_horarios_disponibles():
    """API para obtener horarios disponibles de una fecha"""
    servicio = request.args.get("servicio")
    fecha = request.args.get("fecha")
    
    if not servicio or not fecha:
        return jsonify({"error": "Faltan parámetros"}), 400
    
    try:
        disponibles = Cita.horarios_disponibles(servicio, fecha)
        return jsonify({"disponibles": disponibles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/mis-citas")
@login_required
def mis_citas():
    """Listado de citas del usuario"""
    citas = Cita.buscar_por_usuario(session["user"])
    # Ordenar por fecha (más recientes primero)
    citas.sort(key=lambda x: x.fecha + ' ' + x.hora, reverse=True)
    
    # Convertir a diccionario para el template
    citas_dict = []
    for c in citas:
        c_dict = _objeto_a_dict(c)
        c_dict['servicio_nombre'] = SERVICIOS_CITAS.get(c.servicio, c.servicio)
        citas_dict.append(c_dict)
    
    return render_template("citas/mis_citas.html", citas=citas_dict)

@app.route("/citas/<cita_id>/cancelar", methods=["POST"])
@login_required
def cancelar_cita(cita_id):
    """Cancelar una cita"""
    cita = Cita.buscar_por_id(cita_id)
    if not cita or cita.usuario_email != session["user"]:
        flash("❌ Cita no encontrada.", "error")
        return redirect(url_for("mis_citas"))
    
    cita.estado = 'cancelada'
    citas = Cita.cargar_todos()
    for i, c in enumerate(citas):
        if c.id == cita_id:
            citas[i] = cita
            break
    Cita.guardar_todos(citas)
    
    flash("✅ Cita cancelada correctamente.", "success")
    return redirect(url_for("mis_citas"))

# ================================================================
# MAPA DE INCIDENCIAS
# ================================================================
@app.route("/mapa")
@login_required
def mapa_incidencias():
    """Mapa público de denuncias (ciudadanos ven sus denuncias)"""
    from models import Denuncia
    
    # Si es admin, ve todas
    if session.get('is_admin'):
        denuncias = Denuncia.cargar_todos()
    else:
        # Ciudadano solo ve sus denuncias
        todas = Denuncia.cargar_todos()
        denuncias = [d for d in todas if d.usuario_email == session["user"]]
    
    # Filtrar solo las que tienen coordenadas
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    
    return render_template("mapa.html", 
                          denuncias=denuncias_geo,
                          tipos=NOMBRES_DENUNCIAS)

@app.route("/admin/mapa")
@admin_required
def admin_mapa_incidencias():
    """Mapa administrativo con todas las denuncias"""
    from models import Denuncia
    
    denuncias = Denuncia.cargar_todos()
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    
    return render_template("admin/mapa_admin.html", 
                          denuncias=denuncias_geo,
                          tipos=NOMBRES_DENUNCIAS,
                          stats={
                              'total': len(denuncias),
                              'geolocalizadas': len(denuncias_geo),
                              'pendientes': len([d for d in denuncias if d.estado in ['pendiente', 'en_investigacion']])
                          })

@app.route("/api/denuncias/geojson")
@login_required
def api_denuncias_geojson():
    """API que devuelve las denuncias en formato GeoJSON para el mapa"""
    from models import Denuncia
    
    if session.get('is_admin'):
        denuncias = Denuncia.cargar_todos()
    else:
        todas = Denuncia.cargar_todos()
        denuncias = [d for d in todas if d.usuario_email == session["user"]]
    
    # Filtrar geolocalizadas
    denuncias_geo = [d for d in denuncias if hasattr(d, 'geolocalizada') and d.geolocalizada]
    
    features = []
    for d in denuncias_geo:
        # Color según estado
        color = {
            'pendiente': '#f59e0b',
            'en_investigacion': '#3b82f6',
            'resuelto': '#10b981',
            'rechazado': '#ef4444'
        }.get(d.estado, '#6b7280')
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [d.longitud, d.latitud]
            },
            "properties": {
                "id": d.id,
                "folio": d.folio,
                "tipo": d.tipo,
                "tipo_nombre": NOMBRES_DENUNCIAS.get(d.tipo, d.tipo),
                "descripcion": d.descripcion[:100] + "..." if len(d.descripcion) > 100 else d.descripcion,
                "direccion": d.direccion,
                "fecha": d.fecha_creacion[:10],
                "estado": d.estado,
                "anonimo": getattr(d, 'anonimo', False),
                "usuario": "Anónimo" if getattr(d, 'anonimo', False) else d.usuario_nombre,
                "color": color,
                "url": url_for('admin.detalle_denuncia', denuncia_id=d.id) if session.get('is_admin') else "#"
            }
        })
    
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

# ================================================================
# API PARA GEOLOCALIZACIÓN (usando Nominatim/OpenStreetMap)
# ================================================================
@app.route("/api/geocodificar", methods=["POST"])
@admin_required
def api_geocodificar():
    """Convierte una dirección en coordenadas usando Nominatim"""
    try:
        data = request.get_json()
        direccion = data.get('direccion')
        denuncia_id = data.get('denuncia_id')
        
        if not direccion:
            return jsonify({"error": "Dirección requerida"}), 400
        
        import requests
        from urllib.parse import quote
        
        # Usar Nominatim de OpenStreetMap (gratuito)
        url = f"https://nominatim.openstreetmap.org/search?q={quote(direccion)}&format=json&limit=1"
        
        # IMPORTANTE: Agregar User-Agent con tu email
        headers = {
            'User-Agent': 'VillaCutupuApp/1.0 (contacto@cutupu.gob.do)'
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            
            # Si hay denuncia_id, actualizar la denuncia
            if denuncia_id:
                from models import Denuncia
                denuncias = Denuncia.cargar_todos()
                for i, d in enumerate(denuncias):
                    if str(d.id) == str(denuncia_id):
                        d.latitud = lat
                        d.longitud = lon
                        d.geolocalizada = True
                        denuncias[i] = d
                        break
                Denuncia.guardar_todos(denuncias)
            
            return jsonify({
                "success": True,
                "latitud": lat,
                "longitud": lon,
                "display_name": data[0].get('display_name', direccion)
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo encontrar la dirección"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================================
# PLANTILLAS DE RESPUESTA RÁPIDA
# ================================================================
from models.plantilla import Plantilla

@app.route("/admin/plantillas")
@admin_required
def admin_plantillas():
    """Gestión de plantillas de respuesta"""
    plantillas = Plantilla.cargar_todos()
    
    # Agrupar por categoría
    por_categoria = {}
    for p in plantillas:
        if p.categoria not in por_categoria:
            por_categoria[p.categoria] = []
        por_categoria[p.categoria].append(p)
    
    return render_template("admin/plantillas.html", 
                          plantillas=plantillas,
                          por_categoria=por_categoria,
                          categorias=Plantilla.CATEGORIAS)

@app.route("/admin/plantillas/crear", methods=["POST"])
@admin_required
def admin_crear_plantilla():
    """Crea una nueva plantilla"""
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    contenido = request.form.get("contenido")
    variables = request.form.getlist("variables") or ['folio', 'nombre', 'fecha']
    
    if not nombre or not contenido:
        flash("❌ Nombre y contenido son obligatorios.", "error")
        return redirect(url_for("admin_plantillas"))
    
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
    return redirect(url_for("admin_plantillas"))

@app.route("/admin/plantillas/<plantilla_id>/editar", methods=["POST"])
@admin_required
def admin_editar_plantilla(plantilla_id):
    """Edita una plantilla existente"""
    plantilla = Plantilla.buscar_por_id(plantilla_id)
    if not plantilla:
        flash("❌ Plantilla no encontrada.", "error")
        return redirect(url_for("admin_plantillas"))
    
    plantilla.nombre = request.form.get("nombre")
    plantilla.categoria = request.form.get("categoria")
    plantilla.contenido = request.form.get("contenido")
    plantilla.variables = request.form.getlist("variables") or ['folio', 'nombre', 'fecha']
    
    plantillas = Plantilla.cargar_todos()
    for i, p in enumerate(plantillas):
        if p.id == plantilla_id:
            plantillas[i] = plantilla
            break
    Plantilla.guardar_todos(plantillas)
    
    flash(f"✅ Plantilla '{plantilla.nombre}' actualizada.", "success")
    return redirect(url_for("admin_plantillas"))

@app.route("/admin/plantillas/<plantilla_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_plantilla(plantilla_id):
    """Activa/desactiva una plantilla"""
    plantilla = Plantilla.buscar_por_id(plantilla_id)
    if not plantilla:
        flash("❌ Plantilla no encontrada.", "error")
        return redirect(url_for("admin_plantillas"))
    
    plantilla.activa = not plantilla.activa
    
    plantillas = Plantilla.cargar_todos()
    for i, p in enumerate(plantillas):
        if p.id == plantilla_id:
            plantillas[i] = plantilla
            break
    Plantilla.guardar_todos(plantillas)
    
    estado = "activada" if plantilla.activa else "desactivada"
    flash(f"✅ Plantilla '{plantilla.nombre}' {estado}.", "success")
    return redirect(url_for("admin_plantillas"))

@app.route("/admin/plantillas/<plantilla_id>/eliminar", methods=["POST"])
@admin_required
def admin_eliminar_plantilla(plantilla_id):
    """Elimina una plantilla"""
    plantillas = Plantilla.cargar_todos()
    plantillas = [p for p in plantillas if p.id != plantilla_id]
    Plantilla.guardar_todos(plantillas)
    
    flash("✅ Plantilla eliminada.", "success")
    return redirect(url_for("admin_plantillas"))

@app.route("/api/plantillas/<categoria>")
@admin_required
def api_plantillas_por_categoria(categoria):
    """API para obtener plantillas por categoría"""
    plantillas = Plantilla.buscar_por_categoria(categoria)
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'contenido': p.contenido,
        'variables': p.variables
    } for p in plantillas])

@app.route("/api/plantillas/<plantilla_id>/procesar", methods=["POST"])
@admin_required
def api_procesar_plantilla(plantilla_id):
    """Procesa una plantilla con variables"""
    plantilla = Plantilla.buscar_por_id(plantilla_id)
    if not plantilla:
        return jsonify({"error": "Plantilla no encontrada"}), 404
    
    data = request.get_json()
    contenido = plantilla.procesar(**data)
    plantilla.incrementar_uso()
    
    return jsonify({"contenido": contenido})

# ================================================================
# ADMIN: GESTIÓN DE CITAS (ya está arriba, pero unificamos)
# ================================================================
# Las rutas de admin/citas ya están definidas arriba en la sección de citas

# ================================================================
# ENCUESTAS DE SATISFACCIÓN
# ================================================================
try:
    from models.encuesta import Encuesta
except ImportError:
    # Si el modelo no existe, definimos una clase temporal
    class Encuesta:
        @staticmethod
        def crear(folio_tramite, tipo_tramite, usuario_email, usuario_nombre, calificacion, comentario=""):
            from models import BaseModel
            encuesta = BaseModel.crear('encuesta', {
                'folio_tramite': folio_tramite,
                'tipo_tramite': tipo_tramite,
                'usuario_email': usuario_email,
                'usuario_nombre': usuario_nombre,
                'calificacion': calificacion,
                'comentario': comentario,
                'fecha': datetime.now().isoformat()
            })
            return encuesta
        
        @staticmethod
        def buscar_por_tramite(folio_tramite):
            from models import BaseModel
            return BaseModel.buscar_por('encuesta', 'folio_tramite', folio_tramite)
        
        @staticmethod
        def obtener_estadisticas():
            from models import BaseModel
            encuestas = BaseModel.cargar_todos('encuesta')
            
            if not encuestas:
                return {
                    'total': 0,
                    'promedio': 0,
                    'por_calificacion': {1:0, 2:0, 3:0, 4:0, 5:0},
                    'por_tipo': {'solicitud':0, 'denuncia':0, 'cita':0},
                    'ultimas': []
                }
            
            total = len(encuestas)
            suma = sum(e.calificacion for e in encuestas)
            
            # Calcular distribución por calificación
            por_calificacion = {1:0, 2:0, 3:0, 4:0, 5:0}
            for e in encuestas:
                if e.calificacion in por_calificacion:
                    por_calificacion[e.calificacion] += 1
            
            # Calcular por tipo de trámite
            por_tipo = {'solicitud':0, 'denuncia':0, 'cita':0}
            for e in encuestas:
                if e.tipo_tramite in por_tipo:
                    por_tipo[e.tipo_tramite] += 1
            
            # Últimas 10 encuestas
            ultimas = sorted(encuestas, key=lambda x: x.fecha, reverse=True)[:10]
            ultimas_dict = []
            for e in ultimas:
                e_dict = _objeto_a_dict(e)
                ultimas_dict.append(e_dict)
            
            return {
                'total': total,
                'promedio': round(suma / total, 1),
                'por_calificacion': por_calificacion,
                'por_tipo': por_tipo,
                'ultimas': ultimas_dict
            }

@app.route("/tramite/<folio>/encuesta", methods=["GET", "POST"])
@login_required
def encuesta_tramite(folio):
    """Formulario de encuesta para un trámite completado"""
    from models import Solicitud, Denuncia, Cita
    
    # Verificar que el trámite existe y pertenece al usuario
    tramite = None
    tipo = None
    
    # Buscar en solicitudes
    for s in Solicitud.buscar_por_usuario(session["user"]):
        if s.folio == folio:
            tramite = s
            tipo = 'solicitud'
            break
    
    # Buscar en denuncias
    if not tramite:
        for d in Denuncia.cargar_todos():
            if d.folio == folio and d.usuario_email == session["user"]:
                tramite = d
                tipo = 'denuncia'
                break
    
    # Buscar en citas
    if not tramite:
        for c in Cita.buscar_por_usuario(session["user"]):
            if c.folio == folio:
                tramite = c
                tipo = 'cita'
                break
    
    if not tramite:
        flash("❌ Trámite no encontrado.", "error")
        return redirect(url_for("mis_tramites"))
    
    # Verificar que el trámite está completado
    estados_completados = ['completado', 'resuelto', 'completada']
    if tramite.estado not in estados_completados:
        flash("❌ Solo puedes evaluar trámites completados.", "error")
        return redirect(url_for("mis_tramites"))
    
    # Verificar si ya respondió
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
            tipo_tramite=tipo,
            usuario_email=session["user"],
            usuario_nombre=session.get("user_name", "Ciudadano"),
            calificacion=calif_int,
            comentario=comentario
        )
        
        flash("✅ ¡Gracias por tu evaluación! Tu opinión nos ayuda a mejorar.", "success")
        return redirect(url_for("mis_tramites"))
    
    # GET: mostrar formulario
    nombre_servicio = ""
    if hasattr(tramite, 'servicio_nombre'):
        nombre_servicio = tramite.servicio_nombre
    elif hasattr(tramite, 'tipo_nombre'):
        nombre_servicio = tramite.tipo_nombre
    elif hasattr(tramite, 'servicio'):
        nombre_servicio = SERVICIOS_CITAS.get(tramite.servicio, tramite.servicio)
    
    return render_template("encuestas/encuesta.html", 
                          tramite=tramite, 
                          tipo=tipo,
                          nombre_servicio=nombre_servicio,
                          folio=folio)

# ================================================================
# ADMIN: ESTADÍSTICAS DE ENCUESTAS
# ================================================================
@app.route("/admin/encuestas")
@admin_required
def admin_encuestas():
    """Panel admin con estadísticas de satisfacción"""
    stats = Encuesta.obtener_estadisticas()
    return render_template("admin/encuestas.html", stats=stats)

# ================================================================
# API PARA ADMIN: CITAS PENDIENTES (para el badge)
# ================================================================
@app.route("/api/admin/citas-pendientes")
@admin_required
def api_admin_citas_pendientes():
    """API para obtener el número de citas pendientes"""
    try:
        from models import Cita
        citas = Cita.cargar_todos()
        pendientes = len([c for c in citas if c.estado == 'pendiente'])
        return jsonify({"count": pendientes})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)}), 500

# ================================================================
# APIs GENERALES
# ================================================================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard_redirect():
    return redirect(url_for("admin.dashboard"))

@app.route("/admin-panel")
@admin_required
def admin_panel():
    return redirect(url_for("admin.dashboard"))

@app.route("/api/tramite/<folio>")
@login_required
def api_tramite(folio):
    try:
        from models import Solicitud, Denuncia

        for s in Solicitud.cargar_todos():
            if s.folio == folio and s.usuario_email == session["user"]:
                tramite = s.to_dict() if hasattr(s, 'to_dict') else _objeto_a_dict(s)
                tramite['tipo'] = 'solicitud'
                return jsonify(tramite)

        for d in Denuncia.cargar_todos():
            if d.folio == folio and d.usuario_email == session["user"]:
                tramite = d.to_dict() if hasattr(d, 'to_dict') else _objeto_a_dict(d)
                tramite['tipo'] = 'denuncia'
                return jsonify(tramite)

        return jsonify({'error': 'Trámite no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/tramite/<folio>/responder", methods=["POST"])
@login_required
def api_responder_tramite(folio):
    try:
        data         = request.get_json()
        respuesta    = data.get('respuesta')
        nuevo_estado = data.get('estado')

        from models import Solicitud, Denuncia

        solicitudes = Solicitud.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.folio == folio and s.usuario_email == session["user"]:
                if not hasattr(s, 'historial'):
                    s.historial = []
                s.historial.append({
                    'fecha': datetime.now().isoformat(),
                    'usuario': session["user"],
                    'tipo': 'respuesta',
                    'descripcion': respuesta
                })
                s.estado              = nuevo_estado
                s.fecha_actualizacion = datetime.now().isoformat()
                solicitudes[i]        = s
                Solicitud.guardar_todos(solicitudes)
                return jsonify({'success': True, 'message': 'Respuesta enviada'})

        denuncias = Denuncia.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.folio == folio and d.usuario_email == session["user"]:
                if not hasattr(d, 'historial'):
                    d.historial = []
                d.historial.append({
                    'fecha': datetime.now().isoformat(),
                    'usuario': session["user"],
                    'tipo': 'respuesta',
                    'descripcion': respuesta
                })
                d.estado              = nuevo_estado
                d.fecha_actualizacion = datetime.now().isoformat()
                denuncias[i]          = d
                Denuncia.guardar_todos(denuncias)
                return jsonify({'success': True, 'message': 'Respuesta enviada'})

        return jsonify({'error': 'Trámite no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/admin/api/notificaciones")
@admin_required
def api_notificaciones_admin():
    try:
        from models import Solicitud, Denuncia
        sp = len([s for s in Solicitud.cargar_todos() if s.estado == 'pendiente'])
        dp = len([d for d in Denuncia.cargar_todos()  if d.estado == 'pendiente'])
        return jsonify({
            'count': sp + dp,
            'notifications': [
                {'icon': 'fa-file-alt',            'message': f'{sp} solicitudes pendientes', 'time': 'Ahora', 'read': False},
                {'icon': 'fa-exclamation-triangle', 'message': f'{dp} denuncias pendientes',   'time': 'Ahora', 'read': False},
            ]
        })
    except:
        return jsonify({'count': 0, 'notifications': []})

# ================================================================
# ERROR HANDLERS
# ================================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

# ================================================================
# ARRANQUE
# ================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 SISTEMA MUNICIPAL VILLA CUTUPÚ")
    print("=" * 50)
    print("✅ Blueprint 'auth' registrado")
    print("✅ Blueprint 'admin' registrado")
    print("✅ Configuración de uploads lista")
    print("=" * 50)
    print("📌 Rutas principales:")
    print("   /                → index")
    print("   /login           → login")
    print("   /registro        → registro")
    print("   /admin           → panel admin")
    print("   /mi-cuenta       → perfil (con foto)")
    print("   /mis-tramites    → tramites unificados")
    print("   /citas/solicitar → solicitar cita")
    print("   /mis-citas       → mis citas")
    print("   /admin/citas     → admin citas")
    print("   /mapa            → mapa de incidencias (ciudadano)")
    print("   /admin/mapa      → mapa de incidencias (admin)")
    print("   /tramite/*/encuesta → encuesta satisfacción")
    print("   /admin/encuestas → estadísticas encuestas")
    print("   /admin/plantillas → plantillas de respuesta")
    print("=" * 50)
    
    # Crear carpetas de uploads si no existen
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DOCS_FOLDER, exist_ok=True)
    
    app.run(debug=True, host="0.0.0.0", port=5000)