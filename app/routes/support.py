from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import db, SupportTicket, Notification
from app.services.notifications import send_notification
from datetime import datetime

support_bp = Blueprint('support', __name__)

@support_bp.route('/submit_ticket', methods=['GET', 'POST'])
@login_required
def submit_ticket():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        ticket = SupportTicket(user_id=current_user.id, subject=subject, message=message)
        db.session.add(ticket)
        db.session.commit()
        flash('تم إرسال طلب الدعم بنجاح، سنقوم بالرد عليك قريباً.', 'success')
        return redirect(url_for('dashboard.index'))
    return render_template('support/create.html')

@support_bp.route('/close_ticket/<int:id>', methods=['POST'])
@login_required
def close_ticket(id):
    if current_user.role != 'admin':
        flash('غير مصرح لك بهذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
        
    ticket = SupportTicket.query.get_or_404(id)
    ticket.status = 'closed'
    db.session.commit()
    flash('تم إغلاق تذكرة الدعم بنجاح', 'success')
    return redirect(url_for('dashboard.index'))

@support_bp.route('/reply_ticket/<int:id>', methods=['POST'])
@login_required
def reply_ticket(id):
    if current_user.role != 'admin':
        flash('غير مصرح لك بهذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
        
    ticket = SupportTicket.query.get_or_404(id)
    reply = request.form.get('reply')
    
    if reply:
        ticket.admin_reply = reply
        ticket.admin_replied_at = datetime.utcnow()
        ticket.status = 'closed'
        
        send_notification(
            user_id=ticket.user_id, 
            title='تم الرد على تذكرتك', 
            message=f'قام الدعم الفني بالرد على تذكرتك: {ticket.subject}. الرد: {reply}',
            link=url_for('dashboard.index')
        )
        db.session.commit()
        
        flash('تم إرسال الرد وإغلاق التذكرة بنجاح', 'success')
    return redirect(url_for('dashboard.index'))
