from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    remaining_hours = db.Column(db.Float, default=0)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assigned_servers = db.relationship('Server', secondary='user_server_assignments',
                                     backref=db.backref('assigned_users', lazy='dynamic'),
                                     lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# User-Server association table
user_server_assignments = db.Table('user_server_assignments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('server_id', db.Integer, db.ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True)
)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))
    servers = db.relationship('Server', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Server(db.Model):
    __tablename__ = 'servers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    connection_address = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_status_change = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='server', lazy='dynamic', cascade='all, delete-orphan')

    def toggle_status(self):
        self.is_active = not self.is_active
        self.last_status_change = datetime.utcnow()
        return self.is_active

    def __repr__(self):
        return f'<Server {self.name}>'

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # Duration in hours
    is_demo = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Session {self.id}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    hours_purchased = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(64), nullable=False)
    transaction_id = db.Column(db.String(128), unique=True)
    status = db.Column(db.String(32), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}>' 