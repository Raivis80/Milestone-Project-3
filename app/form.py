from flask_wtf import FlaskForm
from wtforms import (
    Form, StringField, PasswordField,
     validators, SubmitField, TextAreaField)
from wtforms.validators import InputRequired, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired


# Regisrter form 
class RegisterForm(Form):
    username = StringField('Username', [
        validators.InputRequired(),
        validators.Length(min=4, max=15,
        message="Lenght between 5 to 15 charters")])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


# Login Form
class LoginForm(Form):
    username = StringField('Username', [
        validators.InputRequired(),
        validators.Length(min=5, max=15,
        message="Lenght between 5 to 15 charters")])
    password = PasswordField('Password', [
        validators.InputRequired(), validators.Length(
            min=5, max=10, message='Lenght between 5 to 10 charters')])


# Upload new post Form
class UploadForm(Form):
    title = StringField('Title', [
        validators.InputRequired(), validators.Length(
            min=3, max=10, message='Title Lenght between 3 to 10 charters')])
    description = TextAreaField('Description', [
        InputRequired(), validators.length(
            min=20, max=200, message='Between 20 to 200 charters required')])
    file = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'],  message='Wrong file type jpg, png Images only!')
    ])


# edit post Form
class EditForm(Form):
    title = StringField('Title', [
        validators.InputRequired(), validators.Length(
            min=3, max=10, message='Title Lenght between 3 to 10 charters')])
    description = TextAreaField('Description', [
        InputRequired(), validators.length(
            min=20, max=200, message='Between 20 to 200 charters required')])


# Delete form 
class DeleteUser(Form):
    username = StringField('Username', [
        validators.InputRequired(),
        validators.Length(min=4, max=15,
        message="Lenght between 5 to 15 charters")])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


# Add Category form 
class AddCategory(Form):
    category = StringField('Category', [
        validators.InputRequired(),
        validators.Length(min=4, max=15,
        message="Lenght between 5 to 15 charters")])
