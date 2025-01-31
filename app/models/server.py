from datetime import datetime
from app import db

class Server(db.Model):
    __tablename__ = 'servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    connection_address = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', back_populates='servers')
    sessions = db.relationship('Session', back_populates='server', cascade='all, delete-orphan')
    assigned_users = db.relationship('User', secondary='user_server_assignments', back_populates='assigned_servers')
    
    @property
    def is_online(self):
        # A server is considered online if it has any active session
        return any(session.is_active for session in self.sessions)
    
    @property
    def active_users(self):
        # Return list of users with active sessions
        return [session.user for session in self.sessions if session.is_active]
    
    def __repr__(self):
        return f'<Server {self.name}>'
