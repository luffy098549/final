"""
Modelo para plantillas de respuesta rápida
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PLANTILLAS_FILE = DATA_DIR / "plantillas.json"

class Plantilla:
    """Modelo para gestionar plantillas de respuesta"""
    
    CATEGORIAS = {
        'solicitud': 'Solicitudes',
        'denuncia': 'Denuncias',
        'cita': 'Citas',
        'general': 'General'
    }
    
    def __init__(self, id=None, nombre=None, categoria='general', 
                 contenido=None, variables=None, creada_por=None,
                 fecha_creacion=None, usos=0):
        self.id = id or str(uuid.uuid4())
        self.nombre = nombre
        self.categoria = categoria
        self.contenido = contenido or ""
        self.variables = variables or ['folio', 'nombre', 'fecha']
        self.creada_por = creada_por
        self.fecha_creacion = fecha_creacion or datetime.now().isoformat()
        self.usos = usos
        self.activa = True
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'contenido': self.contenido,
            'variables': self.variables,
            'creada_por': self.creada_por,
            'fecha_creacion': self.fecha_creacion,
            'usos': self.usos,
            'activa': self.activa
        }
    
    @classmethod
    def from_dict(cls, data):
        p = cls(
            id=data.get('id'),
            nombre=data.get('nombre'),
            categoria=data.get('categoria', 'general'),
            contenido=data.get('contenido'),
            variables=data.get('variables', ['folio', 'nombre', 'fecha']),
            creada_por=data.get('creada_por'),
            fecha_creacion=data.get('fecha_creacion'),
            usos=data.get('usos', 0)
        )
        p.activa = data.get('activa', True)
        return p
    
    @classmethod
    def cargar_todos(cls):
        if not PLANTILLAS_FILE.exists():
            return cls._crear_plantillas_defecto()
        try:
            with open(PLANTILLAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [cls.from_dict(item) for item in data]
        except:
            return cls._crear_plantillas_defecto()
    
    @classmethod
    def _crear_plantillas_defecto(cls):
        defecto = [
            cls(
                nombre="Acuse de recibo - Solicitud",
                categoria="solicitud",
                contenido="""Estimado/a {{nombre}},

Hemos recibido su solicitud con folio **{{folio}}** con fecha {{fecha}}.

Su caso ha sido asignado al área correspondiente y estará siendo procesado en los próximos días hábiles. Le mantendremos informado sobre cualquier avance.

Atentamente,
**Equipo Municipal de Villa Cutupú**""",
                variables=['nombre', 'folio', 'fecha']
            ),
            cls(
                nombre="Acuse de recibo - Denuncia",
                categoria="denuncia",
                contenido="""Estimado/a {{nombre}},

Hemos recibido su denuncia con folio **{{folio}}** registrada el {{fecha}}.

Su caso ha sido asignado al departamento de investigación y comenzaremos su análisis en un plazo de 48 horas. Agradecemos su colaboración para mantener nuestro municipio seguro.

Atentamente,
**Equipo Municipal de Villa Cutupú**""",
                variables=['nombre', 'folio', 'fecha']
            )
        ]
        cls.guardar_todos(defecto)
        return defecto
    
    @classmethod
    def guardar_todos(cls, plantillas):
        try:
            with open(PLANTILLAS_FILE, 'w', encoding='utf-8') as f:
                json.dump([p.to_dict() for p in plantillas], f,
                         ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    @classmethod
    def buscar_por_id(cls, plantilla_id):
        todas = cls.cargar_todos()
        for p in todas:
            if p.id == plantilla_id:
                return p
        return None
    
    @classmethod
    def buscar_por_categoria(cls, categoria):
        todas = cls.cargar_todos()
        return [p for p in todas if p.categoria == categoria and p.activa]
    
    def procesar(self, **kwargs):
        contenido = self.contenido
        for key, value in kwargs.items():
            contenido = contenido.replace(f'{{{{ {key} }}}}', str(value))
            contenido = contenido.replace(f'{{{{{key}}}}}', str(value))
        return contenido
    
    def incrementar_uso(self):
        self.usos += 1
        plantillas = self.cargar_todos()
        for i, p in enumerate(plantillas):
            if p.id == self.id:
                plantillas[i] = self
                break
        self.guardar_todos(plantillas)