from datetime import datetime
from tracemalloc import start

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms.validators import ValidationError, DataRequired, EqualTo
from gdbgui.app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class AccessRequestForm(FlaskForm):
    start_at = StringField('Start at', validators=[DataRequired()])
    end_at = StringField('End at', validators=[DataRequired()])
    comment = StringField('Comment', validators=[validators.Length(max=100)])

    def validate_start_at(self, start_at):
        start_time = None
        cur_time = datetime.today()
        try:
            start_time = datetime.strptime(start_at.data, '%d-%m-%Y %H:%M:%S')
        except ValueError:
            raise ValidationError("Incorrect data format, should be DD-MM-YYYY HH:mm:s")
        if start_time < cur_time:
            raise ValidationError("Date can only be today or future date")

    def validate_end_at(self, end_at):
        end_time = None
        start_time = None
        try:
            end_time = datetime.strptime(end_at.data, '%d-%m-%Y %H:%M:%S')
        except ValueError:
            raise ValidationError("Incorrect date format, should be DD-MM-YYYY HH:mm:s")
        try:
            start_time = datetime.strptime(self.start_at.data, '%d-%m-%Y %H:%M:%S')
        except Exception: 
            return
        if end_time < start_time:
            raise ValidationError("Start time must be earlier than cat time")
    
    submit = SubmitField('Запросить доступ')

