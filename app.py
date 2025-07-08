from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

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

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout eseguito con successo'})

if __name__ == '__main__':
    app.run(debug=True)