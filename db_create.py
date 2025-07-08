from app import app
from database import db
from models import User, AirQuality

with app.app_context():
    db.create_all()
    print("Database creato con successo.")