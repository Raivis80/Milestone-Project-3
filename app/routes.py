import os
from app import app, mongo
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId


@app.route('/')
@app.route('/index')
def index():
    users = mongo.db.users.find()
    return render_template('index.html', users=users)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        else:
            register = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            mongo.db.users.insert_one(register)
            flash("User registered successfuly")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if check_password_hash(
                existing_user["password"], request.form.get("password")):
            session["user"] = request.form.get("username").lower()
            flash("Welcome, {}".format(
                request.form.get("username")))
            return redirect(url_for(
                "profile", username=session["user"]))
           
        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/gallery')
def galery():
    return render_template('gallery.html')


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Get session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('user')
    return redirect(url_for('index'))