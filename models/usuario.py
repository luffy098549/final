# models/usuario.py
from extensions import db
from datetime import datetime
from flask_login import UserMixin

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # ===============================
    # DATOS PERSONALES
    # ===============================
    nombre = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    nombre_completo = db.Column(db.String(150))
    cedula = db.Column(db.String(50))
    fecha_nacimiento = db.Column(db.String(50))
    direccion = db.Column(db.Text)
    telefono = db.Column(db.String(50))
    
    # ===============================
    # ROLES Y PERMISOS
    # ===============================
    tipo = db.Column(db.String(50), default='ciudadano')  # admin / ciudadano
    rol = db.Column(db.String(50), nullable=True)  # super_admin, admin, moderador
    
    # ===============================
    # CONFIGURACIÓN Y ESTADO
    # ===============================
    foto_perfil = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)
    notas_admin = db.Column(db.Text)
    
    # ===============================
    # FECHAS
    # ===============================
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # ===============================
    # MÉTODO PARA FLASK-LOGIN
    # ===============================
    def get_id(self):
        return str(self.id)
    
    def is_active(self):
        return self.activo
    
    # ===============================
    # MÉTODOS DE VERIFICACIÓN DE ROLES
    # ===============================
    
    def es_admin(self):
        """Verifica si el usuario tiene permisos de administrador"""
        return self.rol in ['super_admin', 'admin'] or self.tipo == 'admin'
    
    def es_super_admin(self):
        """Verifica si es Super Administrador"""
        return self.rol == 'super_admin'
    
    def es_admin_normal(self):
        """Verifica si es Administrador normal (no super)"""
        return self.rol == 'admin'
    
    def es_moderador(self):
        """Verifica si es Moderador"""
        return self.rol == 'moderador'
    
    def es_ciudadano(self):
        """Verifica si es Ciudadano normal"""
        return not self.es_admin() and not self.es_moderador()
    
    # ===============================
    # MÉTODOS DE PERMISOS
    # ===============================
    
    def tiene_permiso(self, permiso):
        """
        Verifica si el usuario tiene un permiso específico
        
        Args:
            permiso (str o Enum): El permiso a verificar
        
        Returns:
            bool: True si tiene el permiso, False en caso contrario
        """
        from rol import tiene_permiso
        if hasattr(permiso, 'value'):
            permiso = permiso.value
        return tiene_permiso(self.rol, permiso)
    
    def tiene_permisos(self, permisos, require_all=False):
        """
        Verifica si el usuario tiene múltiples permisos
        
        Args:
            permisos (list): Lista de permisos a verificar
            require_all (bool): Si True, requiere todos; si False, requiere al menos uno
        
        Returns:
            bool: True si cumple con los requisitos
        """
        from rol import tiene_permisos
        permisos_valores = []
        for p in permisos:
            if hasattr(p, 'value'):
                permisos_valores.append(p.value)
            else:
                permisos_valores.append(p)
        return tiene_permisos(self.rol, permisos_valores, require_all)
    
    def obtener_permisos(self):
        """
        Obtiene todos los permisos del usuario según su rol
        
        Returns:
            list: Lista de permisos que tiene el usuario
        """
        from rol import obtener_permisos_rol
        return obtener_permisos_rol(self.rol)
    
    # ===============================
    # MÉTODOS DE UTILIDAD
    # ===============================
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha del último acceso"""
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def esta_activo(self):
        """Verifica si el usuario está activo"""
        return self.activo
    
    def desactivar(self):
        """Desactiva el usuario"""
        self.activo = False
        db.session.commit()
    
    def activar(self):
        """Activa el usuario"""
        self.activo = True
        db.session.commit()
    
    def obtener_nombre_completo(self):
        """Obtiene el nombre completo del usuario"""
        if self.nombre_completo:
            return self.nombre_completo
        elif self.nombre and self.apellidos:
            return f"{self.nombre} {self.apellidos}"
        elif self.nombre:
            return self.nombre
        else:
            return self.email.split('@')[0]
    
    # ===============================
    # MÉTODOS DE SERIALIZACIÓN
    # ===============================
    
    def to_dict(self):
        """Convierte el usuario a diccionario"""
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.nombre_completo or self.obtener_nombre_completo(),
            'cedula': self.cedula,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'tipo': self.tipo,
            'rol': self.rol,
            'activo': self.activo,
            'foto_perfil': self.foto_perfil,
            'es_admin': self.es_admin(),
            'es_super_admin': self.es_super_admin(),
            'es_moderador': self.es_moderador(),
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
        }
    
    def to_dict_public(self):
        """Convierte a diccionario para vista pública (sin datos sensibles)"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.obtener_nombre_completo(),
            'foto_perfil': self.foto_perfil,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
        }
    
    # ===============================
    # MÉTODOS ESTÁTICOS
    # ===============================
    
    @staticmethod
    def obtener_por_email(email):
        """Obtiene un usuario por su email"""
        return Usuario.query.filter_by(email=email).first()
    
    @staticmethod
    def obtener_por_id(user_id):
        """Obtiene un usuario por su ID"""
        return Usuario.query.get(user_id)
    
    @staticmethod
    def obtener_administradores():
        """Obtiene todos los administradores"""
        from sqlalchemy import or_
        return Usuario.query.filter(
            or_(
                Usuario.rol.in_(['super_admin', 'admin']),
                Usuario.tipo == 'admin'
            ),
            Usuario.activo == True
        ).all()
    
    @staticmethod
    def obtener_moderadores():
        """Obtiene todos los moderadores"""
        return Usuario.query.filter_by(rol='moderador', activo=True).all()
    
    # ===============================
    # REPRESENTACIÓN
    # ===============================
    
    def __repr__(self):
        return f"<Usuario {self.email} - Rol: {self.rol or self.tipo}>"
    
    def __str__(self):
        return self.obtener_nombre_completo()