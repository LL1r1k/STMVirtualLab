from datetime import datetime

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from gdbgui.backend import app, db
from gdbgui.app.forms import LoginForm, RegistrationForm, AccessRequestForm
from gdbgui.app.models import User, Role, Access_Request

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/access_request', methods=['GET', 'POST'])
@login_required
def access_request():
    form = AccessRequestForm()
    if form.validate_on_submit():

        start_time = datetime.strptime(form.start_at.data, '%d-%m-%Y %H:%M:%S')
        end_time = datetime.strptime(form.end_at.data, '%d-%m-%Y %H:%M:%S')
        req = Access_Request(comment=form.comment.data, time_start=start_time, time_end=end_time, status="Created", author=current_user)

        db.session.add(req)
        db.session.commit()
        flash('Запрос отправлен')
        return redirect(url_for('index'))
    return render_template('access_request.html', title='Запрос доступа', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)

        user_role = Role.query.filter_by(name="User").first()
        user.set_role(user_role)

        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)