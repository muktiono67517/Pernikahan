import os

# Konfigurasi Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'ini_secret_key_default')

# config.py (atau di bagian atas app.py)

MYSQL_CONFIG = {
    'host': '127.0.0.1',      # atau 'localhost'
    'user': 'mukti',           # ganti dengan username MySQL-mu
    'password': 'pernikahan2028',  # ganti dengan password MySQL-mu
    'database': 'pernikahan' # ganti dengan nama database yang kamu pakai
}
