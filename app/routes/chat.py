from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import db, Message, User, UserBlock
from app.services.content_filter import filter_message
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def list():
    if not current_user.is_verified and current_user.role != 'admin':
        flash('يجب توثيق حسابك برفع صورة البطاقة وتأكيد الهوية لتتمكن من استخدام نظام الرسائل.', 'warning')
        return redirect(url_for('dashboard.index'))

    from app.models import Conversation
    conversations = Conversation.query.filter(
        or_(
            Conversation.tenant_id == current_user.id,
            Conversation.homeowner_id == current_user.id
        )
    ).all()
    
    conv_user_ids = set()
    for c in conversations:
        conv_user_ids.add(c.tenant_id if c.tenant_id != current_user.id else c.homeowner_id)
        
    sent_msgs = Message.query.filter_by(sender_id=current_user.id).all()
    received_msgs = Message.query.filter_by(receiver_id=current_user.id).all()
    msg_user_ids = set([m.receiver_id for m in sent_msgs] + [m.sender_id for m in received_msgs])
    
    user_ids = conv_user_ids.union(msg_user_ids)
    chat_users = []
    if user_ids:
        chat_users = User.query.filter(User.id.in_(user_ids)).all()
    
    unread_counts = {}
    for uid in user_ids:
        cc = Message.query.filter_by(sender_id=uid, receiver_id=current_user.id, is_read=False).count()
        unread_counts[uid] = cc
    
    return render_template('chat/list.html', chat_users=chat_users, unread_counts=unread_counts)

@chat_bp.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def talk(user_id):
    if not current_user.is_verified and current_user.role != 'admin':
        flash('يجب توثيق حسابك برفع صورة البطاقة وتأكيد الهوية لتتمكن من مراسلة المستخدمين.', 'warning')
        return redirect(url_for('dashboard.index'))

    from app.models import Conversation
    other_user = User.query.get_or_404(user_id)
    
    if not other_user.is_verified and other_user.role != 'admin' and current_user.role != 'admin':
        flash('لا يمكن مراسلة هذا المستخدم لأنه غير موثق.', 'warning')
        return redirect(url_for('chat.list'))
    
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
        
    # Get or create conversation
    conversation = Conversation.query.filter(
        or_(
            and_(Conversation.tenant_id == current_user.id, Conversation.homeowner_id == user_id),
            and_(Conversation.tenant_id == user_id, Conversation.homeowner_id == current_user.id)
        )
    ).first()
    
    if not conversation:
        # Determine tenant vs homeowner based on roles
        if current_user.role == 'homeowner':
            t_id = user_id
            h_id = current_user.id
        else:
            t_id = current_user.id
            h_id = user_id
            
        conversation = Conversation(
            tenant_id=t_id,
            homeowner_id=h_id,
            status='open'
        )
        db.session.add(conversation)
        db.session.commit()
    
    if request.method == 'POST':
        content = request.form.get('content', '')
        if content.strip():
            filtered_content, was_modified = filter_message(content)
            
            if was_modified:
                flash('تم تعديل الرسالة آلياً لحجب معلومات الاتصال أو الألفاظ غير اللائقة.', 'warning')
            
            msg = Message(
                sender_id=current_user.id, 
                receiver_id=user_id, 
                content=filtered_content,
                conversation_id=conversation.id
            )
            db.session.add(msg)
            from datetime import datetime
            conversation.updated_at = datetime.utcnow()
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
