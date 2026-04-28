# models/solicitud.py
from extensions import db
from datetime import datetime
import random
import string
import json
from pathlib import Path

DATA_DIR = Path("data")
SOLICITUDES_FILE = DATA_DIR / "solicitudes.json"

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(50), unique=True, nullable=False, index=True)
    usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=False, index=True)
    usuario_nombre = db.Column(db.String(200))
    usuario_cedula = db.Column(db.String(50))
    servicio_id = db.Column(db.String(100), index=True)
    servicio_nombre = db.Column(db.String(200))
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(50), default='pendiente', index=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    comentarios_admin = db.Column(db.JSON, default=list)
    historial = db.Column(db.JSON, default=list)
    documentos = db.Column(db.JSON, default=list)
    asignado_a = db.Column(db.String(120))
    
    ESTADOS = ['pendiente', 'en_proceso', 'completado', 'rechazado', 'cancelado']
    
    @staticmethod
    def generar_folio():
        fecha = datetime.now().strftime("%y%m%d")
        random_part = ''.join(random.choices(string.digits, k=5))
        return f"SOL-{fecha}-{random_part}"
    
    @classmethod
    def migrar_desde_json(cls):
        """Migra todos los datos del archivo JSON a PostgreSQL"""
        if not SOLICITUDES_FILE.exists():
            print("⚠️ No hay archivo solicitudes.json para migrar")
            return 0
        
        with open(SOLICITUDES_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        contador = 0
        for item in datos:
            # Verificar si ya existe
            existe = cls.query.filter_by(folio=item.get('folio')).first()
            if existe:
                continue
            
            # Convertir fechas
            fecha_creacion = None
            if item.get('fecha_creacion'):
                try:
                    fecha_creacion = datetime.fromisoformat(item.get('fecha_creacion'))
                except:
                    fecha_creacion = datetime.utcnow()
            
            fecha_actualizacion = None
            if item.get('fecha_actualizacion'):
                try:
                    fecha_actualizacion = datetime.fromisoformat(item.get('fecha_actualizacion'))
                except:
                    fecha_actualizacion = fecha_creacion or datetime.utcnow()
            
            nueva = cls(
                folio=item.get('folio'),
                usuario_email=item.get('usuario_email'),
                usuario_nombre=item.get('usuario_nombre'),
                usuario_cedula=item.get('usuario_cedula'),
                servicio_id=item.get('servicio_id'),
                servicio_nombre=item.get('servicio_nombre'),
                descripcion=item.get('descripcion'),
                estado=item.get('estado', 'pendiente'),
                fecha_creacion=fecha_creacion,
                fecha_actualizacion=fecha_actualizacion,
                comentarios_admin=item.get('comentarios_admin', []),
                historial=item.get('historial', []),
                documentos=item.get('documentos', []),
                asignado_a=item.get('asignado_a')
            )
            db.session.add(nueva)
            contador += 1
        
        db.session.commit()
        print(f"✅ Migradas {contador} solicitudes a PostgreSQL")
        return contador
    
    @classmethod
    def crear(cls, usuario_email, usuario_nombre, usuario_cedula,
              servicio_id, servicio_nombre, descripcion):
        """Crea una nueva solicitud en PostgreSQL"""
        nueva = cls(
            folio=cls.generar_folio(),
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            usuario_cedula=usuario_cedula,
            servicio_id=servicio_id,
            servicio_nombre=servicio_nombre,
            descripcion=descripcion,
            estado='pendiente',
            comentarios_admin=[],
            historial=[{
                'fecha': datetime.now().isoformat(),
                'tipo': 'creada',
                'descripcion': 'Solicitud creada',
                'usuario': usuario_email,
                'nombre': usuario_nombre
            }],
            documentos=[],
            asignado_a=None
        )
        db.session.add(nueva)
        db.session.commit()
        return nueva
    
    @classmethod
    def buscar_por_usuario(cls, email):
        return cls.query.filter_by(usuario_email=email).order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def buscar_por_id(cls, solicitud_id):
        return cls.query.get(solicitud_id)
    
    @classmethod
    def buscar_por_folio(cls, folio):
        return cls.query.filter_by(folio=folio).first()
    
    @classmethod
    def cargar_todos(cls):
        """Compatibilidad con el código existente que espera JSON"""
        return cls.query.order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def guardar_todos(cls, solicitudes):
        """Compatibilidad - ya no es necesario, pero mantenemos por si acaso"""
        pass
    
    def actualizar_estado(self, nuevo_estado, comentario=None, admin_email=None):
        if nuevo_estado not in self.ESTADOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {self.ESTADOS}")
        
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
            'usuario_cedula': self.usuario_cedula,
            'servicio_id': self.servicio_id,
            'servicio_nombre': self.servicio_nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'comentarios_admin': self.comentarios_admin,
            'historial': self.historial,
            'documentos': self.documentos,
            'asignado_a': self.asignado_a
        }