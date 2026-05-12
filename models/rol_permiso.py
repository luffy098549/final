# ============================================================
# models/rol_permiso.py
# TABLA PIVOTE ROL-PERMISO
# ============================================================

from extensions import db
from datetime import datetime


class RolPermiso(db.Model):
    __tablename__ = 'roles_permisos'
    
    id = db.Column(db.Integer, primary_key=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permiso_id = db.Column(db.Integer, db.ForeignKey('permisos.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    rol = db.relationship('Rol', back_populates='permisos')
    permiso = db.relationship('Permiso', back_populates='roles')
    
    __table_args__ = (
        db.UniqueConstraint('rol_id', 'permiso_id', name='uq_rol_permiso'),
    )
    
    def __repr__(self):
        return f"<RolPermiso rol={self.rol_id} permiso={self.permiso_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'rol_id': self.rol_id,
            'permiso_id': self.permiso_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'rol_nombre': self.rol.nombre if self.rol else None,
            'permiso_codigo': self.permiso.codigo if self.permiso else None,
            'permiso_nombre': self.permiso.nombre if self.permiso else None,
        }