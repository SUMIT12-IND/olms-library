from models import get_db, get_dict_cursor


def send_message(sender_id, receiver_id, message):
    """Send a chat message."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s) RETURNING id",
            (sender_id, receiver_id, message)
        )
        conn.commit()
        return cursor.fetchone()[0]
    finally:
        cursor.close()
        conn.close()


def get_conversation(user_id, other_id):
    """Get messages between two users."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT m.*, 
                   s.name AS sender_name, r.name AS receiver_name
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.receiver_id = r.id
            WHERE (m.sender_id = %s AND m.receiver_id = %s)
               OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.created_at ASC
        """, (user_id, other_id, other_id, user_id))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_admin_id():
    """Get the first admin user id."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        admin = cursor.fetchone()
        return admin['id'] if admin else None
    finally:
        cursor.close()
        conn.close()


def get_user_chats(my_id):
    """Get list of users who have chatted with this user (admin or regular)."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT DISTINCT u.id, u.name, u.email, u.role,
                   (SELECT COUNT(*) FROM messages WHERE sender_id = u.id AND receiver_id = %s AND is_read = 0) AS unread
            FROM users u
            JOIN messages m ON (m.sender_id = u.id OR m.receiver_id = u.id)
            WHERE u.id != %s
              AND (m.sender_id = %s OR m.receiver_id = %s)
              AND (m.sender_id = u.id OR m.receiver_id = u.id)
            ORDER BY (SELECT MAX(created_at) FROM messages
                      WHERE (sender_id = u.id AND receiver_id = %s)
                         OR (sender_id = %s AND receiver_id = u.id)) DESC
        """, (my_id, my_id, my_id, my_id, my_id, my_id))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_users_for_chat(my_id):
    """Get all users (except self) available to start a new chat with."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT id, name, email, role FROM users
            WHERE id != %s AND is_blocked = 0
            ORDER BY name ASC
        """, (my_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def mark_messages_read(sender_id, receiver_id):
    """Mark messages from sender to receiver as read."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE messages SET is_read = 1 WHERE sender_id = %s AND receiver_id = %s",
            (sender_id, receiver_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_unread_message_count(user_id):
    """Get total unread message count for a user."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM messages WHERE receiver_id = %s AND is_read = 0",
            (user_id,)
        )
        return cursor.fetchone()['cnt']
    finally:
        cursor.close()
        conn.close()
