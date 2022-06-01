from datetime import datetime

from gdbgui.backend import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from gdbgui.backend import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    acess_requests = db.relationship('Access_Request', backref='author', lazy='dynamic')
    roles = db.relationship('Role', secondary='user_roles')

    def __repr__(self):
        return '<User {}>'.format(self.username) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return '<Role {}>'.format(self.name) 

class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

    def __repr__(self):
        return '<UserRoles user: {} role: {}>'.format(self.user_id, self.role_id) 

class Access_Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(140))
    status = db.Column(db.String(140))
    time_start = db.Column(db.DateTime)
    time_end = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Access_Request {}>'.format(self.user_id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))