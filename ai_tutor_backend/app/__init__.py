from flask import Flask
from flask_cors import CORS
from .config import Config
from .extension import db, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Import the models for migration to detect them
    from app.models import User, Progress, Response, Subscription

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.tutor import tutor_bp
    from app.routes.analytics import analytics_bp
    from app.routes.subscription import subscription_bp 

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tutor_bp, url_prefix='/api/tutor')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
        
    @app.route('/api/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500

    return app