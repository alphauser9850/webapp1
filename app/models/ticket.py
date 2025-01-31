from app import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, closed
    priority = db.Column(db.String(20), default='low')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    admin_viewed = db.Column(db.Boolean, default=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='created_tickets')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], back_populates='assigned_tickets')
    messages = db.relationship('TicketMessage', back_populates='ticket', lazy=True, cascade='all, delete-orphan')

    @property
    def status_color(self):
        """Map ticket status to color classes."""
        status_colors = {
            'open': 'warning',
            'in_progress': 'primary',
            'closed': 'success'
        }
        return status_colors.get(self.status, 'secondary')

    @property
    def priority_color(self):
        """Map ticket priority to color classes."""
        priority_colors = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger'
        }
        return priority_colors.get(self.priority, 'secondary')

    def __repr__(self):
        return f'<Ticket {self.id}: {self.subject}>'


class TicketMessage(db.Model):
    __tablename__ = 'ticket_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)
    
    # Foreign Keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    ticket = db.relationship('Ticket', back_populates='messages')
    user = db.relationship('User', back_populates='ticket_messages')

    def __repr__(self):
        return f'<TicketMessage {self.id} for Ticket {self.ticket_id}>' 