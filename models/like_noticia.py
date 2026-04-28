# models/like_noticia.py
from extensions import db
from datetime import datetime

class LikeNoticia(db.Model):
    __tablename__ = 'likes_noticia'
    
    id = db.Column(db.Integer, primary_key=True)
    noticia_id = db.Column(db.Integer, db.ForeignKey('noticias.id'), nullable=False, index=True)
    usuario_ip = db.Column(db.String(45), nullable=False)  # IPv4 (15) o IPv6 (45)
    usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Restricción única: un solo like por IP y noticia
    __table_args__ = (
        db.UniqueConstraint('noticia_id', 'usuario_ip', name='uq_like_noticia_ip'),
    )
    
    @classmethod
    def dar_like(cls, noticia_id, usuario_ip, usuario_email=None):
        """
        Toggle like/unlike para una noticia.
        
        Retorna:
            (liked: bool, total_likes: int)
            liked=True → se dio like
            liked=False → se quitó el like
        """
        # Verificar si ya existe like para esta IP y noticia
        like_existente = cls.query.filter_by(
            noticia_id=noticia_id,
            usuario_ip=usuario_ip
        ).first()
        
        if like_existente:
            # Eliminar like (unlike)
            db.session.delete(like_existente)
            db.session.commit()
            total = cls.contar_por_noticia(noticia_id)
            return (False, total)
        else:
            # Crear nuevo like
            nuevo_like = cls(
                noticia_id=noticia_id,
                usuario_ip=usuario_ip,
                usuario_email=usuario_email
            )
            db.session.add(nuevo_like)
            db.session.commit()
            total = cls.contar_por_noticia(noticia_id)
            return (True, total)
    
    @classmethod
    def contar_por_noticia(cls, noticia_id):
        """Cuenta el total de likes para una noticia"""
        return cls.query.filter_by(noticia_id=noticia_id).count()
    
    @classmethod
    def ya_dio_like(cls, noticia_id, usuario_ip):
        """Verifica si una IP ya ha dado like a una noticia"""
        return cls.query.filter_by(
            noticia_id=noticia_id,
            usuario_ip=usuario_ip
        ).first() is not None
    
    @classmethod
    def obtener_likes_usuario(cls, usuario_email):
        """Obtiene todas las noticias que ha likedo un usuario (por email)"""
        return cls.query.filter_by(usuario_email=usuario_email).all()
    
    @classmethod
    def limpiar_likes_anons(cls, dias=30):
        """Elimina likes anónimos más antiguos de X días"""
        from datetime import timedelta
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        eliminados = cls.query.filter(
            cls.usuario_email.is_(None),
            cls.fecha_creacion < fecha_limite
        ).delete()
        db.session.commit()
        return eliminados
    
    def to_dict(self):
        """Convierte el like a diccionario"""
        return {
            'id': self.id,
            'noticia_id': self.noticia_id,
            'usuario_ip': self.usuario_ip,
            'usuario_email': self.usuario_email,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }