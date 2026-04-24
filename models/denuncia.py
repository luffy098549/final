"""
Modelo para gestionar denuncias ciudadanas
"""
import json
import uuid
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DENUNCIAS_FILE = DATA_DIR / "denuncias.json"

class Denuncia:
    """Modelo para denuncias ciudadanas"""
    
    ESTADOS = ['pendiente', 'en_investigacion', 'resuelto', 'rechazado', 'cancelado']
    
    # Tipos de denuncia predefinidos
    TIPOS_DENUNCIA = {
        'seguridad': 'Seguridad ciudadana',
        'ruidos': 'Contaminación auditiva',
        'basura': 'Acumulación de basura',
        'alumbrado': 'Alumbrado público',
        'vialidad': 'Problemas de vialidad',
        'ambiente': 'Daño ambiental',
        'construccion': 'Construcción ilegal',
        'comercio': 'Comercio ambulante',
        'animales': 'Maltrato animal',
        'otros': 'Otros'
    }
    
    def __init__(self, id=None, folio=None, usuario_email=None, usuario_nombre=None,
                 tipo=None, tipo_nombre=None, descripcion=None, direccion=None,
                 latitud=None, longitud=None, direccion_completa=None,
                 anonimo=False, estado='pendiente', fecha_creacion=None,
                 fecha_actualizacion=None, comentarios_admin=None, historial=None,
                 documentos=None, asignado_a=None, ubicacion=None, evidencia=None,
                 # NUEVOS CAMPOS PARA GEOLOCALIZACIÓN (manteniendo compatibilidad)
                 lat=None, lng=None, geolocalizada=False):
        
        self.id = id or str(uuid.uuid4())
        self.folio = folio or self.generar_folio()
        self.usuario_email = usuario_email
        self.usuario_nombre = usuario_nombre or "Anónimo"
        self.tipo = tipo
        self.tipo_nombre = tipo_nombre or self.TIPOS_DENUNCIA.get(tipo, 'Otros')
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
        self.ubicacion = ubicacion  # Campo para descripción textual de ubicación
        self.evidencia = evidencia  # Campo para evidencia
        
        # NUEVOS CAMPOS PARA GEOLOCALIZACIÓN (compatibilidad con formulario con mapa)
        self.lat = lat if lat is not None else (latitud if latitud else None)
        self.lng = lng if lng is not None else (longitud if longitud else None)
        self.geolocalizada = geolocalizada or (self.lat is not None and self.lng is not None)
    
    @property
    def geolocalizada_prop(self):
        """Indica si la denuncia tiene coordenadas"""
        return (self.lat is not None and self.lng is not None) or (self.latitud is not None and self.longitud is not None)
    
    @staticmethod
    def generar_folio():
        """
        Genera un folio único para la denuncia
        Formato: DEN-YYMMDD-XXXXX
        """
        fecha = datetime.now().strftime("%y%m%d")
        random_part = ''.join(random.choices(string.digits, k=5))
        folio = f"DEN-{fecha}-{random_part}"
        
        # Verificar que el folio no exista ya
        denuncias = Denuncia.cargar_todos()
        while any(d.folio == folio for d in denuncias):
            random_part = ''.join(random.choices(string.digits, k=5))
            folio = f"DEN-{fecha}-{random_part}"
        
        return folio
    
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
            'asignado_a': self.asignado_a,
            'ubicacion': getattr(self, 'ubicacion', ''),
            'evidencia': getattr(self, 'evidencia', ''),
            # NUEVOS CAMPOS
            'lat': getattr(self, 'lat', self.latitud),
            'lng': getattr(self, 'lng', self.longitud),
            'geolocalizada': self.geolocalizada_prop
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
            asignado_a=data.get('asignado_a'),
            ubicacion=data.get('ubicacion', ''),
            evidencia=data.get('evidencia', ''),
            # NUEVOS CAMPOS
            lat=data.get('lat', data.get('latitud')),
            lng=data.get('lng', data.get('longitud')),
            geolocalizada=data.get('geolocalizada', False)
        )
    
    @classmethod
    def cargar_todos(cls):
        """Carga todas las denuncias del archivo JSON"""
        if not DENUNCIAS_FILE.exists():
            print(f"[DEBUG] El archivo {DENUNCIAS_FILE} no existe, creando uno nuevo")
            return []
        try:
            with open(DENUNCIAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[DEBUG] Cargadas {len(data)} denuncias desde {DENUNCIAS_FILE}")
                return [cls.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[ERROR] Error cargando denuncias: {e}")
            return []
    
    @classmethod
    def guardar_todos(cls, denuncias):
        """Guarda todas las denuncias en el archivo JSON"""
        try:
            with open(DENUNCIAS_FILE, 'w', encoding='utf-8') as f:
                json.dump([d.to_dict() for d in denuncias], f,
                         ensure_ascii=False, indent=2)
            print(f"[DEBUG] Guardadas {len(denuncias)} denuncias en {DENUNCIAS_FILE}")
            return True
        except Exception as e:
            print(f"[ERROR] Error guardando denuncias: {e}")
            return False
    
    @classmethod
    def guardar(cls, denuncia):
        """Guarda una denuncia (agrega o actualiza)"""
        denuncias = cls.cargar_todos()
        encontrado = False
        for i, d in enumerate(denuncias):
            if d.id == denuncia.id:
                denuncias[i] = denuncia
                encontrado = True
                break
        if not encontrado:
            denuncias.append(denuncia)
        cls.guardar_todos(denuncias)
        return denuncia
    
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
    def buscar_por_tipo(cls, tipo):
        """Busca denuncias por tipo"""
        todas = cls.cargar_todos()
        return [d for d in todas if d.tipo == tipo]
    
    @classmethod
    def buscar_por_estado(cls, estado):
        """Busca denuncias por estado"""
        todas = cls.cargar_todos()
        return [d for d in todas if d.estado == estado]
    
    @classmethod
    def buscar_por_rango_fechas(cls, fecha_inicio, fecha_fin):
        """Busca denuncias en un rango de fechas"""
        todas = cls.cargar_todos()
        resultado = []
        for d in todas:
            fecha_creacion = datetime.fromisoformat(d.fecha_creacion).date()
            if fecha_inicio <= fecha_creacion <= fecha_fin:
                resultado.append(d)
        return resultado
    
    @classmethod
    def crear(cls, usuario_email=None, usuario_nombre="Anónimo",
              tipo=None, tipo_nombre=None, descripcion=None,
              direccion=None, anonimo=False, latitud=None, longitud=None,
              ubicacion=None, evidencia=None, lat=None, lng=None):
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
            anonimo=anonimo,
            ubicacion=ubicacion,
            evidencia=evidencia,
            lat=lat,
            lng=lng
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
    
    def actualizar_estado(self, nuevo_estado, comentario=None, admin_email=None):
        """Actualiza el estado de la denuncia"""
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
        denuncias = self.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.id == self.id:
                denuncias[i] = self
                break
        self.guardar_todos(denuncias)
    
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
        denuncias = self.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.id == self.id:
                denuncias[i] = self
                break
        self.guardar_todos(denuncias)
    
    def geolocalizar(self, latitud, longitud, direccion_completa=None):
        """Actualiza las coordenadas de la denuncia"""
        self.latitud = latitud
        self.longitud = longitud
        self.lat = latitud
        self.lng = longitud
        self.geolocalizada = True
        if direccion_completa:
            self.direccion_completa = direccion_completa
        self.fecha_actualizacion = datetime.now().isoformat()
        
        self.historial.append({
            'fecha': self.fecha_actualizacion,
            'tipo': 'geolocalizada',
            'descripcion': f'Denuncia geolocalizada: {latitud}, {longitud}',
            'usuario': 'sistema'
        })
        
        # Guardar cambios
        denuncias = self.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.id == self.id:
                denuncias[i] = self
                break
        self.guardar_todos(denuncias)
    
    def asignar(self, admin_email):
        """Asigna la denuncia a un administrador"""
        self.asignado_a = admin_email
        self.fecha_actualizacion = datetime.now().isoformat()
        
        self.historial.append({
            'fecha': self.fecha_actualizacion,
            'tipo': 'asignada',
            'descripcion': f'Asignada a: {admin_email}',
            'usuario': admin_email
        })
        
        # Guardar cambios
        denuncias = self.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.id == self.id:
                denuncias[i] = self
                break
        self.guardar_todos(denuncias)
    
    def agregar_documento(self, nombre_documento, url_documento):
        """Agrega un documento a la denuncia"""
        self.documentos.append({
            'nombre': nombre_documento,
            'url': url_documento,
            'fecha': datetime.now().isoformat()
        })
        self.fecha_actualizacion = datetime.now().isoformat()
        
        # Guardar cambios
        denuncias = self.cargar_todos()
        for i, d in enumerate(denuncias):
            if d.id == self.id:
                denuncias[i] = self
                break
        self.guardar_todos(denuncias)
    
    @classmethod
    def get_estadisticas(cls):
        """Obtiene estadísticas de las denuncias"""
        todas = cls.cargar_todos()
        
        stats = {
            'total': len(todas),
            'por_estado': {estado: 0 for estado in cls.ESTADOS},
            'por_tipo': {tipo: 0 for tipo in cls.TIPOS_DENUNCIA.keys()},
            'anonimas': 0,
            'geolocalizadas': 0,
            'ultimas_30_dias': 0
        }
        
        fecha_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_30_dias = fecha_limite - timedelta(days=30)
        
        for d in todas:
            # Por estado
            stats['por_estado'][d.estado] = stats['por_estado'].get(d.estado, 0) + 1
            
            # Por tipo
            if d.tipo:
                stats['por_tipo'][d.tipo] = stats['por_tipo'].get(d.tipo, 0) + 1
            
            # Anónimas
            if d.anonimo:
                stats['anonimas'] += 1
            
            # Geolocalizadas
            if d.geolocalizada_prop:
                stats['geolocalizadas'] += 1
            
            # Últimos 30 días
            fecha_creacion = datetime.fromisoformat(d.fecha_creacion)
            if fecha_creacion >= fecha_30_dias:
                stats['ultimas_30_dias'] += 1
        
        return stats