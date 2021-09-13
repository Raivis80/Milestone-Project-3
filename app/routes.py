from app import app
from flask import Flask, render_template

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gallery')
def galery():
    return render_template('gallery.html')


@app.route('/user')
def user():
    return render_template('user.html')

