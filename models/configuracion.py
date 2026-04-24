# models/configuracion.py
from extensions import db
from datetime import datetime
import json
from flask import current_app

class Configuracion(db.Model):
    """Modelo de configuración del sistema"""
    __tablename__ = 'configuracion'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='string')  # string, int, bool, json
    seccion = db.Column(db.String(50), default='general')
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Caché en memoria para evitar consultas repetidas
    _cache = {}
    
    def __init__(self, clave, valor=None, tipo='string', seccion='general'):
        self.clave = clave
        self.tipo = tipo
        self.seccion = seccion
        self.set_valor(valor)
    
    def get_valor(self):
        """Obtiene el valor convertido al tipo correcto (método de instancia)"""
        return self._convertir_valor(self.valor, self.tipo)
    
    def set_valor(self, valor):
        """Guarda el valor convirtiéndolo a string según el tipo (método de instancia)"""
        if valor is None:
            self.valor = None
        elif self.tipo == 'bool':
            self.valor = 'true' if valor else 'false'
        elif self.tipo == 'int':
            self.valor = str(valor)
        elif self.tipo == 'json':
            self.valor = json.dumps(valor)
        else:
            self.valor = str(valor)
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'clave': self.clave,
            'valor': self.get_valor(),
            'tipo': self.tipo,
            'seccion': self.seccion,
            'actualizado_en': self.actualizado_en.isoformat() if self.actualizado_en else None
        }
    
    @classmethod
    def get(cls, clave, default=None):
        """Obtiene una configuración por clave (con caché)"""
        # Intentar obtener del caché
        if clave in cls._cache:
            return cls._cache[clave]
        
        # Buscar en BD
        config = cls.query.filter_by(clave=clave).first()
        if config:
            valor = config.get_valor()
            cls._cache[clave] = valor
            return valor
        return default
    
    @classmethod
    def get_all(cls, seccion=None):
        """Obtiene todas las configuraciones de una sección (o todas si seccion=None)"""
        query = cls.query
        if seccion:
            query = query.filter_by(seccion=seccion)
        
        configs = {}
        for config in query.all():
            configs[config.clave] = config.get_valor()
        return configs
    
    @classmethod
    def get_seccion(cls, seccion):
        """Obtiene todas las configuraciones de una sección (alias de get_all)"""
        return cls.get_all(seccion=seccion)
    
    @classmethod
    def set(cls, clave, valor, tipo='string', seccion='general'):
        """Guarda o actualiza una configuración y limpia caché"""
        config = cls.query.filter_by(clave=clave).first()
        if config:
            config.tipo = tipo
            config.seccion = seccion
            config.set_valor(valor)
        else:
            config = cls(clave=clave, valor=valor, tipo=tipo, seccion=seccion)
            db.session.add(config)
        
        db.session.commit()
        
        # Limpiar caché para esta clave
        if clave in cls._cache:
            del cls._cache[clave]
        
        return config
    
    @classmethod
    def guardar_seccion(cls, seccion, datos):
        """Guarda múltiples configuraciones de una sección"""
        for clave, valor in datos.items():
            # Determinar tipo automáticamente si no se especifica
            tipo = 'string'
            if isinstance(valor, bool):
                tipo = 'bool'
            elif isinstance(valor, int):
                tipo = 'int'
            elif isinstance(valor, (dict, list)):
                tipo = 'json'
            
            cls.set(clave, valor, tipo=tipo, seccion=seccion)
        return True
    
    @classmethod
    def clear_cache(cls):
        """Limpia todo el caché de configuración"""
        cls._cache = {}
        if hasattr(current_app, 'config_cache'):
            current_app.config_cache = {}
    
    @classmethod
    def _convertir_valor(cls, valor, tipo):
        """Convertir valor según su tipo (método estático interno)"""
        if valor is None:
            return None
        if tipo == 'int':
            return int(valor)
        elif tipo == 'bool':
            return valor.lower() == 'true' if isinstance(valor, str) else bool(valor)
        elif tipo == 'json':
            return json.loads(valor) if isinstance(valor, str) else valor
        return valor if valor is not None else ''