from app import app, mongo
from flask import (Flask, flash, render_template,
        redirect, request, session, url_for, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import cloudinary.uploader
import cloudinary.api
import requests


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route("/register", methods=["GET", "POST"])
def register():

    """
    Register new users
    Hash the passwords and
    add to the mongo DB user collection
    """

    if request.method == "POST":
        # check username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        # Add user to the Mongo DB
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

    """
    Registered user login
    Chsck if user is stored in the DB
    Verifies that a password matches a hash
    If user war verified The user is
    redirected to a profile page
    """

    if request.method == "POST":
        # check username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            # Check password hash for match
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                # Add user to session cookie
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username").capitalize()))
                return redirect(url_for(
                    "profile", username=session["user"]))
        else:
            # If username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):

    """
    Find user's username from db
    Check if user match session cookie
    Render Profile page if verified
    """

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
    """
    Add new posts to the Mongo DB
    Upload image to the Cloudinary API
    """
    # Return all the categories form DB
    categories = mongo.db.categories.find()
    if request.method == "POST" and request.files:
        # File upoad to cloudinary
        file = request.files['file']
        file_sent = cloudinary.uploader.upload(
            file, folder=request.form.get(
                'category'), width=300, height=300)
        file_URL = file_sent.get('secure_url')
        img_id = file_sent.get('public_id')
        URL_status = requests.get(file_URL)
        # Submit post to Mongo DB if file upload was success
        if URL_status.status_code == 200:
            submit = {
                "category_name": request.form.get("category"),
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "image": file_URL,
                "img_id": img_id,
                "created_by": session["user"]          
                }
            mongo.db.posts.insert_one(submit)
            flash("Post was successfully added")
            return redirect(url_for("add_post", categories=categories))
        else:
            # failed cloudinary API
            if URL_status.status_code != 200:
                flash(f"Status code: {URL_status.status_code}")
                flash("Post did not upload Try again")
                return redirect(url_for("add_post", categories=categories))
                # Failed to uplload to the mongo DB
            else:
                flash("Post failed upload")
                flash("Please try again later")
                return redirect(url_for("add_post", categories=categories))

    else:
        return render_template("add_post.html", categories=categories)


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    """
    Update existing post
    """
    # Update mongo DB "post" collection 
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
    # Delete post from mongo DB
    # Get image url trom DB
    posts = mongo.db.posts.find_one({"_id": ObjectId(post_id)}, {"img_id": 1, "_id": 0})
    for x, y in posts.items():
        if x == "img_id":
            image_id = y
    try:
        # Try destroy image file
        cloudinary.api.delete_resources([image_id])
        status = True
        if status:
            # If 404 delete collection ftom DB
            mongo.db.posts.remove({"_id": ObjectId(post_id)})
            flash("Post was successluly deleted")
        else:
            # Failed to destroy image from cloudinary
            flash("Failed to delete Image file")
            flash("Please try again later")
            return redirect(url_for("profile", username=session["user"]))
    # If try delete same again catch error
    except AttributeError:
        flash("file already wasdeleted")
        return redirect(url_for("profile", username=session["user"]))
    finally:
        return redirect(url_for("profile", username=session["user"]))


@app.route('/gallery')
def galery():
    # Gallery page
    # Get all posts form DB
    posts = mongo.db.posts.find()
    return render_template('gallery.html', posts=posts)
