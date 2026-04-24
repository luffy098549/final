"""
Modelo para gestionar solicitudes de servicios municipales
"""
import json
import uuid
import random
import string
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
        self.folio = folio or self.generar_folio()
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
    
    @staticmethod
    def generar_folio():
        """
        Genera un folio único para la solicitud
        Formato: SOL-YYMMDD-XXXXX
        """
        fecha = datetime.now().strftime("%y%m%d")
        random_part = ''.join(random.choices(string.digits, k=5))
        folio = f"SOL-{fecha}-{random_part}"
        
        # Verificar que el folio no exista ya
        solicitudes = Solicitud.cargar_todos()
        while any(s.folio == folio for s in solicitudes):
            random_part = ''.join(random.choices(string.digits, k=5))
            folio = f"SOL-{fecha}-{random_part}"
        
        return folio
    
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
            print(f"[DEBUG] El archivo {SOLICITUDES_FILE} no existe, creando uno nuevo")
            return []
        try:
            with open(SOLICITUDES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[DEBUG] Cargadas {len(data)} solicitudes desde {SOLICITUDES_FILE}")
                return [cls.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[ERROR] Error cargando solicitudes: {e}")
            return []
    
    @classmethod
    def guardar_todos(cls, solicitudes):
        """Guarda todas las solicitudes en el archivo JSON"""
        try:
            with open(SOLICITUDES_FILE, 'w', encoding='utf-8') as f:
                json.dump([s.to_dict() for s in solicitudes], f,
                         ensure_ascii=False, indent=2)
            print(f"[DEBUG] Guardadas {len(solicitudes)} solicitudes en {SOLICITUDES_FILE}")
            return True
        except Exception as e:
            print(f"[ERROR] Error guardando solicitudes: {e}")
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
        if nuevo_estado not in self.ESTADOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {self.ESTADOS}")
        
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
        
        # Guardar cambios
        solicitudes = self.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.id == self.id:
                solicitudes[i] = self
                break
        self.guardar_todos(solicitudes)
    
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
        
        # Guardar cambios
        solicitudes = self.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.id == self.id:
                solicitudes[i] = self
                break
        self.guardar_todos(solicitudes)
    
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
        
        # Guardar cambios
        solicitudes = self.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.id == self.id:
                solicitudes[i] = self
                break
        self.guardar_todos(solicitudes)
    
    def agregar_documento(self, nombre_documento, url_documento):
        """Agrega un documento a la solicitud"""
        self.documentos.append({
            'nombre': nombre_documento,
            'url': url_documento,
            'fecha': datetime.now().isoformat()
        })
        self.fecha_actualizacion = datetime.now().isoformat()
        
        # Guardar cambios
        solicitudes = self.cargar_todos()
        for i, s in enumerate(solicitudes):
            if s.id == self.id:
                solicitudes[i] = self
                break
        self.guardar_todos(solicitudes)