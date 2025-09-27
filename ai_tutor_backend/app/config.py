# config(dev, prod, secret key, db URL)
import os
from dotenv import load_dotenv

base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir,'..','.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev_secret_key_change_me'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, '..','instance', 'ai_tutor.db')
    SQLALCHEMY_DATABASE_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or 'jwt_secret_key'
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY') or 'huggingface_api_key'