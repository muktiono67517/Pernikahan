import os

# Konfigurasi Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'ini_secret_key_default')

# config.py (atau di bagian atas app.py)

MYSQL_CONFIG = {
    'host': '127.0.0.1',      # atau 'localhost'
    'port': 3306,             # port default MySQL
    'user': 'root',           # ganti dengan username MySQL-mu
    'password': '',  # ganti dengan password MySQL-mu
    'database': 'pernikahan' # ganti dengan nama database yang kamu pakai
}
