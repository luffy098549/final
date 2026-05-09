# ============================================================
# IMPORTS
# ============================================================
from extensions import db
from datetime import datetime


# ============================================================
# MODELO CONTENIDO
# ============================================================
class Contenido(db.Model):
    __tablename__ = 'contenidos'

    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================
    id    = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)  # ej: 'inicio_bienvenida'

    # ===============================
    # CONTENIDO
    # ===============================
    titulo  = db.Column(db.String(200), nullable=True)
    cuerpo  = db.Column(db.Text, nullable=False)          # acepta HTML
    seccion = db.Column(db.String(100), nullable=True)    # ej: 'inicio', 'footer', 'servicios'

    # ===============================
    # ESTADO
    # ===============================
    activo = db.Column(db.Boolean, default=True)

    # ===============================
    # FECHAS
    # ===============================
    creado_en      = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ===============================
    # SERIALIZACIÓN
    # ===============================
    def to_dict(self):
        return {
            'id':             self.id,
            'clave':          self.clave,
            'titulo':         self.titulo,
            'cuerpo':         self.cuerpo,
            'seccion':        self.seccion,
            'activo':         self.activo,
            'creado_en':      self.creado_en.isoformat() if self.creado_en else None,
            'actualizado_en': self.actualizado_en.isoformat() if self.actualizado_en else None,
        }

    # ===============================
    # MÉTODOS ESTÁTICOS
    # ===============================
    @staticmethod
    def obtener_por_clave(clave):
        return Contenido.query.filter_by(clave=clave, activo=True).first()

    @staticmethod
    def obtener_por_seccion(seccion):
        return Contenido.query.filter_by(seccion=seccion, activo=True).all()

    @staticmethod
    def obtener_todos():
        return Contenido.query.order_by(Contenido.seccion, Contenido.clave).all()

    # ===============================
    # REPRESENTACIÓN
    # ===============================
    def __repr__(self):
        return f'<Contenido {self.clave}>'

    def __str__(self):
        return self.clave