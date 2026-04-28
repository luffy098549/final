# models/log_actividad.py
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

class LogActividad(db.Model):
    __tablename__ = 'logs_actividad'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(120), db.ForeignKey('usuarios.email'), nullable=True, index=True)
    usuario_nombre = db.Column(db.String(200), nullable=True)
    accion = db.Column(db.String(100), nullable=False, index=True)
    modulo = db.Column(db.String(50), index=True)
    descripcion = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), index=True)  # IPv4 (15) o IPv6 (45)
    user_agent = db.Column(db.String(300), nullable=True)
    datos_extra = db.Column(db.JSON, default=dict)
    nivel = db.Column(db.String(20), default='info', index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    NIVELES = ['info', 'warning', 'error', 'critico']
    
    @classmethod
    def registrar(cls, accion, modulo, descripcion='', usuario_email=None, usuario_nombre=None,
                  ip_address=None, user_agent=None, datos_extra=None, nivel='info'):
        """
        Registra una acción en el log de actividad
        
        Retorna: instancia del log creado
        """
        if nivel not in cls.NIVELES:
            nivel = 'info'
        
        log = cls(
            accion=accion[:100],
            modulo=modulo[:50] if modulo else None,
            descripcion=descripcion,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre[:200] if usuario_nombre else None,
            ip_address=ip_address[:45] if ip_address else None,
            user_agent=user_agent[:300] if user_agent else None,
            datos_extra=datos_extra or {},
            nivel=nivel
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def listar(cls, pagina=1, por_pagina=50, filtros=None):
        """
        Lista logs con paginación y filtros opcionales
        
        Args:
            pagina: número de página
            por_pagina: registros por página
            filtros: dict con claves opcionales:
                - usuario_email: str
                - modulo: str
                - nivel: str
                - accion: str (contiene)
                - fecha_desde: date/datetime
                - fecha_hasta: date/datetime
                - ip_address: str
        
        Retorna: objeto paginado de SQLAlchemy
        """
        query = cls.query
        
        if filtros:
            if filtros.get('usuario_email'):
                query = query.filter_by(usuario_email=filtros['usuario_email'])
            
            if filtros.get('modulo'):
                query = query.filter_by(modulo=filtros['modulo'])
            
            if filtros.get('nivel'):
                query = query.filter_by(nivel=filtros['nivel'])
            
            if filtros.get('accion'):
                query = query.filter(cls.accion.contains(filtros['accion']))
            
            if filtros.get('ip_address'):
                query = query.filter_by(ip_address=filtros['ip_address'])
            
            if filtros.get('fecha_desde'):
                fecha_desde = filtros['fecha_desde']
                if not isinstance(fecha_desde, datetime):
                    fecha_desde = datetime.combine(fecha_desde, datetime.min.time())
                query = query.filter(cls.fecha_creacion >= fecha_desde)
            
            if filtros.get('fecha_hasta'):
                fecha_hasta = filtros['fecha_hasta']
                if not isinstance(fecha_hasta, datetime):
                    fecha_hasta = datetime.combine(fecha_hasta, datetime.max.time())
                query = query.filter(cls.fecha_creacion <= fecha_hasta)
        
        query = query.order_by(cls.fecha_creacion.desc())
        
        return query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    
    @classmethod
    def detectar_actividad_sospechosa(cls, ip_address, ventana_minutos=5, umbral=10):
        """
        Detecta actividad sospechosa por IP en ventana de tiempo
        
        Args:
            ip_address: IP a analizar
            ventana_minutos: minutos a considerar
            umbral: cantidad máxima de acciones permitidas
        
        Retorna: True si es sospechoso, False si no
        """
        if not ip_address:
            return False
        
        fecha_limite = datetime.utcnow() - timedelta(minutes=ventana_minutos)
        
        count = cls.query.filter(
            cls.ip_address == ip_address,
            cls.fecha_creacion >= fecha_limite
        ).count()
        
        return count > umbral
    
    @classmethod
    def obtener_estadisticas(cls, dias=7):
        """
        Obtiene estadísticas de logs de los últimos X días
        
        Retorna: dict con estadísticas
        """
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        # Total de logs
        total = cls.query.filter(cls.fecha_creacion >= fecha_limite).count()
        
        # Por nivel
        niveles = {}
        for nivel in cls.NIVELES:
            count = cls.query.filter(
                cls.fecha_creacion >= fecha_limite,
                cls.nivel == nivel
            ).count()
            if count > 0:
                niveles[nivel] = count
        
        # Por módulo
        modulos_query = db.session.query(
            cls.modulo, func.count(cls.id).label('total')
        ).filter(
            cls.fecha_creacion >= fecha_limite,
            cls.modulo.isnot(None)
        ).group_by(cls.modulo).order_by(func.count(cls.id).desc()).all()
        
        por_modulo = {modulo: total for modulo, total in modulos_query}
        
        # Por día
        por_dia = []
        for i in range(dias):
            fecha = datetime.utcnow().date() - timedelta(days=i)
            fecha_inicio = datetime.combine(fecha, datetime.min.time())
            fecha_fin = datetime.combine(fecha, datetime.max.time())
            
            count = cls.query.filter(
                cls.fecha_creacion >= fecha_inicio,
                cls.fecha_creacion <= fecha_fin
            ).count()
            
            por_dia.append({
                'fecha': fecha.isoformat(),
                'total': count
            })
        
        # IPs sospechosas (más de 50 logs en el período)
        ips_sospechosas = []
        ips_query = db.session.query(
            cls.ip_address, func.count(cls.id).label('total')
        ).filter(
            cls.fecha_creacion >= fecha_limite,
            cls.ip_address.isnot(None)
        ).group_by(cls.ip_address).having(func.count(cls.id) > 50).all()
        
        for ip, total_ips in ips_query:
            ips_sospechosas.append({'ip': ip, 'total_acciones': total_ips})
        
        return {
            'total': total,
            'por_nivel': niveles,
            'por_modulo': por_modulo,
            'por_dia': por_dia,
            'ips_sospechosas': ips_sospechosas,
            'periodo_dias': dias
        }
    
    @classmethod
    def exportar_a_lista(cls, filtros=None, limite=1000):
        """
        Exporta logs a lista de diccionarios (útil para Excel/PDF)
        
        Args:
            filtros: mismos que en listar()
            limite: máximo de registros a exportar
        
        Retorna: lista de dicts
        """
        query = cls.query
        
        if filtros:
            if filtros.get('usuario_email'):
                query = query.filter_by(usuario_email=filtros['usuario_email'])
            if filtros.get('modulo'):
                query = query.filter_by(modulo=filtros['modulo'])
            if filtros.get('nivel'):
                query = query.filter_by(nivel=filtros['nivel'])
            if filtros.get('accion'):
                query = query.filter(cls.accion.contains(filtros['accion']))
            if filtros.get('fecha_desde'):
                fecha_desde = filtros['fecha_desde']
                if not isinstance(fecha_desde, datetime):
                    fecha_desde = datetime.combine(fecha_desde, datetime.min.time())
                query = query.filter(cls.fecha_creacion >= fecha_desde)
            if filtros.get('fecha_hasta'):
                fecha_hasta = filtros['fecha_hasta']
                if not isinstance(fecha_hasta, datetime):
                    fecha_hasta = datetime.combine(fecha_hasta, datetime.max.time())
                query = query.filter(cls.fecha_creacion <= fecha_hasta)
        
        query = query.order_by(cls.fecha_creacion.desc()).limit(limite)
        
        return [log.to_dict() for log in query.all()]
    
    @classmethod
    def limpiar_antiguos(cls, dias=90):
        """
        Elimina logs más antiguos de X días
        
        Retorna: número de logs eliminados
        """
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        eliminados = cls.query.filter(cls.fecha_creacion < fecha_limite).delete()
        db.session.commit()
        return eliminados
    
    def to_dict(self):
        """Convierte el log a diccionario"""
        return {
            'id': self.id,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'accion': self.accion,
            'modulo': self.modulo,
            'descripcion': self.descripcion,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'datos_extra': self.datos_extra,
            'nivel': self.nivel,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_formateada': self.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S') if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f'<LogActividad {self.id} - {self.accion} - {self.modulo}>'


# ================================================================
# FUNCIÓN HELPER PARA USAR EN app.py Y admin.py
# ================================================================

def registrar_log(accion, modulo, descripcion='', nivel='info', datos_extra=None):
    """
    Helper que extrae automáticamente usuario, IP y user_agent del request de Flask.
    Silencia errores para no interrumpir el flujo principal.
    
    Uso:
        from models.log_actividad import registrar_log
        registrar_log('crear_solicitud', 'solicitudes', f'Folio {folio}')
    """
    try:
        from flask import request, session
        
        # Obtener datos del request
        ip_address = None
        user_agent = None
        
        try:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            user_agent = request.headers.get('User-Agent', '')[:300]
        except:
            pass
        
        # Obtener datos del usuario desde session o flask_login
        usuario_email = None
        usuario_nombre = None
        
        try:
            from flask_login import current_user
            
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                usuario_email = current_user.email if hasattr(current_user, 'email') else None
                usuario_nombre = current_user.nombre_completo if hasattr(current_user, 'nombre_completo') else None
                if not usuario_nombre and hasattr(current_user, 'nombre'):
                    usuario_nombre = current_user.nombre
        except:
            # Fallback a session
            usuario_email = session.get('user')
            usuario_nombre = session.get('user_name')
        
        # Registrar log
        LogActividad.registrar(
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            ip_address=ip_address,
            user_agent=user_agent,
            datos_extra=datos_extra,
            nivel=nivel
        )
    except Exception as e:
        # Silenciar errores para no interrumpir el flujo principal
        print(f"⚠️ Error al registrar log: {e}")