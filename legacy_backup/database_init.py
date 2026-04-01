import os
import hashlib
import psycopg
from psycopg.errors import UniqueViolation

def hash_password(password):
    """Securely hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return psycopg.connect(db_url)

def init_db():
    """Initialize PostgreSQL database for user management."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS users')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            user_type VARCHAR(50) NOT NULL,
            farm_location VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_user(first_name, last_name, email, password, user_type, farm_location=None):
    """Add a new user to the database."""
    conn = get_db_connection()
    hashed_password = hash_password(password)
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
            INSERT INTO users (first_name, last_name, email, password, user_type, farm_location)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (first_name, last_name, email, hashed_password, user_type, farm_location))
            conn.commit()
            return True
    except UniqueViolation:
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_user(email, password):
    """Verify user credentials."""
    conn = get_db_connection()
    hashed_password = hash_password(password)
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, hashed_password))
        user = cursor.fetchone()
    conn.close()
    return user is not None

if __name__ == '__main__':
    init_db()
