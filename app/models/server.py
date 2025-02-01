<<<<<<< HEAD
from app import db
from datetime import datetime

# Association table for server-user many-to-many relationship
server_user_association = db.Table('server_user_association',
    db.Column('server_id', db.Integer, db.ForeignKey('server.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Server(db.Model):
    __tablename__ = 'server'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(15), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
=======
from datetime import datetime
from app import db

class Server(db.Model):
    __tablename__ = 'servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    connection_address = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
>>>>>>> master
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', back_populates='servers')
<<<<<<< HEAD
    sessions = db.relationship('Session', back_populates='server', lazy=True)
    assigned_users = db.relationship('User', 
                                   secondary=server_user_association,
                                   back_populates='assigned_servers')
=======
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
>>>>>>> master
    
    def __repr__(self):
        return f'<Server {self.name}>'
