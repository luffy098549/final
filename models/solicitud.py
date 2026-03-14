"""
Modelo para gestionar solicitudes de servicios municipales
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SOLICITUDES_FILE = DATA_DIR / "solicitudes.json"

class Solicitud:
    """Modelo para solicitudes de servicios"""
    
    ESTADOS = ['pendiente', 'en_proceso', 'completado', 'rechazado', 'cancelado']
    
    def __init__(self, id=None, folio=None, usuario_email=None, usuario_nombre=None,
                 usuario_cedula=None, servicio_id=None, servicio_nombre=None,
                 descripcion=None, estado='pendiente', fecha_creacion=None,
                 fecha_actualizacion=None, comentarios_admin=None, historial=None,
                 documentos=None, asignado_a=None):
        
        self.id = id or str(uuid.uuid4())
        self.folio = folio or self._generar_folio()
        self.usuario_email = usuario_email
        self.usuario_nombre = usuario_nombre
        self.usuario_cedula = usuario_cedula
        self.servicio_id = servicio_id
        self.servicio_nombre = servicio_nombre
        self.descripcion = descripcion
        self.estado = estado
        self.fecha_creacion = fecha_creacion or datetime.now().isoformat()
        self.fecha_actualizacion = fecha_actualizacion or self.fecha_creacion
        self.comentarios_admin = comentarios_admin or []
        self.historial = historial or []
        self.documentos = documentos or []
        self.asignado_a = asignado_a
    
    def _generar_folio(self):
        """Genera folio único para la solicitud"""
        fecha = datetime.now().strftime("%y%m%d")
        random = uuid.uuid4().hex[:6].upper()
        return f"SOL-{fecha}-{random}"
    
    def to_dict(self):
        """Convierte a diccionario para JSON"""
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
            'comentarios_admin': self.comentarios_admin,
            'historial': self.historial,
            'documentos': self.documentos,
            'asignado_a': self.asignado_a
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea instancia desde diccionario"""
        return cls(
            id=data.get('id'),
            folio=data.get('folio'),
            usuario_email=data.get('usuario_email'),
            usuario_nombre=data.get('usuario_nombre'),
            usuario_cedula=data.get('usuario_cedula'),
            servicio_id=data.get('servicio_id'),
            servicio_nombre=data.get('servicio_nombre'),
            descripcion=data.get('descripcion'),
            estado=data.get('estado', 'pendiente'),
            fecha_creacion=data.get('fecha_creacion'),
            fecha_actualizacion=data.get('fecha_actualizacion'),
            comentarios_admin=data.get('comentarios_admin', []),
            historial=data.get('historial', []),
            documentos=data.get('documentos', []),
            asignado_a=data.get('asignado_a')
        )
    
    @classmethod
    def cargar_todos(cls):
        """Carga todas las solicitudes del archivo JSON"""
        if not SOLICITUDES_FILE.exists():
            return []
        try:
            with open(SOLICITUDES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [cls.from_dict(item) for item in data]
        except:
            return []
    
    @classmethod
    def guardar_todos(cls, solicitudes):
        """Guarda todas las solicitudes en el archivo JSON"""
        try:
            with open(SOLICITUDES_FILE, 'w', encoding='utf-8') as f:
                json.dump([s.to_dict() for s in solicitudes], f,
                         ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    @classmethod
    def buscar_por_id(cls, solicitud_id):
        """Busca una solicitud por su ID"""
        todas = cls.cargar_todos()
        for s in todas:
            if s.id == solicitud_id:
                return s
        return None
    
    @classmethod
    def buscar_por_usuario(cls, email):
        """Busca solicitudes de un usuario específico"""
        todas = cls.cargar_todos()
        return [s for s in todas if s.usuario_email == email]
    
    @classmethod
    def buscar_por_folio(cls, folio):
        """Busca una solicitud por su folio"""
        todas = cls.cargar_todos()
        for s in todas:
            if s.folio == folio:
                return s
        return None
    
    @classmethod
    def crear(cls, usuario_email, usuario_nombre, usuario_cedula,
              servicio_id, servicio_nombre, descripcion):
        """Crea una nueva solicitud"""
        nueva = cls(
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            usuario_cedula=usuario_cedula,
            servicio_id=servicio_id,
            servicio_nombre=servicio_nombre,
            descripcion=descripcion
        )
        # Agregar al historial
        nueva.historial.append({
            'fecha': nueva.fecha_creacion,
            'tipo': 'creada',
            'descripcion': 'Solicitud creada',
            'usuario': usuario_email,
            'nombre': usuario_nombre
        })
        solicitudes = cls.cargar_todos()
        solicitudes.append(nueva)
        cls.guardar_todos(solicitudes)
        return nueva
    
    def actualizar_estado(self, nuevo_estado, comentario=None, admin_email=None):
        """Actualiza el estado de la solicitud"""
        self.estado = nuevo_estado
        self.fecha_actualizacion = datetime.now().isoformat()
        
        # Registrar en historial
        self.historial.append({
            'fecha': self.fecha_actualizacion,
            'tipo': 'estado_cambiado',
            'descripcion': f'Estado cambiado a: {nuevo_estado}',
            'usuario': admin_email or 'sistema',
            'comentario': comentario
        })
    
    def agregar_comentario(self, comentario, admin_email, admin_nombre=None):
        """Agrega un comentario administrativo"""
        self.comentarios_admin.append({
            'fecha': datetime.now().isoformat(),
            'admin': admin_email,
            'nombre': admin_nombre or admin_email,
            'comentario': comentario
        })
        self.fecha_actualizacion = datetime.now().isoformat()
        
        # Registrar en historial
        self.historial.append({
            'fecha': self.fecha_actualizacion,
            'tipo': 'comentario',
            'descripcion': comentario,
            'usuario': admin_email,
            'nombre': admin_nombre or admin_email
        })
    
    def asignar(self, admin_email):
        """Asigna la solicitud a un administrador"""
        self.asignado_a = admin_email
        self.fecha_actualizacion = datetime.now().isoformat()
        
        self.historial.append({
            'fecha': self.fecha_actualizacion,
            'tipo': 'asignada',
            'descripcion': f'Asignada a: {admin_email}',
            'usuario': admin_email
        })