# fix_db.py
from app import app
from extensions import db
from sqlalchemy import text

print("🔧 Reparando base de datos...")

with app.app_context():
    try:
        # Intentar agregar la columna fecha_nacimiento
        print("📌 Agregando columna fecha_nacimiento...")
        db.session.execute(text("""
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_nacimiento VARCHAR(50) DEFAULT NULL
        """))
        db.session.commit()
        print("✅ Columna 'fecha_nacimiento' agregada correctamente")
    except Exception as e:
        print(f"⚠️ Error al agregar fecha_nacimiento: {e}")
    
    try:
        # Intentar agregar la columna cedula si no existe
        print("📌 Verificando columna cedula...")
        db.session.execute(text("""
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS cedula VARCHAR(50) DEFAULT NULL
        """))
        db.session.commit()
        print("✅ Columna 'cedula' verificada")
    except Exception as e:
        print(f"⚠️ Error con cedula: {e}")
    
    try:
        # Intentar agregar la columna direccion si no existe
        print("📌 Verificando columna direccion...")
        db.session.execute(text("""
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS direccion TEXT DEFAULT NULL
        """))
        db.session.commit()
        print("✅ Columna 'direccion' verificada")
    except Exception as e:
        print(f"⚠️ Error con direccion: {e}")
    
    try:
        # Intentar agregar la columna notas_admin si no existe
        print("📌 Verificando columna notas_admin...")
        db.session.execute(text("""
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notas_admin TEXT DEFAULT NULL
        """))
        db.session.commit()
        print("✅ Columna 'notas_admin' verificada")
    except Exception as e:
        print(f"⚠️ Error con notas_admin: {e}")

    print("✅ Reparación completada")

# Verificar que las columnas existen
with app.app_context():
    result = db.session.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='usuarios'
    """))
    columnas = [row[0] for row in result]
    print("\n📋 Columnas actuales en tabla usuarios:")
    for col in sorted(columnas):
        print(f"   - {col}")