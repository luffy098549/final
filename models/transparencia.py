# ============================================================
# IMPORTS
# ============================================================
from extensions import db
from datetime import datetime


# ============================================================
# MODELO TRANSPARENCIA
# ============================================================
class Transparencia(db.Model):
    __tablename__ = 'transparencia'

    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================
    id       = db.Column(db.Integer, primary_key=True)
    titulo   = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)   # ver CATEGORIAS abajo

    # ===============================
    # DETALLE DEL DOCUMENTO
    # ===============================
    descripcion = db.Column(db.Text, nullable=True)
    anio        = db.Column(db.Integer, nullable=True)      # año al que corresponde
    periodo     = db.Column(db.String(50), nullable=True)   # ej: 'Enero 2024', 'T1 2024'
    fecha_doc   = db.Column(db.Date, nullable=True)         # fecha del documento

    # ===============================
    # ARCHIVO / ENLACE
    # ===============================
    archivo_url = db.Column(db.String(500), nullable=True)  # ruta Cloudinary o local
    enlace_ext  = db.Column(db.String(500), nullable=True)  # URL externa alternativa

    # ===============================
    # ESTADO
    # ===============================
    publicado = db.Column(db.Boolean, default=False)        # False = borrador

    # ===============================
    # FECHAS
    # ===============================
    creado_en      = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ===============================
    # CATEGORÍAS DISPONIBLES
    # ===============================
    CATEGORIAS = [
        ('presupuesto',  'Presupuesto'),
        ('actas',        'Actas de sesión'),
        ('contratos',    'Contratos'),
        ('nomina',       'Nómina'),
        ('informes',     'Informes de gestión'),
        ('planes',       'Planes y programas'),
        ('licitaciones', 'Licitaciones y compras'),
        ('otros',        'Otros documentos'),
    ]

    # ===============================
    # SERIALIZACIÓN
    # ===============================
    def to_dict(self):
        return {
            'id':             self.id,
            'titulo':         self.titulo,
            'categoria':      self.categoria,
            'descripcion':    self.descripcion,
            'anio':           self.anio,
            'periodo':        self.periodo,
            'fecha_doc':      self.fecha_doc.isoformat() if self.fecha_doc else None,
            'archivo_url':    self.archivo_url,
            'enlace_ext':     self.enlace_ext,
            'publicado':      self.publicado,
            'creado_en':      self.creado_en.isoformat() if self.creado_en else None,
            'actualizado_en': self.actualizado_en.isoformat() if self.actualizado_en else None,
        }

    # ===============================
    # MÉTODOS ESTÁTICOS
    # ===============================
    @staticmethod
    def obtener_publicados():
        return Transparencia.query.filter_by(publicado=True)\
            .order_by(Transparencia.anio.desc(), Transparencia.creado_en.desc()).all()

    @staticmethod
    def obtener_por_categoria(categoria):
        return Transparencia.query.filter_by(categoria=categoria, publicado=True)\
            .order_by(Transparencia.anio.desc()).all()

    @staticmethod
    def obtener_todos():
        return Transparencia.query.order_by(Transparencia.creado_en.desc()).all()

    # ===============================
    # REPRESENTACIÓN
    # ===============================
    def __repr__(self):
        return f'<Transparencia {self.categoria} – {self.titulo[:40]}>'

    def __str__(self):
        return self.titulo