from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import os
import math

with open("config.json","r") as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config["UPLOAD_FOLDER"] = params['upload_folder']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail = Mail(app)

if params["local_server"]:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.all()
    last = math.ceil(len(posts)/int(params['no-of-posts']))

    page = request.args.get("page")
    if (page == None):
        page = 1

    page = int(page)
    j = (page-1)*int(params['no-of-posts'])
    posts = posts[j:j+2]

    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)

    return render_template('index.html',params = params,posts = posts,prev = prev,next = next)

@app.route("/post/<string:post_slug>", methods = ["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',post = post,params = params)

@app.route("/about")
def about():
    return render_template('about.html',params = params)

@app.route("/dashboard",methods = ["POST","GET"])
def dashboard():
    if "user" in session and session['user']==params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method=="POST":
        username = request.form.get("uname")
        userpass = request.form.get("upass")
        if username==params['admin_user'] and userpass==params['admin_pass']:
            # set the session variable
            session['user']=username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
    else:
        return render_template("signin.html", params=params)

@app.route("/uploader",methods=["POST","GET"])
def uploader():
    if "user" in session and session['user']==params['admin_user']:
        if request.method == "POST":
            f = request.files["file1"]
            f.save(os.path.join(app.config["UPLOAD_FOLDER"]),secure_filename(f.filename))
            return ("Uploaded successfully")


@app.route("/edit/<string:sno>",methods = ["POST","GET"])
def edit(sno):
    if "user" in session and session['user']==params['admin_user']:
        if request.method == "POST":
            title = request.form.get("title")
            tline = request.form.get("tline")
            content = request.form.get("content")
            slug = request.form.get("slug")
            img_file = request.form.get("img_file")

            if sno == '0':
                post = Posts(title=title,tagline=tline,slug=slug,content=content,date= datetime.now(),img_file=img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = datetime.now()
                db.session.commit()

                return redirect("/edit/"+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html",params=params,sno=sno,post=post)

@app.route("/delete/<string:sno>" , methods=['GET', 'POST'])
def delete(sno):
    if "user" in session and session['user']==params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message(
            "Mail from " + name,
            sender = email,
            recipients = [params["gmail-user"]],
            body = message + "\n" + phone
        )
    return render_template('contact.html',params = params)


app.run(debug=True)
