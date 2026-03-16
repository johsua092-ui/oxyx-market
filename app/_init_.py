import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta
from flask import Flask, g, request, session

def create_app(config_name=None):
    """App factory pattern untuk fleksibilitas deployment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates',
                static_folder='../static')
    
    # Load configuration
    try:
        from config import config
        app.config.from_object(config[config_name])
    except ImportError:
        # Fallback configuration
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32).hex())
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/oxyx.db')
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
        app.config['WHID_ENABLED'] = True
        app.config['WHID_FORCE_LOGOUT_PREVIOUS'] = True
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Ensure logs folder exists
    log_folder = app.config.get('LOG_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(log_folder, exist_ok=True)
    
    # Setup logging
    if not app.debug:
        file_handler = RotatingFileHandler(
            os.path.join(log_folder, 'oxyx.log'), 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Oxyx Builds startup')
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        headers = app.config.get('SECURITY_HEADERS', {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        })
        for header, value in headers.items():
            response.headers[header] = value
        return response
    
    # Import dan register blueprints
    try:
        from app.auth import init_auth_routes
        init_auth_routes(app)
    except ImportError:
        # Fallback routes
        @app.route('/')
        def index():
            return "Oxyx Builds - Running"
    
    return app
