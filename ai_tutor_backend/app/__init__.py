# app factory, Flask setup
from flask import Flask
from flask_cors import CORS
from .config import Config
from .extension import db, migrate, jwt

def create_app(config_class=Config):
    app=Flask(__name__)
    app.config.from_object(config_class)

    #initializing extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)


    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.tutor import tutor_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tutor_bp, url_prefix='/api/tutor')

    return app