import os


class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SECRET_KEY = os.getenv('SESSION_SECRET')
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://users:5002')
