from flask import Blueprint, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models import db, Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications/mark_read')
@login_required
def mark_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard.index'))

@notifications_bp.route('/notifications/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    n = Notification.query.get_or_404(id)
    if n.user_id != current_user.id:
        flash('غير مصرح لك بحذف هذا التنبيه', 'danger')
    else:
        db.session.delete(n)
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard.index'))

@notifications_bp.route('/notifications/clear_all', methods=['POST'])
@login_required
def clear_all():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('تم مسح جميع التنبيهات بنجاح', 'success')
    return redirect(request.referrer or url_for('dashboard.index'))
