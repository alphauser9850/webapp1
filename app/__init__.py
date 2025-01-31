import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_socketio import SocketIO
from config import Config
import os
import secrets
from flask_wtf import FlaskForm
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.pool import QueuePool

db = SQLAlchemy(engine_options={
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 300
})
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()
sess = Session()
socketio = SocketIO(
    async_mode='eventlet',
    cors_allowed_origins="*",
    ping_timeout=120,
    ping_interval=25,
    max_http_buffer_size=1e8,
    engineio_logger=True,
    logger=True,
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1000,
    reconnection_delay_max=5000
)

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Load configuration
    app.config.from_object(config_class)
    
    # Ensure we have a secret key
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secrets.token_hex(32)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    sess.init_app(app)
    socketio.init_app(app)
    
    # Global context processor for CSRF form
    @app.context_processor
    def inject_csrf_form():
        return {'form': FlaskForm()}
    
    # Register blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.tickets import tickets
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(tickets, url_prefix='/support')
    
    # Register error handlers
    from app.utils.error_handlers import init_error_handlers
    init_error_handlers(app)
    
    # Register CLI commands
    from app import cli
    cli.init_app(app)
    
    # Ensure session directory exists
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    return app

from app.models import User

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 