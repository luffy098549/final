# extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# =========================
# INSTANCIAS
# =========================
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# =========================
# CONFIG LOGIN
# =========================
login_manager.login_view = 'auth.login'
login_manager.login_message = '🔐 Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'
login_manager.session_protection = 'strong'

# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):
    from models.usuario import Usuario
    return Usuario.query.get(int(user_id))