from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
<<<<<<< HEAD
from app.models import User, Category, Server, Session, Ticket
from app.models.physical_server import PhysicalServer
=======
from app.models import User, Category, Server, Session, FormSubmission
>>>>>>> master
from app import db
from werkzeug.security import generate_password_hash
from datetime import datetime
from functools import wraps
<<<<<<< HEAD
import subprocess
import platform
import requests
from app.utils.server_monitor import ServerMonitor
from app.utils.system_monitor import SystemMonitor
=======
from flask_wtf import FlaskForm
>>>>>>> master

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
<<<<<<< HEAD
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    active_sessions = Session.query.filter_by(end_time=None).count()
    categories = Category.query.all()
    recent_sessions = Session.query.order_by(Session.start_time.desc()).limit(10).all()
    current_time = datetime.utcnow()
    
    # Calculate average session duration
    completed_sessions = Session.query.filter(Session.end_time != None).all()
    total_duration = 0
    if completed_sessions:
        for session in completed_sessions:
            duration = (session.end_time - session.start_time).total_seconds() / 3600
            total_duration += duration
        avg_duration = round(total_duration / len(completed_sessions), 1)
    else:
        avg_duration = 0
    
    # Calculate total hours used
    total_hours = round(total_duration, 1)
    
    # Find most active category
    category_sessions = {}
    for category in categories:
        session_count = 0
        for server in category.servers:
            session_count += Session.query.filter_by(server_id=server.id).count()
        category_sessions[category.name] = session_count
    
    most_active_category = max(category_sessions.items(), key=lambda x: x[1])[0] if category_sessions else "None"
    
    # Calculate peak usage time (in 2-hour blocks)
    hour_counts = {i: 0 for i in range(0, 24, 2)}
    for session in completed_sessions:
        hour = session.start_time.hour
        block = (hour // 2) * 2
        hour_counts[block] += 1
    
    peak_hour_block = max(hour_counts.items(), key=lambda x: x[1])[0]
    peak_time = f"{peak_hour_block:02d}-{(peak_hour_block + 2):02d}"
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         active_sessions=active_sessions,
                         categories=categories,
                         recent_sessions=recent_sessions,
                         avg_session_duration=avg_duration,
                         total_hours_used=total_hours,
                         most_active_category=most_active_category,
                         peak_usage_time=peak_time,
                         current_time=current_time,
                         datetime=datetime)
=======
    # Get current time
    current_time = datetime.utcnow()
    
    # Get basic stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    active_sessions = Session.query.filter_by(end_time=None).count()
    
    # Calculate average session duration
    completed_sessions = Session.query.filter(Session.end_time != None).all()
    if completed_sessions:
        total_duration = sum((s.end_time - s.start_time).total_seconds() / 3600 for s in completed_sessions)
        avg_session_duration = total_duration / len(completed_sessions)
    else:
        avg_session_duration = 0
    
    # Calculate total hours used
    total_hours_used = sum(s.duration or 0 for s in completed_sessions)
    
    # Get most active category
    category_sessions = {}
    for session in Session.query.all():
        category_name = session.server.category.name
        category_sessions[category_name] = category_sessions.get(category_name, 0) + 1
    most_active_category = max(category_sessions.items(), key=lambda x: x[1])[0] if category_sessions else "None"
    
    # Get recent form submissions
    form_submissions = FormSubmission.query.order_by(FormSubmission.submitted_at.desc()).limit(10).all()
    
    return render_template('admin/admin_dashboard.html',
                         current_time=current_time,
                         total_users=total_users,
                         active_users=active_users,
                         active_sessions=active_sessions,
                         avg_session_duration=avg_session_duration,
                         total_hours_used=total_hours_used,
                         most_active_category=most_active_category,
                         form_submissions=form_submissions)
>>>>>>> master

@admin.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    categories = Category.query.all()
<<<<<<< HEAD
    return render_template('admin/users.html', 
                         users=users,
                         categories=categories)
=======
    form = FlaskForm()  # For CSRF protection
    return render_template('admin/users.html', users=users, categories=categories, form=form)
>>>>>>> master

@admin.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
<<<<<<< HEAD
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
    user.password_hash = generate_password_hash(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        flash('User created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating user.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin.route('/users/<int:id>/edit', methods=['POST'])
=======
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        is_active = data.get('is_active', True)
        is_admin = data.get('is_admin', False)
        remaining_hours = float(data.get('remaining_hours', 0))
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email and password are required.'}), 400
        
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Username or email already exists.'}), 400
        
        user = User(
            username=username,
            email=email,
            is_active=is_active,
            is_admin=is_admin,
            remaining_hours=remaining_hours
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f'User created successfully: {username}')
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'remaining_hours': user.remaining_hours
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating user: {str(e)}')
        return jsonify({'error': 'Error creating user.'}), 500

@admin.route('/users/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
        'is_admin': user.is_admin,
        'remaining_hours': user.remaining_hours,
        'assigned_servers': [server.id for server in user.assigned_servers]
    })

@admin.route('/users/<int:id>/edit', methods=['PUT'])
>>>>>>> master
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
<<<<<<< HEAD
    if user.is_admin and user != current_user:
        flash('You cannot edit another admin user.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    is_active = request.form.get('is_active') == 'on'
    is_admin = request.form.get('is_admin') == 'on'
    remaining_hours = request.form.get('remaining_hours', type=float)
    
    if username and email:
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).filter(User.id != id).first()
        
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        user.username = username
        user.email = email
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        user.is_active = is_active
        if remaining_hours is not None:
            user.remaining_hours = remaining_hours
        if current_user.is_admin and current_user.id != user.id:
            user.is_admin = is_admin
        
        try:
            db.session.commit()
            flash('User updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating user.', 'danger')
    else:
        flash('Username and email are required.', 'danger')
    
    return redirect(url_for('admin.manage_users'))
=======
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    is_active = request.json.get('is_active')
    is_admin = request.json.get('is_admin')
    remaining_hours = request.json.get('remaining_hours')
    
    if username != user.username:
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
    
    if email != user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
    
    user.username = username
    user.email = email
    if password:
        user.set_password(password)
    user.is_active = is_active
    user.is_admin = is_admin
    user.remaining_hours = remaining_hours
    
    try:
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating user'}), 500

@admin.route('/users/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_user(id):
    if current_user.id == id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error deleting user'}), 500

@admin.route('/users/<int:id>/add-hours', methods=['POST'])
def add_user_hours(id):
    try:
        user = User.query.get_or_404(id)
        data = request.get_json()
        
        if not data or 'hours' not in data:
            return jsonify({'error': 'No hours provided'}), 400
            
        hours = float(data['hours'])
        user.remaining_hours += hours
        db.session.commit()
        
        return jsonify({
            'message': 'Hours added successfully',
            'new_balance': user.remaining_hours
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding hours to user {id}: {str(e)}")
        return jsonify({'error': 'Failed to add hours'}), 500
>>>>>>> master

@admin.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
<<<<<<< HEAD
    user = User.query.get_or_404(id)
    
    if user.is_admin:
        return jsonify({'error': 'Cannot toggle admin user status'}), 400
    
    user.is_active = not user.is_active
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'is_active': user.is_active,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error toggling user status'}), 500

@admin.route('/users/<int:id>/add-hours', methods=['POST'])
@login_required
@admin_required
def add_user_hours(id):
    user = User.query.get_or_404(id)
    hours = request.form.get('hours', type=float)
    
    if not hours or hours <= 0:
        flash('Please enter a valid number of hours.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.remaining_hours += hours
    try:
        db.session.commit()
        flash(f'Successfully added {hours} hours to {user.username}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding hours to user.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    if user.is_admin:
        flash('Cannot delete admin users.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    try:
        # Delete associated sessions first
        Session.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

=======
    try:
        user = User.query.get_or_404(id)
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling user status: {str(e)}')
        return jsonify({'error': 'Error toggling user status'}), 500

>>>>>>> master
@admin.route('/users/<int:id>/assign-servers', methods=['POST'])
@login_required
@admin_required
def assign_user_servers(id):
<<<<<<< HEAD
    user = User.query.get_or_404(id)
    server_ids = request.form.getlist('server_ids')
    
    try:
        # Clear existing assignments first
        user.assigned_servers = []
        
        # Add new assignments
        if server_ids:
            servers = Server.query.filter(Server.id.in_(server_ids)).all()
            user.assigned_servers.extend(servers)
        
        db.session.commit()
        flash('Server assignments updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating server assignments.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin.route('/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin.route('/categories/create', methods=['POST'])
@login_required
@admin_required
def create_category():
    name = request.form.get('name')
    description = request.form.get('description')
    level = request.form.get('level')
    
    if not name or not level:
        flash('Name and level are required.', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        flash('A category with this name already exists.', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    category = Category(name=name, description=description, level=level)
    try:
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating category.', 'danger')
    
    return redirect(url_for('admin.manage_categories'))

@admin.route('/categories/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('name')
    description = request.form.get('description')
    level = request.form.get('level')
    
    if not name or not level:
        flash('Name and level are required.', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    existing_category = Category.query.filter(
        Category.name == name,
        Category.id != id
    ).first()
    
    if existing_category:
        flash('A category with this name already exists.', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    category.name = name
    category.description = description
    category.level = level
    
    try:
        db.session.commit()
        flash('Category updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating category.', 'danger')
    
    return redirect(url_for('admin.manage_categories'))

@admin.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    if category.servers:
        flash('Cannot delete category that has servers. Please remove or reassign servers first.', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category.', 'danger')
    
    return redirect(url_for('admin.manage_categories'))

@admin.route('/categories/<int:id>/copy', methods=['POST'])
@login_required
@admin_required
def copy_category(id):
    category = Category.query.get_or_404(id)
    
    # Create a copy of the category with "(Copy)" appended to the name
    new_name = f"{category.name} (Copy)"
    new_category = Category(
        name=new_name,
        description=category.description,
        level=category.level
    )
    
    try:
        db.session.add(new_category)
        db.session.commit()
        flash('Category copied successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error copying category.', 'danger')
    
    return redirect(url_for('admin.manage_categories'))
=======
    try:
        user = User.query.get_or_404(id)
        data = request.get_json()
        
        if not data or 'server_ids' not in data:
            return jsonify({'error': 'No server IDs provided'}), 400
            
        server_ids = data['server_ids']
        servers = Server.query.filter(Server.id.in_(server_ids)).all()
        
        # Clear existing assignments and add new ones
        user.assigned_servers = servers
        db.session.commit()
        
        return jsonify({'message': 'Servers assigned successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning servers to user {id}: {str(e)}")
        return jsonify({'error': 'Failed to assign servers'}), 500
>>>>>>> master

@admin.route('/servers')
@login_required
@admin_required
def manage_servers():
    servers = Server.query.all()
    categories = Category.query.all()
    return render_template('admin/servers.html', servers=servers, categories=categories)

@admin.route('/servers/create', methods=['POST'])
@login_required
@admin_required
def create_server():
<<<<<<< HEAD
    name = request.form.get('name')
    ip_address = request.form.get('ip_address')
    category_id = request.form.get('category_id')
    
    if not name or not ip_address or not category_id:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.manage_servers'))
    
    existing_server = Server.query.filter(
        (Server.name == name) | (Server.ip_address == ip_address)
    ).first()
    
    if existing_server:
        flash('A server with this name or IP address already exists.', 'danger')
        return redirect(url_for('admin.manage_servers'))
    
    server = Server(
        name=name,
        ip_address=ip_address,
        category_id=category_id
    )
    
    try:
        db.session.add(server)
        db.session.commit()
        flash('Server created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating server.', 'danger')
    
    return redirect(url_for('admin.manage_servers'))

@admin.route('/servers/<int:id>/edit', methods=['POST'])
=======
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        name = data.get('name')
        connection_address = data.get('connection_address')
        category_id = data.get('category_id')
        
        if not all([name, connection_address, category_id]):
            return jsonify({'error': 'All fields are required.'}), 400
        
        server = Server(
            name=name,
            connection_address=connection_address,
            category_id=category_id,
            is_active=True
        )
        
        db.session.add(server)
        db.session.commit()
        
        return jsonify({
            'message': 'Server created successfully',
            'server': {
                'id': server.id,
                'name': server.name,
                'connection_address': server.connection_address,
                'category_id': server.category_id,
                'is_active': server.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating server: {str(e)}')
        return jsonify({'error': 'Error creating server'}), 500

@admin.route('/servers/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_server(id):
    server = Server.query.get_or_404(id)
    return jsonify({
        'id': server.id,
        'name': server.name,
        'connection_address': server.connection_address,
        'category_id': server.category_id,
        'is_active': server.is_active
    })

@admin.route('/servers/<int:id>/edit', methods=['PUT'])
>>>>>>> master
@login_required
@admin_required
def edit_server(id):
    server = Server.query.get_or_404(id)
<<<<<<< HEAD
    name = request.form.get('name')
    ip_address = request.form.get('ip_address')
    category_id = request.form.get('category_id')
    is_active = request.form.get('is_active') == 'true'
    
    if not name or not ip_address or not category_id:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.manage_servers'))
    
    existing_server = Server.query.filter(
        (Server.name == name) | (Server.ip_address == ip_address),
        Server.id != id
    ).first()
    
    if existing_server:
        flash('A server with this name or IP address already exists.', 'danger')
        return redirect(url_for('admin.manage_servers'))
    
    server.name = name
    server.ip_address = ip_address
    server.category_id = category_id
    server.is_active = is_active
    
    try:
        db.session.commit()
        flash('Server updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating server.', 'danger')
    
    return redirect(url_for('admin.manage_servers'))

@admin.route('/servers/<int:id>/copy', methods=['POST'])
@login_required
@admin_required
def copy_server(id):
    server = Server.query.get_or_404(id)
    
    # Create a copy of the server with "(Copy)" appended to the name
    new_name = f"{server.name} (Copy)"
    new_server = Server(
        name=new_name,
        ip_address=server.ip_address,
        category_id=server.category_id,
        is_active=server.is_active
    )
    
    try:
        db.session.add(new_server)
        db.session.commit()
        flash('Server copied successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error copying server.', 'danger')
    
    return redirect(url_for('admin.manage_servers'))

@admin.route('/servers/<int:id>/delete', methods=['POST'])
=======
    
    data = request.get_json()
    server.name = data.get('name', server.name)
    server.connection_address = data.get('connection_address', server.connection_address)
    server.category_id = data.get('category_id', server.category_id)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Server updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating server'}), 500

@admin.route('/servers/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_server(id):
    server = Server.query.get_or_404(id)
    
    try:
        new_status = server.toggle_status()
        db.session.commit()
        return jsonify({
            'message': f'Server {"activated" if new_status else "deactivated"} successfully',
            'is_active': new_status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error toggling server status'}), 500

@admin.route('/servers/<int:id>/toggle-status', methods=['POST'])
def toggle_server_status(id):
    try:
        server = Server.query.get_or_404(id)
        server.is_active = not server.is_active
        db.session.commit()
        
        return jsonify({
            'message': f"Server {'activated' if server.is_active else 'deactivated'} successfully",
            'is_active': server.is_active
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling server {id} status: {str(e)}")
        return jsonify({'error': 'Failed to toggle server status'}), 500

@admin.route('/servers/<int:id>/delete', methods=['DELETE'])
>>>>>>> master
@login_required
@admin_required
def delete_server(id):
    server = Server.query.get_or_404(id)
    
    try:
<<<<<<< HEAD
        # Delete associated sessions first
        Session.query.filter_by(server_id=server.id).delete()
        db.session.delete(server)
        db.session.commit()
        flash('Lab environment deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting lab environment.', 'danger')
    
    return redirect(url_for('admin.manage_servers'))
=======
        db.session.delete(server)
        db.session.commit()
        return jsonify({'message': 'Server deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error deleting server'}), 500

@admin.route('/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin.route('/categories/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_category(id):
    try:
        category = Category.query.get_or_404(id)
        return jsonify({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'level': category.level
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/categories/create', methods=['POST'])
@login_required
@admin_required
def create_category():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        name = data.get('name')
        description = data.get('description')
        level = data.get('level')
        
        if not name:
            return jsonify({'error': 'Category name is required'}), 400
            
        # Check if category with same name exists
        if Category.query.filter_by(name=name).first():
            return jsonify({'error': 'Category with this name already exists'}), 400
        
        category = Category(
            name=name,
            description=description,
            level=level
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'level': category.level
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/categories/<int:id>/edit', methods=['PUT'])
@login_required
@admin_required
def edit_category(id):
    try:
        category = Category.query.get_or_404(id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Category name is required'}), 400
            
        # Check if another category with this name exists
        if Category.query.filter(Category.id != id, Category.name == name).first():
            return jsonify({'error': 'Category with this name already exists'}), 400
            
        category.name = name
        category.description = data.get('description', '')
        category.level = data.get('level')
            
        db.session.commit()
        return jsonify({
            'message': 'Category updated successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'level': category.level
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/categories/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_category(id):
    try:
        category = Category.query.get_or_404(id)
        
        # Check if category has any servers
        if category.servers:
            return jsonify({'error': 'Cannot delete category with associated servers'}), 400
            
        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
>>>>>>> master

@admin.route('/sessions')
@login_required
@admin_required
def manage_sessions():
    sessions = Session.query.order_by(Session.start_time.desc()).all()
<<<<<<< HEAD
    return render_template('admin/sessions.html', sessions=sessions)

@admin.route('/sessions/<int:id>/end', methods=['POST'])
@login_required
@admin_required
def end_session(id):
    session = Session.query.get_or_404(id)
    
    try:
        # Force end the session
        session.end_time = datetime.utcnow()
        session.is_active = False
        
        # Try to terminate VNC session
        try:
            import subprocess
            # Kill any VNC server process running for this session
            subprocess.run(['pkill', '-f', f'websockify.*{session.server.ip_address}:6080'], check=False)
            subprocess.run(['pkill', '-f', f'Xtightvnc.*{session.server.ip_address}'], check=False)
        except Exception as e:
            print(f"Error terminating VNC session: {str(e)}")
        
        db.session.commit()
        flash('Session ended successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error ending session.', 'danger')
    
    return redirect(url_for('admin.manage_sessions'))
=======
    servers = Server.query.all()
    return render_template('admin/sessions.html', sessions=sessions, servers=servers)

@admin.route('/sessions/<int:id>/terminate', methods=['POST'])
@login_required
@admin_required
def terminate_session(id):
    session = Session.query.get_or_404(id)
    
    try:
        if session.is_active:
            session.end_time = datetime.utcnow()
            session.is_active = False
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Session terminated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Session is already terminated'
            })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error terminating session: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error terminating session'
        }), 500
>>>>>>> master

@admin.route('/sessions/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_session(id):
    session = Session.query.get_or_404(id)
    
    try:
        # Force end the session first if it's still active
<<<<<<< HEAD
        if session.end_time is None:
            session.end_time = datetime.utcnow()
            session.is_active = False
            
            # Try to terminate VNC session
            try:
                import subprocess
                subprocess.run(['pkill', '-f', f'websockify.*{session.server.ip_address}:6080'], check=False)
                subprocess.run(['pkill', '-f', f'Xtightvnc.*{session.server.ip_address}'], check=False)
            except Exception as e:
                print(f"Error terminating VNC session: {str(e)}")
=======
        if session.is_active:
            session.end_time = datetime.utcnow()
            session.is_active = False
>>>>>>> master
        
        # Delete the session
        db.session.delete(session)
        db.session.commit()
<<<<<<< HEAD
        flash('Session deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting session.', 'danger')
    
    return redirect(url_for('admin.manage_sessions'))

@admin.route('/dashboard/stats')
@login_required
@admin_required
def get_dashboard_stats():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    active_sessions = Session.query.filter_by(end_time=None, is_active=True).count()
    categories = Category.query.all()
    recent_sessions = Session.query.order_by(Session.start_time.desc()).limit(10).all()
    current_time = datetime.utcnow()
    
    # Calculate average session duration
    completed_sessions = Session.query.filter(Session.end_time != None).all()
    total_duration = 0
    if completed_sessions:
        for session in completed_sessions:
            duration = (session.end_time - session.start_time).total_seconds() / 3600
            total_duration += duration
        avg_duration = round(total_duration / len(completed_sessions), 1)
    else:
        avg_duration = 0
    
    # Calculate total hours used
    total_hours = round(total_duration, 1)
    
    # Find most active category
    category_sessions = {}
    for category in categories:
        session_count = 0
        for server in category.servers:
            session_count += Session.query.filter_by(server_id=server.id).count()
        category_sessions[category.name] = session_count
    
    most_active_category = max(category_sessions.items(), key=lambda x: x[1])[0] if category_sessions else "None"
    
    # Calculate peak usage time (in 2-hour blocks)
    hour_counts = {i: 0 for i in range(0, 24, 2)}
    for session in completed_sessions:
        hour = session.start_time.hour
        block = (hour // 2) * 2
        hour_counts[block] += 1
    
    peak_hour_block = max(hour_counts.items(), key=lambda x: x[1])[0]
    peak_time = f"{peak_hour_block:02d}-{(peak_hour_block + 2):02d}"
    
    # Format category stats
    category_stats = []
    for category in categories:
        total_servers = len(category.servers)
        active_servers = len([s for s in category.servers if s.is_active])
        active_percentage = round((active_servers / total_servers * 100) if total_servers > 0 else 0)
        category_stats.append({
            'name': category.name,
            'level': category.level,
            'total_servers': total_servers,
            'active_servers': active_servers,
            'active_percentage': active_percentage
        })

    # Format recent sessions
    recent_sessions_data = []
    for session in recent_sessions:
        duration = 0
        if session.end_time:
            duration = round((session.end_time - session.start_time).total_seconds() / 3600, 1)
        else:
            duration = round((datetime.utcnow() - session.start_time).total_seconds() / 3600, 1)
        
        recent_sessions_data.append({
            'id': session.id,
            'username': session.user.username,
            'user_initials': session.user.username[:2].upper(),
            'server_name': session.server.name,
            'category_name': session.server.category.name,
            'is_active': session.end_time is None and session.is_active,
            'duration': duration,
            'start_time': session.start_time.strftime('%Y-%m-%d %H:%M')
        })

    # Format the current time in a way that works in all browsers
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'active_sessions': active_sessions,
        'avg_session_duration': avg_duration,
        'total_hours_used': total_hours,
        'most_active_category': most_active_category,
        'peak_usage_time': peak_time,
        'current_time': current_time_str,
        'category_stats': category_stats,
        'recent_sessions': recent_sessions_data
    })

@admin.route('/check_server_status')
@login_required
@admin_required
def check_server_status():
    ip = request.args.get('ip')
    if not ip:
        return jsonify({'error': 'IP address required'}), 400

    try:
        # Initialize server monitor
        monitor = ServerMonitor(current_app)
        
        # Check if this is a hypervisor
        hypervisor = None
        for h in monitor.hypervisors.values():
            if h['ip'] == ip:
                hypervisor = h
                break
        
        if hypervisor:
            # Get hypervisor status
            status = monitor.check_hypervisor_status(hypervisor)
            return jsonify(status)
        else:
            # Check regular VM server
            online = monitor.check_server_ping(ip)
            return jsonify({
                'online': online,
                'cpu_usage': 0,
                'memory_usage': 0
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/system_health')
@login_required
@admin_required
def get_system_health():
    """Get real-time system health metrics"""
    return jsonify(SystemMonitor.get_system_health())

@admin.route('/physical-servers')
@login_required
@admin_required
def manage_physical_servers():
    servers = PhysicalServer.query.all()
    return jsonify([{
        'id': server.id,
        'name': server.name,
        'ip_address': server.ip_address,
        'port': server.port,
        'server_type': server.server_type,
        'is_active': server.is_active
    } for server in servers])

@admin.route('/physical-servers/create', methods=['POST'])
@login_required
@admin_required
def create_physical_server():
    data = request.get_json()
    
    if not all(key in data for key in ['name', 'ip_address', 'port', 'server_type']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    existing_server = PhysicalServer.query.filter_by(ip_address=data['ip_address']).first()
    if existing_server:
        return jsonify({'error': 'Server with this IP already exists'}), 400
        
    server = PhysicalServer(
        name=data['name'],
        ip_address=data['ip_address'],
        port=data['port'],
        server_type=data['server_type'],
        is_active=data.get('is_active', True)
    )
    
    try:
        db.session.add(server)
        db.session.commit()
        return jsonify({
            'id': server.id,
            'name': server.name,
            'ip_address': server.ip_address,
            'port': server.port,
            'server_type': server.server_type,
            'is_active': server.is_active
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/physical-servers/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_physical_server(id):
    server = PhysicalServer.query.get_or_404(id)
    data = request.get_json()
    
    if 'ip_address' in data and data['ip_address'] != server.ip_address:
        existing_server = PhysicalServer.query.filter_by(ip_address=data['ip_address']).first()
        if existing_server:
            return jsonify({'error': 'Server with this IP already exists'}), 400
    
    try:
        for key in ['name', 'ip_address', 'port', 'server_type', 'is_active']:
            if key in data:
                setattr(server, key, data[key])
        
        db.session.commit()
        return jsonify({
            'id': server.id,
            'name': server.name,
            'ip_address': server.ip_address,
            'port': server.port,
            'server_type': server.server_type,
            'is_active': server.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/physical-servers/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_physical_server(id):
    server = PhysicalServer.query.get_or_404(id)
    try:
        db.session.delete(server)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/check-new-tickets')
@login_required
@admin_required
def check_new_tickets():
    """Check for new unviewed tickets."""
    new_tickets = Ticket.query.filter_by(admin_viewed=False).count()
    return jsonify({
        'count': new_tickets,
        'has_new': new_tickets > 0
    })

@admin.route('/sessions/delete-multiple', methods=['POST'])
@login_required
@admin_required
def delete_multiple_sessions():
    session_ids = request.form.getlist('session_ids[]')
    if not session_ids:
        flash('No sessions selected for deletion.', 'warning')
        return redirect(url_for('admin.manage_sessions'))
    
    try:
        # Only delete ended sessions
        sessions = Session.query.filter(
            Session.id.in_(session_ids),
            Session.end_time.isnot(None)
        ).all()
        
        for session in sessions:
            db.session.delete(session)
        
        db.session.commit()
        flash(f'Successfully deleted {len(sessions)} session(s).', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting sessions.', 'danger')
    
    return redirect(url_for('admin.manage_sessions'))
=======
        return jsonify({
            'success': True,
            'message': 'Session deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting session: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error deleting session'
        }), 500
>>>>>>> master

@admin.route('/sessions/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_sessions():
    try:
<<<<<<< HEAD
        # Find all stuck sessions (active but with future start times)
        stuck_sessions = Session.query.filter(
            Session.end_time.is_(None),
            Session.is_active == True,
            Session.start_time > datetime.utcnow()
=======
        # Find all stuck sessions (active but with future start times or inactive but not ended)
        stuck_sessions = Session.query.filter(
            db.or_(
                db.and_(
                    Session.end_time.is_(None),
                    Session.is_active == True,
                    Session.start_time > datetime.utcnow()
                ),
                db.and_(
                    Session.end_time.is_(None),
                    Session.is_active == False
                )
            )
>>>>>>> master
        ).all()
        
        count = 0
        for session in stuck_sessions:
            session.end_time = datetime.utcnow()
            session.is_active = False
<<<<<<< HEAD
            
            # Try to terminate VNC session
            try:
                import subprocess
                subprocess.run(['pkill', '-f', f'websockify.*{session.server.ip_address}:6080'], check=False)
                subprocess.run(['pkill', '-f', f'Xtightvnc.*{session.server.ip_address}'], check=False)
            except Exception as e:
                print(f"Error terminating VNC session: {str(e)}")
            
            count += 1
        
        db.session.commit()
        if count > 0:
            flash(f'Successfully cleaned up {count} stuck sessions.', 'success')
        else:
            flash('No stuck sessions found.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Error cleaning up sessions.', 'danger')
    
    return redirect(url_for('admin.manage_sessions'))
=======
            count += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Successfully cleaned up {count} stuck sessions'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cleaning up sessions: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error cleaning up sessions'
        }), 500

@admin.route('/submissions/<int:id>/notes', methods=['GET'])
@login_required
@admin_required
def get_submission_notes(id):
    """Get notes for a form submission."""
    submission = FormSubmission.query.get_or_404(id)
    return jsonify({'notes': submission.notes})

@admin.route('/submissions/<int:id>/notes', methods=['POST'])
@login_required
@admin_required
def update_submission_notes(id):
    """Update notes for a form submission."""
    submission = FormSubmission.query.get_or_404(id)
    data = request.get_json()
    
    if 'notes' not in data:
        return jsonify({'error': 'Notes field is required'}), 400
    
    try:
        submission.notes = data['notes']
        db.session.commit()
        return jsonify({'success': True, 'notes': submission.notes})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating submission notes: {str(e)}")
        return jsonify({'error': 'An error occurred while updating notes'}), 500

@admin.route('/submissions/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_submission_status(id):
    """Toggle the review status of a form submission."""
    submission = FormSubmission.query.get_or_404(id)
    
    try:
        submission.is_reviewed = not submission.is_reviewed
        db.session.commit()
        return jsonify({
            'success': True,
            'is_reviewed': submission.is_reviewed
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling submission status: {str(e)}")
        return jsonify({'error': 'An error occurred while updating status'}), 500
>>>>>>> master
