from app.models import db, User, Listing, Booking, Transaction
from sqlalchemy import func

def get_platform_stats():
    """
    """
    total_payments = db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'payment').scalar() or 0
    total_payouts = db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'payout').scalar() or 0
    total_refunds = db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'refund').scalar() or 0
    total_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'admin_withdrawal').scalar() or 0
    
    stats = {
        'total_users': User.query.count(),
        'total_listings': Listing.query.count(),
        'total_bookings': Booking.query.count(),
        'total_revenue': total_payments - total_payouts - total_refunds - total_withdrawals,
        'pending_verifications': User.query.filter_by(is_verified=False, id_rejected=False).count()
    }
    return stats
