"""
Modelo para encuestas de satisfacción de trámites
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ENCUESTAS_FILE = DATA_DIR / "encuestas.json"

class Encuesta:
    """Modelo para gestionar encuestas de satisfacción"""
    
    def __init__(self, id=None, folio_tramite=None, tipo_tramite=None,
                 usuario_email=None, usuario_nombre=None,
                 calificacion=None, comentario=None, fecha=None):
        self.id = id or str(uuid.uuid4())
        self.folio_tramite = folio_tramite
        self.tipo_tramite = tipo_tramite
        self.usuario_email = usuario_email
        self.usuario_nombre = usuario_nombre
        self.calificacion = calificacion
        self.comentario = comentario
        self.fecha = fecha or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'folio_tramite': self.folio_tramite,
            'tipo_tramite': self.tipo_tramite,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'calificacion': self.calificacion,
            'comentario': self.comentario,
            'fecha': self.fecha
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            folio_tramite=data.get('folio_tramite'),
            tipo_tramite=data.get('tipo_tramite'),
            usuario_email=data.get('usuario_email'),
            usuario_nombre=data.get('usuario_nombre'),
            calificacion=data.get('calificacion'),
            comentario=data.get('comentario'),
            fecha=data.get('fecha')
        )
    
    @classmethod
    def cargar_todos(cls):
        if not ENCUESTAS_FILE.exists():
            return []
        try:
            with open(ENCUESTAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [cls.from_dict(item) for item in data]
        except:
            return []
    
    @classmethod
    def guardar_todos(cls, encuestas):
        try:
            with open(ENCUESTAS_FILE, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in encuestas], f,
                         ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    @classmethod
    def buscar_por_tramite(cls, folio_tramite):
        todas = cls.cargar_todos()
        for e in todas:
            if e.folio_tramite == folio_tramite:
                return e
        return None
    
    @classmethod
    def crear(cls, folio_tramite, tipo_tramite, usuario_email, 
              usuario_nombre, calificacion, comentario=""):
        if cls.buscar_por_tramite(folio_tramite):
            return None
        nueva = cls(
            folio_tramite=folio_tramite,
            tipo_tramite=tipo_tramite,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            calificacion=calificacion,
            comentario=comentario
        )
        encuestas = cls.cargar_todos()
        encuestas.append(nueva)
        cls.guardar_todos(encuestas)
        return nueva
    
    @classmethod
    def obtener_estadisticas(cls):
        encuestas = cls.cargar_todos()
        if not encuestas:
            return {
                'total': 0,
                'promedio': 0,
                'por_calificacion': {1:0, 2:0, 3:0, 4:0, 5:0},
                'por_tipo': {'solicitud': 0, 'denuncia': 0},
                'ultimas': []
            }
        suma = sum(e.calificacion for e in encuestas)
        promedio = suma / len(encuestas)
        por_calif = {1:0, 2:0, 3:0, 4:0, 5:0}
        for e in encuestas:
            por_calif[e.calificacion] = por_calif.get(e.calificacion, 0) + 1
        solicitudes = len([e for e in encuestas if e.tipo_tramite == 'solicitud'])
        denuncias = len([e for e in encuestas if e.tipo_tramite == 'denuncia'])
        ultimas = sorted(encuestas, key=lambda x: x.fecha, reverse=True)[:10]
        return {
            'total': len(encuestas),
            'promedio': round(promedio, 2),
            'por_calificacion': por_calif,
            'por_tipo': {'solicitud': solicitudes, 'denuncia': denuncias},
            'ultimas': ultimas
        }