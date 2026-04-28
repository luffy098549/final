# models/plantilla.py
from extensions import db
from datetime import datetime
import json
from pathlib import Path

DATA_DIR = Path("data")
PLANTILLAS_FILE = DATA_DIR / "plantillas.json"

class Plantilla(db.Model):
    __tablename__ = 'plantillas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), default='general', index=True)
    contenido = db.Column(db.Text, nullable=False)
    variables = db.Column(db.JSON, default=['folio', 'nombre', 'fecha'])
    activa = db.Column(db.Boolean, default=True)
    usos = db.Column(db.Integer, default=0)
    creada_por = db.Column(db.String(120))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    CATEGORIAS = {
        'solicitud': 'Solicitudes',
        'denuncia': 'Denuncias',
        'cita': 'Citas',
        'general': 'General'
    }
    
    @classmethod
    def migrar_desde_json(cls):
        """Migra todos los datos del archivo JSON a PostgreSQL"""
        if not PLANTILLAS_FILE.exists():
            print("⚠️ No hay archivo plantillas.json para migrar")
            return 0
        
        with open(PLANTILLAS_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        contador = 0
        for item in datos:
            existe = cls.query.filter_by(nombre=item.get('nombre')).first()
            if existe:
                continue
            
            fecha_obj = None
            if item.get('fecha_creacion'):
                try:
                    fecha_obj = datetime.fromisoformat(item.get('fecha_creacion'))
                except:
                    fecha_obj = datetime.utcnow()
            
            nueva = cls(
                nombre=item.get('nombre'),
                categoria=item.get('categoria', 'general'),
                contenido=item.get('contenido', ''),
                variables=item.get('variables', ['folio', 'nombre', 'fecha']),
                activa=item.get('activa', True),
                usos=item.get('usos', 0),
                creada_por=item.get('creada_por'),
                fecha_creacion=fecha_obj
            )
            db.session.add(nueva)
            contador += 1
        
        db.session.commit()
        print(f"✅ Migradas {contador} plantillas a PostgreSQL")
        return contador
    
    @classmethod
    def _crear_plantillas_defecto(cls):
        """Crea plantillas por defecto si no existen"""
        if cls.query.count() == 0:
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
            for p in defecto:
                db.session.add(p)
            db.session.commit()
    
    @classmethod
    def cargar_todos(cls):
        """Compatibilidad con código existente"""
        return cls.query.order_by(cls.nombre).all()
    
    @classmethod
    def buscar_por_id(cls, plantilla_id):
        return cls.query.get(plantilla_id)
    
    @classmethod
    def buscar_por_categoria(cls, categoria):
        return cls.query.filter_by(categoria=categoria, activa=True).all()
    
    def procesar(self, **kwargs):
        contenido = self.contenido
        for key, value in kwargs.items():
            contenido = contenido.replace(f'{{{{ {key} }}}}', str(value))
            contenido = contenido.replace(f'{{{{{key}}}}}', str(value))
        return contenido
    
    def incrementar_uso(self):
        self.usos += 1
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'contenido': self.contenido,
            'variables': self.variables,
            'activa': self.activa,
            'usos': self.usos,
            'creada_por': self.creada_por,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }