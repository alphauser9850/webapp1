import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@deshmukhsystems.cloud',
            name='Administrator',
            is_admin=True,
            is_superadmin=True,
            role='admin'
        )
        admin.set_password('Crysis7972@@!!')  # Using the same password pattern as EVE-NG for consistency
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully")

if __name__ == '__main__':
    create_admin_user() 