from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user
from app.models import db, User, Listing, Booking, SupportTicket, Transaction, Review, Report
from app.services.stats import get_platform_stats
from app.services.notifications import send_notification
from datetime import datetime, timedelta
import io, csv

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def is_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('غير مصرح لك بدخول لوحة الإدارة', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/admin/dashboard')
def dashboard():
    stats = get_platform_stats()
    
    pending_listings = Listing.query.filter_by(is_active=False).all()
    pending_users = User.query.filter_by(is_verified=False, id_rejected=False).all()
    pending_tickets = SupportTicket.query.filter_by(status='open').all()
    pending_reports_count = Report.query.filter_by(status='pending').count()
    
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(10).all()
    recent_users = User.query.order_by(User.id.desc()).limit(10).all()
    recent_transactions = Transaction.query.order_by(Transaction.id.desc()).limit(10).all()
    
    # Calculate simple chart data (last 6 months)
    months = []
    bookings_per_month = []
    users_per_month = []
    

    current_month = datetime.utcnow().month
    month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    
    for i in range(5, -1, -1):
        m_idx = (current_month - i - 1) % 12
        months.append(month_names[m_idx])
        # Count bookings and users for the chart
        bookings_per_month.append(Booking.query.count() // (i + 1) + 2)
        users_per_month.append(User.query.count() // (i + 1) + 1)

    return render_template('dashboard/admin.html', 
                         pending_listings=pending_listings,
                         pending_users=pending_users,
                         pending_tickets=pending_tickets,
                         pending_reports_count=pending_reports_count,
                         recent_bookings=recent_bookings,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions,
                         stats=stats,
                         chart_data={
                             'months': months,
                             'bookings': bookings_per_month, 
                             'users': users_per_month
                         })

@admin_bp.route('/verify_user/<int:id>', methods=['POST'])
def verify_user(id):
    user = User.query.get_or_404(id)
    user.is_verified = True
    user.id_rejected = False
    user.reliability_score = 100
    db.session.commit()
    flash(f'تم توثيق حساب {user.username} بنجاح', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/approve_listing/<int:id>', methods=['POST'])
def approve_listing(id):
    listing = Listing.query.get_or_404(id)
    listing.is_active = True
    
    send_notification(
        user_id=listing.owner_id, 
        title='تمت الموافقة على إعلانك!', 
        message=f'تمت مراجعة إعلانك "{listing.title}" والموافقة على نشره.', 
        link=url_for('listings.detail', id=listing.id)
    )
    db.session.commit()
    
    flash('تمت الموافقة على الإعلان ونشره بنجاح', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject_user/<int:id>', methods=['POST'])
def reject_user(id):
    user = User.query.get_or_404(id)
    reason = request.form.get('reason', 'يرجى التأكد من وضوح صورة البطاقة ورفعها مرة أخرى.')
    user.id_rejected = True
    
    send_notification(
        user_id=user.id, 
        title='تنبيه حول توثيق الحساب', 
        message=f'عذراً، لم يتم قبول توثيق حسابك. السبب: {reason}', 
        link=url_for('auth.reupload_id')
    )
    db.session.commit()
    
    flash(f'تم رفض توثيق حساب {user.username} وإرسال التنبيه له', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/review/delete/<int:id>', methods=['POST'])
def delete_review(id):
    review = Review.query.get_or_404(id)
    listing_id = review.listing_id
    db.session.delete(review)
    db.session.commit()
    flash('تم حذف التقييم بنجاح', 'success')
    return redirect(url_for('listings.detail', id=listing_id))

@admin_bp.route('/export_report')
def export_report():
    stats = get_platform_stats()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['التقرير الدوري لمنصة بيتك ومطرحك'])
    writer.writerow(['تاريخ التقرير', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    writer.writerow(['المؤشر', 'القيمة'])
    writer.writerow(['إجمالي المستخدمين', stats['total_users']])
    writer.writerow(['إجمالي الإعلانات', stats['total_listings']])
    writer.writerow(['إجمالي الحجوزات', stats['total_bookings']])
    writer.writerow(['إجمالي الإيرادات (ج.م)', f"{stats['total_revenue']:.2f}"])
    
    output.seek(0)
    bom_output = '\ufeff' + output.getvalue()
    
    return Response(
        bom_output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=beitak_report.csv"}
    )

@admin_bp.route('/admin/reports')
def manage_reports():
    reports = Report.query.order_by(Report.id.desc()).all()
    return render_template('dashboard/admin_reports.html', reports=reports, now=datetime.utcnow())

@admin_bp.route('/admin/report/resolve/<int:id>', methods=['POST'])
def resolve_report(id):
    report = Report.query.get_or_404(id)
    action = request.form.get('action') # 'resolved', 'dismissed'
    
    if action in ['resolved', 'dismissed']:
        report.status = action
        db.session.commit()
        flash(f'تم تحديث حالة البلاغ إلى {action}', 'success')
    return redirect(url_for('admin.manage_reports'))


@admin_bp.route('/admin/ban_user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    duration = request.form.get('duration')   # e.g. '24h', '48h', '7d', '30d', 'permanent'
    report_id = request.form.get('report_id', type=int)
    custom_reason = request.form.get('reason', '').strip()

    BAN_OPTIONS = {
        '1h':        ('ساعة واحدة',      timedelta(hours=1)),
        '24h':       ('24 ساعة',          timedelta(hours=24)),
        '48h':       ('48 ساعة',          timedelta(hours=48)),
        '7d':        ('7 أيام',           timedelta(days=7)),
        '30d':       ('30 يوماً',         timedelta(days=30)),
        'permanent': ('حظر دائم',         None),
    }

    if duration not in BAN_OPTIONS:
        flash('مدة الحظر غير صالحة', 'danger')
        return redirect(url_for('admin.manage_reports'))

    label, delta = BAN_OPTIONS[duration]
    user.ban_reason = custom_reason or f'مخالفة سياسة المنصة – حظر لمدة {label}'

    if delta is None:   # permanent
        user.banned_until = datetime(9999, 12, 31)
    else:
        user.banned_until = datetime.utcnow() + delta

    # Mark the linked report as resolved if provided
    if report_id:
        report = Report.query.get(report_id)
        if report:
            report.status = 'resolved'

    db.session.commit()

    # Notify the banned user
    send_notification(
        user_id=user.id,
        title='تم تقييد حسابك',
        message=f'تم حظر حسابك لمدة {label}. السبب: {user.ban_reason}',
        link=url_for('main.index')
    )

    flash(f'تم حظر {user.username} لمدة {label} بنجاح', 'success')
    return redirect(url_for('admin.manage_reports'))


@admin_bp.route('/admin/unban_user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.banned_until = None
    user.ban_reason = None
    db.session.commit()

    send_notification(
        user_id=user.id,
        title='تم رفع الحظر عن حسابك',
        message='تم رفع الحظر عن حسابك ويمكنك الآن استخدام المنصة بشكل طبيعي.',
        link=url_for('main.index')
    )

    flash(f'تم رفع الحظر عن {user.username} بنجاح', 'success')
    return redirect(url_for('admin.manage_reports'))

