from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.book import get_all_books, search_books, search_books_advanced, get_book_by_id, get_all_categories, autocomplete_books
from models.issued_book import get_user_issued_books, request_book
from models.notification import get_user_notifications, get_unread_count, mark_read, mark_all_read
from models.message import send_message, get_conversation, mark_messages_read, get_admin_id, get_unread_message_count, get_user_chats, get_all_users_for_chat
from models.fine import get_user_fines, get_user_total_unpaid, calculate_and_update_fines
from models.recommendation import get_recommendations, get_trending, get_most_borrowed

user_bp = Blueprint('user', __name__, url_prefix='/user')


def login_required(f):
    """Decorator to restrict access to logged-in users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'user':
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@user_bp.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    issued = get_user_issued_books(uid)
    active_books = [b for b in issued if b['status'] == 'issued']
    overdue_books = [b for b in issued if b['status'] == 'issued' and b['overdue_days'] > 0]
    requested_books = [b for b in issued if b['status'] == 'requested']

    # Fines
    calculate_and_update_fines()
    total_fine = get_user_total_unpaid(uid)

    # Recommendations
    recommendations = get_recommendations(uid)
    trending = get_trending()
    most_borrowed = get_most_borrowed()

    # Notifications
    notif_count = get_unread_count(uid)

    return render_template('user/dashboard.html',
                           active_books=active_books,
                           overdue_books=overdue_books,
                           requested_books=requested_books,
                           total_fine=total_fine,
                           recommendations=recommendations,
                           trending=trending,
                           most_borrowed=most_borrowed,
                           notif_count=notif_count)


@user_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    search_by = request.args.get('search_by', 'all')
    available_only = request.args.get('available_only') == '1'
    category_filter = request.args.get('category', '')
    sort_by = request.args.get('sort_by', 'title')

    results = search_books_advanced(query, search_by, available_only, category_filter, sort_by)
    categories = get_all_categories()

    return render_template('user/search.html', books=results, query=query,
                           search_by=search_by, available_only=available_only,
                           category_filter=category_filter, sort_by=sort_by,
                           categories=categories)


@user_bp.route('/my-books')
@login_required
def my_books():
    issued = get_user_issued_books(session['user_id'])
    fines = get_user_fines(session['user_id'])
    return render_template('user/my_books.html', books=issued, fines=fines)


@user_bp.route('/request/<int:book_id>', methods=['POST'])
@login_required
def request_book_route(book_id):
    success, msg = request_book(session['user_id'], book_id)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('user.search'))


# ─── Notifications (Feature 2) ───────────────────
@user_bp.route('/notifications')
@login_required
def notifications():
    notifs = get_user_notifications(session['user_id'])
    return render_template('user/notifications.html', notifications=notifs)


@user_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def read_notification(notif_id):
    mark_read(notif_id, session['user_id'])
    return redirect(url_for('user.notifications'))


@user_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def read_all_notifications():
    mark_all_read(session['user_id'])
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('user.notifications'))


# ─── Chat (Feature 3 – All Users) ────────────────
@user_bp.route('/chat')
@login_required
def chat():
    """Show chat list with all conversations + option to start new ones."""
    my_id = session['user_id']
    chats = get_user_chats(my_id)
    all_users = get_all_users_for_chat(my_id)
    return render_template('user/chat.html', chats=chats, all_users=all_users,
                           active_chat=None, messages=[])


@user_bp.route('/chat/<int:other_id>')
@login_required
def chat_with_user(other_id):
    """Chat with a specific user."""
    my_id = session['user_id']
    chats = get_user_chats(my_id)
    all_users = get_all_users_for_chat(my_id)
    messages = get_conversation(my_id, other_id)
    mark_messages_read(other_id, my_id)
    return render_template('user/chat.html', chats=chats, all_users=all_users,
                           active_chat=other_id, messages=messages)


@user_bp.route('/chat/<int:other_id>/send', methods=['POST'])
@login_required
def send_chat(other_id):
    msg = request.form.get('message', '').strip()
    if msg:
        send_message(session['user_id'], other_id, msg)
    return redirect(url_for('user.chat_with_user', other_id=other_id))


# ─── Virtual Library (Feature 9) ─────────────────
@user_bp.route('/library')
@login_required
def library():
    all_books = get_all_books()
    categories = get_all_categories()
    return render_template('user/library.html', books=all_books, categories=categories)


# ─── API Endpoints ───────────────────────────────
@user_bp.route('/api/search')
@login_required
def api_search():
    """JSON endpoint for AJAX search with autocomplete."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    results = autocomplete_books(query)
    return jsonify(results)


@user_bp.route('/api/notifications/count')
@login_required
def api_notif_count():
    count = get_unread_count(session['user_id'])
    msg_count = get_unread_message_count(session['user_id'])
    return jsonify({'notifications': count, 'messages': msg_count})
