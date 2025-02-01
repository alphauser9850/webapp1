from app import db
from datetime import datetime

class Session(db.Model):
<<<<<<< HEAD
    __tablename__ = 'session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    hours_allocated = db.Column(db.Float, nullable=True)  # Store initially allocated hours
=======
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
>>>>>>> master
    
    # Relationships
    user = db.relationship('User', back_populates='sessions')
    server = db.relationship('Server', back_populates='sessions')
    
    @property
    def duration(self):
        """Calculate session duration in hours"""
        if not self.end_time:
<<<<<<< HEAD
            return (datetime.utcnow() - self.start_time).total_seconds() / 3600
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    @property
    def remaining_time(self):
        """Calculate remaining time in hours"""
        if not self.is_active or self.end_time:
            return 0
            
        if self.hours_allocated is None:
            self.hours_allocated = self.user.remaining_hours  # Use all available hours
            db.session.commit()
            
        elapsed_time = self.duration
        return max(0, self.hours_allocated - elapsed_time)
    
    def end(self):
        """End the session and update user's remaining hours"""
        if not self.end_time and self.is_active:
            self.end_time = datetime.utcnow()
            self.is_active = False
            
            # Calculate actual time used and deduct from user's hours
            duration = self.duration
            self.user.remaining_hours = max(0, self.user.remaining_hours - duration)
            
            try:
                # Try to terminate VNC session
                import subprocess
                subprocess.run(['pkill', '-f', f'websockify.*{self.server.ip_address}:6080'], check=False)
                subprocess.run(['pkill', '-f', f'Xtightvnc.*{self.server.ip_address}'], check=False)
            except Exception as e:
                print(f"Error terminating VNC session: {str(e)}")
    
    def save(self):
        """Save the session to the database"""
        try:
            if self.hours_allocated is None:
                self.hours_allocated = self.user.remaining_hours  # Use all available hours
            
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def check_time_availability(user):
        """Check if user has sufficient time to start a new session"""
        if hasattr(user, 'bypass_time_check') and user.bypass_time_check:
            return True, "Time check bypassed"
            
        if user.remaining_hours <= 0:
            return False, "You have no remaining lab hours. Please contact an administrator."
            
        if user.remaining_hours < 0.5:  # Less than 30 minutes
            return False, "You need at least 30 minutes of lab time to start a session."
            
        return True, "Sufficient time available"

    def __repr__(self):
        status = 'Active' if self.is_active else 'Ended'
        return f'<Session {self.id} - User {self.user.username} - {status}>'
=======
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
>>>>>>> master
