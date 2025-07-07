from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Inizializzazione dell'app Flask
app = Flask(__name__)

# Configurazione del database (file SQLite nella stessa cartella)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///air_quality.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Collegamento con SQLAlchemy
db = SQLAlchemy(app)

# Importa i modelli dal models.py
from models import User, AirQuality

# Rotta base di test
@app.route('/')
def home():
    return "Benvenuto al sistema di monitoraggio qualità dell'aria!"

def register_user(username, email, password):
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    print(f"Utente {username} registrato con successo.")

# Avvia il server Flask in modalità debug
if __name__ == '__main__':
    app.run(debug=True)
