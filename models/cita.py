"""
Modelo para el sistema de citas/turnos en línea
"""
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CITAS_FILE = DATA_DIR / "citas.json"

class Cita:
    """Modelo para gestionar citas ciudadanas"""
    
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
    
    HORARIOS = {
        'lunes': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
        'martes': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
        'miercoles': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
        'jueves': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
        'viernes': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
    }
    
    def __init__(self, id=None, folio=None, usuario_email=None, usuario_nombre=None,
                 servicio=None, fecha=None, hora=None, motivo=None,
                 estado='pendiente', fecha_solicitud=None, notas_admin=None):
        self.id = id or str(uuid.uuid4())
        self.folio = folio or self._generar_folio()
        self.usuario_email = usuario_email
        self.usuario_nombre = usuario_nombre
        self.servicio = servicio
        self.fecha = fecha  # YYYY-MM-DD
        self.hora = hora    # HH:MM
        self.motivo = motivo
        self.estado = estado
        self.fecha_solicitud = fecha_solicitud or datetime.now().isoformat()
        self.notas_admin = notas_admin or ""
    
    def _generar_folio(self):
        fecha = datetime.now().strftime("%y%m%d")
        random = uuid.uuid4().hex[:6].upper()
        return f"CT-{fecha}-{random}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'folio': self.folio,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'servicio': self.servicio,
            'servicio_nombre': self.SERVICIOS.get(self.servicio, self.servicio),
            'fecha': self.fecha,
            'hora': self.hora,
            'motivo': self.motivo,
            'estado': self.estado,
            'fecha_solicitud': self.fecha_solicitud,
            'notas_admin': self.notas_admin
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            folio=data.get('folio'),
            usuario_email=data.get('usuario_email'),
            usuario_nombre=data.get('usuario_nombre'),
            servicio=data.get('servicio'),
            fecha=data.get('fecha'),
            hora=data.get('hora'),
            motivo=data.get('motivo'),
            estado=data.get('estado', 'pendiente'),
            fecha_solicitud=data.get('fecha_solicitud'),
            notas_admin=data.get('notas_admin', '')
        )
    
    @classmethod
    def cargar_todos(cls):
        """Carga todas las citas del archivo JSON"""
        if not CITAS_FILE.exists():
            print(f"[DEBUG] El archivo {CITAS_FILE} no existe, creando uno nuevo")
            return []
        try:
            with open(CITAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[DEBUG] Cargadas {len(data)} citas desde {CITAS_FILE}")
                return [cls.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[ERROR] Error cargando citas: {e}")
            return []
    
    @classmethod
    def guardar_todos(cls, citas):
        """Guarda todas las citas en el archivo JSON"""
        try:
            with open(CITAS_FILE, 'w', encoding='utf-8') as f:
                json.dump([c.to_dict() for c in citas], f,
                         ensure_ascii=False, indent=2)
            print(f"[DEBUG] Guardadas {len(citas)} citas en {CITAS_FILE}")
            return True
        except Exception as e:
            print(f"[ERROR] Error guardando citas: {e}")
            return False
    
    @classmethod
    def buscar_por_usuario(cls, email):
        todas = cls.cargar_todos()
        return [c for c in todas if c.usuario_email == email]
    
    @classmethod
    def buscar_por_id(cls, cita_id):
        todas = cls.cargar_todos()
        for c in todas:
            if c.id == cita_id:
                return c
        return None
    
    @classmethod
    def buscar_por_folio(cls, folio):
        """Busca una cita por su folio"""
        todas = cls.cargar_todos()
        for c in todas:
            if c.folio == folio:
                return c
        return None
    
    @classmethod
    def horarios_disponibles(cls, servicio, fecha):
        todas = cls.cargar_todos()
        ocupados = [
            c.hora for c in todas 
            if c.fecha == fecha and c.estado in ['pendiente', 'confirmada']
        ]
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
            dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 
                         'viernes', 'sabado', 'domingo'][fecha_dt.weekday()]
            horarios_base = cls.HORARIOS.get(dia_semana, [])
        except:
            horarios_base = []
        disponibles = [h for h in horarios_base if h not in ocupados]
        return disponibles
    
    @classmethod
    def crear(cls, usuario_email, usuario_nombre, servicio, fecha, hora, motivo):
        nueva = cls(
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            servicio=servicio,
            fecha=fecha,
            hora=hora,
            motivo=motivo
        )
        citas = cls.cargar_todos()
        citas.append(nueva)
        cls.guardar_todos(citas)
        return nueva
    
    def cancelar(self):
        self.estado = 'cancelada'
        citas = self.cargar_todos()
        for i, c in enumerate(citas):
            if c.id == self.id:
                citas[i] = self
                break
        self.guardar_todos(citas)