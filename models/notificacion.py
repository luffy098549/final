# models/notificacion.py
from extensions import db
from datetime import datetime
import json

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # solicitud, denuncia, cita, sistema
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_lectura = db.Column(db.DateTime, nullable=True)
    
    # Datos adicionales (JSON)
    datos_extra = db.Column(db.Text, nullable=True)  # Guardar info extra como folio, etc.
    
    def __init__(self, usuario_email, tipo, titulo, mensaje, datos_extra=None):
        self.usuario_email = usuario_email
        self.tipo = tipo
        self.titulo = titulo
        self.mensaje = mensaje
        self.datos_extra = json.dumps(datos_extra) if datos_extra else None
    
    def marcar_leido(self):
        self.leido = True
        self.fecha_lectura = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_email': self.usuario_email,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'leido': self.leido,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_lectura': self.fecha_lectura.isoformat() if self.fecha_lectura else None,
            'datos_extra': json.loads(self.datos_extra) if self.datos_extra else None
        }
    
    @staticmethod
    def crear_notificacion(usuario_email, tipo, titulo, mensaje, datos_extra=None):
        notif = Notificacion(usuario_email, tipo, titulo, mensaje, datos_extra)
        db.session.add(notif)
        db.session.commit()
        return notif
    
    @staticmethod
    def obtener_no_leidas(usuario_email):
        return Notificacion.query.filter_by(usuario_email=usuario_email, leido=False).order_by(Notificacion.fecha_creacion.desc()).all()
    
    @staticmethod
    def obtener_todas(usuario_email, limit=50):
        return Notificacion.query.filter_by(usuario_email=usuario_email).order_by(Notificacion.fecha_creacion.desc()).limit(limit).all()
    
    @staticmethod
    def marcar_todas_como_leidas(usuario_email):
        notificaciones = Notificacion.query.filter_by(usuario_email=usuario_email, leido=False).all()
        for n in notificaciones:
            n.leido = True
            n.fecha_lectura = datetime.utcnow()
        db.session.commit()
        return len(notificaciones)