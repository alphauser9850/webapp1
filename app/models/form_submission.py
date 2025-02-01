from app import db
from datetime import datetime

class FormSubmission(db.Model):
    __tablename__ = 'form_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'contact' or 'terminal'
    content = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_reviewed = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20), nullable=True)
    country_code = db.Column(db.String(5), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<FormSubmission {self.id}: {self.type} by {self.name}>' 