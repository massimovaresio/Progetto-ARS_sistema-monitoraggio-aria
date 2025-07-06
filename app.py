from flask import Flask
from flask_sqlalchemy import SQLAlchemy

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

# Avvia il server Flask in modalità debug
if __name__ == '__main__':
    app.run(debug=True)
