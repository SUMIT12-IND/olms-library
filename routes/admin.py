from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.book import add_book, update_book, delete_book, get_all_books, get_book_by_id
from models.user import get_all_users, block_user, delete_user
from models.issued_book import (
    issue_book, return_book, get_all_issued_books, get_overdue_books,
    get_dashboard_stats, get_pending_requests, approve_request, reject_request
)
from models.fine import get_all_fines, mark_fine_paid, calculate_and_update_fines
from models.message import get_user_chats, get_conversation, send_message, mark_messages_read, get_admin_id, get_all_users_for_chat
from models.notification import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to restrict access to admin users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ─── Dashboard ──────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = get_dashboard_stats()
    overdue = get_overdue_books()
    requests = get_pending_requests()
    return render_template('admin/dashboard.html', stats=stats, overdue=overdue, requests=requests)


# ─── Book Management ───────────────────────────────
@admin_bp.route('/books')
@admin_required
def books():
    all_books = get_all_books()
    return render_template('admin/books.html', books=all_books)


@admin_bp.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book_route():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        isbn = request.form.get('isbn', '').strip()
        quantity = request.form.get('quantity', '1').strip()

        if not all([title, author, category, isbn]):
            flash('All fields are required.', 'error')
            return render_template('admin/add_book.html')

        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except ValueError:
            flash('Quantity must be a positive number.', 'error')
            return render_template('admin/add_book.html')

        try:
            add_book(title, author, category, isbn, quantity)
            flash(f'Book "{title}" added successfully!', 'success')
            return redirect(url_for('admin.books'))
        except Exception as e:
            if 'Duplicate entry' in str(e):
                flash('A book with this ISBN already exists.', 'error')
            else:
                flash('Error adding book. Please try again.', 'error')
            return render_template('admin/add_book.html')

    return render_template('admin/add_book.html')


@admin_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book_route(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('admin.books'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        isbn = request.form.get('isbn', '').strip()
        quantity = request.form.get('quantity', '1').strip()

        if not all([title, author, category, isbn]):
            flash('All fields are required.', 'error')
            return render_template('admin/edit_book.html', book=book)

        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except ValueError:
            flash('Quantity must be a positive number.', 'error')
            return render_template('admin/edit_book.html', book=book)

        try:
            update_book(book_id, title, author, category, isbn, quantity)
            flash(f'Book "{title}" updated successfully!', 'success')
            return redirect(url_for('admin.books'))
        except Exception as e:
            if 'Duplicate entry' in str(e):
                flash('A book with this ISBN already exists.', 'error')
            else:
                flash('Error updating book. Please try again.', 'error')
            return render_template('admin/edit_book.html', book=book)

    return render_template('admin/edit_book.html', book=book)


@admin_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book_route(book_id):
    delete_book(book_id)
    flash('Book deleted successfully.', 'success')
    return redirect(url_for('admin.books'))


# ─── User Management ──────────────────────────────
@admin_bp.route('/users')
@admin_required
def users():
    all_users = get_all_users()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/block/<int:user_id>', methods=['POST'])
@admin_required
def block_user_route(user_id):
    action = request.form.get('action', 'block')
    block_user(user_id, block=(action == 'block'))
    flash(f'User {"blocked" if action == "block" else "unblocked"} successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user_route(user_id):
    delete_user(user_id)
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.users'))


# ─── Issue & Return ───────────────────────────────
@admin_bp.route('/issue', methods=['GET', 'POST'])
@admin_required
def issue_book_route():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        book_id = request.form.get('book_id')
        due_days = request.form.get('due_days', '14')

        if not user_id or not book_id:
            flash('Please select a user and a book.', 'error')
        else:
            try:
                due_days = int(due_days)
            except ValueError:
                due_days = 14

            success, msg = issue_book(int(user_id), int(book_id), due_days)
            if success:
                # Create notification for the user
                book = get_book_by_id(int(book_id))
                book_title = book['title'] if book else 'a book'
                create_notification(
                    int(user_id),
                    'Book Issued',
                    f'"{book_title}" has been issued to you. Due in {due_days} days.',
                    'success'
                )
            flash(msg, 'success' if success else 'error')
            if success:
                return redirect(url_for('admin.reports'))

    users_list = get_all_users()
    books_list = get_all_books()
    return render_template('admin/issue_book.html', users=users_list, books=books_list)


@admin_bp.route('/return/<int:issued_id>', methods=['POST'])
@admin_required
def return_book_route(issued_id):
    success, msg = return_book(issued_id)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('admin.reports'))


@admin_bp.route('/requests/approve/<int:issued_id>', methods=['POST'])
@admin_required
def approve_request_route(issued_id):
    success, msg = approve_request(issued_id)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/requests/reject/<int:issued_id>', methods=['POST'])
@admin_required
def reject_request_route(issued_id):
    success, msg = reject_request(issued_id)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('admin.dashboard'))


# ─── Reports ──────────────────────────────────────
@admin_bp.route('/reports')
@admin_required
def reports():
    issued = get_all_issued_books()
    overdue = get_overdue_books()
    return render_template('admin/reports.html', issued=issued, overdue=overdue)


# ─── Fines (Feature 5) ───────────────────────────
@admin_bp.route('/fines')
@admin_required
def fines():
    calculate_and_update_fines()
    all_fines = get_all_fines()
    return render_template('admin/fines.html', fines=all_fines)


@admin_bp.route('/fines/pay/<int:fine_id>', methods=['POST'])
@admin_required
def pay_fine_route(fine_id):
    mark_fine_paid(fine_id)
    flash('Fine marked as paid.', 'success')
    return redirect(url_for('admin.fines'))


# ─── Chat (Feature 3 – All Users) ────────────────
@admin_bp.route('/chat')
@admin_required
def chat_list():
    """Show admin chat list + option to start new ones."""
    my_id = session['user_id']
    chats = get_user_chats(my_id)
    all_users = get_all_users_for_chat(my_id)
    return render_template('admin/chat.html', chats=chats, all_users=all_users,
                           active_chat=None, messages=[])


@admin_bp.route('/chat/<int:user_id>')
@admin_required
def chat_with_user(user_id):
    """Chat with a specific user from admin side."""
    my_id = session['user_id']
    chats = get_user_chats(my_id)
    all_users = get_all_users_for_chat(my_id)
    messages = get_conversation(my_id, user_id)
    mark_messages_read(user_id, my_id)
    return render_template('admin/chat.html', chats=chats, all_users=all_users,
                           active_chat=user_id, messages=messages)


@admin_bp.route('/chat/<int:user_id>/send', methods=['POST'])
@admin_required
def send_chat(user_id):
    msg = request.form.get('message', '').strip()
    if msg:
        send_message(session['user_id'], user_id, msg)
    return redirect(url_for('admin.chat_with_user', user_id=user_id))


# ─── QR Scanner (Feature 6) ──────────────────────
@admin_bp.route('/scan')
@admin_required
def scan():
    return render_template('admin/scan.html')


@admin_bp.route('/api/scan', methods=['POST'])
@admin_required
def api_scan():
    """Process a scanned QR code. Expected format: OLMS_BOOK_{id}"""
    data = request.get_json()
    qr_data = data.get('qr_data', '')

    if not qr_data.startswith('OLMS_BOOK_'):
        return jsonify({'success': False, 'message': 'Invalid QR code'})

    try:
        book_id = int(qr_data.replace('OLMS_BOOK_', ''))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid book ID in QR code'})

    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': 'Book not found'})

    return jsonify({
        'success': True,
        'book': {
            'id': book['id'],
            'title': book['title'],
            'author': book['author'],
            'isbn': book['isbn'],
            'available': book['available_quantity']
        }
    })


@admin_bp.route('/api/scan/issue', methods=['POST'])
@admin_required
def api_scan_issue():
    """Issue or return a book via QR scan."""
    data = request.get_json()
    book_id = data.get('book_id')
    user_id = data.get('user_id')
    action = data.get('action', 'issue')

    if action == 'issue':
        success, msg = issue_book(int(user_id), int(book_id))
        if success:
            book = get_book_by_id(int(book_id))
            create_notification(int(user_id), 'Book Issued', f'"{book["title"]}" issued via QR scan.', 'success')
        return jsonify({'success': success, 'message': msg})
    else:
        issued_id = data.get('issued_id')
        if issued_id:
            success, msg = return_book(int(issued_id))
            return jsonify({'success': success, 'message': msg})
        return jsonify({'success': False, 'message': 'Missing issued_id'})
