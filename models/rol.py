# ============================================================
# models/rol.py
# MODELO DE ROLES COMPLETO
# ============================================================

from extensions import db
from datetime import datetime


class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    nivel = db.Column(db.Integer, default=0)  # 0=ciudadano, 1=moderador, 2=admin, 3=super_admin
    es_defecto = db.Column(db.Boolean, default=False)  # Rol asignado a nuevos usuarios
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ===============================
    # RELACIONES (CORREGIDAS)
    # ===============================
    # 🔥 Cambiado: back_populates='rol_relacion' para coincidir con Usuario
    usuarios = db.relationship('Usuario', back_populates='rol_relacion', lazy='dynamic')
    permisos = db.relationship('RolPermiso', back_populates='rol', cascade='all, delete-orphan')
    
    # ===============================
    # REPRESENTACIÓN
    # ===============================
    def __repr__(self):
        return f'<Rol {self.nombre}>'
    
    def __str__(self):
        return self.nombre
    
    # ===============================
    # MÉTODOS DE CLASE
    # ===============================
    @classmethod
    def crear_roles_defecto(cls):
        """Crea los roles por defecto del sistema"""
        roles_default = [
            {'nombre': 'ciudadano', 'descripcion': 'Usuario regular del sistema', 'nivel': 0, 'es_defecto': True},
            {'nombre': 'moderador', 'descripcion': 'Puede gestionar contenido y moderar comentarios', 'nivel': 1, 'es_defecto': False},
            {'nombre': 'admin', 'descripcion': 'Administrador del sistema', 'nivel': 2, 'es_defecto': False},
            {'nombre': 'super_admin', 'descripcion': 'Super administrador con control total', 'nivel': 3, 'es_defecto': False},
        ]
        
        for rol_data in roles_default:
            existe = cls.query.filter_by(nombre=rol_data['nombre']).first()
            if not existe:
                rol = cls(**rol_data)
                db.session.add(rol)
        
        db.session.commit()
    
    @classmethod
    def obtener_por_nombre(cls, nombre):
        """Obtiene un rol por su nombre"""
        return cls.query.filter_by(nombre=nombre).first()
    
    @classmethod
    def obtener_activos(cls):
        """Obtiene todos los roles activos"""
        return cls.query.filter_by(activo=True).order_by(cls.nivel).all()
    
    @classmethod
    def obtener_por_defecto(cls):
        """Obtiene el rol por defecto para nuevos usuarios"""
        return cls.query.filter_by(es_defecto=True, activo=True).first()
    
    # ===============================
    # MÉTODOS DE INSTANCIA
    # ===============================
    def tiene_permiso(self, permiso_codigo):
        """Verifica si este rol tiene un permiso específico"""
        for rp in self.permisos:
            if rp.permiso and rp.permiso.codigo == permiso_codigo:
                return True
        return False
    
    def tiene_permisos(self, permisos_codigos, require_all=False):
        """
        Verifica si este rol tiene múltiples permisos
        
        Args:
            permisos_codigos: Lista de códigos de permisos
            require_all: Si True, necesita todos; si False, necesita al menos uno
        
        Returns:
            bool: True si cumple la condición
        """
        if require_all:
            return all(self.tiene_permiso(p) for p in permisos_codigos)
        else:
            return any(self.tiene_permiso(p) for p in permisos_codigos)
    
    def obtener_permisos_codigos(self):
        """Obtiene la lista de códigos de permisos del rol"""
        return [rp.permiso.codigo for rp in self.permisos if rp.permiso]
    
    def obtener_permisos_detalle(self):
        """Obtiene la lista de permisos con detalles"""
        return [rp.permiso.to_dict() for rp in self.permisos if rp.permiso]
    
    def asignar_permiso(self, permiso):
        """Asigna un permiso a este rol"""
        from models.rol_permiso import RolPermiso
        from models.permiso import Permiso
        
        # Obtener ID del permiso si se pasó como objeto o código
        if isinstance(permiso, Permiso):
            permiso_id = permiso.id
        elif isinstance(permiso, str):
            permiso_obj = Permiso.query.filter_by(codigo=permiso).first()
            if not permiso_obj:
                return False
            permiso_id = permiso_obj.id
        else:
            permiso_id = permiso
        
        # Verificar si ya existe
        existe = RolPermiso.query.filter_by(
            rol_id=self.id,
            permiso_id=permiso_id
        ).first()
        
        if existe:
            return False
        
        # Crear nueva asignación
        rp = RolPermiso(rol_id=self.id, permiso_id=permiso_id)
        db.session.add(rp)
        db.session.commit()
        return True
    
    def eliminar_permiso(self, permiso):
        """Elimina un permiso de este rol"""
        from models.rol_permiso import RolPermiso
        from models.permiso import Permiso
        
        # Obtener ID del permiso
        if isinstance(permiso, Permiso):
            permiso_id = permiso.id
        elif isinstance(permiso, str):
            permiso_obj = Permiso.query.filter_by(codigo=permiso).first()
            if not permiso_obj:
                return False
            permiso_id = permiso_obj.id
        else:
            permiso_id = permiso
        
        # Eliminar asignación
        rp = RolPermiso.query.filter_by(
            rol_id=self.id,
            permiso_id=permiso_id
        ).first()
        
        if rp:
            db.session.delete(rp)
            db.session.commit()
            return True
        return False
    
    def limpiar_permisos(self):
        """Elimina todos los permisos de este rol"""
        for rp in self.permisos:
            db.session.delete(rp)
        db.session.commit()
    
    # ===============================
    # SERIALIZACIÓN
    # ===============================
    def to_dict(self):
        """Convierte el rol a diccionario básico"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'nivel': self.nivel,
            'es_defecto': self.es_defecto,
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_dict_complete(self):
        """Convierte el rol a diccionario con permisos incluidos"""
        data = self.to_dict()
        data['permisos'] = [p.permiso.to_dict() for p in self.permisos if p.permiso]
        data['total_usuarios'] = self.usuarios.count()
        return data
    
    # ===============================
    # MÉTODOS DE VALIDACIÓN
    # ===============================
    def puede_editar_rol(self, target_rol):
        """
        Verifica si este rol puede editar otro rol
        Un rol solo puede editar roles de nivel inferior
        """
        if not target_rol:
            return False
        return self.nivel > target_rol.nivel
    
    def puede_asignar_permiso(self, permiso_codigo):
        """
        Verifica si este rol puede asignar un permiso específico
        Los roles solo pueden asignar permisos que ellos mismos tienen
        """
        return self.tiene_permiso(permiso_codigo)