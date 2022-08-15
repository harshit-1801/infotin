from flask import Flask, render_template, redirect, request,flash,session
from newsapi import NewsApiClient
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import requests
import urllib.parse
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from collections import Counter

app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/infotin'
db = SQLAlchemy(app)

newsapi = NewsApiClient(api_key='205f6116c4984a6ea4ee7e69c00bbde0')


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    hash = db.Column(db.String(120), nullable=False)
    keywords = db.Column(db.Text)


colors = {
    "sports":"#fd916a",
    "entertainment":"#ffbb53",
    "health":"#e64bff",
    "science":"#71d2fe",
    "technology":"#fec70a",
    "business":"#e95554"
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login",methods = ["GET","POST"])
def login():
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Enter username","red")
            return redirect("/login")
        elif not request.form.get("password"):
            flash("Enter password","red")
            return redirect("/login")

        user = Users.query.filter_by(username=request.form.get("username")).first()

        if user == None or not check_password_hash(user.hash,request.form.get("password")):
            flash("Incorrect username/password","red")
            return redirect("/login")

        session["user_id"] = Users.query.filter_by(username=request.form.get("username")).first().id
        flash("Successfully logged in","blue")
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/register",methods = ["GET","POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Enter username","red")
            return redirect("/register")
        elif not request.form.get("password"):
            flash("Enter password","red")
            return redirect("/register")
        elif not request.form.get("confirmation"):
            flash("Enter password confirmation","red")
            return redirect("/register")
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Password don't match","red")
            return redirect("/register")

        if Users.query.filter_by(username=request.form.get("username")).first() == None:
            pwdhash = generate_password_hash(request.form.get("password"))
            user = Users(username=request.form.get("username"),hash=pwdhash)
            db.session.add(user)
            db.session.commit()
            flash("Registered successfully!","blue")
            session["user_id"] = Users.query.filter_by(username=request.form.get("username")).first().id
            return redirect("/")

        else:
            flash("Username already taken!","red")
            return redirect("/register")
    else:
        return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    session["user_id"] = None
    flash("Logged out","blue")
    return redirect("/")

@app.route("/")
def index():
    top_headlines = newsapi.get_top_headlines(country='in')["articles"]
    return render_template("index.html",top_headlines = top_headlines)

@app.route("/categories/<string:category>")
def categories(category):
    news = newsapi.get_top_headlines(country='in',category=category)["articles"]
    return render_template("categories.html",news = news,category=category.title(),colors = colors[category])

@app.route("/search",methods=["GET","POST"])
def search():
    title = request.form.get("query")
    query = urllib.parse.quote(title)
    news = newsapi.get_everything(language="en",sort_by="publishedAt",qintitle=request.form.get("query"))["articles"]
    return render_template("search.html",news = news,title = title.title())

@login_required
@app.route("/add")
def add():
    news = request.args.get('news')
    news = news.strip()
    ind = news[::-1].find(" - ")
    ind += 3
    ind *= -1
    news = news[:ind]

    check_words = list(ENGLISH_STOP_WORDS)
    check_words.extend(["-",":"])

    news = news.split(" ")
    for i in news:
        if i.lower() in check_words or i.isdigit():
            news.remove(i)
    
    dict = {}
    for i in news:
        if i in dict:
            dict[i] += 1
        else:
            dict[i] = 1
    dict = Counter(dict)
    
    user = Users.query.filter_by(id = session["user_id"]).first()
    keywords = user.keywords
    
    if keywords is None:
        keywords = Counter({})
    else:
        keywords = eval(keywords)

    x = keywords+dict
    user.keywords = x
    
    db.session.commit()
    return redirect("/")
    
    

@login_required
@app.route("/recommended")
def recommended():
    user = Users.query.filter_by(id = session["user_id"]).first()
    keywords = user.keywords
    news = []
    count = 0
    if keywords != None:
        for i in keywords:
            if count == 4:
                break
            count += 1

            news.append(newsapi.get_everything(language="en",sort_by="publishedAt",qintitle=i)["articles"][:3])
    else:
        news = [[]]
    
    return render_template("recommended.html",news = news[0])

app.run(debug=True)