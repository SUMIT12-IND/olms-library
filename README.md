# Online Library Management System (OLMS)

A full-stack web-based library management system built with **Flask**, **MySQL**, and **HTML/CSS**.

## Features

- **Role-based access**: Admin and User roles
- **Admin dashboard**: Stats, overdue alerts, pending book requests
- **Book management**: Add, edit, delete books with ISBN tracking
- **User management**: View, block, unblock, delete users
- **Book issuing**: Issue books, track due dates, mark returns
- **User requests**: Users can request books; admins approve/reject
- **Overdue tracking**: Automatic overdue day calculations
- **Search**: Search books by title, author, or category
- **Responsive UI**: Works on desktop, tablet, and mobile

## Prerequisites

- **Python 3.8+**
- **MySQL 8.0+** (running on localhost:3306)
- **pip** (Python package manager)

## Setup Instructions

### 1. Create MySQL Database

Open MySQL shell and run the schema file:

```bash
mysql -u root -p < schema.sql
```

Or copy-paste the contents of `schema.sql` into MySQL Workbench / phpMyAdmin.

### 2. Configure Environment

Create a `.env` file in the `olms/` folder:

```env
SECRET_KEY=your-super-secret-key-here
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=olms_db
```

### 3. Install Dependencies

```bash
cd olms
pip install -r requirements.txt
```

### 4. Seed Admin Account

```bash
python setup_db.py
```

### 5. Run the App

```bash
python app.py
```

The app will start at **http://localhost:5000**

### 6. Login

**Admin account** (seeded automatically):
- Email: `admin@library.com`
- Password: `admin123`

**User account**: Register a new user via the registration page.

## Project Structure

```
olms/
├── app.py                   # Flask entry point
├── config.py                # Configuration
├── schema.sql               # MySQL schema + admin seed
├── requirements.txt         # Python dependencies
├── README.md
├── models/
│   ├── __init__.py          # DB connection pool
│   ├── user.py              # User model
│   ├── book.py              # Book model
│   └── issued_book.py       # Issued book model
├── routes/
│   ├── __init__.py
│   ├── auth.py              # Authentication routes
│   ├── admin.py             # Admin routes
│   └── user.py              # User routes
├── static/css/style.css     # Styles
└── templates/
    ├── base.html            # Base layout
    ├── login.html
    ├── register.html
    ├── admin/               # Admin templates
    └── user/                # User templates
```

## Tech Stack

| Layer    | Technology        |
|----------|-------------------|
| Frontend | HTML, CSS, Jinja2 |
| Backend  | Python (Flask)    |
| Database | MySQL             |
| Auth     | bcrypt            |
