from models import get_db


def get_recommendations(user_id, limit=8):
    """Content-based recommendation: suggest books based on user's reading history (category + author matching + popularity)."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get user's preferred categories and authors
        cursor.execute("""
            SELECT b.category, b.author
            FROM issued_books ib
            JOIN books b ON ib.book_id = b.id
            WHERE ib.user_id = %s
        """, (user_id,))
        history = cursor.fetchall()

        if not history:
            # No history: return popular books
            return get_most_borrowed(limit)

        categories = {}
        authors = {}
        for row in history:
            categories[row['category']] = categories.get(row['category'], 0) + 1
            authors[row['author']] = authors.get(row['author'], 0) + 1

        # Get books user hasn't borrowed
        cursor.execute("""
            SELECT b.* FROM books b
            WHERE b.id NOT IN (
                SELECT book_id FROM issued_books WHERE user_id = %s AND status IN ('issued', 'returned')
            )
            AND b.available_quantity > 0
        """, (user_id,))
        candidates = cursor.fetchall()

        # Score each candidate
        scored = []
        for book in candidates:
            score = 0
            score += categories.get(book['category'], 0) * 3
            score += authors.get(book['author'], 0) * 2
            score += min(book.get('borrow_count', 0), 10)  # cap popularity score
            scored.append((score, book))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
    finally:
        cursor.close()
        conn.close()


def get_trending(limit=6):
    """Get trending books (most borrowed in last 30 days)."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.*, COUNT(ib.id) AS recent_borrows
            FROM books b
            JOIN issued_books ib ON b.id = ib.book_id
            WHERE ib.issue_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY b.id
            ORDER BY recent_borrows DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_most_borrowed(limit=6):
    """Get most borrowed books of all time."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM books ORDER BY borrow_count DESC LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
