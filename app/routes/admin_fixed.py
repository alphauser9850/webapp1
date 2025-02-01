from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Category, Server, Session
from app import db
from werkzeug.security import generate_password_hash
from datetime import datetime
from functools import wraps
from flask_wtf import FlaskForm

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    form = FlaskForm()
    if not form.validate():
        flash('Invalid request.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_active = request.form.get('is_active') == 'true'
    is_admin = request.form.get('is_admin') == 'true'
    remaining_hours = float(request.form.get('remaining_hours', 0))
    
    if not username or not email or not password:
        flash('Username, email and password are required.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        flash('Username or email already exists.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user = User(
        username=username,
        email=email,
        is_active=is_active,
        is_admin=is_admin,
        remaining_hours=remaining_hours
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        flash('User created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating user.', 'danger')
    
    return redirect(url_for('admin.manage_users'))