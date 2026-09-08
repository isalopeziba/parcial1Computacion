import os
from flask import Flask, render_template
from users.controllers.user_controller import user_controller
from db.db import db
from flask_cors import CORS
from flask_consulate import Consul

app = Flask(__name__)
CORS(app)
app.config.from_object('config.Config')
db.init_app(app)

# Registrando el blueprint del controlador de usuarios
app.register_blueprint(user_controller)

# Health check
@app.route('/healthcheck')
def health_check():
    return '', 200

os.environ.setdefault('CONSUL_HOST', os.getenv('CONSUL_HOST', 'consul'))
os.environ.setdefault('CONSUL_PORT', os.getenv('CONSUL_PORT', '8500'))

consul = Consul(app=app)

consul.register_service(
    name='users',
    interval='10s',
    tags=['microservice', 'users'],
    port=5002,
    httpcheck='http://users:5002/healthcheck'
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)