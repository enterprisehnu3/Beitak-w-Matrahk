from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models import db, Booking, Listing, Transaction
from app.services.notifications import send_notification
from datetime import datetime, timedelta

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book/<int:id>', methods=['POST'])
@login_required
def book_listing(id):
    listing = Listing.query.get_or_404(id)
    if current_user.id == listing.owner_id:
        flash('لا يمكنك حجز إعلانك الخاص', 'danger')
        return redirect(url_for('listings.detail', id=id))

    if current_user.role not in ['student', 'employee']:
        flash('يجب أن تكون مستأجرًا لتتمكن من الحجز', 'warning')
        return redirect(url_for('listings.detail', id=id))

    if not current_user.is_verified:
        flash('يجب توثيق حسابك برفع صورة البطاقة أولاً لتتمكن من الحجز', 'warning')
        return redirect(url_for('dashboard.index'))

    # 1. التحقق من توافر أماكن شاغرة
    if listing.available_places <= 0:
        flash('عذراً، هذه الوحدة السكنية محجوزة بالكامل حالياً ولا توجد أماكن شاغرة.', 'danger')
        return redirect(url_for('listings.detail', id=id))

    # 2. التحقق من وجود حجز نشط أو معلق مسبقاً لنفس المستخدم
    existing_booking = Booking.query.filter(
        Booking.listing_id == id,
        Booking.tenant_id == current_user.id,
        Booking.status.in_(['pending', 'pending_approval', 'pending_payment', 'confirmed'])
    ).first()

    if existing_booking:
        if existing_booking.status == 'confirmed':
            flash('لقد قمت بحجز هذه الوحدة بالفعل وحجزك مؤكد حالياً.', 'info')
        else:
            flash('لديك طلب حجز بالفعل (قيد الانتظار أو الدفع) لهذه الوحدة السكنية.', 'info')
        return redirect(url_for('listings.detail', id=id))

    check_in_str = request.form.get('check_in_date')
    check_out_str = request.form.get('check_out_date')
    arrival_time = request.form.get('arrival_time')

    if not check_in_str or not check_out_str or not arrival_time:
        flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
        return redirect(url_for('listings.detail', id=id))

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d')
    except ValueError:
        flash('تنسيق التاريخ غير صحيح', 'danger')
        return redirect(url_for('listings.detail', id=id))

    if check_out <= check_in:
        flash('تاريخ الخروج يجب أن يكون بعد تاريخ الدخول', 'danger')
        return redirect(url_for('listings.detail', id=id))

    # التحقق من أن تاريخ الدخول ليس في الماضي
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if check_in < today:
        flash('تاريخ الدخول لا يمكن أن يكون في الماضي', 'danger')
        return redirect(url_for('listings.detail', id=id))

    diff_days = (check_out - check_in).days
    
    # التحقق من الحد الأدنى للمدة بناءً على نوع إيجار الوحدة
    min_days = 7 if listing.rental_period == 'weekly' else 30
    if diff_days < min_days:
        period_name = 'أسبوع' if listing.rental_period == 'weekly' else 'شهر'
        flash(f'الحد الأدنى للحجز هو {period_name} ({min_days} يوم)', 'danger')
        return redirect(url_for('listings.detail', id=id))

    # حساب إجمالي السعر بناءً على سعر الوحدة ونوعها
    daily_rate = listing.price / 30.0 if listing.rental_period == 'monthly' else listing.price / 7.0
    total_price = diff_days * daily_rate

    new_booking = Booking(
        listing_id=id,
        tenant_id=current_user.id,
        status='pending_approval',
        check_in_date=check_in,
        check_out_date=check_out,
        arrival_time=arrival_time,
        total_price=total_price
    )
    db.session.add(new_booking)
    db.session.commit()

    # إشعار لصاحب السكن بطلب حجز جديد
    send_notification(
        user_id=listing.owner_id,
        title='طلب حجز جديد بانتظار موافقتك',
        message=f'قام المستأجر {current_user.fullname or current_user.username} بطلب حجز لـ {listing.title} من {check_in_str} إلى {check_out_str}. يرجى مراجعة ملفه الشخصي وموثوقيته.',
        link=url_for('dashboard.index')
    )
    
    flash('تم إرسال طلب الحجز بنجاح وبانتظار موافقة صاحب السكن.', 'success')
    return redirect(url_for('dashboard.index'))

@booking_bp.route('/approve_booking/<int:id>', methods=['POST'])
@login_required
def approve(id):
    booking = Booking.query.get_or_404(id)
    if booking.listing.owner_id != current_user.id:
        flash('غير مصرح لك باتخاذ هذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if booking.listing.available_places <= 0:
        flash('عذراً، لا توجد أماكن شاغرة حالياً في هذه الوحدة السكنية', 'danger')
        return redirect(url_for('dashboard.index'))

    # توجيه المالك لإدخال تفاصيل سحب المستحقات قبل إرسال الحجز للمستأجر ليدفع
    return redirect(url_for('booking.payout_info', booking_id=booking.id))

@booking_bp.route('/booking/<int:booking_id>/payout_info', methods=['GET', 'POST'])
@login_required
def payout_info(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.listing.owner_id != current_user.id:
        flash('غير مصرح لك بزيارة هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if booking.status != 'pending_approval':
        flash('هذا الحجز ليس بانتظار الموافقة حالياً.', 'warning')
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        payout_method = request.form.get('payout_method')
        payout_details = request.form.get('payout_details')
        
        if not payout_method or not payout_details:
            flash('يرجى اختيار طريقة السحب وإدخال البيانات المطلوبة.', 'danger')
            return render_template('booking/payout_info.html', booking=booking)
            
        booking.payout_method = payout_method
        booking.payout_details = payout_details
        
        # تغيير حالة الحجز بانتظار الدفع وإرسال إشعار للمستأجر
        booking.status = 'pending_payment'
        
        send_notification(
            user_id=booking.tenant_id, 
            title='تمت الموافقة على طلب الحجز!', 
            message=f'وافق المالك على طلب حجزك لـ {booking.listing.title}. يرجى إتمام عملية الدفع لتأكيد حجزك بشكل نهائي.', 
            link=url_for('booking.payment', booking_id=booking.id)
        )
        
        try:
            db.session.commit()
            flash('تم قبول طلب الحجز وحفظ بيانات تحرير المستحقات بنجاح. بانتظار دفع المستأجر.', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception:
            db.session.rollback()
            flash('حدث خطأ أثناء معالجة الطلب وحفظ البيانات.', 'danger')
            
    return render_template('booking/payout_info.html', booking=booking)

@booking_bp.route('/reject_booking/<int:id>', methods=['POST'])
@login_required
def reject(id):
    booking = Booking.query.get_or_404(id)
    if booking.listing.owner_id != current_user.id:
        flash('غير مصرح لك باتخاذ هذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
        
    # إذا تم الرفض قبل الدفع (وهو التدفق المعتاد)
    if booking.status in ['pending_approval', 'pending_payment']:
        booking.status = 'rejected'
        send_notification(
            user_id=booking.tenant_id, 
            title='تم رفض طلب حجزك', 
            message=f'عذراً، قام المالك برفض طلب حجزك لـ {booking.listing.title}.', 
            link=url_for('dashboard.index')
        )
        db.session.commit()
        flash('تم رفض طلب الحجز بنجاح.', 'info')
    # في حال حدوث رفض طارئ لحجز مؤكد (مستبعد ولكن للحماية البرمجية)
    elif booking.status == 'confirmed':
        booking.listing.available_places += 1
        refund = Transaction(
            user_id=booking.tenant_id, 
            booking_id=booking.id, 
            amount=booking.total_price, 
            transaction_type='refund'
        )
        db.session.add(refund)
        booking.tenant.wallet_balance += booking.total_price
        booking.status = 'rejected'
        
        send_notification(
            user_id=booking.tenant_id, 
            title='تم إلغاء وتفنيد حجزك', 
            message=f'عذراً، قام المالك بإلغاء حجزك لـ {booking.listing.title} وتم إرجاع كامل المبلغ لبطاقتك الائتمانية.', 
            link=url_for('dashboard.index')
        )
        db.session.commit()
        flash('تم إلغاء الحجز وإرجاع كامل المبلغ لبطاقتك الائتمانية.', 'info')
        
    return redirect(url_for('dashboard.index'))

@booking_bp.route('/cancel_booking/<int:id>', methods=['POST'])
@login_required
def cancel(id):
    booking = Booking.query.get_or_404(id)
    if current_user.id != booking.tenant_id and current_user.id != booking.listing.owner_id:
        flash('غير مصرح لك بإلغاء هذا الحجز', 'danger')
        return redirect(url_for('dashboard.index'))

    is_tenant = (current_user.id == booking.tenant_id)
    
    if booking.status == 'confirmed':
        _cancel_confirmed(booking, is_tenant)
    elif booking.status in ['pending_approval', 'pending_payment']:
        # طلب معلق لم يدفع فيه المستأجر شيء، يتم إلغاؤه ببساطة
        booking.status = 'cancelled'
        booking.cancelled_by = 'tenant' if is_tenant else 'homeowner'
        booking.cancelled_at = datetime.utcnow()
        flash('تم إلغاء طلب الحجز (لم يتم دفع أي مبالغ بعد).', 'info')
    else:
        flash('لا يمكن إلغاء الحجز في حالته الحالية.', 'warning')
        return redirect(url_for('dashboard.index'))

    booking.status = 'cancelled'
    booking.cancelled_by = 'tenant' if is_tenant else 'homeowner'
    booking.cancelled_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('dashboard.index'))

def _cancel_confirmed(booking, is_tenant):
    booking.listing.available_places += 1
    if is_tenant:
        # حساب الوقت المتبقي على تاريخ الدخول لتطبيق الغرامات الذكية
        time_diff = booking.check_in_date - datetime.utcnow()
        hours_left = time_diff.total_seconds() / 3600.0
        
        if hours_left >= 72:
            penalty_rate = 0.05
            points_deducted = 2
            msg_text = f'تم إلغاء الحجز المؤكد. خصم {points_deducted} نقاط من موثوقيتك وغرامة 5% تشغيل ({booking.total_price * penalty_rate:.2f} ج.م) وإرجاع الباقي لبطاقتك الائتمانية.'
        else:
            penalty_rate = 0.10
            points_deducted = 10
            msg_text = f'تم إلغاء الحجز المؤكد خلال أقل من 72 ساعة. خصم {points_deducted} نقاط من موثوقيتك وغرامة إلغاء 10% ({booking.total_price * penalty_rate:.2f} ج.م) وإرجاع الباقي لبطاقتك الائتمانية.'
        
        penalty = booking.total_price * penalty_rate
        refund_amount = booking.total_price - penalty
        booking.penalty_applied = penalty
        booking.tenant.reliability_score = max(0, booking.tenant.reliability_score - points_deducted)
        
        refund = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=refund_amount, transaction_type='refund')
        penalty_txn = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=penalty, transaction_type='penalty')
        db.session.add_all([refund, penalty_txn])
        booking.tenant.wallet_balance += refund_amount
        
        send_notification(
            user_id=booking.listing.owner_id, 
            title='تم إلغاء حجز مؤكد من المستأجر', 
            message=f'قام المستأجر {booking.tenant.fullname or booking.tenant.username} بإلغاء الحجز المؤكد لـ {booking.listing.title}', 
            link=url_for('dashboard.index')
        )
        flash(msg_text, 'warning')
    else:
        # إلغاء من المالك لحجز مؤكد: خصم 15 نقطة وإرجاع كامل المبلغ للمستأجر
        booking.listing.owner.reliability_score = max(0, booking.listing.owner.reliability_score - 15)
        refund = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=booking.total_price, transaction_type='refund')
        db.session.add(refund)
        booking.tenant.wallet_balance += booking.total_price
        
        send_notification(
            user_id=booking.tenant_id, 
            title='قام المالك بإلغاء حجزك المؤكد', 
            message=f'عذراً، قام المالك بإلغاء حجزك المؤكد لـ {booking.listing.title}. تم استرداد المبلغ بالكامل لبطاقتك الائتمانية.', 
            link=url_for('dashboard.index')
        )
        flash('تم إلغاء الحجز من طرفك. تم خصم 15 نقطة من موثوقيتك لتعطيل المستأجر وإعادة كامل المبلغ لبطاقته الائتمانية.', 'warning')

@booking_bp.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.tenant_id != current_user.id:
         flash('غير مصرح لك بزيارة هذه الصفحة', 'danger')
         return redirect(url_for('main.index'))
    if booking.status != 'pending_payment':
         flash('هذا الحجز لا ينتظر الدفع حالياً.', 'warning')
         return redirect(url_for('dashboard.index'))
    return render_template('payment/checkout.html', booking=booking)

@booking_bp.route('/process_payment/<int:booking_id>', methods=['POST'])
@login_required
def process_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.tenant_id != current_user.id:
         return redirect(url_for('main.index'))
    if booking.status != 'pending_payment':
         flash('طلب الحجز هذا غير متاح للدفع.', 'danger')
         return redirect(url_for('dashboard.index'))
         
    # يتم قبول أي بطاقة ائتمانية مباشرة دون التحقق من رصيد المحفظة الافتراضي
    
    # حساب العمولة ومستحقات المالك
    prev_bookings = Booking.query.filter_by(tenant_id=booking.tenant_id, status='confirmed').count()
    commission_rate = 0.08
    if prev_bookings == 0:
        commission_rate = 0.04
        
    booking.commission_fee = booking.total_price * commission_rate 
    booking.owner_payout_amount = booking.total_price - booking.commission_fee
    booking.payment_released = False
    
    # ترقية الحالة إلى مؤكدة
    booking.status = 'confirmed'
    booking.listing.available_places -= 1
    
    # ترقية نقاط الموثوقية
    booking.tenant.reliability_score = min(100, booking.tenant.reliability_score + 5)
    booking.listing.owner.reliability_score = min(100, booking.listing.owner.reliability_score + 5)
    
    # تسجيل المعاملة
    t = Transaction(user_id=current_user.id, booking_id=booking.id, amount=booking.total_price, transaction_type='payment')
    db.session.add(t)
    
    send_notification(
        user_id=booking.listing.owner_id, 
        title='تم تأكيد الدفع للحجز!', 
        message=f'قام المستأجر {current_user.fullname or current_user.username} بسداد دفعة الحجز لـ {booking.listing.title}. تم تأكيد الحجز، وسيتم تحرير صافي المبلغ لمحفظتك بعد 24 ساعة من تاريخ الوصول.', 
        link=url_for('dashboard.index')
    )
    db.session.commit()
    
    return redirect(url_for('booking.payment_success', transaction_id=t.id))

@booking_bp.route('/payment_success/<int:transaction_id>')
@login_required
def payment_success(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        flash('غير مصرح لك بزيارة هذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    booking = transaction.booking
    end_date = booking.check_out_date
    
    return render_template('payment/success.html', transaction=transaction, booking=booking, end_date=end_date)




