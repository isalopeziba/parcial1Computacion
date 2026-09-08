import os
from flask import Flask
from products.controllers.product_controller import product_controller
from db.db import db
from flask_cors import CORS
from flask_consulate import Consul

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://192.168.100.3:5001"])
app.config.from_object('config.Config')
db.init_app(app)

app.register_blueprint(product_controller)

# Health check
@app.route('/healthcheck')
def health_check():
    return '', 200

# Configuración de Consul para Docker
os.environ.setdefault('CONSUL_HOST', os.getenv('CONSUL_HOST', 'consul'))
os.environ.setdefault('CONSUL_PORT', os.getenv('CONSUL_PORT', '8500'))

# Inicializar la extensión
consul = Consul(app=app)
consul.register_service(
    name='products',
    interval='10s',
    address='products', 
    tags=['microservice', 'products'],
    port=5003,
    httpcheck='http://products:5003/healthcheck'
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)