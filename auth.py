from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth = Blueprint("auth", __name__)

# Simulación de base de datos de usuarios (luego será BD real)
usuarios_registrados = {
    "ciudadano@example.com": {
        "nombre": "Juan Pérez",
        "password": "ciudadano123",
        "tipo": "ciudadano"
    }
}

@auth.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmar = request.form.get("confirmar_password")
        
        # Validaciones
        if not nombre or not email or not password:
            flash("Todos los campos son obligatorios", "error")
            return render_template("registro.html")
        
        if password != confirmar:
            flash("Las contraseñas no coinciden", "error")
            return render_template("registro.html")
        
        if email in usuarios_registrados:
            flash("Este correo ya está registrado", "error")
            return render_template("registro.html")
        
        # Registrar nuevo usuario
        usuarios_registrados[email] = {
            "nombre": nombre,
            "password": password,
            "tipo": "ciudadano"
        }
        
        flash("Registro exitoso. Ahora puede iniciar sesión.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("registro.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Por favor ingrese su correo y contraseña", "error")
            return render_template("login.html")
        
        # Verificar credenciales
        if email in usuarios_registrados and usuarios_registrados[email]["password"] == password:
            session["user"] = email
            session["user_name"] = usuarios_registrados[email]["nombre"]
            session["user_tipo"] = usuarios_registrados[email]["tipo"]
            flash(f"Bienvenido {usuarios_registrados[email]['nombre']}", "success")
            return redirect(url_for("index"))
        else:
            flash("Correo o contraseña incorrectos", "error")
            return render_template("login.html")
    
    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for("index"))

@auth.route("/mi-cuenta")
def mi_cuenta():
    if "user" not in session:
        flash("Debe iniciar sesión para ver su cuenta", "error")
        return redirect(url_for("auth.login"))
    
    usuario = usuarios_registrados.get(session["user"], {})
    return render_template("mi_cuenta.html", usuario=usuario)

@auth.route("/mis-solicitudes")
def mis_solicitudes():
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    # Aquí luego mostrarías las solicitudes del usuario desde BD
    return render_template("mis_solicitudes.html")

@auth.route("/mis-denuncias")
def mis_denuncias():
    if "user" not in session:
        flash("Debe iniciar sesión", "error")
        return redirect(url_for("auth.login"))
    
    # Aquí luego mostrarías las denuncias del usuario desde BD
    return render_template("mis_denuncias.html")