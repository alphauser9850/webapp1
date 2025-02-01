from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

# Association table for many-to-many relationship between users and servers
user_server_assignments = db.Table('user_server_assignments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('server_id', db.Integer, db.ForeignKey('servers.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    remaining_hours = db.Column(db.Float, default=0)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sessions = db.relationship('Session', back_populates='user', lazy=True)
    assigned_servers = db.relationship('Server', 
                                     secondary=user_server_assignments,
                                     back_populates='assigned_users')
    # Ticket relationships
    created_tickets = db.relationship('Ticket', 
                                    foreign_keys='Ticket.user_id',
                                    back_populates='user',
                                    lazy=True)
    assigned_tickets = db.relationship('Ticket',
                                     foreign_keys='Ticket.assigned_to_id',
                                     back_populates='assigned_to',
                                     lazy=True)
    ticket_messages = db.relationship('TicketMessage',
                                    back_populates='user',
                                    lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def formatted_remaining_time(self):
        """Format remaining hours as 'X hours Y minutes'"""
        hours = int(self.remaining_hours)
        minutes = int((self.remaining_hours - hours) * 60)
        if hours == 0:
            return f"{minutes} minutes"
        elif minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours {minutes} minutes"

    def add_hours(self, hours):
        if hours <= 0:
            raise ValueError("Hours must be positive")
        self.remaining_hours += hours
        db.session.commit()

    def deduct_hours(self, hours):
        if hours <= 0:
            raise ValueError("Hours must be positive")
        if self.remaining_hours < hours:
            raise ValueError("Insufficient hours")
        self.remaining_hours -= hours
        db.session.commit()

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    @property
    def unread_tickets_count(self):
        """Count of unread ticket messages for this user."""
        from app.models import TicketMessage, Ticket
        if self.is_admin:
            # For admins, count tickets with unread messages where they haven't viewed the ticket
            return Ticket.query.filter_by(admin_viewed=False).count()
        else:
            # For regular users, count unread messages in their tickets
            return TicketMessage.query.join(Ticket).filter(
                Ticket.user_id == self.id,
                TicketMessage.is_read == False,
                TicketMessage.user_id != self.id
            ).count()

    def __repr__(self):
        return f'<User {self.username}>'
