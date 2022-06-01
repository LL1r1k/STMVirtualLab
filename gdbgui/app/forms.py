from flask_wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import InputRequired

class LoginForm(Form):
    openid = StringField('openid', validators = [InputRequired()])
    remember_me = BooleanField('remember_me', default = False)