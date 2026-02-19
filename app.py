from flask import Flask, render_template, session, request, redirect, url_for, flash
from auth import auth
import os

app = Flask(__name__)
app.secret_key = "clave_secreta_muy_segura_cambiar_en_produccion_123"

# Registrar el blueprint de autenticación
app.register_blueprint(auth)

# ========== RUTAS PÚBLICAS ==========

@app.route("/")
def index():
    """Página principal"""
    if "user" in session:
        return render_template("index.html", 
                             logged=True, 
                             is_admin=session.get("is_admin", False),
                             user_name=session.get("user_name", ""))
    return render_template("index.html", logged=False)

@app.route("/municipio")
def municipio():
    """Página de información del municipio"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    return render_template("municipio.html", 
                         logged=logged, 
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

@app.route("/servicios")
def servicios():
    """Página de servicios municipales"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    return render_template("servicios.html", 
                         logged=logged, 
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

@app.route("/transparencia")
def transparencia():
    """Portal de transparencia"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    return render_template("transparencia.html", 
                         logged=logged, 
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

@app.route("/noticias")
def noticias():
    """Página de noticias"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    return render_template("noticias.html", 
                         logged=logged, 
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

@app.route("/contacto", methods=["GET"])
def contacto():
    """Página de contacto"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    return render_template("contacto.html", 
                         logged=logged, 
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

@app.route("/enviar-contacto", methods=["POST"])
def enviar_contacto():
    """Procesar formulario de contacto"""
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    telefono = request.form.get("telefono")
    asunto = request.form.get("asunto")
    mensaje = request.form.get("mensaje")

    if not nombre or not email or not asunto or not mensaje:
        flash("Todos los campos obligatorios deben completarse", "error")
        return redirect(url_for("contacto"))

    # Aquí se enviaría el email (simulado)
    flash(f"Gracias {nombre}, tu mensaje ha sido enviado correctamente. Te responderemos a la brevedad.", "success")
    return redirect(url_for("contacto"))

# ========== RUTAS DE SERVICIOS Y DENUNCIAS ==========

@app.route("/solicitar/<servicio>", methods=["GET", "POST"])
def solicitar_servicio(servicio):
    """Formulario para solicitar un servicio específico"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    
    # Lista de servicios válidos
    servicios_validos = ["funeraria", "uso-suelo", "oaim", "limpieza", "basura", "policia"]
    
    if servicio not in servicios_validos:
        flash("Servicio no válido", "error")
        return redirect(url_for("servicios"))
    
    if request.method == "POST":
        nombre = request.form.get("nombre")
        cedula = request.form.get("cedula")
        telefono = request.form.get("telefono")
        descripcion = request.form.get("descripcion")
        
        if not nombre or not cedula or not descripcion:
            flash("Todos los campos obligatorios deben completarse", "error")
            return redirect(url_for("solicitar_servicio", servicio=servicio))
        
        # Aquí se guardaría en base de datos (simulado)
        flash(f"Solicitud de {servicio} enviada correctamente. Pronto recibirás noticias.", "success")
        return redirect(url_for("servicios"))
    
    return render_template("solicitar.html", 
                         servicio=servicio,
                         logged=logged,
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

@app.route("/denunciar/<servicio>", methods=["GET", "POST"])
def denunciar_servicio(servicio):
    """Formulario para denunciar un servicio específico"""
    logged = "user" in session
    is_admin = session.get("is_admin", False) if logged else False
    
    # Lista de servicios válidos para denuncias
    servicios_validos = ["limpieza", "basura", "policia", "otro"]
    
    if servicio not in servicios_validos:
        flash("Servicio no válido para denuncia", "error")
        return redirect(url_for("servicios"))
    
    if request.method == "POST":
        nombre = request.form.get("nombre")
        telefono = request.form.get("telefono")
        tipo = request.form.get("tipo")
        descripcion = request.form.get("descripcion")
        direccion = request.form.get("direccion")

        if not nombre or not tipo or not descripcion:
            flash("Todos los campos obligatorios deben completarse", "error")
            return redirect(url_for("denunciar_servicio", servicio=servicio))

        # Aquí se guardaría en base de datos (simulado)
        flash("Denuncia enviada correctamente. Daremos seguimiento a tu caso.", "success")
        return redirect(url_for("servicios"))
    
    return render_template("denunciar.html", 
                         servicio=servicio,
                         logged=logged,
                         is_admin=is_admin,
                         user_name=session.get("user_name", ""))

# ========== RUTAS PARA USUARIOS AUTENTICADOS ==========

@app.route("/mi-cuenta")
def mi_cuenta():
    """Página de perfil del usuario"""
    if "user" not in session:
        flash("Debe iniciar sesión para ver su cuenta", "error")
        return redirect(url_for("auth.login"))
    
    usuario = {
        "nombre": session.get("user_name", ""),
        "email": session.get("user", ""),
        "tipo": session.get("user_tipo", "ciudadano")
    }
    
    return render_template("mi_cuenta.html", 
                         logged=True,
                         is_admin=session.get("is_admin", False),
                         usuario=usuario)

@app.route("/mis-solicitudes")
def mis_solicitudes():
    """Historial de solicitudes del usuario"""
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    # Datos de ejemplo para demostración
    solicitudes = [
        {"fecha": "15/02/2026", "servicio": "Certificado de Uso de Suelo", "estado": "En proceso", "folio": "SOL-2026-001"},
        {"fecha": "10/02/2026", "servicio": "Funerarias Municipales", "estado": "Completado", "folio": "SOL-2026-002"},
        {"fecha": "05/02/2026", "servicio": "Acceso a la Información", "estado": "En revisión", "folio": "SOL-2026-003"}
    ]
    
    return render_template("mis_solicitudes.html", 
                         logged=True,
                         is_admin=session.get("is_admin", False),
                         user_name=session.get("user_name", ""),
                         solicitudes=solicitudes)

@app.route("/mis-denuncias")
def mis_denuncias():
    """Historial de denuncias del usuario"""
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    # Datos de ejemplo para demostración
    denuncias = [
        {"fecha": "14/02/2026", "tipo": "Recogida de Basura", "estado": "En proceso", "direccion": "Calle Principal #123"},
        {"fecha": "08/02/2026", "tipo": "Limpieza Vía Pública", "estado": "Resuelto", "direccion": "Av. Central #456"},
        {"fecha": "01/02/2026", "tipo": "Alumbrado Público", "estado": "Pendiente", "direccion": "Calle Secundaria #789"}
    ]
    
    return render_template("mis_denuncias.html", 
                         logged=True,
                         is_admin=session.get("is_admin", False),
                         user_name=session.get("user_name", ""),
                         denuncias=denuncias)

# ========== RUTAS ADMINISTRATIVAS (SOLO ADMIN) ==========

@app.route("/admin")
def admin_panel():
    """Panel de administración principal"""
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin.html", 
                         logged=True,
                         is_admin=True,
                         user_name=session.get("user_name", ""))

@app.route("/admin/usuarios")
def admin_usuarios():
    """Gestión de usuarios (solo admin)"""
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    # Datos de ejemplo
    usuarios = [
        {"nombre": "Juan Pérez", "email": "juan@email.com", "tipo": "ciudadano", "fecha_registro": "01/01/2026"},
        {"nombre": "María García", "email": "maria@email.com", "tipo": "ciudadano", "fecha_registro": "15/01/2026"},
        {"nombre": "Administrador", "email": "admin@cutupu.gob.do", "tipo": "admin", "fecha_registro": "01/01/2026"}
    ]
    
    return render_template("admin_usuarios.html", 
                         logged=True,
                         is_admin=True,
                         usuarios=usuarios)

@app.route("/admin/solicitudes")
def admin_solicitudes():
    """Gestión de solicitudes (solo admin)"""
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin_solicitudes.html", 
                         logged=True,
                         is_admin=True)

@app.route("/admin/denuncias")
def admin_denuncias():
    """Gestión de denuncias (solo admin)"""
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin_denuncias.html", 
                         logged=True,
                         is_admin=True)

@app.route("/admin/actualizar-solicitud/<int:solicitud_id>", methods=["POST"])
def actualizar_solicitud(solicitud_id):
    """Actualizar estado de una solicitud (solo admin)"""
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    nuevo_estado = request.form.get("estado")
    flash(f"Solicitud #{solicitud_id} actualizada a: {nuevo_estado}", "success")
    return redirect(url_for("admin_solicitudes"))

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def page_not_found(e):
    """Página de error 404"""
    logged = "user" in session
    return render_template("404.html", 
                         logged=logged,
                         is_admin=session.get("is_admin", False)), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Página de error 500"""
    logged = "user" in session
    return render_template("500.html", 
                         logged=logged,
                         is_admin=session.get("is_admin", False)), 500

# ========== CONTEXTO GLOBAL PARA PLANTILLAS ==========

@app.context_processor
def inject_user():
    """Inyectar variables de usuario en todas las plantillas"""
    return dict(
        logged="user" in session,
        is_admin=session.get("is_admin", False),
        user_name=session.get("user_name", "")
    )

# ========== INICIAR APLICACIÓN ==========

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)