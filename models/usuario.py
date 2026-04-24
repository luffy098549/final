# ============================================================
# IMPORTS
# ============================================================
from extensions import db
from datetime import datetime
from flask_login import UserMixin

# ============================================================
# MODELO USUARIO
# ============================================================
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
    tipo = db.Column(db.String(50), default='ciudadano')
    rol = db.Column(db.String(50), nullable=True)
    
    # ===============================
    # CONFIGURACIÓN Y ESTADO
    # ===============================
    foto_perfil = db.Column(db.String(500))  # legacy/local
    foto_perfil_url = db.Column(db.String(500), nullable=True)  # cloudinary
    foto_perfil_public_id = db.Column(db.String(200), nullable=True)
    
    activo = db.Column(db.Boolean, default=True)
    notas_admin = db.Column(db.Text)
    
    # ===============================
    # FECHAS
    # ===============================
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # ===============================
    # FLASK LOGIN
    # ===============================
    def get_id(self):
        return str(self.id)
    
    def is_active(self):
        return self.activo
    
    # ===============================
    # FOTO PERFIL
    # ===============================
    def obtener_foto_perfil(self):
        if self.foto_perfil_url:
            return self.foto_perfil_url
        elif self.foto_perfil:
            return self.foto_perfil
        return None
    
    # ===============================
    # ROLES
    # ===============================
    def es_admin(self):
        return self.rol in ['super_admin', 'admin'] or self.tipo == 'admin'
    
    def es_super_admin(self):
        return self.rol == 'super_admin'
    
    def es_admin_normal(self):
        return self.rol == 'admin'
    
    def es_moderador(self):
        return self.rol == 'moderador'
    
    def es_ciudadano(self):
        return not self.es_admin() and not self.es_moderador()
    
    # ===============================
    # PERMISOS
    # ===============================
    def tiene_permiso(self, permiso):
        from rol import tiene_permiso
        
        if hasattr(permiso, 'value'):
            permiso = permiso.value
        
        return tiene_permiso(self.rol, permiso)
    
    def tiene_permisos(self, permisos, require_all=False):
        from rol import tiene_permisos
        
        permisos_valores = []
        for p in permisos:
            if hasattr(p, 'value'):
                permisos_valores.append(p.value)
            else:
                permisos_valores.append(p)
        
        return tiene_permisos(self.rol, permisos_valores, require_all)
    
    def obtener_permisos(self):
        from rol import obtener_permisos_rol
        return obtener_permisos_rol(self.rol)
    
    # ===============================
    # UTILIDAD
    # ===============================
    def actualizar_ultimo_acceso(self):
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def esta_activo(self):
        return self.activo
    
    def desactivar(self):
        self.activo = False
        db.session.commit()
    
    def activar(self):
        self.activo = True
        db.session.commit()
    
    def obtener_nombre_completo(self):
        if self.nombre_completo:
            return self.nombre_completo
        elif self.nombre and self.apellidos:
            return f"{self.nombre} {self.apellidos}"
        elif self.nombre:
            return self.nombre
        else:
            return self.email.split('@')[0]
    
    # ===============================
    # SERIALIZACIÓN
    # ===============================
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.obtener_nombre_completo(),
            'cedula': self.cedula,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'tipo': self.tipo,
            'rol': self.rol,
            'activo': self.activo,
            'foto_perfil': self.obtener_foto_perfil(),
            'foto_perfil_url': self.foto_perfil_url,
            'es_admin': self.es_admin(),
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
        }
    
    def to_dict_public(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.obtener_nombre_completo(),
            'foto_perfil': self.obtener_foto_perfil(),
        }
    
    # ===============================
    # MÉTODOS ESTÁTICOS
    # ===============================
    @staticmethod
    def obtener_por_email(email):
        return Usuario.query.filter_by(email=email).first()
    
    @staticmethod
    def obtener_por_id(user_id):
        return Usuario.query.get(user_id)
    
    # ===============================
    # REPRESENTACIÓN (🔥 CLAVE)
    # ===============================
    def __repr__(self):
        return f"<Usuario {self.email}>"
    
    def __str__(self):
        # 🔥 IMPORTANTE: devolver string simple
        return self.email