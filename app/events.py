from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from app.models import User, TicketMessage, Ticket
from datetime import datetime
from sqlalchemy import text

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        # Join user-specific room
        user_room = f'user_{current_user.id}'
        join_room(user_room)
        print(f"\n=== WebSocket Connection ===")
        print(f"User {current_user.username} connected")
        print(f"Joined user room: {user_room}")
        
        if current_user.is_admin:
            join_room('admin_notifications')
            print("Joined admin notifications room")
            
        join_room('dashboard')
        print("Joined dashboard room")
        print("=== Connection complete ===\n")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')
        if current_user.is_admin:
            leave_room('admin_notifications')
        leave_room('dashboard')
        print(f"User {current_user.username} disconnected from WebSocket")

@socketio.on('join')
def on_join(data):
    """Handle client joining a specific room"""
    room = data.get('room')
    if room:
        join_room(room)
        print(f"Client joined room: {room}")

def get_user(user_id):
    """Safely get user from database"""
    if not user_id:
        return None
    return db.session.get(User, user_id)

def mark_message_unread(message_id, ticket_id):
    """Mark message as unread in database"""
    try:
        db.session.execute(
            text("UPDATE ticket_message SET is_read = false WHERE id = :message_id"),
            {'message_id': message_id}
        )
        db.session.execute(
            text("UPDATE ticket SET has_unread = true WHERE id = :ticket_id"),
            {'ticket_id': ticket_id}
        )
        db.session.commit()
    except Exception as e:
        print(f"Error marking message unread: {str(e)}")
        db.session.rollback()

def get_unread_count(user_id):
    """Get total unread notifications count"""
    try:
        user = get_user(user_id)
        if not user:
            return 0

        if user.is_admin:
            # Admins only see messages from users
            result = db.session.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM ticket_message m 
                    JOIN ticket t ON m.ticket_id = t.id
                    JOIN user u ON m.user_id = u.id
                    WHERE m.is_read = false 
                    AND u.is_admin = false  -- Only count messages from non-admin users
                """)
            ).first()
        else:
            # Users only see messages in their tickets from admins
            result = db.session.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM ticket_message m 
                    JOIN ticket t ON m.ticket_id = t.id 
                    JOIN user u ON m.user_id = u.id
                    WHERE m.is_read = false 
                    AND t.user_id = :user_id  -- Only their tickets
                    AND u.is_admin = true     -- Only count messages from admins
                """),
                {'user_id': user_id}
            ).first()
        
        return result.count if result else 0
    except Exception as e:
        print(f"Error getting unread count: {str(e)}")
        return 0

def get_notifications(user_id, last_check=None):
    """Pull-based notification system - returns all unread notifications"""
    try:
        user = get_user(user_id)
        if not user:
            return []

        # Get unread notifications with proper filtering
        query = """
            SELECT 
                t.id,
                t.subject,
                t.status,
                t.priority,
                t.updated_at,
                m.id as message_id,
                m.content as message_content,
                m.created_at as message_time,
                m.user_id as sender_id,
                u.username as sender_name,
                u.is_admin as is_from_admin,
                CASE 
                    WHEN m.created_at > :last_check THEN true 
                    ELSE false 
                END as is_new
            FROM ticket t
            JOIN ticket_message m ON m.ticket_id = t.id
            JOIN user u ON m.user_id = u.id
            WHERE 
                m.is_read = false
                AND (
                    m.created_at > :last_check 
                    OR t.updated_at > :last_check 
                    OR :last_check IS NULL
                )
                AND (
                    -- For admins: show only user messages
                    (:is_admin = true AND u.is_admin = false)
                    OR
                    -- For users: show only admin messages in their tickets
                    (:is_admin = false AND t.user_id = :user_id AND u.is_admin = true)
                )
            ORDER BY m.created_at DESC
        """
        
        results = db.session.execute(text(query), {
            'user_id': user_id,
            'is_admin': user.is_admin,
            'last_check': last_check or datetime.min
        })

        notifications = []
        for row in results:
            notifications.append({
                'type': 'message',
                'ticket': {
                    'id': row.id,
                    'subject': row.subject,
                    'status': row.status,
                    'priority': row.priority,
                    'updated_at': row.updated_at.isoformat(),
                    'has_unread': True
                },
                'message_id': row.message_id,
                'message_content': row.message_content,
                'sender_name': row.sender_name,
                'is_from_admin': row.is_from_admin,
                'timestamp': row.message_time.isoformat(),
                'is_notification': True,
                'is_new': row.is_new
            })

        # Get unread count
        unread_count = get_unread_count(user_id)
        
        return {
            'notifications': notifications,
            'unread_count': unread_count
        }

    except Exception as e:
        print(f"Error in get_notifications: {str(e)}")
        return {'notifications': [], 'unread_count': 0}

@socketio.on('check_notifications')
def handle_notification_check(data):
    """Handle client requesting notifications"""
    if current_user.is_authenticated:
        last_check = data.get('last_check')
        result = get_notifications(current_user.id, last_check)
        emit('notification_update', result)

def emit_message_notification(data, sender_id, recipient_id=None):
    """Hybrid notification handler - uses both push and pull"""
    if not data or 'message_id' not in data:
        print("Error: Invalid notification data")
        return

    try:
        print(f"\n=== Starting notification emission ===")
        print(f"Sender ID: {sender_id}")
        print(f"Recipient ID: {recipient_id}")
        
        # 1. Mark message as unread in database (for pull system)
        mark_message_unread(data['message_id'], data['ticket_id'])
        print("✓ Marked message as unread in database")
        
        # 2. Get fresh notification data from database
        notification_data = get_notifications(
            recipient_id or sender_id,
            datetime.now().isoformat()
        )
        print("✓ Retrieved fresh notification data")
        
        # 3. Push to all relevant rooms
        if notification_data['notifications']:
            latest = notification_data['notifications'][0]
            print(f"Latest notification: {latest['message_content'][:50]}...")
            
            # Create ticket update notification
            sender = get_user(sender_id)
            update_data = {
                'ticket_id': data['ticket_id'],
                'subject': data['subject'],
                'username': sender.username if sender else 'Unknown',
                'status': data['status'],
                'priority': data['priority'],
                'status_color': data.get('status_color', ''),
                'priority_color': data.get('priority_color', ''),
                'updated_at': datetime.now().isoformat(),
                'has_unread': True,
                'update_type': 'message',  # Indicate this is a message update
                'message_content': latest['message_content']
            }
            
            # Send as ticket update
            if sender and sender.is_admin and recipient_id:
                # Admin sending to user
                notify_user(recipient_id, 'ticket_updated', update_data)
                print(f"✓ Sent as ticket update to user {recipient_id}")
            elif sender and not sender.is_admin:
                # User sending to admins
                notify_admins('ticket_updated', update_data)
                print("✓ Sent as ticket update to admins")
            
            # Always update ticket room for real-time chat
            ticket_room = f'ticket_{data["ticket_id"]}'
            socketio.emit('new_message', latest, room=ticket_room)
            print(f"✓ Message sent to ticket room: {ticket_room}")
            
            print("=== Notification emission complete ===\n")
        else:
            print("! No notifications to send")
        
    except Exception as e:
        print(f"Error in emit_message_notification: {str(e)}")
        print(f"Data received: {data}")

def notify_admins(event_type, data):
    """Send notification to all admins"""
    print(f"Sending admin notification: {event_type}")
    
    try:
        if event_type == 'new_message':
            emit_message_notification(
                data, 
                sender_id=data.get('user_id'),
                recipient_id=None
            )
        else:
            ticket_data = {
                'id': data['ticket_id'],
                'subject': data['subject'],
                'username': data['username'],
                'status': data['status'],
                'priority': data['priority'],
                'status_color': data.get('status_color', ''),
                'priority_color': data.get('priority_color', ''),
                'updated_at': data['updated_at'],
                'has_unread': True
            }
            
            notification_data = {
                'ticket': ticket_data,
                'is_notification': True,
                'from_user': True
            }
            
            # Send to admin notifications room
            socketio.emit(event_type, notification_data, room='admin_notifications')
            socketio.emit('new_notification', notification_data, room='admin_notifications')
            print(f"Emitted {event_type} to admin_notifications")
            
            # Always update dashboard for global visibility
            if event_type == 'new_ticket':
                socketio.emit('dashboard_notification', notification_data, room='dashboard')
                socketio.emit('ticket_update', notification_data, room='dashboard')
            elif event_type == 'ticket_updated':
                notification_data.update({
                    'old_status': data.get('old_status', ''),
                    'new_status': data['status']
                })
                socketio.emit('dashboard_notification', notification_data, room='dashboard')
                socketio.emit('ticket_status_change', notification_data, room='dashboard')
            
            print("Emitted global notification to dashboard")
    except Exception as e:
        print(f"Error in notify_admins: {str(e)}")
        raise

def notify_user(user_id, event_type, data):
    """Send notification to a specific user"""
    print(f"Sending user notification: {event_type} to user {user_id}")
    
    try:
        if event_type == 'new_message':
            emit_message_notification(
                data, 
                sender_id=data.get('user_id'),
                recipient_id=user_id
            )
        else:
            ticket_data = {
                'id': data['ticket_id'],
                'subject': data['subject'],
                'username': data['username'],
                'status': data['status'],
                'priority': data['priority'],
                'status_color': data.get('status_color', ''),
                'priority_color': data.get('priority_color', ''),
                'updated_at': data['updated_at'],
                'has_unread': True
            }
            
            notification_data = {
                'ticket': ticket_data,
                'admin_name': data['username'],
                'is_notification': True,
                'is_from_admin': True,
                'update_type': data.get('update_type'),  # Include update type
                'message_content': data.get('message_content')  # Include message content if present
            }
            
            # Send to user's personal room
            user_room = f'user_{user_id}'
            
            # For status changes or message updates
            if event_type == 'ticket_updated':
                if data.get('update_type') == 'message':
                    # This is a message update
                    socketio.emit('ticket_update', notification_data, room=user_room)
                else:
                    # This is a status change
                    notification_data.update({
                        'old_status': data.get('old_status', ''),
                        'new_status': data['status']
                    })
                    socketio.emit('ticket_status_change', notification_data, room=user_room)
                
                socketio.emit('new_notification', notification_data, room=user_room)
                print(f"Emitted notification to {user_room}")
            else:
                socketio.emit('ticket_update', notification_data, room=user_room)
                socketio.emit('new_notification', notification_data, room=user_room)
                print(f"Emitted {event_type} notification to {user_room}")
            
            # Always send to dashboard for global visibility
            socketio.emit('dashboard_notification', notification_data, room='dashboard')
            print(f"Emitted global notification to dashboard")
    except Exception as e:
        print(f"Error in notify_user: {str(e)}")
        raise