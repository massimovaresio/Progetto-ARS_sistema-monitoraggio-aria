from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from datetime import datetime, timedelta
import requests, csv, io, json

app = Flask(__name__)
app.secret_key = 'chiave-segreta-sicura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema_monitoraggio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Carica la mappa comune → lista di id_station
with open("station_map.json", "r", encoding="utf-8") as f:
    station_map = json.load(f)

from models import User, AirQuality

@app.route('/')
def home():
    return "Benvenuto al sistema di monitoraggio qualità dell'aria!"

def register_user(username, email, password):
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    print(f"Utente {username} registrato con successo.")

def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None

def fetch_and_store_data(comune, start_date_str, end_date_str):
    from statistics import mean

    pollutant_ids = {
        "pm10": "3",
        "pm2_5": "7",
        "no2": "4",
        "o3": "5"
    }

    station_ids = station_map.get(comune)
    if not station_ids:
        print(f"Nessuna stazione trovata per il comune '{comune}'")
        return

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    current_date = start_date

    while current_date <= end_date:
        data_str = current_date.strftime("%Y-%m-%d")
        aggregated = {}

        for inquinante, pollutant_id in pollutant_ids.items():
            valori = []

            for station_id in station_ids:
                url = (
                    f"https://dati.arpa.puglia.it/api/v1/measurements?"
                    f"format=CSV&measurement_date={data_str}"
                    f"&id_station={station_id}&id_pollutant={pollutant_id}"
                )

                try:
                    resp = requests.get(url)
                    resp.raise_for_status()
                    csv_file = io.StringIO(resp.text)
                    reader = csv.DictReader(csv_file)
                    row = next(reader, None)
                    if row:
                        val = row["valore_inquinante_misurato"]
                        if val and val.lower() != "null":
                            valori.append(float(val))
                except Exception:
                    continue

            if valori:
                aggregated[inquinante] = mean(valori)

        if aggregated:
            existing = AirQuality.query.filter_by(city=comune, timestamp=current_date).first()
            if not existing:
                record = AirQuality(
                    city=comune,
                    timestamp=current_date,
                    pm10=aggregated.get("pm10"),
                    pm2_5=aggregated.get("pm2_5"),
                    o3=aggregated.get("o3"),
                    no2=aggregated.get("no2")
                )
                db.session.add(record)
                db.session.commit()

        current_date += timedelta(days=1)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'error': 'Dati mancanti'}), 400

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({'error': 'Utente già registrato'}), 409

        register_user(username, email, password)
        return jsonify({'message': f'Utente {username} registrato con successo'}), 201

    # Con metodo GET, restituisce la pagina HTML
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Credenziali mancanti'}), 400

        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user.id
            return jsonify({'message': f'Benvenuto {user.username}'}), 200
        else:
            return jsonify({'error': 'Username o password errati'}), 401

    # Con metodo GET, restituisce la pagina HTML
    return render_template('login.html')
    
@app.route('/profilo')
def profilo():
    if 'user_id' not in session:
        return jsonify({'error': 'Accesso non autorizzato'}), 401

    user = User.query.get(session['user_id'])
    return jsonify({
        'username': user.username,
        'email': user.email
    })

@app.route('/import_data')
def importa_dati():
    comune = request.args.get('comune')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if not comune or not start_date or not end_date:
        return jsonify({"error": "Parametri mancanti"}), 400

    fetch_and_store_data(comune, start_date, end_date)
    return jsonify({"message": f"Dati per {comune} importati con successo"}), 200

@app.route('/dashboard')
def dashboard():
    comuni = sorted(station_map.keys())  # estrai elenco dei comuni dal JSON
    return render_template('dashboard.html', comuni=comuni)

@app.route('/dati_comune')
def dati_comune():
    comune = request.args.get('comune')
    start = request.args.get('start')
    end = request.args.get('end')

    if not comune or not start or not end:
        return jsonify({"error": "Parametri mancanti"}), 400

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    dati = AirQuality.query.filter(
        AirQuality.city == comune,
        AirQuality.timestamp >= start_date,
        AirQuality.timestamp <= end_date
    ).order_by(AirQuality.timestamp).all()

    risultato = []
    for r in dati:
        risultato.append({
            "data": r.timestamp.strftime("%Y-%m-%d"),
            "pm10": r.pm10,
            "pm2_5": r.pm2_5,
            "o3": r.o3,
            "no2": r.no2
        })

    return jsonify(risultato)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout eseguito con successo'})

if __name__ == '__main__':
    app.run(debug=True)