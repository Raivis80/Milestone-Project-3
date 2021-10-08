from flask_wtf import FlaskForm
from wtforms import (
    Form, StringField, PasswordField,
    validators, TextAreaField)
from wtforms.validators import (
    InputRequired, Length, Regexp)
from flask_wtf.file import (
    FileField, FileAllowed, FileRequired)

# Regex help from here
# Regex Great source easy to understand https://www.youtube.com/watch?v=9RksQ5YT7FM


# Regisrter form
class RegisterForm(Form):
    username = StringField('Username', [
        validators.Regexp(r'^[\w]+$', message="A-Z 0-9_"),
        validators.InputRequired(),
        validators.Length(
            min=4, max=15, message="Lenght between 5 to 15 charters")])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


# Login Form
class LoginForm(Form):
    username = StringField('Username', [
        validators.Regexp(r'^[\w]+$', message="A-Z 0-9_"),
        validators.InputRequired(),
        validators.Length(
            min=5, max=15, message="Lenght between 5 to 15 charters")])
    password = PasswordField('Password', [
        validators.InputRequired(), validators.Length(
            min=5, max=10, message='Lenght between 5 to 10 charters')])


# Upload new post Form
class UploadForm(Form):
    title = StringField('Title', [
        validators.Regexp(r'^[\w\- ]*$', message="A-Z 0-9-_"),
        validators.InputRequired(), validators.Length(
            min=3, max=20, message='Title Lenght between 3 to 20 charters')])
    description = TextAreaField('Description', [
        InputRequired(), validators.length(
            min=20, max=500, message='Between 20 to 500 charters required')])
    file = FileField('image', validators=[
        FileRequired(),
        FileAllowed(
            ['png', 'jpg', 'jpeg', 'HEIC', 'RAW', 'HEVC', 'gif'],
            message='Unsupported file format')
    ])


# Edit post Form
class EditForm(Form):
    title = StringField('Title', [
        validators.Regexp(r'^[\w\- ]*$', message="A-Z 0-9-_"),
        validators.InputRequired(), validators.Length(
            min=3, max=20, message='Title Lenght between 3 to 20 charters')])
    description = TextAreaField('Description', [
        InputRequired(), validators.length(
            min=20, max=500, message='Between 20 to 500 charters required')])


# Delete Account user form
class DeleteUser(Form):
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


# Delete User account admin form
class DeleteUsersAdmin(Form):
    username = StringField('Username', [
        validators.Regexp(r'^[\w]+$', message="A-Z 0-9_"),
        validators.InputRequired(),
        validators.Length(
            min=4, max=15, message="Lenght between 5 to 15 charters")])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


# Add Category form
class AddCategory(Form):
    category = StringField('Category', [
        validators.Regexp(r'^[\w]+$', message="A-Z 0-9_"),
        validators.InputRequired(),
        validators.Length(
            min=4, max=15, message="Lenght between 5 to 15 charters")])


# Change Password form
class ChangePassword(Form):
    old_password = PasswordField('Password', [
        validators.InputRequired()
    ])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
