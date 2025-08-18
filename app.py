from flask import Flask, render_template, session, request, redirect, url_for
import mysql.connector
from datetime import datetime
from config import MYSQL_CONFIG

app = Flask(__name__)
app.secret_key = 'Ini-Rahasia-Dan-Wajib-Tidak-Dibocorkan'


# ==================== ADMIN PANEL ====================

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM kode_presensi ORDER BY id ASC")
    data = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM kode_presensi")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS hadir FROM kode_presensi WHERE sudah_dipakai = TRUE")
    hadir = cursor.fetchone()['hadir']

    cursor.execute("SELECT COUNT(DISTINCT dipakai_oleh) AS unik FROM kode_presensi WHERE dipakai_oleh IS NOT NULL")
    unik_pengguna = cursor.fetchone()['unik']

    cursor.execute("SELECT MAX(waktu) AS terakhir FROM kode_presensi WHERE waktu IS NOT NULL")
    waktu_terakhir = cursor.fetchone()['terakhir']

    cursor.execute("""
        SELECT HOUR(waktu) AS jam, COUNT(*) AS jumlah
        FROM kode_presensi
        WHERE waktu IS NOT NULL
        GROUP BY HOUR(waktu)
        ORDER BY jam
    """)
    per_jam = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        data=data,
        total=total,
        hadir=hadir,
        unik_pengguna=unik_pengguna,
        waktu_terakhir=waktu_terakhir,
        per_jam=per_jam
    )


@app.route('/admin/add', methods=['POST'])
def admin_add():
    kode = request.form.get('kode')
    if kode:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kode_presensi (kode) VALUES (%s)", (kode,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit(id):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        kode = request.form.get('kode')
        sudah = request.form.get('sudah_dipakai') == 'on'
        dipakai = request.form.get('dipakai_oleh') or None
        waktu = request.form.get('waktu') or None

        cursor.execute("""
            UPDATE kode_presensi
            SET kode = %s, sudah_dipakai = %s, dipakai_oleh = %s, waktu = %s
            WHERE id = %s
        """, (kode, sudah, dipakai, waktu, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM kode_presensi WHERE id = %s", (id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('admin_edit.html', data=data)


@app.route('/admin/delete/<int:id>')
def admin_delete(id):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kode_presensi WHERE id = %s", (id,))
    cursor.execute("ALTER TABLE kode_presensi AUTO_INCREMENT = 1")
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# ==================== ADMIN PANEL CLOSE ====================


# ==================== HALAMAN LOGIN ====================

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Admin login (hardcoded)
        if username == 'mukti' and password == 'mukti12345':
            session['username'] = 'mukti'
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))

        # User login via DB
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')
                return redirect(url_for('wedding_feed'))
            else:
                message = "Username atau password salah."
        except Exception as e:
            message = "Gagal koneksi database."

    return render_template('login.html', message=message)


# ==================== PRESENSI TAMU ====================

@app.route('/presensi', methods=['POST'])
def presensi():
    if 'username' not in session:
        return "Unauthorized", 401

    message = ''
    message_type = ''
    username = session['username']
    kode_input = request.form.get('kode', '').strip()

    if not kode_input:
        message = "Masukkan kode presensi."
        message_type = 'error'
    else:
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(dictionary=True, buffered=True)

            cursor.execute("SELECT * FROM kode_presensi WHERE dipakai_oleh = %s", (username,))
            sudah_presensi = cursor.fetchone()

            if sudah_presensi:
                message = f"Hai {username}, Anda sudah presensi dengan kode {sudah_presensi['kode']} 🙏"
                message_type = 'warning'
            else:
                cursor.execute("SELECT * FROM kode_presensi WHERE kode = %s", (kode_input,))
                kode = cursor.fetchone()

                if not kode:
                    message = "Kode tidak ditemukan."
                    message_type = 'error'
                elif kode['sudah_dipakai']:
                    message = f"Kode {kode['kode']} sudah digunakan oleh {kode['dipakai_oleh']} 🙏"
                    message_type = 'warning'
                else:
                    cursor.execute("""
                        UPDATE kode_presensi 
                        SET sudah_dipakai = TRUE, dipakai_oleh = %s, waktu = %s 
                        WHERE id = %s
                    """, (username, datetime.now(), kode['id']))
                    conn.commit()
                    message = f"Presensi berhasil 🎉 Kode {kode_input} tercatat untuk {username}."
                    message_type = 'success'

            cursor.close()
            conn.close()
        except Exception as e:
            message = f"Kesalahan sistem: {e}"
            message_type = 'error'

    return render_template('presensi.html', message=message, message_type=message_type)



# ==================== WEDDING FEED ====================

@app.route('/wedding-feed')
def wedding_feed():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('base.html', username=session['username'])


# ==================== LOGOUT ====================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==================== RUN APP ====================

if __name__ == '__main__':
    app.run(debug=True)
