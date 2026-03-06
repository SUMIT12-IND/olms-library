import mysql.connector
from mysql.connector import pooling
from config import Config

# Connection pool for handling multiple simultaneous users
db_pool = pooling.MySQLConnectionPool(
    pool_name="olms_pool",
    pool_size=10,
    host=Config.MYSQL_HOST,
    port=Config.MYSQL_PORT,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DATABASE
)


def get_db():
    """Get a connection from the pool."""
    return db_pool.get_connection()
