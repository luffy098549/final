# models/cita.py
from extensions import db
from datetime import datetime
import uuid
import json
from pathlib import Path

DATA_DIR = Path("data")
CITAS_FILE = DATA_DIR / "citas.json"

class Cita(db.Model):
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(50), unique=True, nullable=False, index=True)
    usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=False, index=True)
    usuario_nombre = db.Column(db.String(200))
    servicio = db.Column(db.String(100), index=True)
    servicio_nombre = db.Column(db.String(200))
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora = db.Column(db.String(5), nullable=False)
    motivo = db.Column(db.Text)
    estado = db.Column(db.String(50), default='pendiente', index=True)
    notas_admin = db.Column(db.Text)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    
    ESTADOS = ['pendiente', 'confirmada', 'cancelada', 'completada']
    
    SERVICIOS = {
        'asesoria_legal': 'Asesoría Legal Municipal',
        'catastro': 'Trámites de Catastro',
        'licencias': 'Licencias y Permisos',
        'atencion_ciudadana': 'Atención Ciudadana',
        'tesoreria': 'Tesorería Municipal',
        'planeamiento': 'Planeamiento Urbano',
        'oaim': 'Oficina de Acceso a la Información',
        'funeraria': 'Servicios Funerarios'
    }
    
    @staticmethod
    def generar_folio():
        fecha = datetime.now().strftime("%y%m%d")
        random_part = uuid.uuid4().hex[:6].upper()
        return f"CT-{fecha}-{random_part}"
    
    @classmethod
    def migrar_desde_json(cls):
        """Migra todos los datos del archivo JSON a PostgreSQL"""
        if not CITAS_FILE.exists():
            print("⚠️ No hay archivo citas.json para migrar")
            return 0
        
        with open(CITAS_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        contador = 0
        for item in datos:
            existe = cls.query.filter_by(folio=item.get('folio')).first()
            if existe:
                continue
            
            # Convertir fecha string a date
            fecha_obj = None
            if item.get('fecha'):
                try:
                    fecha_obj = datetime.strptime(item.get('fecha'), '%Y-%m-%d').date()
                except:
                    fecha_obj = datetime.utcnow().date()
            
            fecha_solicitud = None
            if item.get('fecha_solicitud'):
                try:
                    fecha_solicitud = datetime.fromisoformat(item.get('fecha_solicitud'))
                except:
                    fecha_solicitud = datetime.utcnow()
            
            nueva = cls(
                folio=item.get('folio'),
                usuario_email=item.get('usuario_email'),
                usuario_nombre=item.get('usuario_nombre'),
                servicio=item.get('servicio'),
                servicio_nombre=item.get('servicio_nombre', cls.SERVICIOS.get(item.get('servicio'), item.get('servicio'))),
                fecha=fecha_obj,
                hora=item.get('hora'),
                motivo=item.get('motivo'),
                estado=item.get('estado', 'pendiente'),
                notas_admin=item.get('notas_admin', ''),
                fecha_solicitud=fecha_solicitud
            )
            db.session.add(nueva)
            contador += 1
        
        db.session.commit()
        print(f"✅ Migradas {contador} citas a PostgreSQL")
        return contador
    
    @classmethod
    def crear(cls, usuario_email, usuario_nombre, servicio, fecha, hora, motivo):
        """Crea una nueva cita"""
        nueva = cls(
            folio=cls.generar_folio(),
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            servicio=servicio,
            servicio_nombre=cls.SERVICIOS.get(servicio, servicio),
            fecha=fecha,
            hora=hora,
            motivo=motivo,
            estado='pendiente'
        )
        db.session.add(nueva)
        db.session.commit()
        return nueva
    
    @classmethod
    def buscar_por_usuario(cls, email):
        return cls.query.filter_by(usuario_email=email).order_by(cls.fecha_solicitud.desc()).all()
    
    @classmethod
    def buscar_por_id(cls, cita_id):
        return cls.query.get(cita_id)
    
    @classmethod
    def buscar_por_folio(cls, folio):
        return cls.query.filter_by(folio=folio).first()
    
    @classmethod
    def cargar_todos(cls):
        """Compatibilidad con código existente"""
        return cls.query.order_by(cls.fecha_solicitud.desc()).all()
    
    @classmethod
    def guardar_todos(cls, citas):
        """Compatibilidad"""
        pass
    
    def cancelar(self):
        self.estado = 'cancelada'
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'folio': self.folio,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'servicio': self.servicio,
            'servicio_nombre': self.servicio_nombre,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'hora': self.hora,
            'motivo': self.motivo,
            'estado': self.estado,
            'notas_admin': self.notas_admin,
            'fecha_solicitud': self.fecha_solicitud.isoformat() if self.fecha_solicitud else None
        } 
    