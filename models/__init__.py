import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from config import Config

# Connection pool for handling multiple simultaneous users
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,  # minconn
        10, # maxconn
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        dbname=Config.MYSQL_DATABASE
    )
except Exception as e:
    print(f"Error creating connection pool: {e}")
    db_pool = None

def get_db():
    """Get a connection from the pool."""
    if db_pool:
        # PostgreSQL connections need autocommit=True to behave like MySQL's default in some cases, 
        # but we'll stick to manual commit where needed.
        return db_pool.getconn()
    raise Exception("Database pool not initialized")

def get_dict_cursor(conn):
    """Helper to get a dictionary cursor for PostgreSQL."""
    return conn.cursor(cursor_factory=RealDictCursor)
