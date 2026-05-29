from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import db, Message, User, UserBlock
from app.services.content_filter import filter_message
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def list():
    sent_msgs = Message.query.filter_by(sender_id=current_user.id).all()
    received_msgs = Message.query.filter_by(receiver_id=current_user.id).all()
    
    user_ids = set([m.receiver_id for m in sent_msgs] + [m.sender_id for m in received_msgs])
    chat_users = User.query.filter(User.id.in_(user_ids)).all()
    
    unread_counts = {}
    for uid in user_ids:
        cc = Message.query.filter_by(sender_id=uid, receiver_id=current_user.id, is_read=False).count()
        unread_counts[uid] = cc
    
    return render_template('chat/list.html', chat_users=chat_users, unread_counts=unread_counts)

@chat_bp.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def talk(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Check if blocked
    is_blocked = UserBlock.query.filter(
        or_(
            and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user_id),
            and_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == current_user.id)
        )
    ).first()
    
    if is_blocked:
        flash('لا يمكن مراسلة هذا المستخدم بسبب وجود حظر.', 'danger')
        return redirect(url_for('chat.list'))
    
    if request.method == 'POST':
        content = request.form.get('content', '')
        if content.strip():
            filtered_content, was_modified = filter_message(content)
            
            if was_modified:
                flash('تم تعديل الرسالة آلياً لحجب معلومات الاتصال أو الألفاظ غير اللائقة.', 'warning')
            
            msg = Message(sender_id=current_user.id, receiver_id=user_id, content=filtered_content)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('chat.talk', user_id=user_id))
    
    Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at).all()
    
    return render_template('chat/chat.html', other_user=other_user, messages=messages)
