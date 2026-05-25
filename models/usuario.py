# models/usuario.py
# MODELO USUARIO COMPLETO CON INTEGRACIÓN DE ROLES Y VERIFICACIÓN DE EMAIL
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
    rol = db.Column(db.String(50), nullable=True)  # Legacy: nombre del rol
    
    # 🔥 NUEVO: Relación con tabla roles (FK)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    rol_relacion = db.relationship('Rol', back_populates='usuarios', foreign_keys=[rol_id])
    
    # ===============================
    # CONFIGURACIÓN Y ESTADO
    # ===============================
    foto_perfil = db.Column(db.String(500))  # legacy/local
    foto_perfil_url = db.Column(db.String(500), nullable=True)  # cloudinary
    foto_perfil_public_id = db.Column(db.String(200), nullable=True)
    
    # Google OAuth
    google_id = db.Column(db.String(100), nullable=True, unique=True)
    
    activo = db.Column(db.Boolean, default=True)
    
    # Verificación de email
    email_verificado = db.Column(db.Boolean, default=False)
    token_verificacion = db.Column(db.String(200), nullable=True)
    token_expiracion = db.Column(db.DateTime, nullable=True)
    
    notas_admin = db.Column(db.Text)
    
    # Notificaciones
    notificaciones_email = db.Column(db.Boolean, default=True)
    notificaciones_whatsapp = db.Column(db.Boolean, default=False)
    
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
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
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
    # ROLES (Métodos de compatibilidad)
    # ===============================
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol in ['super_admin', 'admin'] or self.tipo == 'admin'
    
    def es_super_admin(self):
        """Verifica si el usuario es super administrador"""
        return self.rol == 'super_admin'
    
    def es_admin_normal(self):
        """Verifica si el usuario es admin normal"""
        return self.rol == 'admin'
    
    def es_moderador(self):
        """Verifica si el usuario es moderador"""
        return self.rol == 'moderador'
    
    def es_ciudadano(self):
        """Verifica si el usuario es ciudadano"""
        return not self.es_admin() and not self.es_moderador()
    
    def obtener_nivel_rol(self):
        """Obtiene el nivel numérico del rol (0=ciudadano, 1=moderador, 2=admin, 3=super_admin)"""
        if self.rol_relacion:
            return self.rol_relacion.nivel
        
        # Fallback por nombre
        niveles = {
            'ciudadano': 0,
            'moderador': 1,
            'admin': 2,
            'super_admin': 3
        }
        return niveles.get(self.rol, 0)
    
    # ===============================
    # PERMISOS
    # ===============================
    def tiene_permiso(self, permiso):
        """
        Verifica si el usuario tiene un permiso específico.
        Primero usa el nuevo sistema (rol_relacion), luego fallback al antiguo.
        """
        from rol import tiene_permiso as tiene_permiso_legacy
        
        # Obtener el código del permiso
        if hasattr(permiso, 'value'):
            permiso_codigo = permiso.value
        else:
            permiso_codigo = permiso
        
        # Nuevo sistema: usar rol_relacion
        if self.rol_relacion and self.rol_relacion.activo:
            return self.rol_relacion.tiene_permiso(permiso_codigo)
        
        # Fallback: sistema legacy (rol.py)
        return tiene_permiso_legacy(self.rol, permiso_codigo)
    
    def tiene_permisos(self, permisos, require_all=False):
        """
        Verifica si el usuario tiene múltiples permisos.
        
        Args:
            permisos: Lista de permisos a verificar
            require_all: Si True, necesita todos; si False, necesita al menos uno
        
        Returns:
            bool: True si cumple la condición
        """
        from rol import tiene_permisos as tiene_permisos_legacy
        
        # Convertir permisos a códigos
        permisos_codigos = []
        for p in permisos:
            if hasattr(p, 'value'):
                permisos_codigos.append(p.value)
            else:
                permisos_codigos.append(p)
        
        # Nuevo sistema
        if self.rol_relacion and self.rol_relacion.activo:
            if require_all:
                return all(self.rol_relacion.tiene_permiso(p) for p in permisos_codigos)
            else:
                return any(self.rol_relacion.tiene_permiso(p) for p in permisos_codigos)
        
        # Fallback legacy
        return tiene_permisos_legacy(self.rol, permisos_codigos, require_all)
    
    def obtener_permisos(self):
        """Obtiene la lista de códigos de permisos que tiene el usuario"""
        from rol import obtener_permisos_rol as obtener_permisos_legacy
        
        if self.rol_relacion and self.rol_relacion.activo:
            return [rp.permiso.codigo for rp in self.rol_relacion.permisos if rp.permiso]
        
        return obtener_permisos_legacy(self.rol)
    
    # ===============================
    # ROL (Nuevos métodos)
    # ===============================
    def actualizar_rol(self, rol_nombre):
        """
        Actualiza el rol del usuario usando el nuevo sistema.
        
        Args:
            rol_nombre: Nombre del rol ('ciudadano', 'moderador', 'admin', 'super_admin')
        
        Returns:
            bool: True si se actualizó correctamente
        """
        from models.rol import Rol
        
        rol_obj = Rol.query.filter_by(nombre=rol_nombre).first()
        if rol_obj:
            self.rol_id = rol_obj.id
            self.rol = rol_nombre  # Mantener compatibilidad
            db.session.commit()
            return True
        return False
    
    def migrar_a_nuevo_rol(self):
        """
        Migra el usuario del sistema antiguo (campo rol string) al nuevo (rol_id FK).
        Útil para migrar usuarios existentes después de crear las tablas roles.
        
        Returns:
            bool: True si se migró o ya estaba migrado
        """
        if self.rol and not self.rol_id:
            from models.rol import Rol
            rol_obj = Rol.query.filter_by(nombre=self.rol).first()
            if rol_obj:
                self.rol_id = rol_obj.id
                db.session.commit()
                return True
        return False
    
    # ===============================
    # UTILIDAD
    # ===============================
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha de último acceso"""
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def esta_activo(self):
        """Verifica si la cuenta está activa"""
        return self.activo
    
    def desactivar(self):
        """Desactiva la cuenta del usuario"""
        self.activo = False
        db.session.commit()
    
    def activar(self):
        """Activa la cuenta del usuario"""
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
    # SERIALIZACIÓN
    # ===============================
    def to_dict(self):
        """Convierte el usuario a diccionario (completo)"""
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
            'rol_id': self.rol_id,
            'rol_nivel': self.obtener_nivel_rol(),
            'activo': self.activo,
            'email_verificado': self.email_verificado,
            'foto_perfil': self.obtener_foto_perfil(),
            'foto_perfil_url': self.foto_perfil_url,
            'google_id': self.google_id,
            'notificaciones_email': self.notificaciones_email,
            'notificaciones_whatsapp': self.notificaciones_whatsapp,
            'es_admin': self.es_admin(),
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
        }
    
    def to_dict_public(self):
        """Convierte el usuario a diccionario (público, sin datos sensibles)"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.obtener_nombre_completo(),
            'foto_perfil': self.obtener_foto_perfil(),
            'rol': self.rol,
        }
    
    def to_dict_admin(self):
        """Convierte el usuario a diccionario para administradores"""
        data = self.to_dict()
        data['notas_admin'] = self.notas_admin
        data['fecha_nacimiento'] = self.fecha_nacimiento
        return data
    
    # ===============================
    # MÉTODOS ESTÁTICOS
    # ===============================
    @staticmethod
    def obtener_por_email(email):
        """Busca usuario por email"""
        return Usuario.query.filter_by(email=email).first()
    
    @staticmethod
    def obtener_por_id(user_id):
        """Busca usuario por ID"""
        return Usuario.query.get(user_id)
    
    @staticmethod
    def obtener_por_google_id(google_id):
        """Busca usuario por Google ID"""
        return Usuario.query.filter_by(google_id=google_id).first()
    
    @staticmethod
    def obtener_todos_activos():
        """Obtiene todos los usuarios activos"""
        return Usuario.query.filter_by(activo=True).all()
    
    @staticmethod
    def obtener_administradores():
        """Obtiene todos los usuarios con rol de administrador"""
        return Usuario.query.filter(
            db.or_(
                Usuario.rol.in_(['super_admin', 'admin']),
                Usuario.tipo == 'admin'
            )
        ).all()
    
    # ===============================
    # REPRESENTACIÓN
    # ===============================
    def __repr__(self):
        return f"<Usuario {self.email}>"
    
    def __str__(self):
        return self.email