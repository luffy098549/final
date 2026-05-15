# init_render.py
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.rol import Rol
from models.permiso import Permiso
from models.rol_permiso import RolPermiso
from models.usuario import Usuario

def init_production():
    with app.app_context():
        print("🔄 Inicializando sistema de roles y permisos...")
        
        # Crear tablas si no existen
        db.create_all()
        
        # Crear roles
        Rol.crear_roles_defecto()
        print("✅ Roles creados")
        
        # Crear permisos
        Permiso.crear_permisos_defecto()
        print("✅ Permisos creados")
        
        # Obtener referencias
        roles = {r.nombre: r for r in Rol.query.all()}
        permisos = {p.codigo: p for p in Permiso.query.all()}
        
        # Asignar permisos a Super Admin
        if 'super_admin' in roles:
            for permiso in permisos.values():
                existe = RolPermiso.query.filter_by(
                    rol_id=roles['super_admin'].id,
                    permiso_id=permiso.id
                ).first()
                if not existe:
                    db.session.add(RolPermiso(rol_id=roles['super_admin'].id, permiso_id=permiso.id))
            print("✅ Permisos asignados a Super Admin")
        
        # Asignar permisos a Admin
        if 'admin' in roles:
            admin_permisos = [
                'ver_usuarios', 'editar_usuarios', 'crear_usuarios',
                'ver_solicitudes', 'editar_solicitudes', 'eliminar_solicitudes',
                'ver_denuncias', 'editar_denuncias', 'eliminar_denuncias',
                'editar_contenido', 'editar_menu', 'editar_transparencia',
                'crear_noticias', 'editar_noticias', 'eliminar_noticias', 'moderar_comentarios',
                'ver_configuracion', 'exportar_datos'
            ]
            for codigo in admin_permisos:
                if codigo in permisos:
                    existe = RolPermiso.query.filter_by(
                        rol_id=roles['admin'].id,
                        permiso_id=permisos[codigo].id
                    ).first()
                    if not existe:
                        db.session.add(RolPermiso(rol_id=roles['admin'].id, permiso_id=permisos[codigo].id))
            print("✅ Permisos asignados a Admin")
        
        # Asignar permisos a Moderador
        if 'moderador' in roles:
            mod_permisos = [
                'ver_solicitudes', 'ver_denuncias', 'moderar_comentarios',
                'editar_contenido', 'ver_configuracion'
            ]
            for codigo in mod_permisos:
                if codigo in permisos:
                    existe = RolPermiso.query.filter_by(
                        rol_id=roles['moderador'].id,
                        permiso_id=permisos[codigo].id
                    ).first()
                    if not existe:
                        db.session.add(RolPermiso(rol_id=roles['moderador'].id, permiso_id=permisos[codigo].id))
            print("✅ Permisos asignados a Moderador")
        
        db.session.commit()
        
        # Migrar usuarios existentes
        usuarios_migrados = 0
        for usuario in Usuario.query.all():
            if usuario.rol and not usuario.rol_id:
                rol_obj = Rol.query.filter_by(nombre=usuario.rol).first()
                if rol_obj:
                    usuario.rol_id = rol_obj.id
                    usuarios_migrados += 1
        
        db.session.commit()
        
        print(f"\n📊 VERIFICACIÓN FINAL:")
        print(f"   Roles: {Rol.query.count()}")
        print(f"   Permisos: {Permiso.query.count()}")
        print(f"   Relaciones: {RolPermiso.query.count()}")
        print(f"   Usuarios migrados: {usuarios_migrados}")
        print("\n✅ ¡Inicialización completada!")

if __name__ == "__main__":
    init_production()