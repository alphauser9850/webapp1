from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Category, Server, Session, FormSubmission
from app import db
from datetime import datetime, timedelta
import json
from flask_wtf import FlaskForm

main = Blueprint('main', __name__)

@main.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@main.context_processor
def utility_processor():
    return dict(now=datetime.utcnow)

@main.context_processor
def inject_active_session():
    """Inject active session into all templates."""
    if current_user.is_authenticated:
        active_session = Session.query.filter_by(
            user_id=current_user.id,
            end_time=None,
            is_active=True
        ).first()
        form = FlaskForm()  # Create form for CSRF token
        return dict(active_session=active_session, form=form)
    return dict(active_session=None, form=None)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html')

@main.route('/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submissions."""
    data = request.get_json()
    
    if not data or not all(key in data for key in ['name', 'email', 'message']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        form_submission = FormSubmission(
            name=data['name'],
            email=data['email'],
            content=data['message'],
            type='contact',
            phone=data.get('phone'),  # Optional field
            country_code=data.get('country_code')  # Optional field
        )
        db.session.add(form_submission)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Thank you for your message. We will get back to you soon.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving contact form: {str(e)}")
        return jsonify({'error': 'An error occurred while submitting the form. Please try again.'}), 500

@main.route('/documentation')
def documentation():
    """Documentation page for new users."""
    return render_template('main/documentation.html')

@main.route('/dashboard')
@login_required
def dashboard():
    form = FlaskForm()  # Create form for CSRF token
    
    # Get active session if any
    active_session = Session.query.filter_by(
        user_id=current_user.id,
        end_time=None,
        is_active=True
    ).first()
    
    # Calculate remaining hours
    remaining_hours = current_user.remaining_hours
    if active_session:
        elapsed_hours = (datetime.utcnow() - active_session.start_time).total_seconds() / 3600
        remaining_hours = max(0, remaining_hours - elapsed_hours)
    
    # Get all categories
    categories = Category.query.all()
    
    # Get recent sessions
    recent_sessions = Session.query.filter_by(user_id=current_user.id)\
        .order_by(Session.start_time.desc())\
        .limit(5)\
        .all()
    
    return render_template('main/dashboard.html',
                         categories=categories,
                         active_session=active_session,
                         recent_sessions=recent_sessions,
                         remaining_hours=remaining_hours,
                         form=form)  # Pass form to template

@main.route('/servers/<int:category_id>')
@login_required
def list_servers(category_id):
    category = Category.query.get_or_404(category_id)
    servers = Server.query.filter_by(category_id=category_id, is_active=True).all()
    
    # Filter servers based on user assignments if they exist
    if current_user.assigned_servers:
        servers = [server for server in servers if server in current_user.assigned_servers]
    
    # Create a form for CSRF protection
    form = FlaskForm()
    
    return render_template('main/servers.html',
                         category=category,
                         servers=servers,
                         form=form)

@main.route('/sessions/start', methods=['POST'])
@login_required
def start_session():
    form = FlaskForm()
    if not form.validate():
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
        
    server_id = request.form.get('server_id')
    if not server_id:
        flash('Server ID is required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    server = Server.query.get_or_404(server_id)
    
    # Check if user has access to this server
    if current_user.assigned_servers and server not in current_user.assigned_servers:
        flash('You do not have access to this server.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user already has an active session
    active_session = Session.query.filter_by(
        user_id=current_user.id,
        end_time=None,
        is_active=True
    ).first()
    
    if active_session:
        flash('You already have an active session.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Create new session
    session = Session(
        user_id=current_user.id,
        server_id=server_id,
        start_time=datetime.utcnow(),
        is_active=True
    )
    
    try:
        db.session.add(session)
        db.session.commit()
        return redirect(url_for('main.session_detail', session_id=session.id))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error starting session: {str(e)}")
        flash('Error starting session.', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/sessions/<int:session_id>')
@login_required
def session_detail(session_id):
    session = Session.query.get_or_404(session_id)
    form = FlaskForm()  # Create form for CSRF token
    
    # Check if session belongs to user
    if session.user_id != current_user.id:
        flash('You do not have access to this session.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if session is still active
    if not session.is_active:
        flash('This session has ended.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('labs/session.html', 
                         session=session,
                         form=form)  # Pass form to template

@main.route('/sessions/<int:session_id>/end', methods=['POST'])
@login_required
def end_session(session_id):
    session = Session.query.get_or_404(session_id)
    
    # Ensure user can only end their own sessions
    if session.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to end this session.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        session.end()
        db.session.commit()
        flash('Session ended successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error ending session: {str(e)}")
        flash('Error ending session.', 'error')
    
    return redirect(url_for('main.dashboard'))

@main.route('/demo/<int:category_id>')
@login_required
def start_demo(category_id):
    # Check if user already used demo
    demo_session = Session.query.filter_by(
        user_id=current_user.id,
        is_demo=True
    ).first()
    
    if demo_session:
        flash('You have already used your demo session', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get first available server in category
    server = Server.query.filter_by(
        category_id=category_id,
        status='active'
    ).first()
    
    if not server:
        flash('No servers available for demo', 'error')
        return redirect(url_for('main.dashboard'))
    
    return redirect(url_for('main.start_session', id=server.id, demo=True))

@main.route('/start_lab/<int:server_id>', methods=['GET'])
@login_required
def start_lab(server_id):
    # Get the lab path from the query parameters (now optional)
    lab_path = request.args.get('lab_path')
    current_app.logger.info(f"Starting session for user: {current_user.username}")
    
    # Get the server
    server = Server.query.get_or_404(server_id)
    current_app.logger.info(f"Server details - Name: {server.name}, Address: {server.connection_address}")
    
    # Check if server is active and user has access
    if server.status != 'active' or server not in current_user.assigned_servers:
        flash('Server is not available or you do not have access', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user has available time
    has_time, message = Session.check_time_availability(current_user)
    if not has_time:
        flash(message, 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the stored EVE-NG password
    eve_password = current_user.get_eve_ng_password(server)
    if not eve_password:
        flash('EVE-NG account not set up. Please contact administrator to set up your EVE-NG account.', 'error')
        return redirect(url_for('main.list_servers', category_id=server.category_id))
    
    try:
        # Initialize EVE-NG API
        api = EveNGAPI(server)
        
        # Auto login and optionally start lab
        if lab_path:
            success = api.auto_login_and_start_lab(current_user.username, eve_password, lab_path)
        else:
            # Just login to EVE-NG without starting a specific lab
            success = api.login_user(current_user.username, eve_password)
        
        if success:
            # Create a new session record
            session = Session(
                user=current_user, 
                server=server, 
                lab_path=lab_path  # This will be None if no specific lab
            )
            db.session.add(session)
            db.session.commit()
            
            flash('Session started successfully!', 'success')
            return redirect(url_for('main.session_detail', session_id=session.id))
        else:
            flash('Failed to start session. Please contact administrator to verify your EVE-NG account.', 'error')
            return redirect(url_for('main.list_servers', category_id=server.category_id))
            
    except Exception as e:
        current_app.logger.error(f"Error starting session: {str(e)}")
        flash('An error occurred while starting the session. Please contact administrator.', 'error')
        return redirect(url_for('main.list_servers', category_id=server.category_id))