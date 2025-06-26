
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
