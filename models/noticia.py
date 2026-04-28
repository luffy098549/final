# models/noticia.py
from extensions import db
from datetime import datetime
import re
import random
import string
from sqlalchemy.orm import relationship, backref

class CategoriaNoticia(db.Model):
    __tablename__ = 'categorias_noticia'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    color = db.Column(db.String(7), default='#3b82f6')  # Hex color
    icono = db.Column(db.String(50), default='newspaper')
    activa = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)
    
    # Relación de vuelta con noticias
    noticias = relationship('Noticia', back_populates='categoria', lazy='dynamic')
    
    @staticmethod
    def slugify(texto):
        """Convierte un texto en slug amigable para URL"""
        texto = texto.lower()
        texto = re.sub(r'[^\w\s-]', '', texto)
        texto = re.sub(r'[\s_-]+', '-', texto)
        texto = texto.strip('-')
        return texto
    
    @classmethod
    def obtener_o_crear(cls, nombre):
        """Obtiene una categoría existente o la crea si no existe"""
        slug = cls.slugify(nombre)
        categoria = cls.query.filter_by(slug=slug).first()
        if not categoria:
            categoria = cls(nombre=nombre, slug=slug)
            db.session.add(categoria)
            db.session.commit()
        return categoria
    
    @classmethod
    def todas_activas(cls):
        """Retorna todas las categorías activas ordenadas por orden"""
        return cls.query.filter_by(activa=True).order_by(cls.orden.asc(), cls.nombre.asc()).all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'slug': self.slug,
            'color': self.color,
            'icono': self.icono,
            'activa': self.activa,
            'orden': self.orden,
            'total_noticias': self.noticias.count()
        }


class Noticia(db.Model):
    __tablename__ = 'noticias'
    
    ESTADOS = ['borrador', 'publicado', 'archivado']
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)
    titulo = db.Column(db.String(300), nullable=False)
    resumen = db.Column(db.Text, nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    imagen_url = db.Column(db.String(500))
    tags = db.Column(db.JSON, default=list)  # Array de tags
    
    # Estado y visibilidad
    estado = db.Column(db.String(20), default='borrador', index=True)
    destacada = db.Column(db.Boolean, default=False, index=True)
    vistas = db.Column(db.Integer, default=0)
    
    # Fechas
    fecha_publicacion = db.Column(db.DateTime, nullable=True, index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Llaves foráneas
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_noticia.id'), nullable=False)
    autor_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=False)
    
    # Relaciones
    categoria = relationship('CategoriaNoticia', back_populates='noticias')
    autor = relationship('Usuario', foreign_keys=[autor_email])
    
    # Relaciones con likes y comentarios (para extender después)
    # likes = relationship('LikeNoticia', back_populates='noticia', lazy='dynamic', cascade='all, delete-orphan')
    # comentarios = relationship('ComentarioNoticia', back_populates='noticia', lazy='dynamic', cascade='all, delete-orphan')
    
    @staticmethod
    def generar_slug(titulo):
        """Genera un slug único a partir del título"""
        base_slug = re.sub(r'[\s_-]+', '-', re.sub(r'[^\w\s-]', '', titulo.lower())).strip('-')
        slug = base_slug
        existe = Noticia.query.filter_by(slug=slug).first()
        
        # Agregar sufijo numérico hasta encontrar uno único
        while existe:
            sufijo = ''.join(random.choices(string.digits, k=3))
            slug = f"{base_slug}-{sufijo}"
            existe = Noticia.query.filter_by(slug=slug).first()
        
        return slug
    
    @classmethod
    def crear(cls, titulo, contenido, autor_email, categoria_id, 
              resumen=None, imagen_url=None, tags=None, destacada=False, estado='borrador'):
        """Crea una nueva noticia"""
        if not resumen:
            # Si no hay resumen, tomar primeros 200 caracteres
            resumen = contenido[:200] + ('...' if len(contenido) > 200 else '')
        
        noticia = cls(
            slug=cls.generar_slug(titulo),
            titulo=titulo,
            resumen=resumen,
            contenido=contenido,
            autor_email=autor_email,
            categoria_id=categoria_id,
            imagen_url=imagen_url,
            tags=tags or [],
            destacada=destacada,
            estado=estado
        )
        
        db.session.add(noticia)
        db.session.commit()
        return noticia
    
    def publicar(self):
        """Publica la noticia asignando fecha de publicación"""
        if self.estado != 'publicado':
            self.estado = 'publicado'
            if not self.fecha_publicacion:
                self.fecha_publicacion = datetime.utcnow()
            db.session.commit()
    
    def archivar(self):
        """Archiva la noticia"""
        if self.estado != 'archivado':
            self.estado = 'archivado'
            db.session.commit()
    
    def incrementar_vistas(self):
        """Incrementa el contador de vistas"""
        self.vistas += 1
        db.session.commit()
    
    @classmethod
    def buscar_por_slug(cls, slug):
        """Busca una noticia por su slug"""
        return cls.query.filter_by(slug=slug).first()
    
    @classmethod
    def listar_publicadas(cls, pagina=1, por_pagina=9, categoria_slug=None):
        """Lista noticias publicadas con paginación"""
        query = cls.query.filter_by(estado='publicado')
        
        if categoria_slug:
            categoria = CategoriaNoticia.query.filter_by(slug=categoria_slug).first()
            if categoria:
                query = query.filter_by(categoria_id=categoria.id)
        
        query = query.order_by(cls.fecha_publicacion.desc(), cls.fecha_creacion.desc())
        
        paginacion = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        
        return {
            'items': paginacion.items,
            'total': paginacion.total,
            'pagina': paginacion.page,
            'por_pagina': paginacion.per_page,
            'total_paginas': paginacion.pages,
            'tiene_siguiente': paginacion.has_next,
            'tiene_anterior': paginacion.has_prev
        }
    
    @classmethod
    def listar_destacadas(cls, limite=3):
        """Lista las noticias destacadas publicadas"""
        return cls.query.filter_by(
            estado='publicado', 
            destacada=True
        ).order_by(
            cls.fecha_publicacion.desc()
        ).limit(limite).all()
    
    def to_dict(self, incluir_contenido=False):
        """Convierte la noticia a diccionario"""
        from flask import url_for
        
        resultado = {
            'id': self.id,
            'slug': self.slug,
            'titulo': self.titulo,
            'resumen': self.resumen,
            'imagen_url': self.imagen_url,
            'tags': self.tags,
            'estado': self.estado,
            'destacada': self.destacada,
            'vistas': self.vistas,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'fecha_publicacion': self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
            'categoria': self.categoria.to_dict() if self.categoria else None,
            'autor': {
                'email': self.autor.email if self.autor else None,
                'nombre': self.autor.nombre if self.autor else None,
                'foto_perfil': self.autor.foto_perfil_url if self.autor else None
            } if self.autor else None
        }
        
        if incluir_contenido:
            resultado['contenido'] = self.contenido
        
        return resultado


# Modelos para likes y comentarios (para extender después)
# class LikeNoticia(db.Model):
#     __tablename__ = 'likes_noticia'
#     
#     id = db.Column(db.Integer, primary_key=True)
#     noticia_id = db.Column(db.Integer, db.ForeignKey('noticias.id'), nullable=False)
#     usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=False)
#     creado_en = db.Column(db.DateTime, default=datetime.utcnow)
#     
#     __table_args__ = (db.UniqueConstraint('noticia_id', 'usuario_email', name='uq_like_noticia_usuario'),)


# class ComentarioNoticia(db.Model):
#     __tablename__ = 'comentarios_noticia'
#     
#     id = db.Column(db.Integer, primary_key=True)
#     noticia_id = db.Column(db.Integer, db.ForeignKey('noticias.id'), nullable=False)
#     usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=False)
#     contenido = db.Column(db.Text, nullable=False)
#     aprobado = db.Column(db.Boolean, default=False)
#     creado_en = db.Column(db.DateTime, default=datetime.utcnow)
#     
#     noticia = relationship('Noticia', backref=db.backref('comentarios', lazy='dynamic'))
#     usuario = relationship('Usuario')