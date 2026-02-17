from flask import Flask, render_template, session, request, redirect, url_for, flash
from auth import auth
import os

app = Flask(__name__)
app.secret_key = "supersecret"

app.register_blueprint(auth)

@app.route("/")
def index():
    if "user" not in session:
        return render_template("index.html", logged=False)
    return render_template("index.html", 
                         logged=True, 
                         is_admin=session.get("is_admin", False),
                         user_name=session.get("user_name", ""))

@app.route("/solicitar/<servicio>")
def solicitar_servicio(servicio):
    logged = "user" in session
    return render_template("solicitar.html", 
                         servicio=servicio,
                         logged=logged)

@app.route("/solicitar/<servicio>", methods=["POST"])
def enviar_solicitud(servicio):
    nombre = request.form.get("nombre")
    cedula = request.form.get("cedula")
    telefono = request.form.get("telefono")
    descripcion = request.form.get("descripcion")
    
    if not nombre or not cedula or not descripcion:
        flash("Todos los campos obligatorios deben completarse", "error")
        return redirect(url_for("solicitar_servicio", servicio=servicio))
    
    # Aquí se guardaría en base de datos
    flash(f"Solicitud de {servicio} enviada correctamente", "success")
    return redirect(url_for("servicios"))

@app.route("/denunciar/<servicio>")
def denunciar_servicio(servicio):
    logged = "user" in session
    return render_template("denunciar.html", 
                         servicio=servicio,
                         logged=logged)

@app.route("/denuncias")
def denuncias():
    logged = "user" in session
    return render_template("denuncias.html", logged=logged)

@app.route("/denunciar", methods=["POST"])
def enviar_denuncia():
    nombre = request.form.get("nombre")
    telefono = request.form.get("telefono")
    tipo = request.form.get("tipo")
    descripcion = request.form.get("descripcion")
    direccion = request.form.get("direccion")

    if not nombre or not tipo or not descripcion:
        flash("Todos los campos obligatorios deben completarse", "error")
        return redirect(url_for("denuncias"))

    # Aquí se guardaría en base de datos
    flash("Denuncia enviada correctamente", "success")
    return redirect(url_for("denuncias"))

@app.route("/municipio")
def municipio():
    logged = "user" in session
    return render_template("municipio.html", logged=logged)

@app.route("/servicios")
def servicios():
    logged = "user" in session
    return render_template("servicios.html", 
                         logged=logged, 
                         is_admin=session.get("is_admin", False))

@app.route("/transparencia")
def transparencia():
    logged = "user" in session
    return render_template("transparencia.html", logged=logged)

@app.route("/noticias")
def noticias():
    logged = "user" in session
    return render_template("noticias.html", logged=logged)

@app.route("/noticias/<id>")
def noticia_detalle(id):
    logged = "user" in session
    return render_template("noticia_detalle.html", 
                         id=id,
                         logged=logged)

@app.route("/contacto")
def contacto():
    logged = "user" in session
    return render_template("contacto.html", logged=logged)

@app.route("/enviar-contacto", methods=["POST"])
def enviar_contacto():
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    telefono = request.form.get("telefono")
    asunto = request.form.get("asunto")
    mensaje = request.form.get("mensaje")

    if not nombre or not email or not asunto or not mensaje:
        flash("Todos los campos obligatorios deben completarse", "error")
        return redirect(url_for("contacto"))

    # Aquí se enviaría el email o se guardaría en BD
    flash("Mensaje enviado correctamente. Nos pondremos en contacto a la brevedad.", "success")
    return redirect(url_for("contacto"))

@app.route("/recuperar-password")
def recuperar_password():
    return render_template("recuperar.html")

@app.route("/recuperar-password", methods=["POST"])
def enviar_recuperacion():
    email = request.form.get("email")
    flash("Se ha enviado un enlace de recuperación a su correo electrónico", "success")
    return redirect(url_for("login"))

# ===== RUTAS PARA USUARIOS AUTENTICADOS =====
@app.route("/mi-cuenta")
def mi_cuenta():
    if "user" not in session:
        flash("Debe iniciar sesión para ver su cuenta", "error")
        return redirect(url_for("auth.login"))
    
    return render_template("mi_cuenta.html", 
                         logged=True,
                         user_name=session.get("user_name", ""))

@app.route("/editar-perfil")
def editar_perfil():
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    return render_template("editar_perfil.html", 
                         logged=True,
                         user_name=session.get("user_name", ""))

@app.route("/editar-perfil", methods=["POST"])
def actualizar_perfil():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    nombre = request.form.get("nombre")
    telefono = request.form.get("telefono")
    # Aquí se actualizaría en BD
    
    flash("Perfil actualizado correctamente", "success")
    return redirect(url_for("mi_cuenta"))

@app.route("/mis-solicitudes")
def mis_solicitudes():
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    return render_template("mis_solicitudes.html", 
                         logged=True,
                         user_name=session.get("user_name", ""))

@app.route("/mis-denuncias")
def mis_denuncias():
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    return render_template("mis_denuncias.html", 
                         logged=True,
                         user_name=session.get("user_name", ""))

@app.route("/notificaciones")
def notificaciones():
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    return render_template("notificaciones.html", 
                         logged=True,
                         user_name=session.get("user_name", ""))

# ===== RUTAS ADMINISTRATIVAS (SOLO ADMIN) =====
@app.route("/admin")
def admin_panel():
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin.html", 
                         logged=True,
                         is_admin=True,
                         user_name=session.get("user_name", ""))

@app.route("/admin/usuarios")
def admin_usuarios():
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin_usuarios.html", 
                         logged=True,
                         is_admin=True)

@app.route("/admin/solicitudes")
def admin_solicitudes():
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin_solicitudes.html", 
                         logged=True,
                         is_admin=True)

@app.route("/admin/denuncias")
def admin_denuncias():
    if "user" not in session or not session.get("is_admin"):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("index"))
    
    return render_template("admin_denuncias.html", 
                         logged=True,
                         is_admin=True)

if __name__ == "__main__":
    app.run(debug=True)