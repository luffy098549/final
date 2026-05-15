from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
if not DATABASE_URL:
    print("No DATABASE_URL")
    exit()

engine = create_engine(DATABASE_URL)

migraciones = [
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol_id INTEGER",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_perfil_url VARCHAR(500)",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_perfil_public_id VARCHAR(200)",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS google_id VARCHAR(100)",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_email BOOLEAN DEFAULT TRUE",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_whatsapp BOOLEAN DEFAULT FALSE",
    "CREATE TABLE IF NOT EXISTS reportes_guardados (id SERIAL PRIMARY KEY, nombre VARCHAR(200) NOT NULL, tipo_reporte VARCHAR(50) NOT NULL, fecha_generacion TIMESTAMP DEFAULT NOW(), generado_por VARCHAR(100) NOT NULL, total_registros INTEGER DEFAULT 0, datos_json TEXT NOT NULL, columnas_json TEXT, filtros_json TEXT, estilos_json TEXT)",
    "CREATE TABLE IF NOT EXISTS reportes_plantillas (id SERIAL PRIMARY KEY, nombre VARCHAR(200) NOT NULL, tipo_reporte VARCHAR(50) NOT NULL, filtros_json TEXT NOT NULL DEFAULT '{}', columnas_json TEXT NOT NULL DEFAULT '[]', created_by VARCHAR(120) NOT NULL, created_at TIMESTAMP DEFAULT NOW(), estilos_json TEXT)",
    "CREATE TABLE IF NOT EXISTS roles (id SERIAL PRIMARY KEY, nombre VARCHAR(50) NOT NULL UNIQUE, descripcion VARCHAR(200))",
    "CREATE TABLE IF NOT EXISTS permisos (id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL UNIQUE, descripcion VARCHAR(200), modulo VARCHAR(50))",
    "CREATE TABLE IF NOT EXISTS roles_permisos (id SERIAL PRIMARY KEY, rol_id INTEGER REFERENCES roles(id), permiso_id INTEGER REFERENCES permisos(id))",
]

with engine.connect() as conn:
    for sql in migraciones:
        try:
            conn.execute(text(sql))
            print(f"OK: {sql[:50]}...")
        except Exception as e:
            print(f"SKIP: {e}")
    conn.commit()
    print("Migracion completada")