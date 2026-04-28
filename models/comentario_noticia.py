# models/comentario_noticia.py
from extensions import db
from datetime import datetime

class ComentarioNoticia(db.Model):
    __tablename__ = 'comentarios_noticia'
    
    id = db.Column(db.Integer, primary_key=True)
    noticia_id = db.Column(db.Integer, db.ForeignKey('noticias.id'), nullable=False, index=True)
    autor_nombre = db.Column(db.String(100), nullable=False)
    autor_email = db.Column(db.String(120), nullable=True)
    contenido = db.Column(db.Text, nullable=False)
    aprobado = db.Column(db.Boolean, default=False, index=True)
    ip_autor = db.Column(db.String(45), nullable=True)  # IPv4 (15) o IPv6 (45)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relación con Noticia (opcional, para acceder desde el comentario)
    # noticia = relationship('Noticia', back_populates='comentarios')
    
    @classmethod
    def crear(cls, noticia_id, autor_nombre, contenido, autor_email=None, ip_autor=None):
        """
        Crea un nuevo comentario (pendiente de aprobación por defecto)
        
        Retorna: instancia del comentario creado
        """
        comentario = cls(
            noticia_id=noticia_id,
            autor_nombre=autor_nombre[:100],  # Truncar por seguridad
            autor_email=autor_email[:120] if autor_email else None,
            contenido=contenido,
            aprobado=False,
            ip_autor=ip_autor[:45] if ip_autor else None
        )
        db.session.add(comentario)
        db.session.commit()
        return comentario
    
    @classmethod
    def aprobar(cls, comentario_id):
        """
        Aprueba un comentario pendiente
        
        Retorna: True si se aprobó, False si no existía
        """
        comentario = cls.query.get(comentario_id)
        if comentario:
            comentario.aprobado = True
            db.session.commit()
            return True
        return False
    
    @classmethod
    def rechazar(cls, comentario_id):
        """
        Rechaza/elimina un comentario
        
        Retorna: True si se eliminó, False si no existía
        """
        comentario = cls.query.get(comentario_id)
        if comentario:
            db.session.delete(comentario)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def listar_por_noticia(cls, noticia_id, solo_aprobados=True):
        """
        Lista los comentarios de una noticia
        
        Args:
            noticia_id: ID de la noticia
            solo_aprobados: si True, solo muestra comentarios aprobados
        
        Retorna: lista de comentarios ordenados por fecha (más antiguos primero)
        """
        query = cls.query.filter_by(noticia_id=noticia_id)
        if solo_aprobados:
            query = query.filter_by(aprobado=True)
        return query.order_by(cls.fecha_creacion.asc()).all()
    
    @classmethod
    def listar_pendientes(cls):
        """
        Lista todos los comentarios pendientes de aprobación
        """
        return cls.query.filter_by(aprobado=False).order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def contar_pendientes(cls):
        """
        Cuenta los comentarios pendientes de aprobación
        """
        return cls.query.filter_by(aprobado=False).count()
    
    @classmethod
    def contar_por_noticia(cls, noticia_id, solo_aprobados=True):
        """
        Cuenta los comentarios de una noticia
        """
        query = cls.query.filter_by(noticia_id=noticia_id)
        if solo_aprobados:
            query = query.filter_by(aprobado=True)
        return query.count()
    
    @classmethod
    def eliminar_por_noticia(cls, noticia_id):
        """
        Elimina todos los comentarios de una noticia (útil al eliminar la noticia)
        
        Retorna: número de comentarios eliminados
        """
        eliminados = cls.query.filter_by(noticia_id=noticia_id).delete()
        db.session.commit()
        return eliminados
    
    def to_dict(self):
        """Convierte el comentario a diccionario"""
        return {
            'id': self.id,
            'noticia_id': self.noticia_id,
            'autor_nombre': self.autor_nombre,
            'autor_email': self.autor_email,
            'contenido': self.contenido,
            'aprobado': self.aprobado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_formateada': self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f'<ComentarioNoticia {self.id} - {self.autor_nombre[:20]}>'