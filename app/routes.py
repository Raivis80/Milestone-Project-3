import os
from app import app, mongo
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import jsonify


cloudinary.config(
    cloud_name=os.environ.get('CLOUD_NAME'),
    api_key=os.environ.get('API_KEY'),
    api_secret=os.environ.get('API_SECRET')
)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        # Add user to DB
        else:
            register = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            mongo.db.users.insert_one(register)
            flash(f'Welcome, {request.form.get("username").capitalize()}')
            flash("Registration successfuly")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                # Add user to session cookie
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username").capitalize()))
                return redirect(url_for(
                    "profile", username=session["user"]))
        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Get session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    # Get categories from DB
    categories = mongo.db.categories.find()
    # IsButton=True show account button for profile page
    if session["user"]:
        posts = mongo.db.posts.find()
        return render_template(
            "profile.html", username=username,
            isButton=True, categories=categories, posts=posts)

    return redirect(url_for("login"))


@app.route("/delete_profile", methods=["GET", "POST"])
def delete_profile():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                mongo.db.users.remove(existing_user)
                flash("Good Buy")
                return redirect(url_for("logout"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("delete_profile"))
        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("delete_profile"))

    return render_template("edit_profile.html")


@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    session.pop('user')
    return redirect(url_for('index'))


@app.route("/add_post", methods=("POST", "GET"))
def add_post():  
    # Return all the categories form DB
    categories = mongo.db.categories.find()
    # Add posts to db
    if request.method == "POST":
        if request.files:
            file = request.files['file']
            file_sent = cloudinary.uploader.upload(
                file, folder=request.form.get('category'), width=580, height=580)
            file_URL  = file_sent.get('secure_url')
        # Submit post to DB
            submit = {
                "category_name": request.form.get("category"),
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "image": file_URL,
                "created_by": session["user"]          
                }
            mongo.db.posts.insert_one(submit)
            flash("Post Successfully added")
            return redirect(url_for("add_post", categories=categories))

    return render_template("add_post.html", categories=categories)


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    # Update existing post
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "created_by": session["user"]
        }
        mongo.db.posts.update({"_id": ObjectId(post_id)}, submit)
        flash("post Successfully Updated")
    # Find existing post id
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_post.html", categories=categories, post=post)


@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    # Delete post from DB
    mongo.db.posts.remove({"_id": ObjectId(post_id)})
    flash("Your post was deleted")
    return redirect(url_for("profile", username=session["user"]))


@app.route('/gallery')
def galery():
    # Get all posts form DB
    posts = mongo.db.posts.find()
    return render_template('gallery.html', posts=posts)
