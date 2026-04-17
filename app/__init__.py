"""
Flask 3.1.3 Application Factory
Modern patterns: SQLAlchemy 2.0, explicit app context
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Modern SQLAlchemy 2.0 instance
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name: str = 'default') -> Flask:
    """
    Application factory pattern - Flask 3.x compliant
    Type hints using Python 3.10+ syntax
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Load config
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with Flask 3.x pattern
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints (modern Flask 3.x way)
    from app.routes import farms_bp, harvests_bp, dashboard_bp
    
    app.register_blueprint(farms_bp, url_prefix='/api/farms')
    app.register_blueprint(harvests_bp, url_prefix='/api/harvests')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    
    # Modern error handlers (Flask 3.x - using app.errorhandler as decorator)
    _register_error_handlers(app)
    
    # Create tables within app context (Flask 3.x best practice)
    with app.app_context():
        # Import models to ensure they're registered
        from app import models
        db.create_all()
    
    return app


def _register_error_handlers(app: Flask) -> None:
    """Centralized error handling for Flask 3.x"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(422)  # Pydantic validation errors
    def unprocessable_entity(error):
        return jsonify({
            'error': 'Validation Error',
            'details': getattr(error, 'data', {}).get('messages', {})
        }), 422
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Critical: rollback on error
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500