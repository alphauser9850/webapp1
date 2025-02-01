from app import db
<<<<<<< HEAD
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'category'
=======

class Category(db.Model):
    __tablename__ = 'categories'
>>>>>>> master
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
<<<<<<< HEAD
    level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
=======
    level = db.Column(db.String(20))  # basic, intermediate, expert
>>>>>>> master
    
    # Relationships
    servers = db.relationship('Server', back_populates='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
