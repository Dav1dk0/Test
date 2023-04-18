from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'my-secret-key'


DB_HOST = '127.0.0.1'
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASS = 'Davyd'

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)


@app.route('/')
def home():
    if 'loggedin' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM posts WHERE author = %s", (session['username'],))
        posts = cursor.fetchall()
        return render_template('profile.html', username=session['username'], email=session['email'], fullname=session['fullname'], posts=posts)
    return redirect(url_for('login'))


@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("DELETE FROM posts WHERE id = %s AND author = %s", (post_id, session['username']))
    conn.commit()
    return redirect(url_for('profile'))


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM posts WHERE id = %s AND author = %s", (post_id, session['username'],))
    post = cursor.fetchone()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute("UPDATE posts SET title = %s, content = %s WHERE id = %s AND author = %s", (title, content, post_id, session['username'],))
        conn.commit()
        return redirect(url_for('profile'))
    return render_template('edit_post.html', post=post)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            password_rs = account['password']
            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['email'] = account['email']
                session['fullname'] = account['fullname']
                return redirect(url_for('home'))
            else:
                flash('Incorrect username/password')
        else:
            flash('Incorrect username/password')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        _hashed_password = generate_password_hash(password)

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            cursor.execute("INSERT INTO users (fullname, username, password, email) VALUES (%s,%s,%s,%s)",
                           (fullname, username, _hashed_password, email))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        flash('Please fill out the form!')
    return render_template('register.html')


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST' and 'title' in request.form and 'content' in request.form:
        title = request.form['title']
        content = request.form['content']
        author = session['username']

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("INSERT INTO posts (title, content, author) VALUES (%s, %s, %s)", (title, content, author))
        conn.commit()

        flash('Post created successfully!')
        return redirect(url_for('view_posts'))

    return render_template('create_post.html')


@app.route('/view_posts')
def view_posts():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM posts")

    posts = cursor.fetchall()

    return render_template('view_posts.html', posts=posts)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)