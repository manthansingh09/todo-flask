from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong key in production

# Initialize the database and create tables if they don't exist
def init_db():
    with sqlite3.connect('todo.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        content TEXT NOT NULL,
                        done INTEGER DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
        conn.commit()

# Automatically run init_db before the first request
@app.before_first_request
def setup():
    if not os.path.exists('todo.db'):
        init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT id, content, done FROM tasks WHERE user_id=?', (session['user_id'],))
    tasks = c.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    content = request.form.get('content')
    if content and 'user_id' in session:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        c.execute('INSERT INTO tasks (user_id, content) VALUES (?, ?)', (session['user_id'], content))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/done/<int:task_id>')
def done(task_id):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('UPDATE tasks SET done = 1 - done WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        try:
            conn = sqlite3.connect('todo.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already exists'
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
