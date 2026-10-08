import os
import base64
from flask import Flask, render_template, request, redirect, url_for, session
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = 'clave_secreta_sesion_enamorandome_de_ti'

PASSWORD_SECRETA = "MoraHorn0209"

# FUNCIÓN PARA ENVIAR SMS CON TWILIO
def send_sms_notification(memory_title, memory_date):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
    target_numbers = os.environ.get('TARGET_PHONE_NUMBER')

    print(f"DEBUG: Intentando enviar SMS. SID: {'Configurado' if account_sid else 'Falta'}, Destino: {target_numbers}")

    if not all([account_sid, auth_token, twilio_number, target_numbers]):
        print("ERROR: Variables de Twilio no configuradas en Environment de Render.")
        return

    try:
        client = Client(account_sid, auth_token)
        mensaje_texto = (
            f"❤️ ¡Nuevo recuerdo añadido a nuestra historia!\n"
            f"✨ {memory_title} ({memory_date})\n"
            f"Entra a revivirlo: https://enamorandome-de-ti.onrender.com"
        )
        
        # Soporta uno o varios números separados por coma
        numeros = [n.strip() for n in target_numbers.split(',') if n.strip()]
        for num in numeros:
            msg = client.messages.create(
                body=mensaje_texto,
                from_=twilio_number,
                to=num
            )
            print(f"ÉXITO: SMS enviado a {num} con ID: {msg.sid}")
    except Exception as e:
        print(f"ERROR al enviar SMS con Twilio: {e}")

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        import psycopg
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return psycopg.connect(db_url)
    import sqlite3
    return sqlite3.connect('timeline.db')

def init_db():
    db_url = os.environ.get('DATABASE_URL')
    conn = get_db_connection()
    cursor = conn.cursor()
    if db_url:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                date_event TEXT NOT NULL,
                story TEXT,
                photo_data TEXT
            );
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_event TEXT NOT NULL,
                story TEXT,
                photo_data TEXT
            );
        ''')
    conn.commit()
    cursor.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"Error inicializando DB: {e}")

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html', logged_in=False)
    
    conn = get_db_connection()
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

    db_url = os.environ.get('DATABASE_URL')
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = '%s' if db_url else '?'
    query = f'INSERT INTO memories (title, date_event, story, photo_data) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})'
    cursor.execute(query, (title, date_event, story, photo_b64))
    conn.commit()
    cursor.close()
    conn.close()

    # Enviar notificación automática por SMS
    send_sms_notification(title, date_event)

    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    title = request.form.get('title')
    date_event = request.form.get('date_event')
    story = request.form.get('story')
    photo = request.files.get('photo')

    db_url = os.environ.get('DATABASE_URL')
    conn = get_db_connection()
    cursor = conn.cursor()
    p = '%s' if db_url else '?'

    if photo and photo.filename != '':
        data = photo.read()
        mime = photo.mimetype or 'image/jpeg'
        photo_b64 = f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"
        query = f'UPDATE memories SET title = {p}, date_event = {p}, story = {p}, photo_data = {p} WHERE id = {p}'
        cursor.execute(query, (title, date_event, story, photo_b64, id))
    else:
        query = f'UPDATE memories SET title = {p}, date_event = {p}, story = {p} WHERE id = {p}'
        cursor.execute(query, (title, date_event, story, id))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    db_url = os.environ.get('DATABASE_URL')
    conn = get_db_connection()
    cursor = conn.cursor()
    p = '%s' if db_url else '?'
    cursor.execute(f'DELETE FROM memories WHERE id = {p}', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
