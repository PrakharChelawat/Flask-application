from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail, Message
import os.path
from werkzeug.utils  import secure_filename
import math

app = Flask(__name__)

app.config['SECRET_KEY'] = 'the random string'
f = open('templates/config.json','r')
with open('templates/config.json','r') as c:
    params = json.load(c)["params"]

app.config.update(
MAIL_SERVER='smtp.gmail.com',
MAIL_PORT = 465,
MAIL_USE_TLS= False,
MAIL_USE_SSL = True,
MAIL_USERNAME = params['MAIL_USERNAME'],
MAIL_PASSWORD = params['MAIL_PASSWORD']
)


mail = Mail(app)
localhost = True
# SQLALCHEMY is a connection object that connects flask application to MySQL.
if localhost==True:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['LOCALHOST_DB_URI']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['PROD_DB_URI']


# app.config["SQLALCHEMY_DATABASE_URI"] ='mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user='root', password='root', server='localhost', database='blogging')


db = SQLAlchemy(app)



class Contacts(db.Model):
    ''''id Name Email phone Message PostedOn'''

    id = db.Column(db.Integer,primary_key=True)
    fullname = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.Integer)
    message = db.Column(db.String(255))
    postedon = db.Column(db.String(255),nullable=True)


class Posts(db.Model):

    '''postid Title Message PostedBy PostedOn'''

    postid = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255))
    subtitle = db.Column(db.String(255))
    message = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    date = db.Column(db.String(255))
    img_url = db.Column(db.String(255))



# Home Page Url
@app.route("/",methods=["GET","POST"])
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


# Admin Sign In to Dashboard 
@app.route("/dashboard",methods=["GET","POST"])
def login():
    if 'user' in session and session['user']==params['adminUser']:
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html',params=params,posts=posts)
        
    if(request.method=="POST"):

        uname = request.form.get("uname")
        password = request.form.get("password")

        if(uname==params['adminUser'] and password==params['adminPassword']):
            session['user'] = uname
            posts = Posts.query.filter_by().all()
            return render_template('dashboard.html',params=params,posts=posts)
        
        # check credentials from config file and Pass

    return render_template('login.html',params=params)

# Add New Post
@app.route("/add",methods=["GET","POST"])
def add():
    if 'user' in session and session['user']==params['adminUser']:
        if request.method=="POST":
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            message = request.form.get('message')
            img_url = request.form.get('img_url')

            newpost= Posts(title=title,subtitle=subtitle,slug=slug,message=message,img_url=img_url,date=datetime.now())
            db.session.add(newpost)
            db.session.commit()
        return render_template('add.html',params=params)

# Admin Editing the post
@app.route("/edit/<string:postid>/",methods=["GET","POST"])
def edit(postid):
    if 'user' in session and session['user']==params['adminUser']:
        if(request.method=="POST"):
            print("Data loaded for post --->>>>",postid)
            postdetails = Posts.query.filter_by(postid= postid).first()
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            message = request.form.get('message')
            img_url = request.form.get('img_url')

            postdetails.title = title
            postdetails.subtitle = subtitle
            postdetails.slug = slug
            postdetails.message = message
            postdetails.img_url = img_url
            
            db.session.commit()
            
            return redirect('/edit/'+postid)
        post = Posts.query.filter_by(postid= postid).first()
        return render_template('edit.html',params=params,post=post)




#delete the posts

@app.route("/delete/<string:postid>/",methods=["GET","POST"])
def delete(postid):
    if 'user' in session and session['user']==params['adminUser']:
        post = Posts.query.filter_by(postid=postid).first()
        if(post):
            db.session.delete(post)
            db.session.commit()
            return "Deleted Successfully"

@app.route("/logout",methods=["GET","POST"])
def logout():
    session.pop('user')
    return render_template('login.html',params=params)

@app.route("/upload",methods=["GET","POST"])
def uploadFile():
    if 'user' in session and session['user']==params['adminUser']:
        if request.method == 'POST':  
            f = request.files['file']
            f.save(os.path.join(params['file_path'],secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route("/contact",methods=["GET", "POST"])
def Contact():
    if request.method == "POST":
        
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        Contacts_obj = Contacts(fullname=name,email=email,phone=phone,message=message,postedon=datetime.now())
        db.session.add(Contacts_obj)
        # Mail Trigger
        # Details of Registration with heading as New Account in Blog having folowing Details:
        db.session.commit()
        email_msg = Message(
                'New Message from ' + name,
                sender=email,
                recipients = ['prakharchelawat2112@gmail.com']
               )
        email_msg.body = message + "\n" + phone
        mail.send(email_msg)

    return render_template('contact.html',params=params)

@app.route("/post/<string:post_slug>",methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)


app.run(debug=True)