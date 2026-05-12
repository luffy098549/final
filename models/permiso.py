# ============================================================
# models/permiso.py
# MODELO DE PERMISOS COMPLETO
# ============================================================

from extensions import db
from datetime import datetime


class Permiso(db.Model):
    __tablename__ = 'permisos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(100), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    modulo = db.Column(db.String(50))
    descripcion = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    roles = db.relationship('RolPermiso', back_populates='permiso', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Permiso {self.codigo}>"
    
    def __str__(self):
        return self.nombre
    
    @classmethod
    def crear_permisos_defecto(cls):
        """Crea los permisos por defecto del sistema"""
        permisos_default = [
            # Usuarios
            ('ver_usuarios', 'Ver usuarios', 'usuarios', 'Permite ver la lista de usuarios'),
            ('editar_usuarios', 'Editar usuarios', 'usuarios', 'Permite editar datos de usuarios'),
            ('eliminar_usuarios', 'Eliminar usuarios', 'usuarios', 'Permite eliminar usuarios'),
            ('crear_usuarios', 'Crear usuarios', 'usuarios', 'Permite crear nuevos usuarios'),
            
            # Solicitudes
            ('ver_solicitudes', 'Ver solicitudes', 'solicitudes', 'Permite ver todas las solicitudes'),
            ('editar_solicitudes', 'Editar solicitudes', 'solicitudes', 'Permite editar solicitudes'),
            ('eliminar_solicitudes', 'Eliminar solicitudes', 'solicitudes', 'Permite eliminar solicitudes'),
            
            # Denuncias
            ('ver_denuncias', 'Ver denuncias', 'denuncias', 'Permite ver todas las denuncias'),
            ('editar_denuncias', 'Editar denuncias', 'denuncias', 'Permite editar denuncias'),
            ('eliminar_denuncias', 'Eliminar denuncias', 'denuncias', 'Permite eliminar denuncias'),
            
            # Contenido
            ('editar_contenido', 'Editar contenido', 'contenido', 'Permite editar contenido estático'),
            ('editar_menu', 'Editar menú', 'contenido', 'Permite editar el menú de navegación'),
            ('editar_transparencia', 'Editar transparencia', 'contenido', 'Permite editar documentos de transparencia'),
            
            # Noticias
            ('crear_noticias', 'Crear noticias', 'noticias', 'Permite crear nuevas noticias'),
            ('editar_noticias', 'Editar noticias', 'noticias', 'Permite editar noticias existentes'),
            ('eliminar_noticias', 'Eliminar noticias', 'noticias', 'Permite eliminar noticias'),
            ('moderar_comentarios', 'Moderar comentarios', 'noticias', 'Permite moderar comentarios en noticias'),
            
            # Sistema
            ('ver_configuracion', 'Ver configuración', 'sistema', 'Permite ver la configuración del sistema'),
            ('editar_configuracion', 'Editar configuración', 'sistema', 'Permite editar la configuración del sistema'),
            ('ver_logs', 'Ver logs', 'sistema', 'Permite ver los logs de actividad'),
            ('exportar_datos', 'Exportar datos', 'sistema', 'Permite exportar datos del sistema'),
            ('mantenimiento', 'Mantenimiento', 'sistema', 'Permite realizar tareas de mantenimiento'),
            
            # Roles y Permisos (solo super_admin)
            ('ver_roles', 'Ver roles', 'roles', 'Permite ver la lista de roles'),
            ('editar_roles', 'Editar roles', 'roles', 'Permite editar roles y permisos'),
        ]
        
        for codigo, nombre, modulo, descripcion in permisos_default:
            existe = cls.query.filter_by(codigo=codigo).first()
            if not existe:
                permiso = cls(
                    codigo=codigo,
                    nombre=nombre,
                    modulo=modulo,
                    descripcion=descripcion
                )
                db.session.add(permiso)
        
        db.session.commit()
    
    @classmethod
    def obtener_por_modulo(cls, modulo):
        """Obtiene todos los permisos de un módulo específico"""
        return cls.query.filter_by(modulo=modulo).order_by(cls.nombre).all()
    
    @classmethod
    def obtener_por_codigo(cls, codigo):
        """Obtiene un permiso por su código"""
        return cls.query.filter_by(codigo=codigo).first()
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'modulo': self.modulo,
            'descripcion': self.descripcion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }