"""
Modelo para gestión de usuarios (capa de abstracción sobre auth)
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USUARIOS_FILE = DATA_DIR / "usuarios.json"

class Usuario:
    """Modelo para usuarios del sistema"""
    
    ROLES = {
        'ciudadano': 'Ciudadano',
        'moderador': 'Moderador',
        'admin': 'Administrador',
        'super_admin': 'Super Administrador'
    }
    
    def __init__(self, email, datos):
        self.email = email
        self.nombre = datos.get('nombre', '')
        self.apellidos = datos.get('apellidos', '')
        self.nombre_completo = datos.get('nombre_completo', f"{self.nombre} {self.apellidos}".strip())
        self.tipo = datos.get('tipo', 'ciudadano')
        self.rol = datos.get('rol', None)
        self.telefono = datos.get('telefono', '')
        self.cedula = datos.get('cedula', '')
        self.fecha_nacimiento = datos.get('fecha_nacimiento', '')
        self.direccion = datos.get('direccion', '')
        self.fecha_registro = datos.get('fecha_registro', '')
        self.ultimo_acceso = datos.get('ultimo_acceso', None)
        self.activo = datos.get('activo', True)
        self.notas_admin = datos.get('notas_admin', '')
        self.foto_perfil = datos.get('foto_perfil', '')
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'tipo': self.tipo,
            'rol': self.rol,
            'telefono': self.telefono,
            'cedula': self.cedula,
            'fecha_nacimiento': self.fecha_nacimiento,
            'direccion': self.direccion,
            'fecha_registro': self.fecha_registro,
            'ultimo_acceso': self.ultimo_acceso,
            'activo': self.activo,
            'notas_admin': self.notas_admin,
            'foto_perfil': self.foto_perfil
        }
    
    @classmethod
    def cargar_todos(cls):
        """Carga todos los usuarios"""
        from auth import _cargar_usuarios
        usuarios_data = _cargar_usuarios()
        return [cls(email, datos) for email, datos in usuarios_data.items()]
    
    @classmethod
    def buscar_por_email(cls, email):
        """Busca un usuario por email"""
        from auth import _cargar_usuarios
        usuarios_data = _cargar_usuarios()
        if email in usuarios_data:
            return cls(email, usuarios_data[email])
        return None
    
    def tiene_permiso(self, permiso):
        """Verifica si el usuario tiene un permiso específico"""
        from rol import tiene_permiso
        return tiene_permiso(self.rol, permiso)
    
    def es_admin(self):
        """Verifica si es administrador"""
        return self.rol in ['admin', 'super_admin'] or self.tipo == 'admin'
    
    def es_super_admin(self):
        """Verifica si es super administrador"""
        return self.rol == 'super_admin'