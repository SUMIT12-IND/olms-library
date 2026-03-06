from datetime import date, timedelta
from models import get_db, get_dict_cursor


def issue_book(user_id, book_id, due_days=14):
    """Issue a book to a user. Default loan period is 14 days."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        # Check availability
        cursor.execute("SELECT available_quantity FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        if not book or book['available_quantity'] <= 0:
            return False, "Book not available"

        issue_date = date.today()
        due_date = issue_date + timedelta(days=due_days)

        cursor.execute(
            "INSERT INTO issued_books (user_id, book_id, issue_date, due_date, status) VALUES (%s, %s, %s, %s, 'issued')",
            (user_id, book_id, issue_date, due_date)
        )
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity - 1, borrow_count = borrow_count + 1 WHERE id = %s",
            (book_id,)
        )
        conn.commit()
        return True, "Book issued successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def return_book(issued_id):
    """Mark a book as returned."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT * FROM issued_books WHERE id = %s AND return_date IS NULL", (issued_id,))
        record = cursor.fetchone()
        if not record:
            return False, "Record not found or already returned"

        cursor.execute(
            "UPDATE issued_books SET return_date = %s, status = 'returned' WHERE id = %s",
            (date.today(), issued_id)
        )
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity + 1 WHERE id = %s",
            (record['book_id'],)
        )
        conn.commit()
        return True, "Book returned successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def approve_request(issued_id, due_days=14):
    """Approve a book request – change status from 'requested' to 'issued'."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT * FROM issued_books WHERE id = %s AND status = 'requested'", (issued_id,))
        record = cursor.fetchone()
        if not record:
            return False, "Request not found"

        cursor.execute("SELECT available_quantity FROM books WHERE id = %s", (record['book_id'],))
        book = cursor.fetchone()
        if not book or book['available_quantity'] <= 0:
            return False, "Book not available"

        issue_date = date.today()
        due_date = issue_date + timedelta(days=due_days)

        cursor.execute(
            "UPDATE issued_books SET issue_date = %s, due_date = %s, status = 'issued' WHERE id = %s",
            (issue_date, due_date, issued_id)
        )
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity - 1 WHERE id = %s",
            (record['book_id'],)
        )
        conn.commit()
        return True, "Request approved"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def reject_request(issued_id):
    """Reject and delete a book request."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM issued_books WHERE id = %s AND status = 'requested'", (issued_id,))
        conn.commit()
        return True, "Request rejected"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def request_book(user_id, book_id):
    """User requests a book issue (pending admin approval)."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        # Check if user already has an active issue or request for this book
        cursor.execute(
            "SELECT id FROM issued_books WHERE user_id = %s AND book_id = %s AND status IN ('issued', 'requested')",
            (user_id, book_id)
        )
        if cursor.fetchone():
            return False, "You already have an active issue or pending request for this book"

        cursor.execute(
            "INSERT INTO issued_books (user_id, book_id, issue_date, due_date, status) VALUES (%s, %s, %s, %s, 'requested')",
            (user_id, book_id, date.today(), date.today())
        )
        conn.commit()
        return True, "Book request submitted successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def get_all_issued_books():
    """Get all issued/requested books with user and book info."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT ib.*, u.name AS user_name, u.email AS user_email,
                   b.title AS book_title, b.author AS book_author, b.isbn AS book_isbn,
                   CASE
                       WHEN ib.status = 'issued' AND ib.due_date < CURRENT_DATE THEN CAST(CURRENT_DATE - ib.due_date AS INTEGER)
                       ELSE 0
                   END AS overdue_days
            FROM issued_books ib
            JOIN users u ON ib.user_id = u.id
            JOIN books b ON ib.book_id = b.id
            ORDER BY ib.created_at DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_user_issued_books(user_id):
    """Get all books issued to a specific user."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT ib.*, b.title AS book_title, b.author AS book_author, b.isbn AS book_isbn,
                   CASE
                       WHEN ib.status = 'issued' AND ib.due_date < CURRENT_DATE THEN CAST(CURRENT_DATE - ib.due_date AS INTEGER)
                       ELSE 0
                   END AS overdue_days
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.id
            WHERE ib.user_id = %s
            ORDER BY ib.created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_overdue_books():
    """Get all overdue books (issued and past due date)."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT ib.*, u.name AS user_name, u.email AS user_email,
                   b.title AS book_title, b.author AS book_author,
                   CAST(CURRENT_DATE - ib.due_date AS INTEGER) AS overdue_days
            FROM issued_books ib
            JOIN users u ON ib.user_id = u.id
            JOIN books b ON ib.book_id = b.id
            WHERE ib.status = 'issued' AND ib.due_date < CURRENT_DATE
            ORDER BY overdue_days DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_dashboard_stats():
    """Get summary stats for admin dashboard."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        stats = {}
        cursor.execute("SELECT COUNT(*) AS total FROM books")
        stats['total_books'] = cursor.fetchone()['total']

        cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM books")
        stats['total_copies'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'user'")
        stats['total_users'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM issued_books WHERE status = 'issued'")
        stats['books_issued'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM issued_books WHERE status = 'issued' AND due_date < CURRENT_DATE")
        stats['overdue_books'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM issued_books WHERE status = 'requested'")
        stats['pending_requests'] = cursor.fetchone()['total']

        return stats
    finally:
        cursor.close()
        conn.close()


def get_pending_requests():
    """Get all pending book requests."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT ib.*, u.name AS user_name, u.email AS user_email,
                   b.title AS book_title, b.author AS book_author, b.isbn AS book_isbn,
                   b.available_quantity
            FROM issued_books ib
            JOIN users u ON ib.user_id = u.id
            JOIN books b ON ib.book_id = b.id
            WHERE ib.status = 'requested'
            ORDER BY ib.created_at ASC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
