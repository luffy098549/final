# models/denuncia.py
from extensions import db
from datetime import datetime
import random
import string
import json
from pathlib import Path

DATA_DIR = Path("data")
DENUNCIAS_FILE = DATA_DIR / "denuncias.json"

class Denuncia(db.Model):
    __tablename__ = 'denuncias'
    
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(50), unique=True, nullable=False, index=True)
    usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=True, index=True)
    usuario_nombre = db.Column(db.String(200))
    tipo = db.Column(db.String(100), index=True)
    tipo_nombre = db.Column(db.String(200))
    descripcion = db.Column(db.Text)
    ubicacion = db.Column(db.String(500))
    direccion = db.Column(db.String(500))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    geolocalizada = db.Column(db.Boolean, default=False)
    anonimo = db.Column(db.Boolean, default=False)
    evidencia = db.Column(db.Text)
    estado = db.Column(db.String(50), default='pendiente', index=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    comentarios_admin = db.Column(db.JSON, default=list)
    historial = db.Column(db.JSON, default=list)
    documentos = db.Column(db.JSON, default=list)
    asignado_a = db.Column(db.String(120))
    
    ESTADOS = ['pendiente', 'en_investigacion', 'resuelto', 'rechazado', 'cancelado']
    
    @staticmethod
    def generar_folio():
        fecha = datetime.now().strftime("%y%m%d")
        random_part = ''.join(random.choices(string.digits, k=5))
        folio = f"DEN-{fecha}-{random_part}"
        return folio
    
    @classmethod
    def migrar_desde_json(cls):
        """Migra todos los datos del archivo JSON a PostgreSQL"""
        if not DENUNCIAS_FILE.exists():
            print("⚠️ No hay archivo denuncias.json para migrar")
            return 0
        
        with open(DENUNCIAS_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        contador = 0
        for item in datos:
            existe = cls.query.filter_by(folio=item.get('folio')).first()
            if existe:
                continue
            
            fecha_creacion = None
            if item.get('fecha_creacion'):
                try:
                    fecha_creacion = datetime.fromisoformat(item.get('fecha_creacion'))
                except:
                    fecha_creacion = datetime.utcnow()
            
            nueva = cls(
                folio=item.get('folio'),
                usuario_email=item.get('usuario_email'),
                usuario_nombre=item.get('usuario_nombre', 'Anónimo'),
                tipo=item.get('tipo'),
                tipo_nombre=item.get('tipo_nombre'),
                descripcion=item.get('descripcion'),
                ubicacion=item.get('ubicacion'),
                direccion=item.get('direccion'),
                lat=item.get('lat') or item.get('latitud'),
                lng=item.get('lng') or item.get('longitud'),
                geolocalizada=item.get('geolocalizada', False),
                anonimo=item.get('anonimo', False),
                evidencia=item.get('evidencia', ''),
                estado=item.get('estado', 'pendiente'),
                fecha_creacion=fecha_creacion,
                comentarios_admin=item.get('comentarios_admin', []),
                historial=item.get('historial', []),
                documentos=item.get('documentos', []),
                asignado_a=item.get('asignado_a')
            )
            db.session.add(nueva)
            contador += 1
        
        db.session.commit()
        print(f"✅ Migradas {contador} denuncias a PostgreSQL")
        return contador
    
    @classmethod
    def crear(cls, usuario_email=None, usuario_nombre="Anónimo",
              tipo=None, tipo_nombre=None, descripcion=None,
              ubicacion=None, direccion=None, anonimo=False,
              lat=None, lng=None, evidencia=None):
        """Crea una nueva denuncia"""
        nueva = cls(
            folio=cls.generar_folio(),
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            tipo=tipo,
            tipo_nombre=tipo_nombre,
            descripcion=descripcion,
            ubicacion=ubicacion,
            direccion=direccion,
            lat=lat,
            lng=lng,
            geolocalizada=bool(lat and lng),
            anonimo=anonimo,
            evidencia=evidencia,
            estado='pendiente',
            comentarios_admin=[],
            historial=[{
                'fecha': datetime.now().isoformat(),
                'tipo': 'creada',
                'descripcion': 'Denuncia creada',
                'usuario': usuario_email or 'anónimo',
                'nombre': usuario_nombre
            }],
            documentos=[]
        )
        db.session.add(nueva)
        db.session.commit()
        return nueva
    
    @classmethod
    def buscar_por_usuario(cls, email):
        return cls.query.filter_by(usuario_email=email).order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def buscar_por_id(cls, denuncia_id):
        return cls.query.get(denuncia_id)
    
    @classmethod
    def buscar_por_folio(cls, folio):
        return cls.query.filter_by(folio=folio).first()
    
    @classmethod
    def cargar_todos(cls):
        """Compatibilidad con código existente"""
        return cls.query.order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def guardar(cls, denuncia):
        """Guardar denuncia"""
        db.session.add(denuncia)
        db.session.commit()
    
    @classmethod
    def guardar_todos(cls, denuncias):
        """Compatibilidad"""
        pass
    
    def actualizar_estado(self, nuevo_estado, comentario=None, admin_email=None):
        if nuevo_estado not in self.ESTADOS:
            raise ValueError(f"Estado inválido")
        
        self.estado = nuevo_estado
        self.fecha_actualizacion = datetime.utcnow()
        
        if comentario:
            self.comentarios_admin.append({
                'fecha': datetime.now().isoformat(),
                'admin': admin_email,
                'comentario': comentario
            })
        
        self.historial.append({
            'fecha': datetime.now().isoformat(),
            'tipo': 'estado_cambiado',
            'descripcion': f'Estado cambiado a: {nuevo_estado}',
            'usuario': admin_email or 'sistema',
            'comentario': comentario
        })
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'folio': self.folio,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'tipo': self.tipo,
            'tipo_nombre': self.tipo_nombre,
            'descripcion': self.descripcion,
            'ubicacion': self.ubicacion,
            'direccion': self.direccion,
            'lat': self.lat,
            'lng': self.lng,
            'geolocalizada': self.geolocalizada,
            'anonimo': self.anonimo,
            'evidencia': self.evidencia,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'comentarios_admin': self.comentarios_admin,
            'historial': self.historial,
            'documentos': self.documentos,
            'asignado_a': self.asignado_a
        }