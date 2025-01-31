from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))  # basic, intermediate, expert
    
    # Relationships
    servers = db.relationship('Server', back_populates='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
