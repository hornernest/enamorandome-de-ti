import os
import sqlite3
import base64
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'clave_secreta_sesion_enamorandome_de_ti'

PASSWORD_SECRETA = "MoraHorn0209"
DB_NAME = 'timeline.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_event TEXT NOT NULL,
                story TEXT,
                photo_data TEXT
            )
        ''')

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html', logged_in=False)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT title, date_event, story, photo_data FROM memories ORDER BY date_event ASC')
        rows = cursor.fetchall()

    memories = [
        {"title": r[0], "date": r[1], "story": r[2], "photo": r[3]}
        for r in rows
    ]
    return render_template('index.html', logged_in=True, memories=memories)

@app.route('/login', methods=['POST'])
def login():
    entered_password = request.form.get('password')
    if entered_password == PASSWORD_SECRETA:
        session['logged_in'] = True
        return redirect(url_for('index'))
    return render_template('index.html', logged_in=False, error="Contraseña incorrecta, amor ❤️")

@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    title = request.form.get('title')
    date_event = request.form.get('date_event')
    story = request.form.get('story')
    photo = request.files.get('photo')

    photo_b64 = None
    if photo and photo.filename != '':
        # Guardamos la foto directo en la base de datos como base64
        # para que nunca se borre aunque se reinicie el servidor
        data = photo.read()
        mime = photo.mimetype or 'image/jpeg'
        photo_b64 = f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    with get_db() as conn:
        conn.execute(
            'INSERT INTO memories (title, date_event, story, photo_data) VALUES (?, ?, ?, ?)',
            (title, date_event, story, photo_b64)
        )
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
