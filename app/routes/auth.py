from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User
from app import db
from datetime import datetime
<<<<<<< HEAD

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(next_page or url_for('admin.admin_dashboard'))
            return redirect(next_page or url_for('main.user_dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')
=======
from app.models.server import Server
from flask import current_app
from app.utils.eve_ng_api import EveNGAPI
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from werkzeug.urls import url_parse

auth = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.is_active:
            flash('Your account is inactive. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Sign In', form=form)
>>>>>>> master

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
<<<<<<< HEAD
        return redirect(url_for('main.user_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
=======
        return redirect(url_for('main.index'))
    
    form = FlaskForm()  # Create a basic form for CSRF protection
    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', username)
>>>>>>> master
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
<<<<<<< HEAD
            flash('Email address already exists', 'error')
            return redirect(url_for('auth.register'))
        
        new_user = User(
            username=username,
            email=email,
            is_admin=False
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration. Please try again.', 'error')
    
    return render_template('auth/register.html')
=======
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, email=email, name=name)
        user.set_password(password)
        
        try:
            # Create user in our database only
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration failed: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html', form=form)
>>>>>>> master

@auth.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('main.index'))
