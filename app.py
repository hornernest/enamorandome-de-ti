import os
import psycopg2
import base64
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'clave_secreta_sesion_enamorandome_de_ti'

PASSWORD_SECRETA = "MoraHorn0209"

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return psycopg2.connect(db_url)
    import sqlite3
    return sqlite3.connect('timeline.db')

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            date_event TEXT NOT NULL,
            story TEXT,
            photo_data TEXT
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html', logged_in=False)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, date_event, story, photo_data FROM memories ORDER BY date_event ASC')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    memories = [
        {"id": r[0], "title": r[1], "date": r[2], "story": r[3], "photo": r[4]}
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
        data = photo.read()
        mime = photo.mimetype or 'image/jpeg'
        photo_b64 = f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO memories (title, date_event, story, photo_data) VALUES (%s, %s, %s, %s)',
        (title, date_event, story, photo_b64)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    title = request.form.get('title')
    date_event = request.form.get('date_event')
    story = request.form.get('story')
    photo = request.files.get('photo')

    conn = get_db()
    cursor = conn.cursor()

    if photo and photo.filename != '':
        data = photo.read()
        mime = photo.mimetype or 'image/jpeg'
        photo_b64 = f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"
        cursor.execute(
            'UPDATE memories SET title = %s, date_event = %s, story = %s, photo_data = %s WHERE id = %s',
            (title, date_event, story, photo_b64, id)
        )
    else:
        cursor.execute(
            'UPDATE memories SET title = %s, date_event = %s, story = %s WHERE id = %s',
            (title, date_event, story, id)
        )

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM memories WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
