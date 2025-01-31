from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models import Session, Server, Lab
from app import db, socketio
from datetime import datetime
import requests
from urllib.parse import urljoin
import eventlet
from engineio.async_drivers import eventlet as async_eventlet
from app.utils.server_utils import get_lab_url_from_ip
from ..utils.eve_ng_api import EveNGAPI

labs = Blueprint('labs', __name__)

@labs.route('/session/<int:id>')
@login_required
def session(id):
    session = Session.query.get_or_404(id)
    if session.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user still has time
    has_time = True
    if not session.is_demo:
        has_time, message = Session.check_time_availability(current_user)
        if not has_time:
            session.end()
            db.session.commit()
            return render_template('labs/session.html',
                                session=None,
                                has_time=False,
                                error_message=message)
    
    # Initialize EVE-NG session
    try:
        api = EveNGAPI(session.server)
        if not api._login():
            flash('Failed to connect to lab environment', 'error')
            return redirect(url_for('main.dashboard'))
    except Exception as e:
        current_app.logger.error(f"Failed to initialize EVE-NG session: {str(e)}")
        flash('Failed to connect to lab environment', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Calculate remaining time
    remaining_hours = session.remaining_time if not session.is_demo else 0.5
    
    return render_template('labs/session.html', 
                         session=session,
                         has_time=True,
                         remaining_hours=remaining_hours,
                         connection_address=session.server.connection_address)

@labs.route('/session/<int:id>/status')
@login_required
def session_status(id):
    session = Session.query.get_or_404(id)
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Calculate duration if session is ended
    duration = None
    if not session.is_active and session.end_time:
        duration = (session.end_time - session.start_time).total_seconds() / 3600
    
    return jsonify({
        'is_active': session.is_active,
        'duration': duration,
        'server_status': session.server.status
    })

@labs.route('/session/<int:id>/end', methods=['POST'])
@login_required
def end_session(id):
    session = Session.query.get_or_404(id)
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not session.is_active:
        return jsonify({'error': 'Session already ended'}), 400
    
    # Use the session.end() method which handles everything
    session.end()
    db.session.commit()
    
    # Calculate final duration
    duration = (session.end_time - session.start_time).total_seconds() / 3600
    
    return jsonify({
        'success': True,
        'duration': duration,
        'remaining_hours': current_user.available_hours
    })

@labs.route('/labs/start/<int:lab_id>', methods=['POST'])
@login_required
def start_lab(lab_id):
    lab = Lab.query.get_or_404(lab_id)
    server = lab.server
    
    # Check if server is active and user has access
    if server.status != 'active' or server not in current_user.assigned_servers:
        return jsonify({
            'success': False,
            'message': 'Server is not available or you do not have access'
        })
    
    # Check if user has available time
    has_time, message = Session.check_time_availability(current_user)
    if not has_time:
        return jsonify({
            'success': False,
            'message': message
        })
    
    # Get stored EVE-NG password
    eve_password = current_user.get_eve_ng_password(server)
    if not eve_password:
        return jsonify({
            'success': False,
            'message': 'EVE-NG credentials not found. Please contact administrator.'
        })
    
    try:
        # Initialize EVE-NG API
        api = EveNGAPI(server)
        
        # Auto login and start lab
        if api.auto_login_and_start_lab(current_user.username, eve_password, lab.lab_path):
            # Create a new session record
            session = Session(user=current_user, server=server, lab=lab)
            db.session.add(session)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Lab started successfully',
                'session_id': session.id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start lab. Please try again or contact administrator.'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error starting lab: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while starting the lab.'
        })

@labs.route('/vnc/<int:server_id>')
@login_required
def vnc_view(server_id):
    """Return the VNC viewer page"""
    server = Server.query.get_or_404(server_id)
    
    # Check if user has access to this server
    if not current_user.is_admin:
        active_session = Session.query.filter_by(
            user_id=current_user.id,
            server_id=server_id,
            is_active=True,
            end_time=None
        ).first()
        if not active_session:
            return "Unauthorized", 403
    
    vnc_host = server.ip_address
    vnc_port = 6080
    
    return render_template('labs/vnc.html',
                         server=server,
                         vnc_host=vnc_host,
                         vnc_port=vnc_port)

# WebSocket handlers
@socketio.on('connect', namespace='/vnc')
def vnc_connect():
    if not current_user.is_authenticated:
        return False
    return True

@socketio.on('vnc_data', namespace='/vnc')
def handle_vnc_data(data):
    """Handle VNC data through WebSocket"""
    if not current_user.is_authenticated:
        return
    
    server_id = data.get('server_id')
    if not server_id:
        return
    
    server = Server.query.get(server_id)
    if not server:
        return
    
    # Check if user has access to this server
    if not current_user.is_admin:
        active_session = Session.query.filter_by(
            user_id=current_user.id,
            server_id=server_id,
            is_active=True,
            end_time=None
        ).first()
        if not active_session:
            return
    
    # Forward the VNC data
    try:
        # Here you would implement the actual WebSocket forwarding to the VNC server
        # This is a placeholder for the actual implementation
        pass
    except Exception as e:
        current_app.logger.error(f"VNC WebSocket error: {str(e)}")