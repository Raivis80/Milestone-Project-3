from app import app, mongo
from flask import (Flask, flash, render_template,
        redirect, request, session, url_for, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
import cloudinary.uploader
import cloudinary.api
import requests

# dd/mm/YY H:M:S format
now = datetime.now().strftime("%d-%m-%y, %H:%M:%S")


@app.route('/')
@app.route('/index')
def index():
    # Find existing post by id and get category
    digital_art = mongo.db.posts.find({"category_name": "digital_art"}).limit(3)
    painting = mongo.db.posts.find({"category_name": "paintings"}).limit(3)
    images = mongo.db.posts.find({"category_name": "images"}).limit(3)
    return render_template(
        'index.html', digital_art=digital_art, painting=painting, images=images)


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
    try:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        # Get categories from DB
        categories = mongo.db.categories.find()
        # IsButton=True show account button for profile page
        if session["user"]:
            posts = mongo.db.posts.find().sort('time_created', -1)
            return render_template(
                "profile.html", username=username,
                isButton=True, categories=categories, posts=posts)
    # Catch and rediret unauthorized users page access
    except KeyError:
        flash("Please log in or register")
        return redirect(url_for("login"))

    return redirect(url_for("login"))
    

@app.route("/delete_profile", methods=["GET", "POST"])
def delete_profile():

    """ 
    Delete user rofile Get input
    from form and find username
    and password in the DB For deletion
    """
    try:
        # Find user's username from db 
        # #and chect matching session cookie
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
    except KeyError:
        flash("Please log in or register")
        return redirect(url_for("login"))

    if request.method == "POST" and username:
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
    """
    remove the username from the session if it's there
    """
    try:
        # Find user's username from db
        # #and chect match session cookie
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]

    except KeyError:
        flash("Please log in or register")
        return redirect(url_for("login"))

    # Remove session cookie
    if username:
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash("Please log in or register")
        return redirect(url_for('index'))


@app.route("/add_post", methods=("POST", "GET"))
def add_post():
    """
    Add new posts to the Mongo DB
    Upload image to the Cloudinary API
    """
    try:
        # Find user's username from db
        # #and chect match session cookie
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
    except KeyError:
        flash("Please log in or register")
        return redirect(url_for("login"))

    # Return all the categories form DB
    categories = mongo.db.categories.find()

    if username and request.method == "POST" and request.files:
        # File upoad to cloudinary
        file = request.files['file']
        file_sent = cloudinary.uploader.upload(
            file, folder=request.form.get(
                'category'))
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
                "created_by": session["user"],
                "time_created": now
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
    Update mongo DB "post" collection
    Update existing post Title and
    description only
    """

    try:
        # Find user's username from db
        # and chect matching session cookie
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
    except KeyError:
        flash("Please log in or register")
        return redirect(url_for("login"))

    # Find existing post by id and get category
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)

    # Get image id and url out of mongo DB
    for k, v in post.items():
        if k == "image":
            image_URL = v
        elif k == "img_id":
            image = v
        elif k == "time_created":
            time_stamp = v

    # Update Object to be submitet for update
    if username and request.method == "POST":
        submit = {
            "category_name": request.form.get("category"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "image": image_URL,
            "img_id": image,
            "created_by": session["user"],
            "time_created": time_stamp
        }
        mongo.db.posts.update({"_id": ObjectId(post_id)}, submit)
        flash("post Successfully Updated")

    return render_template("edit_post.html", categories=categories, post=post)


@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    """
    DElete post from mongo DB
    Get image url trom DB and
    delete from cloudinary storage
    """
    try:
        # Find user's username from db
        # #and chect matching session cookie
        mongo.db.users.find_one(
            {"username": session["user"]})["username"]
    except KeyError:
        flash("Please log in or register")
        return redirect(url_for("login"))

    # Find post by id and iterate
    # over to extract image id and URL
    posts = mongo.db.posts.find_one({"_id": ObjectId(post_id)}, {"img_id": 1, "_id": 0})
    for x, y in posts.items():
        if x == "img_id":
            image_id = y

    try:
        # Try destroy image file
        cloudinary.api.delete_resources([image_id])
        status = True
    # If try delete same again catch error
    except AttributeError:
        flash("file already was deleted")
        return redirect(url_for("profile", username=session["user"]))

    if status:
        mongo.db.posts.remove({"_id": ObjectId(post_id)})
        flash("Post was successluly deleted")
    else:
        # Failed to destroy image from cloudinary
        flash("Failed to delete Image file")
        flash("Please try again later")
        return redirect(url_for("profile", username=session["user"]))

    return redirect(url_for("profile", username=session["user"]))


@app.route('/gallery')
def galery():
    # Gallery page
    # Get all posts form DB
    posts = mongo.db.posts.find().sort('time_created', -1)
    return render_template('gallery.html', posts=posts)
