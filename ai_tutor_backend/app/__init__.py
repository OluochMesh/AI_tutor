from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .extension import db, migrate, jwt


def create_app(config_class=Config):
    package_root = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        static_folder=str(package_root / "static"),
        template_folder=str(package_root / "templates"),
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    # Allow cookies/session to be sent from the frontend
    CORS(app, supports_credentials=True)
    
    # Import the models for migration to detect them
    from app.models import User, Progress, Response, Subscription

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.tutor import tutor_bp
    # Ensure analytics blueprint is imported
    from app.routes.analytics import analytics_bp
    from app.routes.subscription import subscription_bp
    from app.routes.response import response_bp
    from app.routes.export import export_bp
    # FIX: Import the blueprint instance from frontend module
    from app.routes.frontend import frontend  # This imports the blueprint instance

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tutor_bp, url_prefix='/api/tutor')
    # Register analytics blueprint with API prefix
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
    app.register_blueprint(response_bp, url_prefix='/api/response')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    # FIX: Now this will work - registering the blueprint instance
    app.register_blueprint(frontend)  # No url_prefix for frontend routes
        
    @app.route('/api/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'success': True, 'status': 'healthy', 'database': 'connected'}), 200
        except Exception as e:
            return jsonify({'success': False, 'status': 'unhealthy', 'error': str(e)}), 500

    return app