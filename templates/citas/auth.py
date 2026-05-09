from flask import Blueprint, render_template, request, redirect, url_for, flash, session

auth = Blueprint('auth', __name__)

# ========== BASE DE DATOS SIMULADA (EN MEMORIA) ==========
# En un entorno real, esto sería una base de datos
USUARIOS = {
    "admin@cutupu.gob.do": {
        "password": "admin123",
        "nombre": "Administrador Municipal",
        "tipo": "admin",
        "telefono": "809-691-7111",
        "fecha_registro": "01/01/2026"
    },
    "ciudadano@email.com": {
        "password": "123456",
        "nombre": "Juan Pérez",
        "tipo": "ciudadano",
        "telefono": "809-555-1234",
        "fecha_registro": "15/01/2026"
    },
    "maria.garcia@email.com": {
        "password": "maria2026",
        "nombre": "María García",
        "tipo": "ciudadano",
        "telefono": "809-555-5678",
        "fecha_registro": "20/01/2026"
    },
    "roberto.torres@email.com": {
        "password": "roberto123",
        "nombre": "Roberto Torres",
        "tipo": "ciudadano",
        "telefono": "809-555-9012",
        "fecha_registro": "05/02/2026"
    }
}

# ========== RUTAS DE AUTENTICACIÓN ==========

@auth.route("/login", methods=["GET", "POST"])
def login():
    """Página de inicio de sesión"""
    # Si ya está logueado, redirigir al inicio
    if "user" in session:
        flash(f"Ya has iniciado sesión como {session.get('user_name')}", "info")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        recordar = request.form.get("recordar")  # No implementado, solo para la interfaz
        
        # Validaciones básicas
        if not email or not password:
            flash("Por favor, completa todos los campos", "error")
            return render_template("login.html")
        
        # Verificar credenciales
        if email in USUARIOS and USUARIOS[email]["password"] == password:
            # Iniciar sesión
            session["user"] = email
            session["user_name"] = USUARIOS[email]["nombre"]
            session["user_tipo"] = USUARIOS[email]["tipo"]
            session["is_admin"] = (USUARIOS[email]["tipo"] == "admin")
            
            # Mensaje de bienvenida personalizado
            flash(f"¡Bienvenido, {USUARIOS[email]['nombre']}! Has iniciado sesión correctamente.", "success")
            
            # Redirigir según el tipo de usuario
            if session["is_admin"]:
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("mi_cuenta"))
        else:
            flash("Correo electrónico o contraseña incorrectos", "error")
            return render_template("login.html")
    
    return render_template("login.html")

@auth.route("/registro", methods=["GET", "POST"])
def registro():
    """Página de registro de nuevos usuarios"""
    if "user" in session:
        flash("Ya tienes una sesión activa", "info")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar_password", "")
        terminos = request.form.get("terminos")
        
        # Validaciones
        if not nombre or not email or not password:
            flash("Todos los campos son obligatorios", "error")
            return render_template("registro.html")
        
        if password != confirmar:
            flash("Las contraseñas no coinciden", "error")
            return render_template("registro.html")
        
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres", "error")
            return render_template("registro.html")
        
        if not terminos:
            flash("Debes aceptar los términos y condiciones", "error")
            return render_template("registro.html")
        
        # Verificar si el email ya está registrado
        if email in USUARIOS:
            flash("Este correo electrónico ya está registrado. ¿Olvidaste tu contraseña?", "error")
            return render_template("registro.html")
        
        # Registrar nuevo usuario (en memoria - se pierde al reiniciar)
        from datetime import datetime
        USUARIOS[email] = {
            "password": password,
            "nombre": nombre,
            "tipo": "ciudadano",
            "telefono": "",
            "fecha_registro": datetime.now().strftime("%d/%m/%Y")
        }
        
        flash("¡Registro exitoso! Ya puedes iniciar sesión con tus credenciales.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("registro.html")

@auth.route("/logout")
def logout():
    """Cerrar sesión"""
    if "user" in session:
        nombre = session.get("user_name", "Usuario")
        session.clear()
        flash(f"¡Hasta pronto, {nombre}! Has cerrado sesión correctamente.", "success")
    else:
        flash("No habías iniciado sesión", "info")
    
    return redirect(url_for("index"))

@auth.route("/recuperar-password", methods=["GET", "POST"])
def recuperar_password():
    """Recuperación de contraseña"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("Por favor, ingresa tu correo electrónico", "error")
            return render_template("recuperar.html")
        
        # Verificar si el email existe (por seguridad, no revelamos si existe o no)
        if email in USUARIOS:
            # En un entorno real, aquí se enviaría un email
            flash(f"Se ha enviado un enlace de recuperación a {email}. Revisa tu bandeja de entrada.", "success")
        else:
            # Por seguridad, mostramos el mismo mensaje aunque no exista
            flash(f"Si el correo existe en nuestro sistema, recibirás instrucciones en {email}", "info")
        
        return redirect(url_for("auth.login"))
    
    return render_template("recuperar.html")

@auth.route("/cambiar-password", methods=["POST"])
def cambiar_password():
    """Cambiar contraseña (usuario autenticado)"""
    if "user" not in session:
        flash("Debes iniciar sesión para cambiar tu contraseña", "error")
        return redirect(url_for("auth.login"))
    
    password_actual = request.form.get("password_actual", "")
    password_nueva = request.form.get("password_nueva", "")
    password_confirmar = request.form.get("password_confirmar", "")
    
    email = session["user"]
    
    # Verificar contraseña actual
    if email not in USUARIOS or USUARIOS[email]["password"] != password_actual:
        flash("La contraseña actual es incorrecta", "error")
        return redirect(url_for("mi_cuenta"))
    
    # Validar nueva contraseña
    if len(password_nueva) < 6:
        flash("La nueva contraseña debe tener al menos 6 caracteres", "error")
        return redirect(url_for("mi_cuenta"))
    
    if password_nueva != password_confirmar:
        flash("Las contraseñas nuevas no coinciden", "error")
        return redirect(url_for("mi_cuenta"))
    
    # Actualizar contraseña
    USUARIOS[email]["password"] = password_nueva
    flash("¡Contraseña actualizada correctamente!", "success")
    
    return redirect(url_for("mi_cuenta"))

# ========== FUNCIONES AUXILIARES ==========

def get_usuario_actual():
    """Obtener datos del usuario actual"""
    if "user" in session:
        email = session["user"]
        if email in USUARIOS:
            return USUARIOS[email]
    return None

def es_admin():
    """Verificar si el usuario actual es administrador"""
    return session.get("is_admin", False)

def listar_usuarios():
    """Listar todos los usuarios (solo para administración)"""
    return USUARIOS

# ========== CONTEXTO PARA PLANTILLAS DEL BLUEPRINT ==========

@auth.context_processor
def inject_auth_variables():
    """Inyectar variables útiles en todas las plantillas de auth"""
    return dict(
        es_admin=es_admin(),
        usuario_actual=get_usuario_actual()
    )