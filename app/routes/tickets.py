from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from app.models import Ticket, TicketMessage, User
from app.forms.tickets import TicketForm, MessageForm, TicketStatusForm
from app.events import notify_admins, notify_user
from datetime import datetime
from flask_socketio import emit, join_room
from flask_wtf import FlaskForm

tickets = Blueprint('tickets', __name__, url_prefix='/support')

@tickets.route('/')
@login_required
def dashboard():
    """Display the support dashboard."""
    tickets_query = Ticket.query
    if not current_user.is_admin:
        tickets_query = tickets_query.filter_by(user_id=current_user.id)
    
    tickets = tickets_query.order_by(Ticket.updated_at.desc()).all()
    
    # Count tickets by status
    open_count = sum(1 for t in tickets if t.status == 'open')
    in_progress_count = sum(1 for t in tickets if t.status == 'in_progress')
    resolved_count = sum(1 for t in tickets if t.status == 'closed')
    
    form = TicketForm()
    return render_template('tickets/dashboard.html',
                         tickets=tickets,
                         open_count=open_count,
                         in_progress_count=in_progress_count,
                         resolved_count=resolved_count,
                         form=form)

@tickets.route('/tickets')
@login_required
def view_tickets():
    if current_user.is_admin:
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('tickets/tickets.html', tickets=tickets)

@tickets.route('/create', methods=['POST'])
@login_required
def create_ticket():
    """Create a new support ticket."""
    data = request.get_json()
    
    if not data.get('subject') or not data.get('message'):
        return jsonify({'error': 'Subject and message are required'}), 400
    
    ticket = Ticket(
        subject=data['subject'],
        status='open',
        priority=data.get('priority', 'low'),
        user_id=current_user.id
    )
    db.session.add(ticket)
    db.session.flush()  # Get the ticket ID
    
    # Create initial message
    message = TicketMessage(
        content=data['message'],
        ticket_id=ticket.id,
        user_id=current_user.id
    )
    db.session.add(message)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'ticket_id': ticket.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets.route('/tickets/<int:id>/close', methods=['POST'])
@login_required
def close_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Only ticket owner or admin can close tickets
    if ticket.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to close this ticket.', 'danger')
        return redirect(url_for('tickets.view_tickets'))
    
    try:
        ticket.status = 'closed'
        ticket.closed_at = datetime.utcnow()
        db.session.commit()
        flash('Ticket closed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error closing ticket.', 'danger')
    
    return redirect(url_for('tickets.view_tickets'))

@tickets.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    """View a specific ticket."""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check if user has access to this ticket
    if not current_user.is_admin and ticket.user_id != current_user.id:
        return redirect(url_for('tickets.dashboard'))
    
    # Mark unread messages as read
    unread_messages = TicketMessage.query.filter_by(
        ticket_id=ticket_id,
        is_read=False
    ).filter(TicketMessage.user_id != current_user.id).all()
    
    for message in unread_messages:
        message.is_read = True
    
    try:
        db.session.commit()
    except:
        db.session.rollback()
    
    form = MessageForm()
    return render_template('tickets/view.html',
                         ticket=ticket,
                         form=form)

@socketio.on('join')
def on_join(data):
    """Handle client joining a ticket's room"""
    room = data.get('room')
    if room and room.startswith('ticket_'):
        join_room(room)

@tickets.route('/ticket/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_status(ticket_id):
    """Update ticket status"""
    ticket = Ticket.query.get_or_404(ticket_id)
    form = TicketStatusForm()
    
    if form.validate_on_submit():
        old_status = ticket.status
        new_status = form.status.data
        
        if old_status != new_status:
            ticket.status = new_status
            ticket.updated_at = datetime.utcnow()
            
            # Create system message for status change
            system_message = TicketMessage(
                ticket_id=ticket.id,
                content=f"Status changed from {old_status} to {new_status}",
                is_system_message=True,
                user_id=current_user.id
            )
            db.session.add(system_message)
            
            try:
                db.session.commit()
                
                # Prepare ticket data for notifications
                ticket_data = {
                    'ticket_id': ticket.id,
                    'subject': ticket.subject,
                    'username': current_user.username,
                    'status': ticket.status,
                    'old_status': old_status,
                    'priority': ticket.priority,
                    'status_color': ticket.status_color,
                    'priority_color': ticket.priority_color,
                    'updated_at': ticket.updated_at.isoformat(),
                    'has_unread': False
                }
                
                # Emit to ticket room
                socketio.emit('new_message', {
                    'ticket_id': ticket.id,
                    'message': {
                        'id': system_message.id,
                        'content': system_message.content,
                        'is_system_message': True,
                        'created_at': system_message.created_at.isoformat()
                    }
                }, room=f'ticket_{ticket.id}')
                
                # Notify admins about status change
                notify_admins('ticket_updated', ticket_data)
                
                # Notify ticket owner if not the current user
                if ticket.user_id != current_user.id:
                    notify_user(ticket.user_id, 'ticket_updated', ticket_data)
                
                return jsonify({
                    'success': True,
                    'status': new_status,
                    'status_color': ticket.status_color,
                    'message': system_message.content
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Invalid form data'}), 400

@tickets.route('/ticket/<int:ticket_id>/message', methods=['POST'])
@login_required
def add_message(ticket_id):
    """Add a new message to a ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    form = MessageForm()
    
    if form.validate_on_submit():
        message = TicketMessage(
            ticket_id=ticket.id,
            user_id=current_user.id,
            content=form.content.data
        )
        db.session.add(message)
        ticket.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # Prepare consistent message data structure
            message_data = {
                'id': message.id,
                'content': message.content,
                'user_id': message.user_id,
                'username': current_user.username,
                'created_at': message.created_at.isoformat(),
                'is_system_message': False
            }
            
            # Prepare ticket data for notifications
            ticket_data = {
                'ticket_id': ticket.id,
                'subject': ticket.subject,
                'username': current_user.username,
                'message': message_data,
                'status': ticket.status,
                'priority': ticket.priority,
                'status_color': ticket.status_color,
                'priority_color': ticket.priority_color,
                'updated_at': ticket.updated_at.isoformat(),
                'has_unread': True
            }
            
            # Notify the other party first
            if current_user.is_admin:
                # If admin is sending, notify only the ticket owner
                notify_user(ticket.user_id, 'new_message', ticket_data)
            else:
                # If user is sending, notify only admins
                notify_admins('new_message', ticket_data)
            
            # Then emit to ticket room for real-time updates
            socketio.emit('new_message', {
                'ticket_id': ticket.id,
                'message': message_data,
                'username': current_user.username
            }, room=f'ticket_{ticket.id}')  # Remove include_self parameter
            
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Invalid form data'}), 400

@tickets.route('/ticket/<int:ticket_id>/messages')
@login_required
def get_messages(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if not current_user.is_admin and ticket.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    last_message_id = request.args.get('last_message_id', 0, type=int)
    
    new_messages = TicketMessage.query.filter(
        TicketMessage.ticket_id == ticket_id,
        TicketMessage.id > last_message_id
    ).order_by(TicketMessage.created_at.asc()).all()
    
    messages = [{
        'id': message.id,
        'content': message.content,
        'user_id': message.user_id,
        'username': message.user.username,
        'created_at': message.created_at.isoformat(),
        'is_system_message': message.is_system_message
    } for message in new_messages]
    
    # Mark messages as read
    unread_messages = [m for m in new_messages if m.user_id != current_user.id and not m.is_read]
    for message in unread_messages:
        message.is_read = True
    if unread_messages:
        db.session.commit()
    
    return jsonify({
        'success': True,
        'messages': messages
    }) 

@tickets.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Clear closed ticket history."""
    form = FlaskForm()
    if not form.validate():
        flash('Invalid request.', 'error')
        return redirect(url_for('tickets.dashboard'))
    
    try:
        # Delete all closed tickets for the current user
        if current_user.is_admin:
            closed_tickets = Ticket.query.filter_by(status='closed').all()
        else:
            closed_tickets = Ticket.query.filter_by(user_id=current_user.id, status='closed').all()
        
        for ticket in closed_tickets:
            db.session.delete(ticket)
        
        db.session.commit()
        flash('Ticket history cleared successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error clearing ticket history.', 'error')
    
    return redirect(url_for('tickets.dashboard'))

@tickets.route('/bulk-update-status', methods=['POST'])
@login_required
def bulk_update_status():
    """Update status for multiple tickets at once."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data or 'ticket_ids' not in data or 'status' not in data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    ticket_ids = data['ticket_ids']
    new_status = data['status']
    
    if new_status not in ['open', 'in_progress', 'closed']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    try:
        tickets = Ticket.query.filter(Ticket.id.in_(ticket_ids)).all()
        for ticket in tickets:
            old_status = ticket.status
            if old_status != new_status:
                ticket.status = new_status
                ticket.updated_at = datetime.utcnow()
                
                # Create system message for status change
                system_message = TicketMessage(
                    ticket_id=ticket.id,
                    content=f"Status changed from {old_status} to {new_status} (Bulk Update)",
                    is_system_message=True,
                    user_id=current_user.id
                )
                db.session.add(system_message)
                
                # Prepare notification data
                ticket_data = {
                    'ticket_id': ticket.id,
                    'subject': ticket.subject,
                    'username': current_user.username,
                    'status': ticket.status,
                    'old_status': old_status,
                    'priority': ticket.priority,
                    'status_color': ticket.status_color,
                    'priority_color': ticket.priority_color,
                    'updated_at': ticket.updated_at.isoformat(),
                    'has_unread': False
                }
                
                # Notify ticket owner
                notify_user(ticket.user_id, 'ticket_updated', ticket_data)
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in bulk update: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update tickets'}), 500 

@tickets.route('/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
def reply_to_ticket(ticket_id):
    """Add a reply to a ticket."""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check if user has access to this ticket
    if not current_user.is_admin and ticket.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if ticket is closed
    if ticket.status == 'closed':
        return jsonify({'error': 'Cannot reply to a closed ticket'}), 400
    
    data = request.get_json()
    if not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400
    
    message = TicketMessage(
        content=data['message'],
        ticket_id=ticket_id,
        user_id=current_user.id
    )
    db.session.add(message)
    
    # Update ticket timestamp
    ticket.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets.route('/ticket/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    """Update a ticket's status."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    if not data.get('status') or data['status'] not in ['open', 'in_progress', 'closed']:
        return jsonify({'error': 'Invalid status'}), 400
    
    old_status = ticket.status
    ticket.status = data['status']
    ticket.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets.route('/ticket/<int:ticket_id>/priority', methods=['POST'])
@login_required
def update_ticket_priority(ticket_id):
    """Update a ticket's priority."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    if not data.get('priority') or data['priority'] not in ['low', 'medium', 'high']:
        return jsonify({'error': 'Invalid priority'}), 400
    
    ticket.priority = data['priority']
    ticket.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets.route('/ticket/<int:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    """Delete a ticket."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    try:
        # Delete all messages first
        TicketMessage.query.filter_by(ticket_id=ticket_id).delete()
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets.route('/message/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message."""
    message = TicketMessage.query.get_or_404(message_id)
    
    # Check if user has permission to delete this message
    if not current_user.is_admin and message.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(message)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 