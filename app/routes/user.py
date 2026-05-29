from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Report, UserBlock

user_bp = Blueprint('user', __name__)

@user_bp.route('/report/<int:user_id>', methods=['POST'])
@login_required
def report_user(user_id):
    reported_user = User.query.get_or_404(user_id)
    if reported_user.id == current_user.id:
        flash('لا يمكنك الإبلاغ عن نفسك', 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    reason = request.form.get('reason')
    if not reason or len(reason.strip()) < 5:
        flash('يرجى كتابة سبب البلاغ بوضوح (5 أحرف على الأقل)', 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    new_report = Report(
        reporter_id=current_user.id,
        reported_user_id=reported_user.id,
        reason=reason
    )
    db.session.add(new_report)
    db.session.commit()
    
    flash('تم إرسال بلاغك للإدارة، شكراً لمساعدتنا في الحفاظ على أمان المنصة', 'success')
    return redirect(request.referrer or url_for('main.index'))

@user_bp.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user_to_block = User.query.get_or_404(user_id)
    if user_to_block.id == current_user.id:
        flash('لا يمكنك حظر نفسك', 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    # Check if already blocked
    existing_block = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user_to_block.id).first()
    if existing_block:
        flash('هذا المستخدم محظور بالفعل', 'info')
        return redirect(request.referrer or url_for('main.index'))
    
    new_block = UserBlock(blocker_id=current_user.id, blocked_id=user_to_block.id)
    db.session.add(new_block)
    db.session.commit()
    
    flash(f'تم حظر {user_to_block.username} بنجاح. لن يتمكن من مراسلتك.', 'success')
    return redirect(request.referrer or url_for('main.index'))

@user_bp.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    block = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user_id).first_or_404()
    db.session.delete(block)
    db.session.commit()
    flash('تم إلغاء الحظر بنجاح', 'success')
    return redirect(request.referrer or url_for('main.index'))
