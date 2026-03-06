import os
from flask import Flask
from config import Config


def init_db():
    """Auto-create database tables on first startup."""
    from models import get_db
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Read and execute schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                cursor.execute(f.read())
            conn.commit()
            print("[DB] Base schema initialized.")

        # Read and execute alter_schema.sql
        alter_path = os.path.join(os.path.dirname(__file__), 'alter_schema.sql')
        if os.path.exists(alter_path):
            with open(alter_path, 'r') as f:
                cursor.execute(f.read())
            conn.commit()
            print("[DB] Migration schema applied.")

        # Seed admin user
        import bcrypt
        admin_password = 'admin123'
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            """INSERT INTO users (name, email, password_hash, role)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (email) DO NOTHING""",
            ('Admin', 'admin@library.com', password_hash, 'admin')
        )
        conn.commit()
        print("[DB] Admin account ready.")
    except Exception as e:
        print(f"[DB] Init error (may be OK if tables exist): {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

    # Auto-initialize database tables
    with app.app_context():
        init_db()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
