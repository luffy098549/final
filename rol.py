"""
Modelo para gestión de roles y permisos
"""
class Permiso:
    VER_SOLICITUDES = "ver_solicitudes"
    EDITAR_SOLICITUDES = "editar_solicitudes" 
    ELIMINAR_SOLICITUDES = "eliminar_solicitudes"
    VER_DENUNCIAS = "ver_denuncias"
    EDITAR_DENUNCIAS = "editar_denuncias"
    ELIMINAR_DENUNCIAS = "eliminar_denuncias"
    VER_USUARIOS = "ver_usuarios"
    EDITAR_USUARIOS = "editar_usuarios"
    CREAR_ADMINS = "crear_admins"
    VER_CONFIG = "ver_configuracion"
    EDITAR_CONFIG = "editar_configuracion"
    VER_BITACORA = "ver_bitacora"
    EXPORTAR_DATOS = "exportar_datos"
    MANTENIMIENTO = "modo_mantenimiento"
    COMENTAR = "comentar"
    ASIGNAR = "asignar"

PERMISOS_POR_ROL = {
    "super_admin": [
        Permiso.VER_SOLICITUDES, Permiso.EDITAR_SOLICITUDES, Permiso.ELIMINAR_SOLICITUDES,
        Permiso.VER_DENUNCIAS, Permiso.EDITAR_DENUNCIAS, Permiso.ELIMINAR_DENUNCIAS,
        Permiso.VER_USUARIOS, Permiso.EDITAR_USUARIOS, Permiso.CREAR_ADMINS,
        Permiso.VER_CONFIG, Permiso.EDITAR_CONFIG, Permiso.VER_BITACORA,
        Permiso.EXPORTAR_DATOS, Permiso.MANTENIMIENTO, Permiso.COMENTAR, Permiso.ASIGNAR
    ],
    "admin": [
        Permiso.VER_SOLICITUDES, Permiso.EDITAR_SOLICITUDES,
        Permiso.VER_DENUNCIAS, Permiso.EDITAR_DENUNCIAS,
        Permiso.VER_USUARIOS, Permiso.EDITAR_USUARIOS,
        Permiso.VER_CONFIG, Permiso.VER_BITACORA,
        Permiso.EXPORTAR_DATOS, Permiso.COMENTAR, Permiso.ASIGNAR
    ],
    "moderador": [
        Permiso.VER_SOLICITUDES, Permiso.VER_DENUNCIAS,
        Permiso.VER_USUARIOS, Permiso.COMENTAR
    ]
}

def tiene_permiso(usuario_rol, permiso):
    if not usuario_rol or usuario_rol not in PERMISOS_POR_ROL:
        return False
    return permiso in PERMISOS_POR_ROL[usuario_rol]

def obtener_roles():
    return [
        {"id": "super_admin", "nombre": "Super Administrador"},
        {"id": "admin", "nombre": "Administrador"},
        {"id": "moderador", "nombre": "Moderador"}
    ]