from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

app = Flask(__name__)
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
        return jsonify({'message': f'Benvenuto {user.username}'}), 200
    else:
        return jsonify({'error': 'Username o password errati'}), 401

if __name__ == '__main__':
    app.run(debug=True)