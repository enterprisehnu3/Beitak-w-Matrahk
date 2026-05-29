from flask import Flask
from flask_login import LoginManager
from config import Config, DevelopmentConfig
from app.models import db, User
from app.constants import CITY_TRANSLATIONS, GENDER_TRANSLATIONS
import logging

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.listings import listings_bp
    from app.routes.admin import admin_bp
    from app.routes.booking import booking_bp
    from app.routes.chat import chat_bp
    from app.routes.support import support_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.notifications import notifications_bp
    from app.routes.api import api_bp
    from app.routes.user import user_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(user_bp)

    # Context Processor for Global Variables
    from datetime import datetime
    @app.context_processor
    def inject_now():
        unread_count = 0
        unread_notifications = 0
        from flask_login import current_user
        if current_user.is_authenticated:
            try:
                from app.models import Message, Notification
                unread_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
                unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            except Exception as e:
                app.logger.error(f"Error in context processor: {e}")
        return {'now': datetime.utcnow(), 'unread_msg_count': unread_count, 'unread_notifications': unread_notifications}

    @app.template_filter('ar_city')
    def ar_city(city):
        return CITY_TRANSLATIONS.get(city, city)

    @app.template_filter('ar_gender')
    def ar_gender(gender):
        return GENDER_TRANSLATIONS.get(gender, gender)

    return app
