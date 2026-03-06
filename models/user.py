import bcrypt
from models import get_db


def create_user(name, email, password, role='user'):
    """Register a new user with hashed password."""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (name, email, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email):
    """Fetch a user by email."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    """Fetch a user by ID."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_users():
    """Fetch all non-admin users."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, email, is_blocked, created_at FROM users WHERE role = 'user' ORDER BY created_at DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def verify_password(plain_password, hashed_password):
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def block_user(user_id, block=True):
    """Block or unblock a user."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET is_blocked = %s WHERE id = %s", (1 if block else 0, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def delete_user(user_id):
    """Delete a user."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s AND role = 'user'", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
