from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectMultipleField
from wtforms.validators import ValidationError, DataRequired, EqualTo, Length

import sqlalchemy as sa

from app import db
from app.models import User


class LoginForm(FlaskForm): #implements login options
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm): #implements registration options
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')

    def validate_username(self, username): #checks if the username is possible with the database
        user = db.session.scalar(
            sa.select(User).where(User.username == username.data) #from the User table
        )
        if user is not None: #no double usernames in registration
            raise ValidationError('Please use a different username.')


class PrivateMessageForm(FlaskForm): #implements personal message options
    body = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send')


class GroupChatForm(FlaskForm): #implements adding groupchat options
    name = StringField('Group name', validators=[DataRequired()])
    members = SelectMultipleField('Members', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create group')


class GroupMessageForm(FlaskForm): #implements sending groupchats options
    body = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send')
