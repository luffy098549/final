# ================================================================
# MODELO MENSAJE - PARA GUARDAR CONTACTOS Y COMUNICACIONES
# ================================================================
from extensions import db
from datetime import datetime
import json

class Mensaje(db.Model):
    __tablename__ = 'mensajes'
    
    id = db.Column(db.Integer, primary_key=True)
    tramite_folio = db.Column(db.String(20), nullable=False, index=True)
    tramite_tipo = db.Column(db.String(50), nullable=False, index=True)
    usuario_email = db.Column(db.String(120), nullable=False, index=True)
    autor_email = db.Column(db.String(120), nullable=False)
    autor_nombre = db.Column(db.String(200), nullable=False)
    autor_rol = db.Column(db.String(50), nullable=True, default='ciudadano')
    mensaje = db.Column(db.Text, nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    leido = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Columna para respuestas anidadas (hilos de conversación)
    respuesta_a = db.Column(db.Integer, db.ForeignKey('mensajes.id'), nullable=True)
    
    # Relación para obtener las respuestas de un mensaje
    respuestas = db.relationship('Mensaje', backref=db.backref('padre', remote_side=[id]), lazy='dynamic')
    
    def __init__(self, tramite_folio, tramite_tipo, usuario_email, autor_email, 
                 autor_nombre, mensaje, es_admin=False, autor_rol=None, leido=False, respuesta_a=None):
        self.tramite_folio = tramite_folio
        self.tramite_tipo = tramite_tipo
        self.usuario_email = usuario_email
        self.autor_email = autor_email
        self.autor_nombre = autor_nombre
        self.mensaje = mensaje
        self.es_admin = es_admin
        self.autor_rol = autor_rol if autor_rol else ('admin' if es_admin else 'ciudadano')
        self.leido = leido
        self.respuesta_a = respuesta_a
        self.fecha_creacion = datetime.utcnow()
    
    # ================================================================
    # PROPIEDADES PARA FACILITAR EL ACCESO A DATOS
    # ================================================================
    @property
    def tiene_respuesta(self):
        """Verifica si este mensaje tiene respuestas"""
        return Mensaje.query.filter_by(respuesta_a=self.id).count() > 0
    
    @property
    def asunto(self):
        """Extrae el asunto del mensaje"""
        lineas = self.mensaje.split('\n')
        for linea in lineas:
            if 'Asunto:' in linea:
                return linea.replace('Asunto:', '').strip()
        # Si no hay asunto, tomar las primeras 50 caracteres
        return self.mensaje[:50] + ('...' if len(self.mensaje) > 50 else '')
    
    @property
    def mensaje_sin_asunto(self):
        """Obtiene el mensaje sin la línea del asunto"""
        lineas = self.mensaje.split('\n')
        lineas_filtradas = [l for l in lineas if 'Asunto:' not in l and 'Teléfono:' not in l]
        # Eliminar la primera línea si está vacía
        if lineas_filtradas and not lineas_filtradas[0].strip():
            lineas_filtradas = lineas_filtradas[1:]
        return '\n'.join(lineas_filtradas).strip()
    
    @property
    def telefono(self):
        """Extrae el teléfono del mensaje"""
        lineas = self.mensaje.split('\n')
        for linea in lineas:
            if 'Teléfono:' in linea:
                telefono = linea.replace('Teléfono:', '').strip()
                if telefono and telefono != 'No especificado':
                    return telefono
        return None
    
    def marcar_leido(self):
        """Marca el mensaje como leído"""
        if not self.leido:
            self.leido = True
            db.session.commit()
    
    def to_dict(self):
        """Convierte el mensaje a diccionario para JSON"""
        return {
            'id': self.id,
            'tramite_folio': self.tramite_folio,
            'tramite_tipo': self.tramite_tipo,
            'usuario_email': self.usuario_email,
            'autor_email': self.autor_email,
            'autor_nombre': self.autor_nombre,
            'autor_rol': self.autor_rol,
            'mensaje': self.mensaje,
            'mensaje_sin_asunto': self.mensaje_sin_asunto,
            'asunto': self.asunto,
            'telefono': self.telefono,
            'es_admin': self.es_admin,
            'leido': self.leido,
            'tiene_respuesta': self.tiene_respuesta,
            'respuesta_a': self.respuesta_a,
            'fecha_creacion': self.fecha_creacion.strftime("%d/%m/%Y %H:%M") if self.fecha_creacion else None
        }
    
    # ================================================================
    # CREAR CONTACTO DESDE FORMULARIO (MÉTODO SIMPLIFICADO)
    # ================================================================
    @staticmethod
    def crear_contacto(nombre, email, telefono, asunto, mensaje):
        """Crea un nuevo contacto desde el formulario público"""
        folio = f"CTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Formatear el mensaje con asunto y teléfono
        mensaje_completo = f"Asunto: {asunto}\nTeléfono: {telefono if telefono else 'No especificado'}\n\nMensaje: {mensaje}"
        
        nuevo = Mensaje(
            tramite_folio=folio,
            tramite_tipo='consulta',
            usuario_email=email,
            autor_email=email,
            autor_nombre=nombre,
            mensaje=mensaje_completo,
            es_admin=False
        )
        db.session.add(nuevo)
        db.session.commit()
        
        # Notificar a los administradores
        try:
            from models.notificacion import Notificacion
            from models.usuario import Usuario
            
            admins = Usuario.query.filter(Usuario.rol.in_(['admin', 'super_admin'])).all()
            for admin in admins:
                Notificacion.crear_notificacion(
                    usuario_email=admin.email,
                    titulo="📬 Nuevo contacto recibido",
                    mensaje=f"El usuario {nombre} ha enviado un nuevo mensaje. Folio: {folio}",
                    tipo='contacto',
                    datos_extra={'folio': folio, 'contacto_id': nuevo.id}
                )
        except Exception as e:
            print(f"⚠️ Error al crear notificaciones para admins: {e}")
        
        return nuevo
    
    # ================================================================
    # RESPONDER CONTACTO (ADMIN)
    # ================================================================
    @staticmethod
    def responder_contacto(contacto_id, admin_email, admin_nombre, respuesta):
        """El administrador responde a un contacto"""
        contacto_original = Mensaje.query.get(contacto_id)
        
        if not contacto_original:
            raise Exception("Contacto no encontrado")
        
        # Crear la respuesta del admin
        respuesta_mensaje = Mensaje(
            tramite_folio=contacto_original.tramite_folio,
            tramite_tipo='consulta',
            usuario_email=contacto_original.usuario_email,
            autor_email=admin_email,
            autor_nombre=admin_nombre,
            mensaje=respuesta,
            es_admin=True,
            autor_rol='admin',
            respuesta_a=contacto_id
        )
        
        db.session.add(respuesta_mensaje)
        db.session.commit()
        
        # Marcar el contacto original como leído
        if not contacto_original.leido:
            contacto_original.leido = True
            db.session.commit()
        
        # Notificar al usuario que recibió respuesta
        try:
            from models.notificacion import Notificacion
            
            Notificacion.crear_notificacion(
                usuario_email=contacto_original.usuario_email,
                titulo="✅ Respuesta a tu consulta",
                mensaje=f"El administrador ha respondido a tu consulta. Folio: {contacto_original.tramite_folio}",
                tipo='contacto',
                datos_extra={'folio': contacto_original.tramite_folio, 'contacto_id': contacto_id}
            )
        except Exception as e:
            print(f"⚠️ Error al crear notificación para usuario: {e}")
        
        return respuesta_mensaje
    
    # ================================================================
    # OBTENER CONVERSACIÓN COMPLETA
    # ================================================================
    @staticmethod
    def obtener_conversacion_contacto(contacto_id):
        """Obtiene todo el hilo de conversación de un contacto"""
        contacto = Mensaje.query.get(contacto_id)
        if not contacto:
            return None
        
        conversacion = Mensaje.query.filter_by(
            tramite_folio=contacto.tramite_folio,
            tramite_tipo='consulta'
        ).order_by(Mensaje.fecha_creacion.asc()).all()
        
        return {
            'original': conversacion[0] if conversacion else None,
            'respuestas': conversacion[1:] if len(conversacion) > 1 else [],
            'tiene_respuesta': len(conversacion) > 1
        }
    
    # ================================================================
    # CONTACTOS PENDIENTES (SIN RESPUESTA)
    # ================================================================
    @staticmethod
    def obtener_contactos_pendientes():
        """Obtiene todos los contactos que NO han sido respondidos"""
        from sqlalchemy import func
        
        # Subquery para contar mensajes por folio
        subquery = db.session.query(
            Mensaje.tramite_folio,
            func.count(Mensaje.id).label('total_mensajes')
        ).filter_by(tramite_tipo='consulta').group_by(Mensaje.tramite_folio).subquery()
        
        # Obtener solo los mensajes originales (sin respuesta)
        resultados = db.session.query(Mensaje).join(
            subquery, Mensaje.tramite_folio == subquery.c.tramite_folio
        ).filter(
            Mensaje.tramite_tipo == 'consulta',
            Mensaje.es_admin == False,
            subquery.c.total_mensajes == 1
        ).order_by(Mensaje.fecha_creacion.desc()).all()
        
        return resultados
    
    # ================================================================
    # TODOS LOS CONTACTOS (AGRUPADOS POR CONVERSACIÓN)
    # ================================================================
    @staticmethod
    def obtener_todos_contactos():
        """Obtiene todos los contactos agrupados por conversación"""
        # Obtener todos los folios únicos
        folios = db.session.query(Mensaje.tramite_folio).filter_by(
            tramite_tipo='consulta'
        ).distinct().all()
        
        conversaciones = []
        for folio in folios:
            # Obtener todos los mensajes de este folio
            mensajes = Mensaje.query.filter_by(
                tramite_folio=folio[0],
                tramite_tipo='consulta'
            ).order_by(Mensaje.fecha_creacion.asc()).all()
            
            if mensajes:
                primer_mensaje = mensajes[0]
                tiene_respuesta = len(mensajes) > 1
                
                # Crear objeto de conversación
                conversaciones.append({
                    'id': primer_mensaje.id,
                    'folio': folio[0],
                    'autor_nombre': primer_mensaje.autor_nombre,
                    'usuario_email': primer_mensaje.usuario_email,
                    'asunto': primer_mensaje.asunto,
                    'mensaje': primer_mensaje.mensaje,
                    'fecha_creacion': primer_mensaje.fecha_creacion,
                    'tiene_respuesta': tiene_respuesta,
                    'leido': primer_mensaje.leido,
                    'respuesta': mensajes[1].mensaje if len(mensajes) > 1 else None,
                    'fecha_respuesta': mensajes[1].fecha_creacion if len(mensajes) > 1 else None
                })
        
        # Ordenar por fecha más reciente
        conversaciones.sort(key=lambda x: x['fecha_creacion'], reverse=True)
        return conversaciones
    
    # ================================================================
    # OTROS MÉTODOS ÚTILES
    # ================================================================
    @staticmethod
    def crear_mensaje(tramite_folio, tramite_tipo, usuario_email, autor_email, autor_nombre, mensaje, es_admin=False, respuesta_a=None):
        """Crea un nuevo mensaje y notifica al destinatario"""
        try:
            nuevo = Mensaje(
                tramite_folio=tramite_folio,
                tramite_tipo=tramite_tipo,
                usuario_email=usuario_email,
                autor_email=autor_email,
                autor_nombre=autor_nombre,
                mensaje=mensaje,
                es_admin=es_admin,
                respuesta_a=respuesta_a
            )
            db.session.add(nuevo)
            db.session.commit()
            
            # Crear notificación para el destinatario
            try:
                from models.notificacion import Notificacion
                
                if es_admin:
                    titulo = f"Nuevo mensaje en tu {tramite_tipo}"
                    mensaje_notif = f"El administrador ha respondido a tu {tramite_tipo} {tramite_folio}"
                    
                    Notificacion.crear_notificacion(
                        usuario_email=usuario_email,
                        titulo=titulo,
                        mensaje=mensaje_notif,
                        tipo=tramite_tipo,
                        datos_extra={'folio': tramite_folio, 'tipo': tramite_tipo}
                    )
                else:
                    titulo = f"Nuevo mensaje de {autor_nombre}"
                    mensaje_notif = f"El usuario {autor_nombre} ha respondido en el trámite {tramite_folio}"
                    
                    from models.usuario import Usuario
                    admins = Usuario.query.filter_by(rol='admin').all()
                    for admin in admins:
                        Notificacion.crear_notificacion(
                            usuario_email=admin.email,
                            titulo=titulo,
                            mensaje=mensaje_notif,
                            tipo=tramite_tipo,
                            datos_extra={'folio': tramite_folio, 'tipo': tramite_tipo}
                        )
            except Exception as e:
                print(f"⚠️ Error al crear notificación: {e}")
            
            return nuevo
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear mensaje: {e}")
            raise e
    
    @staticmethod
    def obtener_mensajes_tramite(folio, tipo):
        """Obtiene todos los mensajes de un trámite ordenados por fecha"""
        return Mensaje.query.filter_by(
            tramite_folio=folio, 
            tramite_tipo=tipo
        ).order_by(Mensaje.fecha_creacion.asc()).all()
    
    @staticmethod
    def obtener_estadisticas():
        """Obtiene estadísticas de contactos"""
        total = Mensaje.query.filter_by(tramite_tipo='consulta').count()
        
        # Contactos con respuesta
        contactos_con_respuesta = db.session.query(
            Mensaje.respuesta_a
        ).filter(
            Mensaje.respuesta_a.isnot(None)
        ).distinct().count()
        
        no_leidos = Mensaje.query.filter_by(tramite_tipo='consulta', leido=False).count()
        leidos = total - no_leidos
        pendientes = total - contactos_con_respuesta
        
        return {
            'total': total,
            'leidos': leidos,
            'no_leidos': no_leidos,
            'respondidos': contactos_con_respuesta,
            'pendientes': pendientes
        }
    
    def __repr__(self):
        return f'<Mensaje {self.tramite_folio} - {self.autor_nombre}>'