from datetime import date
from models import get_db, get_dict_cursor

FINE_PER_DAY = 5.00  # Rs. 5 per day


def calculate_and_update_fines():
    """Calculate fines for all overdue books and upsert into fines table."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT ib.id AS issued_book_id, ib.user_id, ib.due_date,
                   CAST(CURRENT_DATE - ib.due_date AS INTEGER) AS overdue_days
            FROM issued_books ib
            WHERE ib.status = 'issued' AND ib.due_date < CURRENT_DATE
        """)
        overdue = cursor.fetchall()

        for record in overdue:
            amount = round(record['overdue_days'] * FINE_PER_DAY, 2)
            # Upsert: update if exists, insert if not
            cursor.execute("""
                INSERT INTO fines (user_id, issued_book_id, amount)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, issued_book_id) DO UPDATE SET amount = EXCLUDED.amount
            """, (record['user_id'], record['issued_book_id'], amount))

        conn.commit()
    except Exception:
        # If duplicate key constraint doesn't exist, use select-then-update approach
        conn.rollback()
        for record in overdue:
            amount = round(record['overdue_days'] * FINE_PER_DAY, 2)
            cursor.execute(
                "SELECT id FROM fines WHERE issued_book_id = %s AND is_paid = 0",
                (record['issued_book_id'],)
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE fines SET amount = %s WHERE id = %s",
                    (amount, existing['id'])
                )
            else:
                cursor.execute(
                    "INSERT INTO fines (user_id, issued_book_id, amount) VALUES (%s, %s, %s)",
                    (record['user_id'], record['issued_book_id'], amount)
                )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_user_fines(user_id):
    """Get all fines for a user."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT f.*, b.title AS book_title, b.author AS book_author,
                   ib.due_date, ib.return_date,
                   CAST(CURRENT_DATE - ib.due_date AS INTEGER) AS overdue_days
            FROM fines f
            JOIN issued_books ib ON f.issued_book_id = ib.id
            JOIN books b ON ib.book_id = b.id
            WHERE f.user_id = %s
            ORDER BY f.is_paid ASC, f.created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_fines():
    """Get all fines (admin view)."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT f.*, u.name AS user_name, u.email AS user_email,
                   b.title AS book_title, ib.due_date,
                   CAST(CURRENT_DATE - ib.due_date AS INTEGER) AS overdue_days
            FROM fines f
            JOIN users u ON f.user_id = u.id
            JOIN issued_books ib ON f.issued_book_id = ib.id
            JOIN books b ON ib.book_id = b.id
            ORDER BY f.is_paid ASC, f.amount DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def mark_fine_paid(fine_id):
    """Mark a fine as paid."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE fines SET is_paid = 1, paid_at = NOW() WHERE id = %s",
            (fine_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_user_total_unpaid(user_id):
    """Get total unpaid fine amount for a user."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM fines WHERE user_id = %s AND is_paid = 0",
            (user_id,)
        )
        return float(cursor.fetchone()['total'])
    finally:
        cursor.close()
        conn.close()
