import os
from dotenv import load_dotenv
from datetime import timedelta

# Load .env from project root
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    # Flask config
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool management for Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,      # Automatically check if connections are still alive
        "pool_recycle": 300,        # Recycle connections every 5 minutes
        "pool_size": 5,             # Maintain up to 5 connections
        "max_overflow": 10          # Allow 10 temporary extra connections if load spikes
    }

    # JWT config
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

