import os, requests

from flask import Flask, session, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask import render_template

app = Flask(__name__)

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
 
@app.route('/')
def index():
    status = 'Loggedout'
    try:
        user_email=session['user_email']
        status=''

    except KeyError:
        user_email=''
    return render_template('index.html', status=status, user_email=user_email)

@app.route('/search')
def search():
    user_email=session['user_email']
    status=''
    if 'user_email' not in session:
        return render_template('search.html', error_message='Please Login First')
    return render_template('search.html', status=status, user_email=user_email)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if db.execute("SELECT id FROM users WHERE email= :email", {"email": email}).fetchone() is not None:
            return render_template('register.html', status="Loggedout", error_message='The user has already registered. Please Login.')
        password = request.form['password']
        if password == "":
            return render_template('register.html', status="Loggedout", error_message='Please enter password!')
        db.execute("INSERT INTO users (email, password) VALUES (:email, :password)",
                   {"email": email, "password": generate_password_hash(password)})
        db.commit()
        flash('You were successfully registered!')
        return redirect(url_for('login'))
    return render_template('register.html', status="Loggedout")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = db.execute("SELECT id, password FROM users WHERE email= :email", {"email": email}).fetchone()
        if user is None:
            return render_template('login.html', status='Loggedout', error_message="The user hasn't been registered. Please register.")
        password = request.form['password']
        if not check_password_hash(user.password, password):
            return render_template('login.html', status='Loggedout', error_message='Wrong password!')
        session['user_email'] = email
        session['user_id'] = user.id
        flash('You were successfully logged in!')
        return redirect(url_for('search'))
    if request.method == 'GET' and 'user_email' not in session:
        return render_template('login.html', status='Loggedout')

@app.route('/logout')
def logout():
    try:
        session.pop('user_email')

    except KeyError:
        return render_template('index.html', error_message='Please Login First')
    return render_template('index.html', status='Loggedout')

@app.route('/booklist', methods=['POST'])
def booklist():
    user_email = session['user_email']
    if 'user_email' not in session:
        return render_template('login.html', error_message='Please Login First', status='Loggedout')
    book_column = request.form.get('book_column')
    query = request.form.get('query')
    if book_column == "year":
        book_list = db.execute("SELECT * FROM books WHERE year = :query", {"query": query}).fetchall()
    else:
        book_list = db.execute("SELECT * FROM books WHERE UPPER(" + book_column + ") = :query ORDER BY title",
                               {"query": query.upper()}).fetchall()
    if len(book_list):
        return render_template('bookList.html', book_list=book_list, user_email=session["user_email"])
    elif book_column != 'year':
        error_message = "We couldn't find the books you searched for."
        book_list = db.execute("SELECT * FROM books WHERE UPPER(" + book_column + ") LIKE :query ORDER BY title",
                               {"query": "%" + query.upper() + "%"}).fetchall()
        if not len(book_list):
            return render_template("error.html", error_message=error_message)
        message = "You might be searching for:"
        return render_template("bookList.html", error_message=error_message, book_list=book_list, message=message,
                               user_email=session["user_email"])
    else:
        return render_template('error.html', error_message="Please check for errors and try again.")

@app.route('/detail/<int:book_id>', methods=['GET', 'POST'])
def detail(book_id):
    user_id = session["user_id"]
    if 'user_id' not in session:
        return render_template('login.html', error_message='Please Login First', status='Loggedout')
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    if book is None:
        return render_template('error.html', error_message="There isn't a book with provided ID!")
    if request.method == 'POST':
        rating = request.form['rating']
        comment = request.form['comment']
        if db.execute("SELECT id FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                {"user_id": user_id, "book_id": book_id}).fetchone() is None:
            db.execute("INSERT INTO reviews (user_id, book_id, rating, comment) VALUES (:user_id, :book_id, :rating, :comment)",
                {"user_id": user_id, "book_id": book.id, "rating": rating, "comment": comment})
        else:
            db.execute("UPDATE reviews SET comment = :comment, rating = :rating WHERE user_id = :user_id AND book_id = :book_id", 
            {"user_id": user_id, "book_id": book.id, "rating": rating, "comment": comment})
        db.commit()

    """Goodreads API"""
    key="O32FR1NaA884y6R1noOtMA"
    res = requests.get("https://www.goodreads.com/book/review_counts.json", 
    params={"key": key, "isbns": book.isbn}).json()["books"][0]

    ratings_count=res["ratings_count"]
    average_rating = res["average_rating"]
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", 
        {"book_id": book.id}).fetchall()

    users = []
    for review in reviews:
        email = db.execute("SELECT email FROM users WHERE id = :user_id",
        {"user_id": review.user_id}).fetchone().email
        users.append((email, review))
        print("User")
    return render_template("detail.html", book=book, users=users,
                           ratings_count=ratings_count, average_rating=average_rating, user_email=session["user_email"])

@app.route('/api/<isbn>', methods=['GET'])
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return render_template("error.html", error_message="We got an invalid ISBN.")

    key = "O32FR1NaA884y6R1noOtMA"
    res = requests.get("https://www.goodreads.com/book/review_counts.json", 
    params={"key": key, "isbns": isbn}).json()["books"][0]
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", 
        {"book_id": book.id}).fetchall()
    count = res["ratings_count"]
    average_rating = res["average_rating"]
    for review in reviews:
        count = count+1
        average_rating = (average_rating+review.rating)/2

    return jsonify(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        review_count=count,
        average_score=average_rating
    )
