from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from datetime import datetime, timedelta
import requests, csv, io

app = Flask(__name__)
app.secret_key = 'chiave-segreta-sicura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema_monitoraggio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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

def fetch_and_store_data(station_id, start_date_str, end_date_str):
    pollutant_ids = {
        "pm10": "3",
        "pm2_5": "7",
        "no2": "4",
        "o3": "5"
    }

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    current_date = start_date
    while current_date <= end_date:
        data_str = current_date.strftime("%Y-%m-%d")
        valori = {}
        city = None

        for name, pollutant_id in pollutant_ids.items():
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
                    valore = row["valore_inquinante_misurato"]
                    if valore and valore.lower() != "null":
                        valori[name] = float(valore)
                        if not city:
                            city = row["comune"]
            except Exception:
                continue

        if valori and city:
            timestamp = datetime.strptime(data_str, "%Y-%m-%d")
            existing = AirQuality.query.filter_by(city=city, timestamp=timestamp).first()
            if not existing:
                record = AirQuality(
                    city=city,
                    timestamp=timestamp,
                    pm10=valori.get("pm10"),
                    pm2_5=valori.get("pm2_5"),
                    o3=valori.get("o3"),
                    no2=valori.get("no2")
                )
                db.session.add(record)
                db.session.commit()

        current_date += timedelta(days=1)

@app.route('/register', methods=['POST'])
def register():
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

@app.route('/login', methods=['POST'])
def login():
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
    
@app.route('/profilo')
def profilo():
    if 'user_id' not in session:
        return jsonify({'error': 'Accesso non autorizzato'}), 401

    user = User.query.get(session['user_id'])
    return jsonify({
        'username': user.username,
        'email': user.email
    })

@app.route('/import_csv')
def importa_csv():
    station_id = request.args.get('station')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if not station_id or not start_date or not end_date:
        return jsonify({"error": "Parametri mancanti"}), 400

    fetch_and_store_data(station_id, start_date, end_date)
    return jsonify({"message": "Importazione completata"}), 200

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout eseguito con successo'})

if __name__ == '__main__':
    app.run(debug=True)