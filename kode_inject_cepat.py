import random
import string
import mysql.connector
from config import MYSQL_CONFIG

karakter = string.ascii_uppercase + string.digits
jumlah_kode = 100
prefixes = ['SH','MN', ]

def generate_kode(length=6):
    prefix = random.choice(prefixes)
    kode_acak = ''.join(random.choices(karakter, k=length))
    return f"{prefix}-{kode_acak}"

try:
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    hasil_kode = []
    existing_kode = set()

    # Ambil semua kode yang sudah ada dari DB
    cursor.execute("SELECT kode FROM kode_presensi")
    for row in cursor.fetchall():
        existing_kode.add(row[0])

    while len(hasil_kode) < jumlah_kode:
        kode = generate_kode()
        if kode in existing_kode:
            continue  # Skip duplikat

        try:
            cursor.execute("INSERT INTO kode_presensi (kode) VALUES (%s)", (kode,))
            hasil_kode.append(kode)
            existing_kode.add(kode)
        except mysql.connector.IntegrityError:
            continue  # Skip jika tetap terjadi duplikat karena race condition

    conn.commit()
    cursor.close()
    conn.close()

    print(f"{jumlah_kode} kode unik berhasil dimasukkan ke database.")
    print("Daftar kode:")
    for kode in hasil_kode:
        print(kode)

except Exception as e:
    print("Gagal:", e)
