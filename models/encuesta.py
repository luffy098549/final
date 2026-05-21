from extensions import db
from datetime import datetime
import json
from pathlib import Path

DATA_DIR = Path("data")
ENCUESTAS_FILE = DATA_DIR / "encuestas.json"


class Encuesta(db.Model):
    __tablename__ = 'encuestas'

    id = db.Column(db.Integer, primary_key=True)
    folio_tramite = db.Column(db.String(50), nullable=True, unique=True, index=True)
    folio_contacto = db.Column(db.String(50), nullable=True, unique=True, index=True)
    tipo_tramite = db.Column(db.String(50), index=True)  # 'tramite' o 'contacto'
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
            existe = cls.query.filter(
                (cls.folio_tramite == item.get('folio_tramite')) |
                (cls.folio_contacto == item.get('folio_contacto'))
            ).first()
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
                folio_contacto=item.get('folio_contacto'),
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
    def crear(cls, tipo_tramite, calificacion, usuario_nombre=None, usuario_email=None,
              folio_tramite=None, folio_contacto=None, comentario=""):
        """
        Crea una nueva encuesta.
        - Para trámites: tipo_tramite='tramite', folio_tramite requerido.
        - Para contacto: tipo_tramite='contacto', folio_contacto requerido.
        """
        if tipo_tramite == 'tramite':
            if not folio_tramite:
                raise ValueError("Se requiere folio_tramite para encuestas de trámite")
            if cls.buscar_por_tramite(folio_tramite):
                return None
        elif tipo_tramite == 'contacto':
            if not folio_contacto:
                raise ValueError("Se requiere folio_contacto para encuestas de contacto")
            if cls.buscar_por_contacto(folio_contacto):
                return None
        else:
            raise ValueError("tipo_tramite debe ser 'tramite' o 'contacto'")

        nueva = cls(
            folio_tramite=folio_tramite,
            folio_contacto=folio_contacto,
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
    def buscar_por_contacto(cls, folio_contacto):
        return cls.query.filter_by(folio_contacto=folio_contacto).first()

    @classmethod
    def cargar_todos(cls):
        """Compatibilidad con código existente: devuelve todas las encuestas ordenadas por fecha descendente"""
        return cls.query.order_by(cls.fecha.desc()).all()

    @classmethod
    def obtener_estadisticas(cls):
        from models.mensaje import Mensaje
        from models.usuario import Usuario
        from datetime import datetime

        encuestas = cls.cargar_todos()
        if not encuestas:
            return {
                'total': 0, 'promedio': 0.0, 'tasa_satisfaccion': 0,
                'con_comentarios': 0, 'distribucion': [
                    {'estrellas': i, 'cantidad': 0, 'porcentaje': 0} for i in range(5, 0, -1)
                ],
                'por_tipo': {}, 'ultimos_comentarios': [], 'todas': []
            }

        total = len(encuestas)
        suma = sum(e.calificacion for e in encuestas)
        promedio = float(suma) / float(total)

        # Distribución por estrellas
        por_calif = {i: 0 for i in range(1, 6)}
        for e in encuestas:
            if e.calificacion in por_calif:
                por_calif[e.calificacion] += 1

        distribucion = []
        for i in range(5, 0, -1):
            cantidad = por_calif[i]
            porcentaje = round((cantidad / total) * 100, 1) if total > 0 else 0
            distribucion.append({'estrellas': i, 'cantidad': cantidad, 'porcentaje': porcentaje})

        satisfechos = por_calif[4] + por_calif[5]
        tasa_satisfaccion = round((satisfechos / total) * 100, 1) if total > 0 else 0
        con_comentarios = len([e for e in encuestas if e.comentario and e.comentario.strip()])

        # Por tipo de trámite (incluye 'tramite' y 'contacto')
        tipos = {}
        for e in encuestas:
            t = e.tipo_tramite or 'otro'
            if t not in tipos:
                tipos[t] = {'total': 0, 'suma': 0}
            tipos[t]['total'] += 1
            tipos[t]['suma'] += e.calificacion

        por_tipo = {}
        for t, datos in tipos.items():
            prom = float(datos['suma']) / float(datos['total'])
            satisf = len([e for e in encuestas if e.tipo_tramite == t and e.calificacion >= 4])
            tasa = round((satisf / datos['total']) * 100, 1) if datos['total'] else 0
            por_tipo[t] = {'total': datos['total'], 'promedio': round(prom, 1), 'tasa_satisfaccion': tasa}

        # Últimos comentarios (hasta 10)
        con_com = [e for e in encuestas if e.comentario and e.comentario.strip()]
        ultimos = sorted(con_com, key=lambda x: x.fecha or datetime.min, reverse=True)[:10]
        ultimos_comentarios = [{
            'fecha': e.fecha.isoformat() if e.fecha else '',
            'usuario_nombre': e.usuario_nombre or 'Anónimo',
            'folio_tramite': e.folio_tramite,
            'folio_contacto': e.folio_contacto,
            'calificacion': e.calificacion,
            'comentario': e.comentario
        } for e in ultimos]

        # Construir lista completa con el administrador que respondió (si existe)
        todas = []
        for e in encuestas:
            folio = e.folio_tramite or e.folio_contacto
            admin_nombre = None
            admin_email = None

            if folio:
                tipo_msg = 'consulta' if e.tipo_tramite == 'contacto' else e.tipo_tramite
                resp_admin = Mensaje.query.filter_by(
                    tramite_folio=folio,
                    es_admin=True
                ).order_by(Mensaje.fecha_creacion.asc()).first()

                if resp_admin:
                    admin_email = resp_admin.autor_email
                    admin_nombre = resp_admin.autor_nombre
                    if not admin_nombre and admin_email:
                        u = Usuario.query.filter_by(email=admin_email).first()
                        admin_nombre = u.nombre_completo if u else admin_email

            todas.append({
                'id': e.id,
                'folio': folio,
                'tipo_tramite': e.tipo_tramite,
                'usuario_nombre': e.usuario_nombre or 'Anónimo',
                'usuario_email': e.usuario_email,
                'calificacion': e.calificacion,
                'comentario': e.comentario or '',
                'fecha': e.fecha.strftime('%d/%m/%Y %H:%M') if e.fecha else '',
                'admin_nombre': admin_nombre or 'Sin asignar',
                'admin_email': admin_email or '',
            })

        return {
            'total': total,
            'promedio': round(promedio, 2),
            'tasa_satisfaccion': tasa_satisfaccion,
            'con_comentarios': con_comentarios,
            'distribucion': distribucion,
            'por_tipo': por_tipo,
            'ultimos_comentarios': ultimos_comentarios,
            'todas': todas
        }

    def to_dict(self):
        return {
            'id': self.id,
            'folio_tramite': self.folio_tramite,
            'folio_contacto': self.folio_contacto,
            'tipo_tramite': self.tipo_tramite,
            'usuario_email': self.usuario_email,
            'usuario_nombre': self.usuario_nombre,
            'calificacion': self.calificacion,
            'comentario': self.comentario,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }