# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Instancias de extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Configuración de login_manager
login_manager.login_view = 'auth.login'
login_manager.login_message = '🔐 Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'