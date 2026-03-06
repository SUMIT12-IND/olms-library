"""
Database setup script for OLMS.
Run this after creating the database with schema.sql to seed the admin account.

Usage:
    python setup_db.py
"""

import bcrypt
import psycopg2
from config import Config


def setup():
    conn = psycopg2.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        dbname=Config.MYSQL_DATABASE
    )
    cursor = conn.cursor()

    # Generate bcrypt hash for admin password
    admin_password = 'admin123'
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute(
            """INSERT INTO users (name, email, password_hash, role)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name""",
            ('Admin', 'admin@library.com', password_hash, 'admin')
        )
        conn.commit()
        print("[OK] Admin account created/verified successfully!")
        print("   Email:    admin@library.com")
        print("   Password: admin123")
    except Exception as e:
        print(f"[ERROR] {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    setup()
