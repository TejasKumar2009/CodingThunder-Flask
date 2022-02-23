from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import pymysql
import json
import math

def checkUserLogin():
    if "user" in session and session['user']==params['admin_user']:
        return True
    else:
        return False
    

# Opening config.js file
with open("config.json", "r") as f:
    params = json.load(f)["params"]

pymysql.install_as_MySQLdb()

app = Flask(__name__)

app.secret_key = params['secret_key']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['email_id'],
    MAIL_PASSWORD=  params['email_password']
)

mail = Mail(app)


if params['local_server']:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_db_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_db_uri']    

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Contacts(db.Model):
    contact_sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.Text, nullable=False)
    contact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

class Blogposts(db.Model):
    '''
    post_id, post_title, post_desc, post_content, author, date
    '''
    post_id = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String(200), nullable=False)
    post_desc = db.Column(db.Text, nullable=False)
    post_content = db.Column(db.Text, nullable=False)
    post_slug = db.Column(db.String(30), nullable=False)
    author = db.Column(db.String(100), nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    img_file = db.Column(db.String(300), nullable=False, default="post-bg.jpg")


@app.context_processor
def inject_variables():

    dashboard_btn = checkUserLogin()
    return dict(dashboard_btn=dashboard_btn)


@app.route("/")
def index():
    posts = Blogposts.query.filter_by().all()
    short_posts = [posts[-1], posts[-2]]

    return render_template("index.html", params=params, short_posts=short_posts)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/blog")
def blog():
    posts = Blogposts.query.filter_by().all()
    posts.reverse()

    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')

    if (not str(page).isnumeric()) or int(page)<=0:
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    if page == 1:
        prevPage = "#"
        nextPage = "?page=" + str(page+1)
    if page == last:
        prevPage = "?page=" + str(page-1)
        nextPage = "#"
    else:
        prevPage = "?page=" + str(page-1)
        nextPage = "?page=" + str(page+1)

    return render_template("blog.html", posts=posts, prevPage=prevPage, nextPage=nextPage)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post_slug_filter = Blogposts.query.filter_by(post_slug=post_slug).first()

    return render_template("post.html", params=params, post_slug_filter=post_slug_filter)


@app.route("/contact", methods=['GET', 'POST'])
def contact():

    if request.method == "POST":
        contact_request = 0
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")
        print(type(name), type(email), type(phone), type(message))

        # Basic Checks
        if len(name) <= 3 or len(email) <= 3 or "@" not in email or "." not in email or len(phone) < 10 or len(message) < 4:
            pass
        else:
            contact_entry = Contacts(name=name, email=email, phone_num=phone, message=message)
            db.session.add(contact_entry)
            db.session.commit()
            contact_request = 1
            mail.send_message("New Message from " + name, sender=email, recipients=[params['email_id']],
            body = f"{message}\nName - {name}\nContact No. - {phone}\nEmail - {email}")

        return render_template("contact.html", contact_request=contact_request)

    return render_template("contact.html")


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():

    if "user" in session and session['user']==params['admin_user']:
        posts = Blogposts.query.all()

        return render_template("dashboard.html", params=params, posts=posts)
        

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username==params['admin_user'] and password==params['admin_password']:
            session['user']=username
            posts = Blogposts.query.all()

            return render_template("dashboard.html", params=params, posts=posts)

        else:
            return render_template("login.html")
        
    else:
        return render_template("login.html")


@app.route("/dashboard/edit/<string:sno>", methods=['GET', 'POST'])
def db_edit(sno):

    if "user" in session and session['user']==params['admin_user']:
        if request.method == "POST":
            title = request.form.get("post_title")
            desc = request.form.get("post_desc")
            slug = request.form.get("post_slug")
            content = request.form.get("post_content")
            img_file = request.form.get("img_file")
            author = request.form.get("post_author")
            date = datetime.now()

            if sno=='0':
                post = Blogposts(post_title=title, post_desc=desc, post_content=content, post_slug=slug, author=author, date=date, img_file=img_file)
                db.session.add(post)
                db.session.commit()
                
            else:
                post = Blogposts.query.filter_by(post_id=sno).first()
                post.post_title = title
                post.post_desc = desc
                post.post_content = content
                post.post_slug = slug
                post.author = author
                post.date = datetime.now()
                post.img_file = img_file
                db.session.commit()
                print("Successfully edited post number "+sno)
                return redirect('/post/'+post.post_slug)
            
    post = Blogposts.query.filter_by(post_id=sno).first()
    return render_template("db_edit.html", post=post,sno=sno)


@app.route("/dashboard/delete/<string:sno>", methods=['GET', 'POST'])
def db_delete(sno):
    if "user" in session and session['user']==params['admin_user']:
        post = Blogposts.query.filter_by(post_id=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/")


app.run(debug=True)
