from flask import render_template, flash, redirect, url_for
from gdbgui.backend import app
from gdbgui.app.forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    return render_template('index.html', title='Home', user=user)


    