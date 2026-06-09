from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Secret key for session management
app.secret_key = "secret123"

# SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Create Database
with app.app_context():
    db.create_all()

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return "Username already exists!"

        new_user = User(
            username=username,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            session['username'] = username
            return redirect('/welcome')

        return "Invalid Username or Password"

    return render_template('login.html')

# Welcome Page
@app.route('/welcome')
def welcome():

    if 'username' not in session:
        return redirect('/login')

    return render_template(
        'welcome.html',
        username=session['username']
    )

# Logout
@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/login')

# Run App
if __name__ == '__main__':
    app.run(debug=True)