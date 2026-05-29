from app.models import db, User, Listing, Booking, Transaction
from sqlalchemy import func

def get_platform_stats():
    """
    Returns global statistics for the admin dashboard.
    """
    stats = {
        'total_users': User.query.count(),
        'total_listings': Listing.query.count(),
        'total_bookings': Booking.query.count(),
        'total_revenue': db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'payment').scalar() or 0,
        'pending_verifications': User.query.filter_by(is_verified=False, id_rejected=False).count()
    }
    return stats
