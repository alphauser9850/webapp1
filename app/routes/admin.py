from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Category, Server, Session, FormSubmission
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

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
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

@admin.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    categories = Category.query.all()
    form = FlaskForm()  # For CSRF protection
    return render_template('admin/users.html', users=users, categories=categories, form=form)

@admin.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
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
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
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

@admin.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
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

@admin.route('/users/<int:id>/assign-servers', methods=['POST'])
@login_required
@admin_required
def assign_user_servers(id):
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
@login_required
@admin_required
def edit_server(id):
    server = Server.query.get_or_404(id)
    
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
@login_required
@admin_required
def delete_server(id):
    server = Server.query.get_or_404(id)
    
    try:
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

@admin.route('/sessions')
@login_required
@admin_required
def manage_sessions():
    sessions = Session.query.order_by(Session.start_time.desc()).all()
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

@admin.route('/sessions/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_session(id):
    session = Session.query.get_or_404(id)
    
    try:
        # Force end the session first if it's still active
        if session.is_active:
            session.end_time = datetime.utcnow()
            session.is_active = False
        
        # Delete the session
        db.session.delete(session)
        db.session.commit()
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

@admin.route('/sessions/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_sessions():
    try:
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
        ).all()
        
        count = 0
        for session in stuck_sessions:
            session.end_time = datetime.utcnow()
            session.is_active = False
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
