# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
# pyrefly: ignore [missing-import]
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
    
    # Calculate real chart data (last 6 months)
    from sqlalchemy import extract
    months = []
    bookings_per_month = []
    users_per_month = [0, 0, 0, 0, 0, 0]
    
    current_date = datetime.utcnow()
    month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    
    # Build list of target year/months for the last 6 months
    target_months = []
    for i in range(5, -1, -1):
        offset_months = i
        target_year = current_date.year
        target_month = current_date.month - offset_months
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        target_months.append((target_year, target_month))
        months.append(month_names[target_month - 1])
        
        # Count bookings created in this target month
        count_bookings = Booking.query.filter(
            extract('year', Booking.booking_date) == target_year,
            extract('month', Booking.booking_date) == target_month
        ).count()
        bookings_per_month.append(count_bookings)
        
    # Calculate cumulative user growth
    users = User.query.all()
    max_user_id = max([u.id for u in users]) if users else 1
    
    for u in users:
        # Determine earliest activity date as proxy for signup
        earliest_date = None
        first_b = Booking.query.filter_by(tenant_id=u.id).order_by(Booking.booking_date.asc()).first()
        if first_b:
            earliest_date = first_b.booking_date
        first_l = Listing.query.filter_by(owner_id=u.id).order_by(Listing.created_at.asc()).first()
        if first_l and (not earliest_date or first_l.created_at < earliest_date):
            earliest_date = first_l.created_at
        first_t = SupportTicket.query.filter_by(user_id=u.id).order_by(SupportTicket.created_at.asc()).first()
        if first_t and (not earliest_date or first_t.created_at < earliest_date):
            earliest_date = first_t.created_at
            
        if earliest_date:
            uy, um = earliest_date.year, earliest_date.month
        else:
            # Fallback based on User ID auto-increment sequence
            fraction = u.id / max_user_id
            months_ago = int((1.0 - fraction) * 5)
            fallback_date = current_date - timedelta(days=months_ago * 30)
            uy, um = fallback_date.year, fallback_date.month
            
        for idx in range(6):
            ty, tm = target_months[idx]
            if uy < ty or (uy == ty and um <= tm):
                users_per_month[idx] += 1

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
    
    send_notification(
        user_id=user.id,
        title='تم توثيق حسابك بنجاح!',
        message='تهانينا، تمت مراجعة وثائق الهوية الخاصة بك وقبولها. حسابك الآن موثق بالكامل ويمكنك استخدام جميع مميزات المنصة.',
        link=url_for('dashboard.index')
    )
    
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
    next_url = request.form.get('next')

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
        return redirect(next_url or url_for('admin.manage_reports'))

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

    # Rename any past appeals so a new ban period starts fresh without old appeals showing
    from app.models import SupportTicket
    appeals = SupportTicket.query.filter(
        SupportTicket.user_id == user.id,
        SupportTicket.subject.like('[التماس رفع حظر]%')
    ).all()
    for appeal in appeals:
        appeal.subject = appeal.subject.replace('[التماس رفع حظر]', '[التماس سابق تم معالجته]')

    db.session.commit()

    # Notify the banned user
    send_notification(
        user_id=user.id,
        title='تم تقييد حسابك',
        message=f'تم حظر حسابك لمدة {label}. السبب: {user.ban_reason}',
        link=url_for('main.index')
    )

    flash(f'تم حظر {user.username} لمدة {label} بنجاح', 'success')
    return redirect(next_url or url_for('admin.manage_reports'))


@admin_bp.route('/admin/unban_user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.banned_until = None
    user.ban_reason = None
    
    # Rename all their past appeals so they aren't retrieved again
    from app.models import SupportTicket
    appeals = SupportTicket.query.filter(
        SupportTicket.user_id == user.id,
        SupportTicket.subject.like('[التماس رفع حظر]%')
    ).all()
    for appeal in appeals:
        appeal.subject = appeal.subject.replace('[التماس رفع حظر]', '[التماس سابق تم معالجته]')

    next_url = request.form.get('next')
    db.session.commit()

    send_notification(
        user_id=user.id,
        title='تم رفع الحظر عن حسابك',
        message='تم رفع الحظر عن حسابك ويمكنك الآن استخدام المنصة بشكل طبيعي.',
        link=url_for('main.index')
    )

    flash(f'تم رفع الحظر عن {user.username} بنجاح', 'success')
    return redirect(next_url or url_for('admin.manage_reports'))


@admin_bp.route('/release_payout/<int:booking_id>', methods=['POST'])
def release_payout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status != 'confirmed':
        flash('لا يمكن تحرير مستحقات لحجز غير مؤكد.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if booking.payment_released:
        flash('تم تحرير مستحقات هذا الحجز بالفعل للمالك.', 'warning')
        return redirect(url_for('admin.dashboard'))
        
    try:
        owner = booking.listing.owner
        payout_amount = booking.owner_payout_amount or 0.0
        
        # إضافة المبلغ لمحفظة المالك داخلياً في DB (رغم إلغاء العرض في لوحة المؤجر، قد يستخدم لأغراض الإحصائيات أو السجلات)
        owner.wallet_balance = (owner.wallet_balance or 0.0) + payout_amount
        
        # تسجيل المعاملة
        txn = Transaction(
            user_id=owner.id,
            booking_id=booking.id,
            amount=payout_amount,
            transaction_type='payout'
        )
        db.session.add(txn)
        
        booking.payment_released = True
        
        # إرسال إشعار للمالك
        send_notification(
            user_id=owner.id,
            title='تم تحرير دفعة مالية!',
            message=f'قام المسؤول بتحرير وإرسال مستحقاتك بقيمة {payout_amount:.2f} ج.م للحجز الخاص بـ {booking.listing.title} إلى وسيلة الدفع التي قمت بتسجيلها.',
            link=url_for('dashboard.index')
        )
        db.session.commit()
        flash(f'تم تحرير مستحقات المالك {owner.fullname or owner.username} بقيمة {payout_amount:.2f} ج.م بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحرير الدفعة: {e}', 'danger')
        
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/withdraw_profits', methods=['POST'])
def withdraw_profits():
    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('المبلغ المدخل غير صالح.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    method = request.form.get('method')
    details = request.form.get('details')
    
    if amount <= 0:
        flash('يجب أن يكون مبلغ السحب أكبر من الصفر.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    if not method or not details:
        flash('يرجى تحديد طريقة السحب وتفاصيل الحساب.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    stats = get_platform_stats()
    available_balance = stats['total_revenue']
    
    if amount > available_balance:
        flash(f'المبلغ المطلوب ({amount:.2f} ج.م) يتجاوز الرصيد الحالي المتاح للمنصة وهو ({available_balance:.2f} ج.م).', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    try:
        txn = Transaction(
            user_id=current_user.id,
            amount=amount,
            transaction_type='admin_withdrawal'
        )
        db.session.add(txn)
        db.session.commit()
        flash(f'تم تسجيل عملية سحب أرباح للمسؤول بقيمة {amount:.2f} ج.م بنجاح عبر ({method}: {details}).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تسجيل عملية السحب: {e}', 'danger')
        
    return redirect(url_for('admin.dashboard'))

