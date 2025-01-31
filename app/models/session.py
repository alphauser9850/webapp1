from app import db
from datetime import datetime

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', back_populates='sessions')
    server = db.relationship('Server', back_populates='sessions')
    
    @property
    def duration(self):
        """Calculate session duration in hours"""
        if not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
    
    def end(self):
        """End the session"""
        if self.is_active:
            self.end_time = datetime.utcnow()
            self.is_active = False
    
    def __repr__(self):
        return f'<Session {self.id}>'
