from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Use instance path for DB to allow cleaner volume mapping
    db_path = os.path.join(app.instance_path, 'users.db')
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    if test_config:
        app.config.update(test_config)

    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from . import models
        
        # Create database tables
        db.create_all()
        
        # Create default admin user if not exists
        if not models.User.query.filter_by(username='pyats').first():
            print("Creating default admin user 'pyats'...")
            default_user = models.User(username='pyats', role='admin', must_change_password=True)
            default_user.set_password('pyats123')
            db.session.add(default_user)
            db.session.commit()

    # Register Blueprints
    from .routes import main_bp, auth_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
        
    return app
