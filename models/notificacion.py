# ================================================================
# MODELO NOTIFICACIÓN - VERSIÓN COMPLETA
# ================================================================
from extensions import db
from datetime import datetime
import json

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(120), nullable=False, index=True)
    tipo = db.Column(db.String(50), nullable=False, default='info')  # solicitud, denuncia, cita, sistema, contacto, info, warning, success, error
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False, index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    fecha_lectura = db.Column(db.DateTime, nullable=True)
    
    # Datos adicionales (JSON)
    datos_extra = db.Column(db.Text, nullable=True)  # Guardar info extra como folio, id, etc.
    
    def __init__(self, usuario_email, tipo, titulo, mensaje, datos_extra=None):
        self.usuario_email = usuario_email
        self.tipo = tipo
        self.titulo = titulo
        self.mensaje = mensaje
        self.datos_extra = json.dumps(datos_extra) if datos_extra else None
        self.fecha_creacion = datetime.utcnow()
    
    def marcar_leido(self):
        """Marca la notificación como leída"""
        if not self.leido:
            self.leido = True
            self.fecha_lectura = datetime.utcnow()
            db.session.commit()
    
    def to_dict(self):
        """Convierte la notificación a diccionario para JSON"""
        return {
            'id': self.id,
            'usuario_email': self.usuario_email,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'leido': self.leido,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_creacion_formateada': self.fecha_creacion.strftime("%d/%m/%Y %H:%M") if self.fecha_creacion else None,
            'fecha_lectura': self.fecha_lectura.isoformat() if self.fecha_lectura else None,
            'datos_extra': json.loads(self.datos_extra) if self.datos_extra else None
        }
    
    # ================================================================
    # MÉTODOS ESTÁTICOS PRINCIPALES
    # ================================================================
    
    @staticmethod
    def crear_notificacion(usuario_email, tipo, titulo, mensaje, datos_extra=None):
        """
        Crea una nueva notificación
        
        Args:
            usuario_email: Email del usuario destinatario
            tipo: Tipo de notificación (solicitud, denuncia, cita, sistema, contacto, info, warning, success, error)
            titulo: Título de la notificación
            mensaje: Contenido del mensaje
            datos_extra: Diccionario con datos adicionales (ej: {'folio': 'xxx', 'id': 123})
        """
        notif = Notificacion(usuario_email, tipo, titulo, mensaje, datos_extra)
        db.session.add(notif)
        db.session.commit()
        return notif
    
    @staticmethod
    def crear_notificacion_masiva(emails, tipo, titulo, mensaje, datos_extra=None):
        """
        Crea la misma notificación para múltiples usuarios
        
        Args:
            emails: Lista de emails de destinatarios
            tipo: Tipo de notificación
            titulo: Título de la notificación
            mensaje: Contenido del mensaje
            datos_extra: Datos adicionales
        """
        notificaciones = []
        for email in emails:
            notif = Notificacion(email, tipo, titulo, mensaje, datos_extra)
            db.session.add(notif)
            notificaciones.append(notif)
        db.session.commit()
        return notificaciones
    
    @staticmethod
    def obtener_no_leidas(usuario_email):
        """Obtiene todas las notificaciones no leídas de un usuario"""
        return Notificacion.query.filter_by(
            usuario_email=usuario_email, 
            leido=False
        ).order_by(Notificacion.fecha_creacion.desc()).all()
    
    @staticmethod
    def obtener_todas(usuario_email, limit=50):
        """Obtiene todas las notificaciones de un usuario (con límite)"""
        return Notificacion.query.filter_by(
            usuario_email=usuario_email
        ).order_by(Notificacion.fecha_creacion.desc()).limit(limit).all()
    
    @staticmethod
    def obtener_por_tipo(usuario_email, tipo, limit=50):
        """Obtiene notificaciones de un tipo específico"""
        return Notificacion.query.filter_by(
            usuario_email=usuario_email,
            tipo=tipo
        ).order_by(Notificacion.fecha_creacion.desc()).limit(limit).all()
    
    @staticmethod
    def marcar_todas_como_leidas(usuario_email):
        """Marca todas las notificaciones de un usuario como leídas"""
        notificaciones = Notificacion.query.filter_by(usuario_email=usuario_email, leido=False).all()
        for n in notificaciones:
            n.leido = True
            n.fecha_lectura = datetime.utcnow()
        db.session.commit()
        return len(notificaciones)
    
    @staticmethod
    def eliminar_antiguas(dias=30):
        """Elimina notificaciones leídas más antiguas de X días"""
        from sqlalchemy import func
        fecha_limite = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        fecha_limite = fecha_limite - timedelta(days=dias)
        
        antiguas = Notificacion.query.filter(
            Notificacion.leido == True,
            Notificacion.fecha_lectura < fecha_limite
        ).delete()
        db.session.commit()
        return antiguas
    
    @staticmethod
    def contar_no_leidas(usuario_email):
        """Cuenta las notificaciones no leídas de un usuario"""
        return Notificacion.query.filter_by(usuario_email=usuario_email, leido=False).count()
    
    @staticmethod
    def obtener_estadisticas(usuario_email=None):
        """Obtiene estadísticas de notificaciones"""
        query = Notificacion.query
        if usuario_email:
            query = query.filter_by(usuario_email=usuario_email)
        
        total = query.count()
        no_leidas = query.filter_by(leido=False).count()
        leidas = total - no_leidas
        
        # Estadísticas por tipo
        from sqlalchemy import func
        tipos = db.session.query(
            Notificacion.tipo, 
            func.count(Notificacion.id).label('count')
        ).filter(
            Notificacion.usuario_email == usuario_email if usuario_email else True
        ).group_by(Notificacion.tipo).all()
        
        return {
            'total': total,
            'leidas': leidas,
            'no_leidas': no_leidas,
            'por_tipo': {tipo: count for tipo, count in tipos}
        }
    
    # ================================================================
    # MÉTODOS DE CONVENIENCIA PARA TIPOS COMUNES
    # ================================================================
    
    @staticmethod
    def notificar_nuevo_mensaje(usuario_email, folio, tramite_tipo, autor_nombre):
        """Notifica que hay un nuevo mensaje en un trámite"""
        return Notificacion.crear_notificacion(
            usuario_email=usuario_email,
            tipo='mensaje',
            titulo=f"Nuevo mensaje en tu {tramite_tipo}",
            mensaje=f"{autor_nombre} ha respondido a tu {tramite_tipo} {folio}",
            datos_extra={'folio': folio, 'tipo': tramite_tipo}
        )
    
    @staticmethod
    def notificar_cambio_estado(usuario_email, folio, tramite_tipo, estado_anterior, estado_nuevo):
        """Notifica que un trámite cambió de estado"""
        return Notificacion.crear_notificacion(
            usuario_email=usuario_email,
            tipo='estado',
            titulo=f"Estado actualizado - {tramite_tipo}",
            mensaje=f"Tu {tramite_tipo} {folio} ha cambiado de {estado_anterior} a {estado_nuevo}",
            datos_extra={'folio': folio, 'tipo': tramite_tipo, 'estado_anterior': estado_anterior, 'estado_nuevo': estado_nuevo}
        )
    
    @staticmethod
    def notificar_respuesta_contacto(usuario_email, folio):
        """Notifica que un contacto ha sido respondido"""
        return Notificacion.crear_notificacion(
            usuario_email=usuario_email,
            tipo='contacto',
            titulo="✅ Respuesta a tu consulta",
            mensaje=f"El administrador ha respondido a tu consulta. Folio: {folio}",
            datos_extra={'folio': folio}
        )
    
    @staticmethod
    def notificar_nuevo_contacto(admin_email, nombre_usuario, folio):
        """Notifica a los administradores que hay un nuevo contacto"""
        return Notificacion.crear_notificacion(
            usuario_email=admin_email,
            tipo='contacto',
            titulo="📬 Nuevo contacto recibido",
            mensaje=f"El usuario {nombre_usuario} ha enviado un nuevo mensaje. Folio: {folio}",
            datos_extra={'folio': folio, 'usuario': nombre_usuario}
        )
    
    def __repr__(self):
        return f'<Notificacion {self.id} - {self.usuario_email} - {self.titulo[:30]}>'