from flask import Blueprint, render_template, send_from_directory
from flask_login import current_user
from app.models import Listing
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(main_bp.root_path, '../../static'), 'manifest.json')

@main_bp.route('/sw.js')
def service_worker():
    return send_from_directory(os.path.join(main_bp.root_path, '../../static'), 'sw.js')

@main_bp.route('/')
def index():
    # Show featured listings or latest
    recent_listings = Listing.query.filter_by(is_active=True).order_by(Listing.created_at.desc()).limit(6).all()
    user_favorites = []
    if current_user.is_authenticated:
        from app.models import Favorite
        user_favorites = [f.listing_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]
    return render_template('index.html', listings=recent_listings, user_favorites=user_favorites)

@main_bp.route('/about')
def about():
    return render_template('pages/about.html')

@main_bp.route('/terms')
def terms():
    return render_template('pages/terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')
