from flask import Blueprint, render_template, redirect, url_for, flash
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

    new_booking = Booking(
        listing_id=id,
        tenant_id=current_user.id,
        status='pending_payment',
        total_price=listing.price
    )
    db.session.add(new_booking)
    db.session.commit()
    
    return redirect(url_for('booking.payment', booking_id=new_booking.id))

@booking_bp.route('/approve_booking/<int:id>', methods=['POST'])
@login_required
def approve(id):
    booking = Booking.query.get_or_404(id)
    if booking.listing.owner_id != current_user.id:
        flash('غير مصرح لك باتخاذ هذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if booking.listing.available_places <= 0:
        flash('عذراً، لا توجد أماكن شاغرة حالياً', 'danger')
        return redirect(url_for('dashboard.index'))

    # Fix Commission Bug: Count confirmed bookings BEFORE setting this one to confirmed
    prev_bookings = Booking.query.filter_by(tenant_id=booking.tenant_id, status='confirmed').count()
    commission_rate = 0.08
    if prev_bookings == 0:
        commission_rate = 0.04
        
    booking.status = 'confirmed'
    booking.listing.available_places -= 1
    booking.commission_fee = (booking.total_price or 0) * commission_rate 
    
    booking.tenant.reliability_score = min(100, booking.tenant.reliability_score + 5)
    booking.listing.owner.reliability_score = min(100, booking.listing.owner.reliability_score + 5)
    
    send_notification(
        user_id=booking.tenant_id, 
        title='تم قبول طلبك!', 
        message=f'وافق المالك على حجزك وتأكد الدفع في {booking.listing.title}', 
        link=url_for('dashboard.index')
    )
    
    try:
        db.session.commit()
        flash('تم قبول وتأكيد الحجز بنجاح', 'success')
    except Exception:
        db.session.rollback()
        flash('حدث خطأ أثناء تأكيد الحجز', 'danger')

    return redirect(url_for('dashboard.index'))

@booking_bp.route('/reject_booking/<int:id>', methods=['POST'])
@login_required
def reject(id):
    booking = Booking.query.get_or_404(id)
    if booking.listing.owner_id != current_user.id:
        flash('غير مصرح لك باتخاذ هذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if booking.status == 'confirmed':
        booking.listing.available_places += 1
        
    # Refund logic
    if booking.status in ['pending', 'confirmed']:
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
        title='تم رفض طلبك', 
        message=f'عذراً، قام المالك برفض طلب حجزك لـ {booking.listing.title} وتم إرجاع المبلغ لمحفظتك', 
        link=url_for('dashboard.index')
    )
    
    db.session.commit()
    flash('تم رفض طلب السكن ورجوع المبلغ للمستأجر', 'info')
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
    elif booking.status == 'pending':
        _cancel_pending(booking, is_tenant)
    elif booking.status == 'pending_payment':
        flash('تم إلغاء طلب الحجز (لم يتم الدفع).', 'info')

    booking.status = 'cancelled'
    booking.cancelled_by = 'tenant' if is_tenant else 'homeowner'
    booking.cancelled_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('dashboard.index'))

def _cancel_confirmed(booking, is_tenant):
    booking.listing.available_places += 1
    if is_tenant:
        booking.tenant.reliability_score = max(0, booking.tenant.reliability_score - 10)
        penalty = booking.total_price * 0.10
        refund_amount = booking.total_price - penalty
        booking.penalty_applied = penalty
        
        refund = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=refund_amount, transaction_type='refund')
        penalty_txn = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=penalty, transaction_type='penalty')
        db.session.add_all([refund, penalty_txn])
        booking.tenant.wallet_balance += refund_amount
        
        send_notification(booking.listing.owner_id, 'تم إلغاء حجز مؤكد', f'قام المستأجر {booking.tenant.username} بإلغاء الحجز المؤكد لـ {booking.listing.title}', url_for('dashboard.index'))
        flash(f'تم الإلغاء. خصم 10 نقاط من موثوقيتك وغرامة {penalty} ج.م.', 'warning')
    else:
        booking.listing.owner.reliability_score = max(0, booking.listing.owner.reliability_score - 15)
        refund = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=booking.total_price, transaction_type='refund')
        db.session.add(refund)
        booking.tenant.wallet_balance += booking.total_price
        
        send_notification(booking.tenant_id, 'قام المالك بإلغاء حجزك', f'عذراً، قام المالك بإلغاء حجزك المؤكد لـ {booking.listing.title}. تم استرداد المبلغ بالكامل.', url_for('dashboard.index'))
        flash('تم الإلغاء. خصم 15 نقطة من موثوقيتك لتعطيل المستأجر.', 'warning')

def _cancel_pending(booking, is_tenant):
    if is_tenant:
        booking.tenant.reliability_score = max(0, booking.tenant.reliability_score - 2)
        flash('تم إلغاء طلبك واسترداد المبلغ كاملاً قبل موافقة المالك.', 'info')
    else:
        flash('تم إلغاء الطلب من قبل المالك وإرجاع المبلغ.', 'info')
    
    refund = Transaction(user_id=booking.tenant_id, booking_id=booking.id, amount=booking.total_price, transaction_type='refund')
    db.session.add(refund)
    booking.tenant.wallet_balance += booking.total_price

@booking_bp.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.tenant_id != current_user.id:
         flash('غير مصرح لك بزيارة هذه الصفحة', 'danger')
         return redirect(url_for('main.index'))
    return render_template('payment/checkout.html', booking=booking)

@booking_bp.route('/process_payment/<int:booking_id>', methods=['POST'])
@login_required
def process_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.tenant_id != current_user.id:
         return redirect(url_for('main.index'))
    
    t = Transaction(user_id=current_user.id, booking_id=booking.id, amount=booking.total_price, transaction_type='payment')
    db.session.add(t)
    booking.status = 'pending' 
    
    send_notification(
        user_id=booking.listing.owner_id, 
        title='طلب حجز مدفوع جديد!', 
        message=f'قام {current_user.username} بطلب حجز لـ {booking.listing.title} وتم سداد المبلغ!', 
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
    end_date = booking.booking_date + timedelta(days=30)
    
    return render_template('payment/success.html', transaction=transaction, booking=booking, end_date=end_date)



