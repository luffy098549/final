"""
Modelo para gestionar denuncias ciudadanas
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DENUNCIAS_FILE = DATA_DIR / "denuncias.json"

class Denuncia:
    """Modelo para denuncias ciudadanas"""
    
    ESTADOS = ['pendiente', 'en_investigacion', 'resuelto', 'rechazado', 'cancelado']
    
    def __init__(self, id=None, folio=None, usuario_email=None, usuario_nombre=None,
                 tipo=None, tipo_nombre=None, descripcion=None, direccion=None,
                 latitud=None, longitud=None, direccion_completa=None,
                 anonimo=False, estado='pendiente', fecha_creacion=None,
                 fecha_actualizacion=None, comentarios_admin=None, historial=None,
                 documentos=None, asignado_a=None):
        
        self.id = id or str(uuid.uuid4())
        self.folio = folio or self._generar_folio()
        self.usuario_email = usuario_email
        self.usuario_nombre = usuario_nombre or "Anónimo"
        self.tipo = tipo
        self.tipo_nombre = tipo_nombre
        self.descripcion = descripcion
        self.direccion = direccion
        self.latitud = latitud
        self.longitud = longitud
        self.direccion_completa = direccion_completa or direccion
        self.anonimo = anonimo
        self.estado = estado
        self.fecha_creacion = fecha_creacion or datetime.now().isoformat()
        self.fecha_actualizacion = fecha_actualizacion or self.fecha_creacion
        self.comentarios_admin = comentarios_admin or []
        self.historial = historial or []
        self.documentos = documentos or []
        self.asignado_a = asignado_a
    
    @property
    def geolocalizada(self):
        """Indica si la denuncia tiene coordenadas"""
        return self.latitud is not None and self.longitud is not None
    
    def _generar_folio(self):
        """Genera folio único para la denuncia"""
        fecha = datetime.now().strftime("%y%m%d")
        random = uuid.uuid4().hex[:6].upper()
        return f"DEN-{fecha}-{random}"
    
    def to_dict(self):
        """Convierte a diccionario para JSON"""
        return {
            'id': self.id,
            'folio': self.folio,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'tipo': self.tipo,
            'tipo_nombre': self.tipo_nombre,
            'descripcion': self.descripcion,
            'direccion': self.direccion,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'direccion_completa': self.direccion_completa,
            'anonimo': self.anonimo,
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
            tipo=data.get('tipo'),
            tipo_nombre=data.get('tipo_nombre'),
            descripcion=data.get('descripcion'),
            direccion=data.get('direccion'),
            latitud=data.get('latitud'),
            longitud=data.get('longitud'),
            direccion_completa=data.get('direccion_completa'),
            anonimo=data.get('anonimo', False),
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
        """Carga todas las denuncias del archivo JSON"""
        if not DENUNCIAS_FILE.exists():
            return []
        try:
            with open(DENUNCIAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [cls.from_dict(item) for item in data]
        except:
            return []
    
    @classmethod
    def guardar_todos(cls, denuncias):
        """Guarda todas las denuncias en el archivo JSON"""
        try:
            with open(DENUNCIAS_FILE, 'w', encoding='utf-8') as f:
                json.dump([d.to_dict() for d in denuncias], f,
                         ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    @classmethod
    def buscar_por_id(cls, denuncia_id):
        """Busca una denuncia por su ID"""
        todas = cls.cargar_todos()
        for d in todas:
            if d.id == denuncia_id:
                return d
        return None
    
    @classmethod
    def buscar_por_usuario(cls, email):
        """Busca denuncias de un usuario específico"""
        todas = cls.cargar_todos()
        return [d for d in todas if d.usuario_email == email]
    
    @classmethod
    def buscar_por_folio(cls, folio):
        """Busca una denuncia por su folio"""
        todas = cls.cargar_todos()
        for d in todas:
            if d.folio == folio:
                return d
        return None
    
    @classmethod
    def crear(cls, usuario_email=None, usuario_nombre="Anónimo",
              tipo=None, tipo_nombre=None, descripcion=None,
              direccion=None, anonimo=False, latitud=None, longitud=None):
        """Crea una nueva denuncia"""
        nueva = cls(
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            tipo=tipo,
            tipo_nombre=tipo_nombre,
            descripcion=descripcion,
            direccion=direccion,
            latitud=latitud,
            longitud=longitud,
            anonimo=anonimo
        )
        # Agregar al historial
        nueva.historial.append({
            'fecha': nueva.fecha_creacion,
            'tipo': 'creada',
            'descripcion': 'Denuncia creada',
            'usuario': usuario_email or 'anónimo',
            'nombre': usuario_nombre
        })
        denuncias = cls.cargar_todos()
        denuncias.append(nueva)
        cls.guardar_todos(denuncias)
        return nueva
    
    def geolocalizar(self, latitud, longitud, direccion_completa=None):
        """Actualiza las coordenadas de la denuncia"""
        self.latitud = latitud
        self.longitud = longitud
        if direccion_completa:
            self.direccion_completa = direccion_completa
        self.fecha_actualizacion = datetime.now().isoformat()
        
        self.historial.append({
            'fecha': self.fecha_actualizacion,
            'tipo': 'geolocalizada',
            'descripcion': f'Denuncia geolocalizada: {latitud}, {longitud}',
            'usuario': 'sistema'
        })