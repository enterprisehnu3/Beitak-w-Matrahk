from app.models import db, Notification

def send_notification(user_id, title, message, link=None):
    """
    Creates a notification for a user.
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        link=link
    )
    db.session.add(notification)
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
