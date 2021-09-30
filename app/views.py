from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from app.form import (
    RegisterForm, LoginForm, UploadForm,
    EditForm, DeleteUser, AddCategory, ChangePassword, DeleteUsersAdmin)
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
    """
    Index page: find by category name posts
    in "posts collection" and limit to 3 items.
    For each of the 3 categories. And render
    Index page with all required parameters.

    """
    digital_art = mongo.db.posts.find({"category_name": "digital_art"}).limit(3)
    painting = mongo.db.posts.find({"category_name": "paintings"}).limit(3)
    images = mongo.db.posts.find({"category_name": "images"}).limit(4)
    return render_template(
        'index.html', digital_art=digital_art,
        painting=painting, images=images, title="home")


@app.route('/gallery', methods=["GET", "POST"])
def gallery():

    """
    Gallery page: Get all posts
    form Mongo DB Search qurey.
    """

    categories = mongo.db.categories.find()
    posts = list(mongo.db.posts.find().sort('_id', -1))

    return render_template(
        'gallery.html', posts=posts, categories=categories, title="gallery")


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register new user Usernames Hash the
    passwords and add to the mongo DB user
    collection, redirect to login page.
    """

    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        existing_user = mongo.db.users.find_one(
            {"username": form.username.data.lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(request.url)   
        else:
            register = {
                "username": form.username.data.lower(),
                "password": generate_password_hash(
                    form.password.data)
            }
            mongo.db.users.insert_one(register)
            flash(f'Welcome, {form.username.data.capitalize()}', 'success')
            return redirect(url_for("login"))

    return render_template('register.html', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():

    """
    Registered user login: Check if user
    is stored in the DB Check password
    hash for match. If user was verified
    Add user to the session cookie and
    redirected to a profile page Or If
    user net existreturn to register page
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
                    return redirect(url_for("manage"))

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
    Find user's username from db Check
    if user match session cookie and
    render Profile page if verified Or 
    Rediret unauthorized users page access
    """

    if "user" in session and session["user"] != "admin":
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        categories = mongo.db.categories.find()
        posts = list(mongo.db.posts.find({"created_by": session["user"]}))
        return render_template(
            "profile.html", username=username,
            isButton=True, categories=categories,
            posts=posts,  profile=True)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    """
    change user password: Usernames Hash the
    passwords and add to the mongo DB user
    collection, redirect to login page.
    """

    if "user" in session:
        form = ChangePassword(request.form)

        if request.method == 'POST' and form.validate():
            username = session["user"]
            user = mongo.db.users.find_one(
                {"username": session["user"]})

            if check_password_hash(
                    user["password"], form.old_password.data.lower()):
                update = {
                    "username": username.lower(),
                    "password": generate_password_hash(
                        form.password.data)
                    }

                mongo.db.users.update({"username": username}, update)
                flash("Password Update success", 'success')
                return redirect(request.referrer)

            else:
                flash("You Entered Incorrect Password", 'error')
                return redirect(request.referrer)
        else:
            flash("You Entered Incorrect Password", 'error')
            return redirect(request.referrer)

    else:
        flash("Register or Login", 'success')
        return redirect(url_for("logout"))


@app.route("/delete_profile", methods=["GET", "POST"])
def delete_profile():

    """
    Delete user rofile: Get input from DB and
    find username, check if username exists
    in db and ensure hashed password matches.
    Admin user Management, If admin in session
    Admin able to delete any existing user by
    Providing and confirming admin Password.
    """

    if "user" in session:
        form = DeleteUsersAdmin(request.form)
        form3 = DeleteUser(request.form)
        if request.method == "POST":
            username = session["user"]
            # Admin User management Delete a user account
            if username == "admin":
                delete_usr = mongo.db.users.find_one(
                    {"username": form.username.data.lower()})
                if delete_usr:
                    if check_password_hash(
                            username["password"], form.password.data.lower()):
                        mongo.db.users.remove(delete_usr)
                        flash("User was remover", 'success')
                        return redirect(request.referrer)
                    else:
                        flash("You Entered Incorrect Password", 'error')
                        return redirect(request.referrer)
                else:
                    flash(f"{username} not found")
                    return redirect(request.referrer)

            # Existing user delete own account
            elif username == session["user"]:
                user = mongo.db.users.find_one(
                    {"username": session["user"]})
                if check_password_hash(
                        user["password"],
                        form3.password.data.lower()):
                    mongo.db.users.remove(user)
                    flash("Good Buy", 'success')
                    return redirect(url_for("logout"))
                else:
                    flash("Incorrect Username and/or Password", 'error')
                    return redirect(request.referrer)

            else:
                flash("Incorrect Username and/or Password", 'error')
                return redirect(request.referrer)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/add_post", methods=("POST", "GET"))
def add_post():

    """
    Add new posts to the Mongo DB:
    Return all the categories form DB.
    Get File input and upoad to cloudinary.
    Get user input title and descriptions.
    Upload image to the Cloudinary API.
    inserts a single document into a collection.
    Create url for 1920p size image URL.
    Create url for 300p image thumblail URL.
    Render template with required parameters.              
    """

    form = UploadForm(CombinedMultiDict((request.files, request.form)))
    if "user" in session and session["user"] != "admin":
        categories = mongo.db.categories.find()

        if request.method == "POST" and form.validate():
            file = request.files['file']
            upload_result = None
            image = None
            image_small = None

            if file:
                folder = request.form.get("category").lower()
                upload_result = upload(file, folder=folder)
                image, options = cloudinary_url(
                    upload_result['public_id'],
                    format="jpg", crop="fill", width=1920)
                image_small, options = cloudinary_url(
                    upload_result['public_id'],
                    format="jpg", crop="fill", width=300)
                img_id = upload_result.get('public_id')
                URL_status = requests.get(image)

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
                    return redirect(request.url)

                else:
                    if URL_status.status_code != 200:
                        flash(f"Status code: {URL_status.status_code}")
                        flash("Post did not upload Try again", 'error')
                        return redirect(request.url)
                    else:
                        flash("Post failed upload", 'error')
                        flash("Please try again later", 'error')
                        return redirect(request.url)

            else:
                flash('File is required', 'error')
                return render_template(
                    "add_post.html", categories=categories,
                    post=True, form=form)

        else:
            return render_template(
                "add_post.html", categories=categories,
                post=True, form=form)
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):

    """
    Find existing post by id and get category.
    Update mongo existing post's Title and
    description only Create DB object for Update.
    Update a document into a "posts" collection.
    Render Template with required parameters.
    """

    if "user" in session:
        form2 = DeleteUser(request.form)
        form = EditForm(request.form)
        post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        categories = mongo.db.categories.find().sort("category_name", 1)
        if session["user"] == "admin":
            for key, value in post.items():
                if key == "created_by":
                    created_by = mongo.db.users.find_one({"username": value})

        for k, v in post.items():
            if k == "image":
                image = v
            elif k == "img_id":
                image_id = v
            elif k == "image_sm":
                image_sm = v
            elif k == "time_created":
                time_stamp = v
            elif k == "created_by":
                created = v

        if request.method == "POST" and form.validate():
            submit = {
                "category_name": request.form.get("category").lower(),
                "title": form.title.data.lower(),
                "description": form.description.data,
                "image": image,
                "image_sm": image_sm,
                "img_id": image_id,
                "created_by": created,
                "time_created": time_stamp
            }
            mongo.db.posts.update({"_id": ObjectId(post_id)}, submit)
            flash("post Successfully Updated", 'success')
            return redirect(request.referrer)

        if session["user"] != "admin":
            return render_template(
                "edit_post.html", categories=categories,
                post=post, form=form, form2=form2)
        else:
            return redirect(url_for("manage"))

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route("/delete_post/<post_id>")
def delete_post(post_id):

    """
    Delete post from mongo DB: Find post
    by id to extract image id, Get image
    url trom DB and permanently delete a
    single asset witch Invalidates
    cloudinary CDN cached of the asset
    """

    if "user" in session:
        posts = mongo.db.posts.find_one(
            {"_id": ObjectId(post_id)}, {"img_id": 1, "_id": 0})
        for x, y in posts.items():
            if x == "img_id":
                image_id = y

        try:
            cloudinary.uploader.destroy(image_id, invalidate='true')
            status = True
        except AttributeError:
            flash("file already was deleted", 'error')
            if session["user"] != "admin":
                return redirect(url_for("profile", username=session["user"]))
            else:
                return redirect(url_for("user_posts"))

        if status:
            mongo.db.posts.remove({"_id": ObjectId(post_id)})
            flash("Post was successluly deleted", 'success')
            if session["user"] != "admin":
                return redirect(url_for("profile", username=session["user"]))
            else:
                return redirect(url_for("user_posts"))

        else:
            flash("Failed to delete Image file", 'error')
            flash("Please try again later", 'error')
            if session["user"] != "admin":
                return redirect(url_for("profile", username=session["user"]))
            else:
                return redirect(url_for("user_posts"))

        if session["user"] != "admin":
            return redirect(url_for("profile", username=session["user"]))

        else:
            return redirect(url_for("user_posts"))
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))


@app.route('/new_category', methods=["GET", "POST"])
def new_category():

    """
    Create New category: If user in session
    is Administrator. Insert one documet
    into Mongo DB categories collection
    Return back to request route after insert.
    """

    if session["user"] == "admin":
        form = AddCategory(request.form)
        if request.method == "POST":
            add_category = form.category.data.lower()

            if not mongo.db.categories.find_one(
                    {"category_name": add_category}):
                try:
                    mongo.db.categories.insert_one(
                        {"category_name": add_category})
                    flash(f"New Category {add_category} was created", "success")
                    return redirect(request.referrer)

                except Exception:
                    add_category = form.category.data.lower()
                    flash(f"Failed to create category {add_category}", "error")
                    return redirect(request.referrer)
            else:
                flash(f"{add_category} category already exists", "error")
                return redirect(request.referrer)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route('/delete_category', methods=["GET", "POST"])
def delete_category():

    """
    Delete category: If user in session
    is Administrator. Delete one documet
    From Mongo DB categories collection
    Return back to request route after insert.
    Redirect non administrator accounts.
    """

    if session["user"] == "admin":
        if request.method == "POST":
            delete_category = request.form.get("category").lower()

            if mongo.db.categories.find_one(
                    {"category_name": delete_category}):
                try:
                    mongo.db.categories.remove(
                        {"category_name": delete_category})
                    flash(f"Category {delete_category} was deleted", "success")
                    return redirect(request.referrer)

                except Exception:
                    flash(f"Failed to remove category {delete_category}", "error")
                    return redirect(request.referrer)

            else:
                flash(f"{delete_category} category not exist", "error")
                return redirect(request.referrer)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route('/query', methods=["GET", "POST"])
def query():
    """
    Query function: Get "posts" collection
    form DB, enables Search by keyword, 
    username Or Query posts by category name.
    """

    categories = mongo.db.categories.find()
    posts = list(mongo.db.posts.find().sort('_id', -1))
    if "user" in session and session["user"] == "admin":
        url = "user_posts.html"
        title = "user_posts"
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
            posts = list(
                mongo.db.posts.find(
                    {"$and": [
                        {"category_name": category_name},
                        {"$text": {"$search": search}}
                        ]}))
            if len(posts) == 0:
                flash(
                    f"No results for {search}"
                    in "{category_name}", 'error')
                return render_template(
                    url, posts=posts, categories=categories, title=title)
            else:
                flash(
                    f"{len(posts)} Results for {search}"
                    in "{category_name}", 'success')
                return render_template(
                    url, posts=posts, categories=categories, title=title)

        # Search by Key word only
        elif search != "":
            posts = list(mongo.db.posts.find({"$text": {"$search": search}}))
            if len(posts) == 0:
                flash(f"No results for {search}", 'error')
                return render_template(
                    url, posts=posts, categories=categories, title=title)
            else:
                flash(f"{len(posts)} Results for {search}", 'success')
                return render_template(
                    url, posts=posts, categories=categories, title=title)

        # Search by category only
        elif category_name != not_selected and search == "":
            posts = list(mongo.db.posts.find({"category_name": category_name}))
            if len(posts) == 0:
                flash(f"No results for {category_name}", 'error')
                return render_template(
                    url, posts=posts, categories=categories, title=title)
            else:
                flash(f"{len(posts)} Results for category {category_name}", 'success')
                return render_template(
                    url, posts=posts, categories=categories, title=title)

        else:
            return render_template(
                url, posts=posts, categories=categories, title=title)
    else:
        return render_template(
            url, posts=posts, categories=categories, title=title)


@app.route('/edit_profile', methods=["GET", "POST"])
def edit_profile():

    """
    Manage users Profile: Find a session
    if Mondo Db, Check for session user
    Match and render template
    Else redirect to the login page if not.
    """

    if "user" in session and session["user"] != "admin":
        form3 = DeleteUser(request.form)
        form = ChangePassword(request.form)
        return render_template(
            "edit_profile.html", form=form, form3=form3, account=True)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route("/resset_index")
def resset_index():
    """
    Resseet Mongo Db Search Index.
    Drop Old index and create New.
    Redirect back ro request URL.
    Unauthorized redirect to logout function.
    """
    if session["user"] == "admin":
        mongo.db.posts.drop_indexes()
        mongo.db.posts.create_index([
            ("title", "text"), ("description", "text"),
            ("created_by", "text")])
        flash("Indexes was resset", "success")
        return redirect(request.referrer)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


# ==============ADMIN================
@app.route("/user_posts", methods=["GET", "POST"])
def user_posts():

    """
    Find Admin username from db Check
    if user match session cookie Render
    Admin Profile page if verified Or
    Rediret unauthorized users page access
    Create index for quering DB by keyword.
    """

    if "user" in session and session["user"] == "admin":
        categories = mongo.db.categories.find()
        posts = list(mongo.db.posts.find().sort('_id', -1))
        users = list(mongo.db.users.find())
        return render_template(
            "user_posts.html", categories=categories,
            posts=posts, users=users, admin=True)
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route("/manage", methods=["GET", "POST"])
def manage():

    """
    Manage users: Find a session user if
    Admin render template "manage"
    Else redirect to the login page if not.
    """
    if "user" in session and session["user"] == "admin":
        form = AddCategory(request.form)
        categories = mongo.db.categories.find()
        posts = list(mongo.db.posts.find().sort('_id', -1))
        users = list(mongo.db.user.find())
        form2 = DeleteUsersAdmin(request.form)
        form3 = ChangePassword(request.form)

        return render_template(
            "manage.html", posts=posts, categories=categories,
            users=users, form=form, form2=form2, form3=form3, manage=True)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route("/admin_posts/<post_id>", methods=["GET", "POST"])
def admin_posts(post_id):

    """
    Find existing post by id and get category.
    Update mongo existing post's Title and
    description only Create DB object for Update.
    Update a document into a "posts" collection.
    Render Template with required parameters.
    """

    if "user" in session and session["user"] == "admin":
        form2 = DeleteUsersAdmin(request.form)
        form = EditForm(request.form)
        post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        categories = mongo.db.categories.find().sort("category_name", 1)
        for key, value in post.items():
            if key == "created_by":
                created_by = mongo.db.users.find_one({"username": value})

        return render_template( 
            "admin_posts.html", categories=categories,
            post=post, form=form, form2=form2, created_by=created_by)

    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("logout"))


@app.route("/logout")
def logout():

    """
    remove the username from session if it's there
    """

    if "user" in session:
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash("Please log in or register", 'error')
        return redirect(url_for("login"))