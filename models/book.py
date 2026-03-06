import io
import base64
import qrcode
from models import get_db, get_dict_cursor


def generate_qr_code(book_id):
    """Generate a base64-encoded QR code PNG for a book."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"OLMS_BOOK_{book_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def add_book(title, author, category, isbn, quantity):
    """Add a new book to the library."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO books (title, author, category, isbn, quantity, available_quantity) VALUES (%s, %s, %s, %s, %s, %s)",
            (title, author, category, isbn, quantity, quantity)
        )
        book_id = cursor.lastrowid
        # Generate and store QR code
        qr_data = generate_qr_code(book_id)
        cursor.execute("UPDATE books SET qr_code = %s WHERE id = %s", (qr_data, book_id))
        conn.commit()
        return book_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def update_book(book_id, title, author, category, isbn, quantity):
    """Update an existing book's details."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        # Calculate the difference to adjust available_quantity
        cursor.execute("SELECT quantity, available_quantity FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        if not book:
            return False

        diff = quantity - book['quantity']
        new_available = max(0, book['available_quantity'] + diff)

        cursor.execute(
            "UPDATE books SET title=%s, author=%s, category=%s, isbn=%s, quantity=%s, available_quantity=%s WHERE id=%s",
            (title, author, category, isbn, quantity, new_available, book_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def delete_book(book_id):
    """Delete a book from the library."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_all_books():
    """Get all books."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT * FROM books ORDER BY title ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_book_by_id(book_id):
    """Get a single book by ID."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def search_books(query, search_by='title'):
    """Search books by title, author, or category."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        allowed_fields = {'title', 'author', 'category', 'isbn'}
        if search_by not in allowed_fields:
            search_by = 'title'

        sql = f"SELECT * FROM books WHERE {search_by} LIKE %s ORDER BY title ASC"
        cursor.execute(sql, (f"%{query}%",))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def search_books_advanced(query='', search_by='all', available_only=False, category_filter='', sort_by='title'):
    """Advanced search with multi-field matching, filters, and sorting."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        conditions = []
        params = []

        if query:
            if search_by == 'all':
                conditions.append("(title LIKE %s OR author LIKE %s OR category LIKE %s OR isbn LIKE %s)")
                params.extend([f"%{query}%"] * 4)
            else:
                allowed = {'title', 'author', 'category', 'isbn'}
                field = search_by if search_by in allowed else 'title'
                conditions.append(f"{field} LIKE %s")
                params.append(f"%{query}%")

        if available_only:
            conditions.append("available_quantity > 0")

        if category_filter:
            conditions.append("category = %s")
            params.append(category_filter)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        sort_map = {
            'title': 'title ASC',
            'author': 'author ASC',
            'popular': 'borrow_count DESC',
            'newest': 'created_at DESC'
        }
        order = sort_map.get(sort_by, 'title ASC')

        sql = f"SELECT * FROM books {where} ORDER BY {order}"
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_categories():
    """Get distinct book categories."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT DISTINCT category FROM books ORDER BY category ASC")
        return [row['category'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def autocomplete_books(query, limit=8):
    """Get autocomplete suggestions (title + author)."""
    conn = get_db()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute(
            "SELECT id, title, author, category FROM books WHERE title LIKE %s OR author LIKE %s LIMIT %s",
            (f"%{query}%", f"%{query}%", limit)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

