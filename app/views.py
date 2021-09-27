from flask import (Flask, flash, render_template,
        redirect, request, session, url_for, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from app.form import RegisterForm, LoginForm, UploadForm, EditForm
from cloudinary.utils import cloudinary_url
from cloudinary.uploader import upload
from bson.objectid import ObjectId
from datetime import datetime
from app import app, mongo

import cloudinary.api
import requests

from werkzeug.datastructures import CombinedMultiDict

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
        'index.html', digital_art=digital_art,
        painting=painting, images=images, title="home")


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register new user Usernames
    Hash the passwords and
    add to the mongo DB user collection
    """

    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        existing_user = mongo.db.users.find_one(
            {"username": form.username.data.lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))   
        else:
            register = {
                "username": form.username.data.lower(),
                "password": generate_password_hash(
                    form.password.data)
            }
            mongo.db.users.insert_one(register)
            flash(f'Welcome, {form.username.data.capitalize()}')
            flash("Registration successfuly")
            return redirect(url_for("login"))
        
        flash('Thanks for registering')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():

    """
    Registered user login
    Check if user is stored in the DB
    Check password hash for match
    If user war verified The user is
    Add user to session cookie
    redirected to a profile page
    Or If username doesn't exist
    Back to register page
    """

    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        existing_user = mongo.db.users.find_one(
            {"username": form.username.data.lower()})
        if existing_user:
            if check_password_hash(
                    existing_user["password"], form.password.data.lower()):
                session["user"] = form.username.data.lower()
                flash("Welcome, {}".format(
                    form.username.data.capitalize()), 'success')
                if session["user"] != "admin":
                    return redirect(url_for(
                        "profile", username=session["user"]))
                else:
                    return redirect(url_for("admin"))
            else:
                flash("Incorrect Username and/or Password", 'error')
                return redirect(url_for("login"))
        else:
            flash("Incorrect Username and/or Password", 'error')
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):

    """
    Find user's username from db
    Check if user match session cookie
    Render Profile page if verified
    Or Rediret unauthorized users page access
    """

    if "user" in session and session["user"] != "admin":
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        categories = mongo.db.categories.find()
        posts = list(mongo.db.posts.find({"created_by": session["user"]}))
        return render_template(
            "profile.html", username=username,
                isButton=True, categories=categories, posts=posts,  profile=True)
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/delete_profile", methods=["GET", "POST"])
def delete_profile():

    """ 
    Delete user rofile Get input
    from form and find username
    and password in the DB For deletion
    """

    if "user" in session:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        if request.method == "POST":
            # check if username exists in db
            existing_user = mongo.db.users.find_one(
                {"username": request.form.get("username").lower()})
            # Admin user management
            if existing_user and session["user"] == "admin":
                admin = mongo.db.users.find_one(
                            {"username": session["user"].lower()})
                if check_password_hash(
                        admin["password"], request.form.get("password")):
                    mongo.db.users.remove(existing_user)
                    flash("User was remover", 'success')
                    return redirect(url_for("admin"))
                else:
                    flash("You Entered Incorrect Password", 'error')
                    return redirect(url_for("delete_profile", account=True))
                # Existing user delete self
            elif existing_user == session["user"]:
                # ensure hashed password matches user input
                if check_password_hash(
                        existing_user["password"], request.form.get("password")):
                    mongo.db.users.remove(existing_user)
                    flash("Good Buy", 'success')
                    return redirect(url_for("logout"))
                else:
                    flash("Incorrect Username and/or Password", 'error')
                    return redirect(url_for("delete_profile", account=True))
            else:
                flash("Incorrect Username and/or Password", 'error')
                return redirect(url_for("delete_profile", account=True))

        return render_template("edit_profile.html", account=True)
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/add_post", methods=("POST", "GET"))
def add_post():

    """
    Add new posts to the Mongo DB
    Upload image to the Cloudinary API
    """

    form = UploadForm(CombinedMultiDict((request.files, request.form)))
    if "user" in session and session["user"] != "admin":
        # Return all the categories form DB
        categories = mongo.db.categories.find()
        if request.method == "POST" and form.validate():
            file = request.files['file']
            upload_result = None
            image = None
            image_small = None
            if file:
                # File upoad to cloudinary
                folder = request.form.get("category").lower()
                upload_result = upload(file, folder=folder)
                # Get 1920p size image URL
                image, options = cloudinary_url(
                    upload_result['public_id'],
                    format="jpg", crop="fill", width=1920)
                # Get image thumblail URL
                image_small, options = cloudinary_url(
                    upload_result['public_id'],
                    format="jpg", crop="fill", width=300)
                # Get image public id
                img_id = upload_result.get('public_id')
                # requers url status
                URL_status = requests.get(image)
                # Submit post to Mongo DB if file upload was success
                if URL_status.status_code == 200:
                    submit = {
                        "category_name": request.form.get("category").lower(),
                        "title": form.title.data.lower(),
                        "description": form.description.data,
                        "image": image,
                        "image_sm": image_small,
                        "img_id": img_id,
                        "created_by": session["user"],
                        "time_created": now
                        }
                    mongo.db.posts.insert_one(submit)
                    flash("Post was successfully added", 'success')
                    return redirect(url_for("add_post", categories=categories, post=True, form=form))
                else:
                    if URL_status.status_code != 200:
                        flash(f"Status code: {URL_status.status_code}")
                        flash("Post did not upload Try again", 'error')
                        return redirect(url_for("add_post", categories=categories, post=True, form=form))
                    else:
                        flash("Post failed upload", 'error')
                        flash("Please try again later", 'error')
                        return redirect(url_for("add_post", categories=categories, post=True, form=form))
            else:
                flash('File is required', 'error')
                return render_template("add_post.html", categories=categories, post=True, form=form)
        else:
            return render_template("add_post.html", categories=categories, post=True, form=form)
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):

    """
    Update mongo DB "post" collection
    Update existing post Title and
    description only
    """

    if "user" in session:
        form = EditForm(request.form)
        # Find existing post by id and get category
        post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        categories = mongo.db.categories.find().sort("category_name", 1)
        if session["user"] == "admin":
            for key, value in post.items():
                if key == "created_by":
                    created_by = mongo.db.users.find_one({"username": value})
            
        # Get image id and url out of mongo DB
        for k, v in post.items():
            if k == "image":
                image = v
            elif k == "img_id":
                image_id = v
            elif k == "image_sm":
                image_sm = v
            elif k == "time_created":
                time_stamp = v

        # Update Object to be submitet for update
        if request.method == "POST" and form.validate():
            submit = {
                "category_name": request.form.get("category").lower(),
                "title": form.title.data.lower(),
                "description": form.description.data,
                "image": image,
                "image_sm": image_sm,
                "img_id": image_id,
                "created_by": session["user"],
                "time_created": time_stamp
            }
            mongo.db.posts.update({"_id": ObjectId(post_id)}, submit)
            flash("post Successfully Updated", 'success')
            if session["user"] != "admin":
                return redirect(url_for("profile", username=session["user"]))
            else:
                return redirect(url_for("admin"))

        return render_template("edit_post.html", categories=categories, post=post, form=form, created_by=created_by )
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))
   

@app.route("/delete_post/<post_id>")
def delete_post(post_id):

    """
    DElete post from mongo DB
    Get image url trom DB and
    delete from cloudinary storage
    """

    if "user" in session:
        # Find post by id and iterate
        # over to extract image id and URL
        posts = mongo.db.posts.find_one(
            {"_id": ObjectId(post_id)}, {"img_id": 1, "_id": 0})
        for x, y in posts.items():
            if x == "img_id":
                image_id = y
        try:
            # Destroy permanently delete a single asset
            # Invalidates CDN cached copies of the asset
            cloudinary.uploader.destroy(image_id, invalidate='true')
            status = True
        # Catch error If try delete same asset again
        except AttributeError:
            flash("file already was deleted", 'error')
            if session["user"] != "admin":
                return redirect(url_for("profile", username=session["user"]))
            else:
                return redirect(url_for("admin"))
        if status:
            mongo.db.posts.remove({"_id": ObjectId(post_id)})
            flash("Post was successluly deleted", 'success')
        else:
            flash("Failed to delete Image file", 'error')
            flash("Please try again later", 'error')
            if session["user"] != "admin":
                return redirect(url_for("profile", username=session["user"]))
            else:
                return redirect(url_for("admin"))

        if session["user"] != "admin":
            return redirect(url_for("profile", username=session["user"]))
        else:
            return redirect(url_for("admin"))
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))



@app.route('/query', methods=["GET", "POST"])
def query():
    """
    Search function
    Get all posts form DB
    Search by keyword, username
    Or Query posts by category
    """

    categories = mongo.db.categories.find()
    posts = list(mongo.db.posts.find().sort('_id', -1))
    if session["user"] == "admin":
        url = "admin.html"
        title= "admin"
    else:
        url = "gallery.html"
        title = "gallery"
    if request.method == "POST":
        search = request.form.get("search").lower()
        category_name = request.form.get("category").lower()
        categories = mongo.db.categories.find()
        not_selected = "select category"
        # Search by keyword and category
        if search != "" and category_name != not_selected:
            posts = list(mongo.db.posts.find({ "$and" : [ {
                "category_name": category_name }, {"$text": {"$search": search}}] }))
            if len(posts) == 0:     
                flash(f"No results for {search} in {category_name}", 'error')
                return render_template(url, posts=posts, 
                    categories=categories, title=title)
            else:
                flash(f"Results for {search} in {category_name}", 'success')
                return render_template(url, posts=posts, 
                    categories=categories, title=title)
        # Search by Key word only
        elif search != "":
            posts = list(mongo.db.posts.find({"$text": {"$search": search}}))
            if len(posts) == 0:     
                flash(f"No results for {search}", 'error')
                return render_template(url, posts=posts, 
                    categories=categories, title=title)
            else:
                flash(f"Results for {search}", 'success')
                return render_template(url, posts=posts, 
                    categories=categories, title=title)
        # Search by category only
        elif category_name != not_selected and search == "":
            posts = list(mongo.db.posts.find({"category_name": category_name }))
            if len(posts) == 0:     
                flash(f"No results for {category_name}", 'error')
                return render_template(url, posts=posts, 
                    categories=categories, title=title)
            else:
                flash(f"Results for category {category_name}", 'success')
                return render_template(url, posts=posts, 
                    categories=categories, title=title)
        else:
            return render_template(url, posts=posts, 
                categories=categories, title=title)
    else:
        return render_template(url, posts=posts, 
            categories=categories, title=title)


@app.route('/gallery', methods=["GET", "POST"])
def gallery():
    """
    Gallery page
    Get all posts form DB
    Search by keyword, username
    Or Query posts by category
    """
    categories = mongo.db.categories.find()
    posts = list(mongo.db.posts.find().sort('_id', -1))

    return render_template('gallery.html', posts=posts,
        categories=categories, title="gallery")


#==============ADMIN================
@app.route("/admin", methods=["GET", "POST"])
def admin():

    """
    Find user's username from db
    Check if user match session cookie
    Render Profile page if verified
    Or Rediret unauthorized users page access
    """

    # mongo.db.posts.drop_indexes()
    # mongo.db.posts.create_index([
    #   ("title", "text"), ("description", "text"), ("created_by", "text")])

    if "user" in session and session["user"] == "admin":
        categories = mongo.db.categories.find()
        posts = list(mongo.db.posts.find().sort('_id', -1))
        users = list(mongo.db.users.find())
        return render_template(
            "admin.html", categories=categories, posts=posts, users=users, admin=True)
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route("/manage_users", methods=["GET", "POST"])
def manage_users():

    """ 
    Manage users Get input
    from form and find username
    and password in the DB For deletion
    """
    if "user" in session and session["user"] == "admin":
        users = list(mongo.db.user.find())
        
        return render_template("manage_users.html", users=users)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/logout")
def logout():

    """
    remove the username from the session if it's there
    """

    if "user" in session:
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))