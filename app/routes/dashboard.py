from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.models import Listing, Booking, Favorite, SupportTicket

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.role == 'pending':
        return redirect(url_for('auth.choose_role'))
        
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
                               
    elif current_user.role == 'homeowner':
        my_listings = Listing.query.filter_by(owner_id=current_user.id).all()
        incoming_bookings = Booking.query.join(Listing).filter(Listing.owner_id == current_user.id).order_by(Booking.booking_date.desc()).all()
        return render_template('dashboard/homeowner.html', listings=my_listings, bookings=incoming_bookings)
    else:
        my_bookings = Booking.query.filter_by(tenant_id=current_user.id).order_by(Booking.booking_date.desc()).all()
        my_favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        my_tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
        return render_template('dashboard/user.html', bookings=my_bookings, favorites=my_favorites, tickets=my_tickets)
