import psycopg
from psycopg.rows import dict_row
from config import Config
import os

# Build the connection string for PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# If DATABASE_URL is provided (e.g., from Render), use it directly
# Otherwise, build it from individual config variables
if DATABASE_URL:
    conninfo = DATABASE_URL
else:
    conninfo = f"host={Config.MYSQL_HOST} port={Config.MYSQL_PORT} user={Config.MYSQL_USER} password={Config.MYSQL_PASSWORD} dbname={Config.MYSQL_DATABASE}"

def get_db():
    """Get a new database connection."""
    try:
        conn = psycopg.connect(conninfo, autocommit=False)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def get_dict_cursor(conn):
    """Helper to get a dictionary cursor for PostgreSQL."""
    return conn.cursor(row_factory=dict_row)
