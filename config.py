import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-beitak-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@127.0.0.1/beitak_db' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Use absolute path for upload folder to ensure consistency
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
