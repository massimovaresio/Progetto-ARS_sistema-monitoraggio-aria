from app import app, db

# Serve per dire a Flask: "usa questa app"
with app.app_context():
    db.create_all()

print("Database creato con successo.")