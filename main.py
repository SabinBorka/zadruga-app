
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kooperanti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naziv TEXT UNIQUE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS odvage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datum TEXT, tip TEXT, kooperant_id INTEGER,
        roba TEXT, vozilo TEXT, vozac TEXT,
        bruto REAL, tara REAL, neto REAL, napomena TEXT,
        FOREIGN KEY(kooperant_id) REFERENCES kooperanti(id)
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect('/odvage')

@app.route('/kooperanti', methods=['GET', 'POST'])
def kooperanti():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        naziv = request.form['naziv']
        c.execute("INSERT OR IGNORE INTO kooperanti(naziv) VALUES (?)", (naziv,))
        conn.commit()
    c.execute("SELECT * FROM kooperanti ORDER BY naziv")
    data = c.fetchall()
    conn.close()
    return render_template('kooperanti.html', kooperanti=data)

@app.route('/odvage')
def odvage():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT odvage.id, datum, tip, k.naziv, roba, bruto, tara, neto, vozilo, vozac
        FROM odvage LEFT JOIN kooperanti k ON odvage.kooperant_id=k.id
        ORDER BY datum DESC
    ''')
    data = c.fetchall()
    conn.close()
    return render_template('index_odvage.html', odvage=data)

@app.route('/odvage/add', methods=['GET', 'POST'])
def add_odvaga():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, naziv FROM kooperanti")
    koops = c.fetchall()
    if request.method == 'POST':
        d = request.form
        bruto, tara = float(d['bruto']), float(d['tara'])
        neto = bruto - tara
        c.execute('''INSERT INTO odvage(datum, tip, kooperant_id, roba, vozilo, vozac, bruto, tara, neto, napomena)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (d['datum'], d['tip'], d['kooperant'], d['roba'], d['vozilo'], d['vozac'], bruto, tara, neto, d['napomena']))
        conn.commit()
        conn.close()
        return redirect('/odvage')
    conn.close()
    return render_template('add_odvaga.html', koops=koops)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=3000, debug=True)


@app.route('/zaduzenja')
def zaduzenja():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS zaduzenja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kooperant_id INTEGER,
        roba TEXT,
        kolicina REAL,
        datum TEXT,
        FOREIGN KEY(kooperant_id) REFERENCES kooperanti(id)
    )''')
    c.execute('''SELECT z.id, k.naziv, z.roba, z.kolicina, z.datum
                 FROM zaduzenja z LEFT JOIN kooperanti k ON z.kooperant_id = k.id
                 ORDER BY z.datum DESC''')
    data = c.fetchall()
    conn.close()
    return render_template('zaduzenja.html', zaduzenja=data)

@app.route('/zaduzenja/add', methods=['GET', 'POST'])
def add_zaduzenje():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, naziv FROM kooperanti")
    koops = c.fetchall()
    if request.method == 'POST':
        d = request.form
        c.execute('''INSERT INTO zaduzenja (kooperant_id, roba, kolicina, datum)
                     VALUES (?, ?, ?, ?)''',
                  (d['kooperant'], d['roba'], float(d['kolicina']), d['datum']))
        conn.commit()
        conn.close()
        return redirect('/zaduzenja')
    conn.close()
    return render_template('add_zaduzenje.html', koops=koops)


@app.route('/lager')
def lager():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, naziv FROM kooperanti")
    koops = c.fetchall()
    c.execute("SELECT DISTINCT roba FROM odvage")
    robe = [r[0] for r in c.fetchall()]
    lager_data = []
    for k_id, k_name in koops:
        for r in robe:
            c.execute("SELECT SUM(neto) FROM odvage WHERE tip='Ulaz' AND kooperant_id=? AND roba=?", (k_id, r))
            ulaz = c.fetchone()[0] or 0
            c.execute("SELECT SUM(neto) FROM odvage WHERE tip='Izlaz' AND kooperant_id=? AND roba=?", (k_id, r))
            izlaz = c.fetchone()[0] or 0
            c.execute("SELECT SUM(kolicina) FROM zaduzenja WHERE kooperant_id=? AND roba=?", (k_id, r))
            zaduzenje = c.fetchone()[0] or 0
            stanje = ulaz - izlaz - zaduzenje
            if ulaz or izlaz or zaduzenje:
                lager_data.append((k_name, r, ulaz, izlaz, zaduzenje, stanje))
    conn.close()
    return render_template('lager.html', lager=lager_data)

@app.route('/kartica/<int:kooperant_id>')
def kartica(kooperant_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT naziv FROM kooperanti WHERE id=?", (kooperant_id,))
    kooperant = c.fetchone()[0]
    redovi = []

    c.execute("SELECT datum, 'Ulaz', roba, neto FROM odvage WHERE tip='Ulaz' AND kooperant_id=?", (kooperant_id,))
    redovi += c.fetchall()
    c.execute("SELECT datum, 'Izlaz', roba, neto FROM odvage WHERE tip='Izlaz' AND kooperant_id=?", (kooperant_id,))
    redovi += c.fetchall()
    c.execute("SELECT datum, 'Zaduženje', roba, kolicina FROM zaduzenja WHERE kooperant_id=?", (kooperant_id,))
    redovi += c.fetchall()

    redovi.sort(key=lambda x: x[0])  # Sort by datum
    conn.close()
    return render_template('kartica.html', redovi=redovi, kooperant=kooperant)


from flask import session, url_for

app.secret_key = 'tajna_lozinka_zadruga123'

# Login dummy user data
users = {'admin': 'admin123', 'magacioner': 'mag123'}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u in users and users[u] == p:
            session['user'] = u
            return redirect('/')
        return "Neispravni podaci"
    return render_template('login.html')

@app.before_request
def require_login():
    allowed = ['login', 'static']
    if 'user' not in session and not any(x in request.path for x in allowed):
        return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/izvestaji')
def izvestaji():
    return render_template('izvestaji.html')


import pandas as pd
from flask import send_file
import io

@app.route('/export/odvage.xlsx')
def export_odvage():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query('''
        SELECT datum, tip, (SELECT naziv FROM kooperanti WHERE id = kooperant_id) AS kooperant,
               roba, vozilo, vozac, bruto, tara, neto, napomena
        FROM odvage
    ''', conn)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Odvage')
    output.seek(0)
    return send_file(output, download_name='odvage.xlsx', as_attachment=True)


@app.route('/srps', methods=['GET', 'POST'])
def srps():
    if request.method == 'POST':
        # Ovde bi se snimali parametri u bazu
        return "SRPS norme sačuvane (demo)"
    return render_template('srps.html')
