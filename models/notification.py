from models import get_db


def create_notification(user_id, title, message, notif_type='info'):
    """Create a notification for a user."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO notifications (user_id, title, message, notif_type) VALUES (%s, %s, %s, %s)",
            (user_id, title, message, notif_type)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_user_notifications(user_id, limit=20):
    """Get notifications for a user."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_unread_count(user_id):
    """Get unread notification count."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
        return cursor.fetchone()['cnt']
    finally:
        cursor.close()
        conn.close()


def mark_read(notification_id, user_id):
    """Mark a notification as read."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, user_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def mark_all_read(user_id):
    """Mark all notifications as read."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
