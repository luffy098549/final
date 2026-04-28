# models/encuesta.py
from extensions import db
from datetime import datetime
import json
from pathlib import Path

DATA_DIR = Path("data")
ENCUESTAS_FILE = DATA_DIR / "encuestas.json"

class Encuesta(db.Model):
    __tablename__ = 'encuestas'
    
    id = db.Column(db.Integer, primary_key=True)
    folio_tramite = db.Column(db.String(50), nullable=False, unique=True, index=True)
    tipo_tramite = db.Column(db.String(50), index=True)
    usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=True, index=True)
    usuario_nombre = db.Column(db.String(200))
    calificacion = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @classmethod
    def migrar_desde_json(cls):
        """Migra todos los datos del archivo JSON a PostgreSQL"""
        if not ENCUESTAS_FILE.exists():
            print("⚠️ No hay archivo encuestas.json para migrar")
            return 0
        
        with open(ENCUESTAS_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        contador = 0
        for item in datos:
            existe = cls.query.filter_by(folio_tramite=item.get('folio_tramite')).first()
            if existe:
                continue
            
            fecha_obj = None
            if item.get('fecha'):
                try:
                    fecha_obj = datetime.fromisoformat(item.get('fecha'))
                except:
                    fecha_obj = datetime.utcnow()
            
            nueva = cls(
                folio_tramite=item.get('folio_tramite'),
                tipo_tramite=item.get('tipo_tramite'),
                usuario_email=item.get('usuario_email'),
                usuario_nombre=item.get('usuario_nombre'),
                calificacion=item.get('calificacion'),
                comentario=item.get('comentario', ''),
                fecha=fecha_obj
            )
            db.session.add(nueva)
            contador += 1
        
        db.session.commit()
        print(f"✅ Migradas {contador} encuestas a PostgreSQL")
        return contador
    
    @classmethod
    def crear(cls, folio_tramite, tipo_tramite, usuario_email, usuario_nombre, calificacion, comentario=""):
        """Crea una nueva encuesta"""
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
        db.session.add(nueva)
        db.session.commit()
        return nueva
    
    @classmethod
    def buscar_por_tramite(cls, folio_tramite):
        return cls.query.filter_by(folio_tramite=folio_tramite).first()
    
    @classmethod
    def cargar_todos(cls):
        """Compatibilidad con código existente"""
        return cls.query.order_by(cls.fecha.desc()).all()
    
    @classmethod
    def obtener_estadisticas(cls):
        encuestas = cls.cargar_todos()
        if not encuestas:
            return {
                'total': 0,
                'promedio': 0,
                'por_calificacion': {1:0, 2:0, 3:0, 4:0, 5:0},
                'por_tipo': {'solicitud': 0, 'denuncia': 0, 'cita': 0},
                'ultimas': []
            }
        
        suma = sum(e.calificacion for e in encuestas)
        promedio = suma / len(encuestas)
        por_calif = {1:0, 2:0, 3:0, 4:0, 5:0}
        for e in encuestas:
            por_calif[e.calificacion] = por_calif.get(e.calificacion, 0) + 1
        
        solicitudes = len([e for e in encuestas if e.tipo_tramite == 'solicitud'])
        denuncias = len([e for e in encuestas if e.tipo_tramite == 'denuncia'])
        citas = len([e for e in encuestas if e.tipo_tramite == 'cita'])
        
        ultimas = sorted(encuestas, key=lambda x: x.fecha, reverse=True)[:10]
        
        return {
            'total': len(encuestas),
            'promedio': round(promedio, 2),
            'por_calificacion': por_calif,
            'por_tipo': {'solicitud': solicitudes, 'denuncia': denuncias, 'cita': citas},
            'ultimas': ultimas
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'folio_tramite': self.folio_tramite,
            'tipo_tramite': self.tipo_tramite,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'calificacion': self.calificacion,
            'comentario': self.comentario,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }