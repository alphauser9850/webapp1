import os
from datetime import timedelta
import secrets

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or secrets.token_hex(32)
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_CHECK_DEFAULT = True
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'instance/flask_session'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Default server IPs for testing
    DEFAULT_SERVERS = ['192.168.1.51', '192.168.1.52']
   