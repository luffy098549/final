# ============================================================
# IMPORTS
# ============================================================
from extensions import db
from datetime import datetime


# ============================================================
# MODELO MENU ITEM
# ============================================================
class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================
    id       = db.Column(db.Integer, primary_key=True)
    etiqueta = db.Column(db.String(100), nullable=False)         # texto visible: "Servicios"
    url      = db.Column(db.String(300), nullable=False)         # ruta: '/servicios' o URL completa
    orden    = db.Column(db.Integer, default=0, nullable=False)  # posición en el menú

    # ===============================
    # APARIENCIA
    # ===============================
    icono    = db.Column(db.String(100), nullable=True)          # clase CSS: 'fas fa-cog'

    # ===============================
    # COMPORTAMIENTO
    # ===============================
    nueva_tab = db.Column(db.Boolean, default=False)             # abrir en _blank

    # ===============================
    # SUBMENÚ (auto-referencia)
    # ===============================
    padre_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=True)
    hijos    = db.relationship(
        'MenuItem',
        backref=db.backref('padre', remote_side='MenuItem.id'),
        lazy='dynamic',
        order_by='MenuItem.orden'
    )

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
    def to_dict(self, incluir_hijos=True):
        data = {
            'id':        self.id,
            'etiqueta':  self.etiqueta,
            'url':       self.url,
            'orden':     self.orden,
            'icono':     self.icono,
            'nueva_tab': self.nueva_tab,
            'padre_id':  self.padre_id,
            'activo':    self.activo,
        }
        if incluir_hijos:
            data['hijos'] = [h.to_dict(incluir_hijos=False)
                             for h in self.hijos if h.activo]
        return data

    # ===============================
    # MÉTODOS ESTÁTICOS
    # ===============================
    @staticmethod
    def obtener_menu_completo():
        """Devuelve solo los ítems raíz activos con sus hijos incluidos."""
        return MenuItem.query.filter_by(padre_id=None, activo=True)\
            .order_by(MenuItem.orden).all()

    @staticmethod
    def obtener_todos():
        return MenuItem.query.order_by(MenuItem.orden).all()

    # ===============================
    # REPRESENTACIÓN
    # ===============================
    def __repr__(self):
        return f'<MenuItem {self.orden} – {self.etiqueta}>'

    def __str__(self):
        return self.etiqueta