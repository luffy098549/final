from app import app, db
with app.app_context():
    db.session.commit()
    print('Listo')
