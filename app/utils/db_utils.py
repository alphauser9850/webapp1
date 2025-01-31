import os
from flask import current_app
from sqlalchemy import inspect
from app import db

def verify_database_integrity():
    """Verify database exists in correct location and has proper structure"""
    try:
        # Get the Config class from current app
        Config = current_app.config.get('Config', None)
        if not Config:
            raise ValueError("Config not found in app configuration")
            
        # Validate database path
        Config.validate_database_path()
        
        # Check if we can connect to the database
        inspector = inspect(db.engine)
        
        # Verify essential tables exist
        required_tables = {'user', 'server', 'category', 'session'}
        existing_tables = set(inspector.get_table_names())
        
        if not required_tables.issubset(existing_tables):
            missing_tables = required_tables - existing_tables
            print(f"Missing required tables: {missing_tables}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Database integrity check failed: {str(e)}")
        return False

def get_database_info():
    """Get information about the current database"""
    try:
        Config = current_app.config.get('Config', None)
        if not Config:
            raise ValueError("Config not found in app configuration")
            
        db_path = os.path.join(current_app.instance_path, 'app.db')
        
        info = {
            'location': db_path,
            'exists': os.path.exists(db_path),
            'size': os.path.getsize(db_path) if os.path.exists(db_path) else 0,
            'uri': current_app.config['SQLALCHEMY_DATABASE_URI'],
        }
        
        # Add table information if database exists
        if info['exists']:
            inspector = inspect(db.engine)
            info['tables'] = inspector.get_table_names()
            
        return info
        
    except Exception as e:
        return {'error': str(e)}