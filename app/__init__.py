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

    @app.before_request
    def check_and_release_payouts():
        from flask import request
        # تخطي ملفات static والـ assets لتجنب استهلاك اتصالات قاعدة البيانات
        if request.endpoint == 'static' or request.path.startswith('/static/'):
            return
            
        from datetime import datetime, timedelta
        from app.models import Booking, Transaction
        from app.services.notifications import send_notification
        
        # البحث عن الحجوزات المؤكدة التي لم تُحرر دفعاتها بعد ومر 24 ساعة على تاريخ الدخول
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        due_bookings = Booking.query.filter(
            Booking.status == 'confirmed',
            Booking.payment_released == False,
            Booking.check_in_date <= cutoff_time
        ).all()
        
        for booking in due_bookings:
            try:
                owner = booking.listing.owner
                payout_amount = booking.owner_payout_amount or 0.0
                
                # إضافة المبلغ لمحفظة المالك
                owner.wallet_balance = (owner.wallet_balance or 0.0) + payout_amount
                
                # تسجيل المعاملة المالية كـ payout
                txn = Transaction(
                    user_id=owner.id,
                    booking_id=booking.id,
                    amount=payout_amount,
                    transaction_type='payout'
                )
                db.session.add(txn)
                
                # تعيين الحقل إلى تم التحرير
                booking.payment_released = True
                
                # إرسال إشعار للمالك
                send_notification(
                    user_id=owner.id,
                    title='تم تحرير دفعة مالية!',
                    message=f'مرت 24 ساعة على وصول المستأجر لـ {booking.listing.title}. تم تحرير صافي المبلغ {payout_amount:.2f} ج.م وإرساله إلى وسيلة الدفع التي قمت بتسجيلها (Vodafone Cash / InstaPay / Visa).',
                    link='/dashboard'
                )
                app.logger.info(f"Released payout of {payout_amount} for booking {booking.id} to owner {owner.id}")
            except Exception as e:
                app.logger.error(f"Error releasing payout for booking {booking.id}: {e}")
                
        if due_bookings:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error committing released payouts: {e}")

    @app.before_request
    def check_user_ban_status():
        # pyrefly: ignore [missing-import]
        from flask import request, redirect, url_for, render_template
        # pyrefly: ignore [missing-import]
        from flask_login import current_user
        from datetime import datetime
        
        # Skip static assets, manifest, service worker, logout, and ban appeals
        if not request.endpoint or request.endpoint in ['static', 'main.manifest', 'main.service_worker', 'auth.logout', 'auth.appeal_ban'] or request.path.startswith('/static/'):
            return
            
        if current_user.is_authenticated:
            if current_user.banned_until:
                if current_user.banned_until > datetime.utcnow():
                    is_permanent = current_user.banned_until.year == 9999
                    banned_until_str = 'دائم' if is_permanent else current_user.banned_until.strftime('%Y-%m-%d — %H:%M UTC')
                    banned_until_iso = '' if is_permanent else current_user.banned_until.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                    
                    # Query the latest ban appeal support ticket for the user
                    from app.models import SupportTicket
                    latest_appeal = SupportTicket.query.filter(
                        SupportTicket.user_id == current_user.id,
                        SupportTicket.subject.like('[التماس رفع حظر]%')
                    ).order_by(SupportTicket.created_at.desc()).first()
                    
                    return render_template(
                        'auth/banned.html',
                        user_id=current_user.id,
                        is_permanent=is_permanent,
                        banned_until_str=banned_until_str,
                        banned_until_iso=banned_until_iso,
                        ban_reason=current_user.ban_reason or 'مخالفة سياسة المنصة',
                        latest_appeal=latest_appeal
                    )
                else:
                    # Ban has expired naturally! Clean it up immediately on first access
                    current_user.banned_until = None
                    current_user.ban_reason = None
                    from app.models import SupportTicket
                    appeals = SupportTicket.query.filter(
                        SupportTicket.user_id == current_user.id,
                        SupportTicket.subject.like('[التماس رفع حظر]%')
                    ).all()
                    for appeal in appeals:
                        appeal.subject = appeal.subject.replace('[التماس رفع حظر]', '[التماس سابق تم معالجته]')
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()

    return app

