import os
from urllib.parse import quote_plus

class Config:
   MYSQL_HOST = os.getenv('MYSQL_HOST', 'orders_db')
   MYSQL_USER = os.getenv('MYSQL_USER')
   MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
   MYSQL_DB = os.getenv('MYSQL_DATABASE', 'orders_db')
   SQLALCHEMY_DATABASE_URI = (
       f'mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD or "")}@{MYSQL_HOST}/{MYSQL_DB}'
   )
   SQLALCHEMY_TRACK_MODIFICATIONS = False
   SECRET_KEY = os.getenv('SESSION_SECRET')
  