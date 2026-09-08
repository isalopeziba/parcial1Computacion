import os

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_consulate import Consul

app = Flask(__name__)
CORS(app)
app.config.from_object('config.Config')

# Ruta para renderizar el template index.html
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session['username'])


@app.route('/login', methods=['GET'])
def login_page():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Usuario y contraseña son obligatorios'}), 400

    try:
        response = requests.post(
            f"{app.config['USER_SERVICE_URL'].rstrip('/')}/api/login",
            json={'username': username, 'password': password},
            timeout=5
        )
    except requests.RequestException:
        return jsonify({'message': 'El servicio de usuarios no está disponible'}), 503

    if response.status_code != 200:
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

    user = response.json()['user']
    session['username'] = user['username']
    session['email'] = user['email']
    return jsonify({'message': 'Login correcto', 'redirect': url_for('index')}), 200


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada', 'redirect': url_for('login_page')}), 200

# Ruta para renderizar el template users.html
@app.route('/users')
def users():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('users.html')

@app.route('/editUser/<string:id>')
def edit_user(id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    print("id recibido",id)
    return render_template('editUser.html', id=id)

# Ruta para renderizar el template producto.html
@app.route('/products')
def products():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('products.html')

@app.route('/orders')
def orders():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('orders.html')

@app.route('/editProduct/<string:id>')
def edit_product(id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    print("id recibido",id)
    return render_template('editProducts.html', id=id)


@app.route('/healthcheck')
def health_check():
    return '', 200


os.environ.setdefault('CONSUL_HOST', 'consul')
os.environ.setdefault('CONSUL_PORT', '8500')

consul = Consul(app=app)
consul.register_service(
    name='frontend',
    interval='10s',
    tags=['frontend'],
    port=5001,
    httpcheck='http://frontend:5001/healthcheck'
)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
