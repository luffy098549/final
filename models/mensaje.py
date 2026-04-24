# models/mensaje.py
from extensions import db
from datetime import datetime
import json

class Mensaje(db.Model):
    __tablename__ = 'mensajes'
    
    id = db.Column(db.Integer, primary_key=True)
    tramite_folio = db.Column(db.String(20), nullable=False)  # Folio de solicitud/denuncia/cita
    tramite_tipo = db.Column(db.String(50), nullable=False)   # solicitud, denuncia, cita
    usuario_email = db.Column(db.String(120), nullable=False) # Email del usuario dueño del trámite
    autor_email = db.Column(db.String(120), nullable=False)   # Email de quien escribe (admin o usuario)
    autor_nombre = db.Column(db.String(200), nullable=False)  # Nombre de quien escribe
    autor_rol = db.Column(db.String(50), nullable=True)       # admin, ciudadano, moderador
    mensaje = db.Column(db.Text, nullable=False)
    es_admin = db.Column(db.Boolean, default=False)           # True si es admin, False si es usuario
    leido = db.Column(db.Boolean, default=False)              # Si el destinatario lo ha leído
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, tramite_folio, tramite_tipo, usuario_email, autor_email, autor_nombre, mensaje, es_admin=False):
        self.tramite_folio = tramite_folio
        self.tramite_tipo = tramite_tipo
        self.usuario_email = usuario_email
        self.autor_email = autor_email
        self.autor_nombre = autor_nombre
        self.mensaje = mensaje
        self.es_admin = es_admin
        self.autor_rol = 'admin' if es_admin else 'ciudadano'
    
    def marcar_leido(self):
        self.leido = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'tramite_folio': self.tramite_folio,
            'tramite_tipo': self.tramite_tipo,
            'autor_email': self.autor_email,
            'autor_nombre': self.autor_nombre,
            'autor_rol': self.autor_rol,
            'mensaje': self.mensaje,
            'es_admin': self.es_admin,
            'leido': self.leido,
            'fecha': self.fecha_creacion.strftime("%d/%m/%Y %H:%M") if self.fecha_creacion else None
        }
    
    @staticmethod
    def crear_mensaje(tramite_folio, tramite_tipo, usuario_email, autor_email, autor_nombre, mensaje, es_admin=False):
        nuevo = Mensaje(
            tramite_folio=tramite_folio,
            tramite_tipo=tramite_tipo,
            usuario_email=usuario_email,
            autor_email=autor_email,
            autor_nombre=autor_nombre,
            mensaje=mensaje,
            es_admin=es_admin
        )
        db.session.add(nuevo)
        db.session.commit()
        
        # Crear notificación para el destinatario
        from models.notificacion import Notificacion
        if es_admin:
            # El admin escribió → notificar al usuario
            titulo = f"Nuevo mensaje en tu {tramite_tipo}"
            mensaje_notif = f"El administrador ha respondido a tu {tramite_tipo} {tramite_folio}"
            url_extra = {'folio': tramite_folio, 'tipo': tramite_tipo}
        else:
            # El usuario escribió → notificar a los admins
            titulo = f"Nuevo mensaje de {autor_nombre}"
            mensaje_notif = f"El usuario {autor_nombre} ha respondido en el trámite {tramite_folio}"
            url_extra = {'folio': tramite_folio, 'tipo': tramite_tipo}
            # Notificar a todos los admins
            from models.usuario import Usuario
            admins = Usuario.obtener_administradores()
            for admin in admins:
                Notificacion.crear_notificacion(
                    usuario_email=admin.email,
                    tipo=tramite_tipo,
                    titulo=titulo,
                    mensaje=mensaje_notif,
                    datos_extra=url_extra
                )
            return nuevo
        
        Notificacion.crear_notificacion(
            usuario_email=usuario_email,
            tipo=tramite_tipo,
            titulo=titulo,
            mensaje=mensaje_notif,
            datos_extra=url_extra
        )
        return nuevo
    
    @staticmethod
    def obtener_mensajes_tramite(folio, tipo):
        return Mensaje.query.filter_by(tramite_folio=folio, tramite_tipo=tipo).order_by(Mensaje.fecha_creacion).all()
    
    @staticmethod
    def contar_no_leidos(usuario_email, es_admin=False):
        query = Mensaje.query.filter_by(usuario_email=usuario_email, leido=False)
        if es_admin:
            query = query.filter_by(es_admin=False)
        else:
            query = query.filter_by(es_admin=True)
        return query.count()