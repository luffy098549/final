"""
Modelos de datos preparados para migrar a una base de datos real.
Actualmente usa almacenamiento en memoria/archivos JSON.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

# ================================================================
# CONFIGURACIÓN DE ALMACENAMIENTO
# ================================================================

DATA_DIR = "data"
SOLICITUDES_FILE = os.path.join(DATA_DIR, "solicitudes.json")
DENUNCIAS_FILE = os.path.join(DATA_DIR, "denuncias.json")
CONSULTAS_FILE = os.path.join(DATA_DIR, "consultas.json")
ADMIN_ACTIONS_FILE = os.path.join(DATA_DIR, "admin_actions.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Asegurar que el directorio data existe
os.makedirs(DATA_DIR, exist_ok=True)

# ================================================================
# FUNCIONES AUXILIARES DE PERSISTENCIA
# ================================================================

def _load_json(file_path: str, default: Any = None) -> Any:
    """Carga datos desde un archivo JSON."""
    if default is None:
        default = [] if 'solicitudes' in file_path or 'denuncias' in file_path else {}
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error cargando {file_path}: {e}")
    
    return default

def _save_json(file_path: str, data: Any) -> bool:
    """Guarda datos en un archivo JSON."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"Error guardando {file_path}: {e}")
        return False

# ================================================================
# MODELO: SOLICITUDES DE SERVICIO
# ================================================================

class Solicitud:
    """Modelo para solicitudes de servicios municipales."""
    
    ESTADOS = ['pendiente', 'en_proceso', 'completado', 'rechazado', 'cancelado']
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.folio = kwargs.get('folio', self._generar_folio())
        self.usuario_email = kwargs.get('usuario_email', '')
        self.usuario_nombre = kwargs.get('usuario_nombre', '')
        self.usuario_cedula = kwargs.get('usuario_cedula', '')
        self.servicio_id = kwargs.get('servicio_id', '')
        self.servicio_nombre = kwargs.get('servicio_nombre', '')
        self.descripcion = kwargs.get('descripcion', '')
        self.estado = kwargs.get('estado', 'pendiente')
        self.fecha_creacion = kwargs.get('fecha_creacion', datetime.now().isoformat())
        self.fecha_actualizacion = kwargs.get('fecha_actualizacion', datetime.now().isoformat())
        self.fecha_resolucion = kwargs.get('fecha_resolucion', None)
        self.asignado_a = kwargs.get('asignado_a', None)  # Email del admin asignado
        self.comentarios_admin = kwargs.get('comentarios_admin', [])
        self.documentos = kwargs.get('documentos', [])
        self.historial = kwargs.get('historial', [self._crear_evento('creada', 'Solicitud creada por el usuario')])
    
    def _generar_folio(self):
        """Genera un folio único para la solicitud."""
        fecha = datetime.now().strftime("%y%m")
        import random
        return f"SOL-{fecha}-{random.randint(1000, 9999)}"
    
    def _crear_evento(self, tipo: str, descripcion: str, usuario: str = 'sistema'):
        return {
            'fecha': datetime.now().isoformat(),
            'tipo': tipo,
            'descripcion': descripcion,
            'usuario': usuario
        }
    
    def actualizar_estado(self, nuevo_estado: str, comentario: str = '', admin_email: str = ''):
        """Actualiza el estado de la solicitud y registra en historial."""
        if nuevo_estado not in self.ESTADOS:
            raise ValueError(f"Estado no válido: {nuevo_estado}")
        
        viejo_estado = self.estado
        self.estado = nuevo_estado
        self.fecha_actualizacion = datetime.now().isoformat()
        
        if nuevo_estado == 'completado':
            self.fecha_resolucion = datetime.now().isoformat()
        
        # Registrar en historial
        evento = self._crear_evento(
            'estado_cambiado',
            f"Estado cambiado de '{viejo_estado}' a '{nuevo_estado}'. {comentario}",
            admin_email or 'sistema'
        )
        self.historial.append(evento)
        
        # Guardar cambios
        Solicitud.guardar_todos()
    
    def agregar_comentario(self, comentario: str, admin_email: str):
        """Agrega un comentario de administrador."""
        self.comentarios_admin.append({
            'fecha': datetime.now().isoformat(),
            'admin': admin_email,
            'comentario': comentario
        })
        self.historial.append(self._crear_evento(
            'comentario',
            f"Comentario agregado: {comentario[:50]}...",
            admin_email
        ))
        Solicitud.guardar_todos()
    
    def asignar(self, admin_email: str):
        """Asigna la solicitud a un administrador."""
        self.asignado_a = admin_email
        self.historial.append(self._crear_evento(
            'asignada',
            f"Asignada a {admin_email}",
            admin_email
        ))
        Solicitud.guardar_todos()
    
    def to_dict(self):
        """Convierte a diccionario para JSON."""
        return {
            'id': self.id,
            'folio': self.folio,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'usuario_cedula': self.usuario_cedula,
            'servicio_id': self.servicio_id,
            'servicio_nombre': self.servicio_nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion,
            'fecha_actualizacion': self.fecha_actualizacion,
            'fecha_resolucion': self.fecha_resolucion,
            'asignado_a': self.asignado_a,
            'comentarios_admin': self.comentarios_admin,
            'documentos': self.documentos,
            'historial': self.historial
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Crea una instancia desde diccionario."""
        return cls(**data)
    
    # ========== MÉTODOS DE PERSISTENCIA ==========
    
    @classmethod
    def cargar_todos(cls) -> List['Solicitud']:
        """Carga todas las solicitudes desde el archivo."""
        data = _load_json(SOLICITUDES_FILE, [])
        solicitudes = []
        for item in data:
            if 'id' not in item:
                item['id'] = len(solicitudes) + 1
            solicitudes.append(cls.from_dict(item))
        return solicitudes
    
    @classmethod
    def guardar_todos(cls, solicitudes: List['Solicitud'] = None):
        """Guarda todas las solicitudes en el archivo."""
        if solicitudes is None:
            solicitudes = cls.cargar_todos()
        
        data = [s.to_dict() for s in solicitudes]
        _save_json(SOLICITUDES_FILE, data)
    
    @classmethod
    def buscar_por_id(cls, solicitud_id: int) -> Optional['Solicitud']:
        """Busca una solicitud por ID."""
        solicitudes = cls.cargar_todos()
        for s in solicitudes:
            if s.id == solicitud_id:
                return s
        return None
    
    @classmethod
    def buscar_por_usuario(cls, email: str) -> List['Solicitud']:
        """Busca solicitudes de un usuario."""
        solicitudes = cls.cargar_todos()
        return [s for s in solicitudes if s.usuario_email == email]
    
    @classmethod
    def crear(cls, **kwargs) -> 'Solicitud':
        """Crea una nueva solicitud y la guarda."""
        solicitudes = cls.cargar_todos()
        
        # Generar ID
        nuevo_id = max([s.id for s in solicitudes], default=0) + 1
        
        solicitud = cls(id=nuevo_id, **kwargs)
        solicitudes.append(solicitud)
        
        cls.guardar_todos(solicitudes)
        return solicitud
    
    @classmethod
    def eliminar(cls, solicitud_id: int) -> bool:
        """Elimina una solicitud (solo admin)."""
        solicitudes = cls.cargar_todos()
        solicitudes = [s for s in solicitudes if s.id != solicitud_id]
        cls.guardar_todos(solicitudes)
        return True


# ================================================================
# MODELO: DENUNCIAS
# ================================================================

class Denuncia:
    """Modelo para denuncias ciudadanas."""
    
    ESTADOS = ['pendiente', 'en_investigacion', 'resuelto', 'archivado']
    TIPOS = ['policia', 'limpieza', 'basura', 'alumbrado', 'otro']
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.folio = kwargs.get('folio', self._generar_folio())
        self.usuario_email = kwargs.get('usuario_email', None)  # None = anónimo
        self.usuario_nombre = kwargs.get('usuario_nombre', 'Anónimo')
        self.tipo = kwargs.get('tipo', 'otro')
        self.tipo_nombre = kwargs.get('tipo_nombre', '')
        self.descripcion = kwargs.get('descripcion', '')
        self.direccion = kwargs.get('direccion', '')
        self.anonimo = kwargs.get('anonimo', True)
        self.estado = kwargs.get('estado', 'pendiente')
        self.fecha_creacion = kwargs.get('fecha_creacion', datetime.now().isoformat())
        self.fecha_actualizacion = kwargs.get('fecha_actualizacion', datetime.now().isoformat())
        self.asignado_a = kwargs.get('asignado_a', None)
        self.comentarios_admin = kwargs.get('comentarios_admin', [])
        self.fotos = kwargs.get('fotos', [])
        self.historial = kwargs.get('historial', [self._crear_evento('creada', 'Denuncia creada')])
    
    def _generar_folio(self):
        fecha = datetime.now().strftime("%y%m")
        import random
        return f"DEN-{fecha}-{random.randint(1000, 9999)}"
    
    def _crear_evento(self, tipo: str, descripcion: str, usuario: str = 'sistema'):
        return {
            'fecha': datetime.now().isoformat(),
            'tipo': tipo,
            'descripcion': descripcion,
            'usuario': usuario
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'folio': self.folio,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'tipo': self.tipo,
            'tipo_nombre': self.tipo_nombre,
            'descripcion': self.descripcion,
            'direccion': self.direccion,
            'anonimo': self.anonimo,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion,
            'fecha_actualizacion': self.fecha_actualizacion,
            'asignado_a': self.asignado_a,
            'comentarios_admin': self.comentarios_admin,
            'fotos': self.fotos,
            'historial': self.historial
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
    # Métodos de persistencia (similar a Solicitud)
    @classmethod
    def cargar_todos(cls) -> List['Denuncia']:
        data = _load_json(DENUNCIAS_FILE, [])
        denuncias = []
        for item in data:
            if 'id' not in item:
                item['id'] = len(denuncias) + 1
            denuncias.append(cls.from_dict(item))
        return denuncias
    
    @classmethod
    def guardar_todos(cls, denuncias: List['Denuncia'] = None):
        if denuncias is None:
            denuncias = cls.cargar_todos()
        data = [d.to_dict() for d in denuncias]
        _save_json(DENUNCIAS_FILE, data)
    
    @classmethod
    def crear(cls, **kwargs) -> 'Denuncia':
        denuncias = cls.cargar_todos()
        nuevo_id = max([d.id for d in denuncias], default=0) + 1
        denuncia = cls(id=nuevo_id, **kwargs)
        denuncias.append(denuncia)
        cls.guardar_todos(denuncias)
        return denuncia
    
    @classmethod
    def buscar_por_id(cls, denuncia_id: int) -> Optional['Denuncia']:
        """Busca una denuncia por ID."""
        denuncias = cls.cargar_todos()
        for d in denuncias:
            if d.id == denuncia_id:
                return d
        return None


# ================================================================
# MODELO: USUARIOS EXTENDIDO (para auth.py)
# ================================================================

class Usuario:
    """Modelo extendido de usuario con más funcionalidades."""
    
    def __init__(self, email: str, datos: dict):
        self.email = email
        self.nombre = datos.get('nombre', '')
        self.password = datos.get('password', '')
        self.tipo = datos.get('tipo', 'ciudadano')
        self.rol = datos.get('rol', None)
        self.telefono = datos.get('telefono', '')
        self.fecha_registro = datos.get('fecha_registro', '')
        self.activo = datos.get('activo', True)
        self.ultimo_acceso = datos.get('ultimo_acceso', None)
        self.notas_admin = datos.get('notas_admin', '')
    
    @property
    def is_admin(self):
        return self.tipo == 'admin' or self.rol in ['super_admin', 'admin', 'moderador']
    
    @property
    def rol_nombre(self):
        nombres = {
            'super_admin': 'Super Administrador',
            'admin': 'Administrador',
            'moderador': 'Moderador'
        }
        return nombres.get(self.rol, 'Ciudadano')
    
    def to_dict(self):
        return {
            'password': self.password,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'rol': self.rol,
            'telefono': self.telefono,
            'fecha_registro': self.fecha_registro,
            'activo': self.activo,
            'ultimo_acceso': self.ultimo_acceso,
            'notas_admin': self.notas_admin
        }


# ================================================================
# MODELO: REPORTES Y ESTADÍSTICAS
# ================================================================

class Reportes:
    """Genera estadísticas y reportes para el dashboard."""
    
    @staticmethod
    def obtener_estadisticas_generales():
        """Obtiene estadísticas generales del sistema."""
        from auth import _cargar_usuarios
        
        usuarios = _cargar_usuarios()
        solicitudes = Solicitud.cargar_todos()
        denuncias = Denuncia.cargar_todos()
        
        # Usuarios
        total_usuarios = len(usuarios)
        admins = sum(1 for u in usuarios.values() if u.get('tipo') == 'admin' or u.get('rol') in ['super_admin', 'admin'])
        moderadores = sum(1 for u in usuarios.values() if u.get('rol') == 'moderador')
        ciudadanos = total_usuarios - admins - moderadores
        
        # Solicitudes
        solicitudes_pendientes = sum(1 for s in solicitudes if s.estado in ['pendiente', 'en_proceso'])
        solicitudes_completadas = sum(1 for s in solicitudes if s.estado == 'completado')
        
        # Denuncias
        denuncias_pendientes = sum(1 for d in denuncias if d.estado in ['pendiente', 'en_investigacion'])
        denuncias_resueltas = sum(1 for d in denuncias if d.estado == 'resuelto')
        
        # Actividad reciente
        hoy = datetime.now().date()
        solicitudes_hoy = sum(1 for s in solicitudes if datetime.fromisoformat(s.fecha_creacion).date() == hoy)
        denuncias_hoy = sum(1 for d in denuncias if datetime.fromisoformat(d.fecha_creacion).date() == hoy)
        
        return {
            'usuarios': {
                'total': total_usuarios,
                'admins': admins,
                'moderadores': moderadores,
                'ciudadanos': ciudadanos
            },
            'solicitudes': {
                'total': len(solicitudes),
                'pendientes': solicitudes_pendientes,
                'completadas': solicitudes_completadas
            },
            'denuncias': {
                'total': len(denuncias),
                'pendientes': denuncias_pendientes,
                'resueltas': denuncias_resueltas
            },
            'actividad_hoy': {
                'solicitudes': solicitudes_hoy,
                'denuncias': denuncias_hoy
            }
        }
    
    @staticmethod
    def obtener_solicitudes_por_servicio():
        """Obtiene conteo de solicitudes por tipo de servicio."""
        solicitudes = Solicitud.cargar_todos()
        try:
            from app import NOMBRES_SERVICIOS
        except:
            NOMBRES_SERVICIOS = {}
        
        resultado = {}
        for servicio_id, nombre in NOMBRES_SERVICIOS.items():
            count = sum(1 for s in solicitudes if s.servicio_id == servicio_id)
            resultado[nombre] = count
        
        return resultado
    
    @staticmethod
    def obtener_denuncias_por_tipo():
        """Obtiene conteo de denuncias por tipo."""
        denuncias = Denuncia.cargar_todos()
        try:
            from app import NOMBRES_DENUNCIAS
        except:
            NOMBRES_DENUNCIAS = {}
        
        resultado = {}
        for tipo_id, nombre in NOMBRES_DENUNCIAS.items():
            count = sum(1 for d in denuncias if d.tipo == tipo_id)
            resultado[nombre] = count
        
        return resultado