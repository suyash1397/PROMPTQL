"""Script to set up test databases with sample data"""
import sqlite3
import mysql.connector
from pymongo import MongoClient
from sqlalchemy import create_engine, text
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


# Database connection strings
POSTGRES_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
MONGODB_URI = os.getenv('MONGODB_URI')
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DB')
}
SQLITE_PATH = os.getenv('DB_PATH')


def setup_postgres():
    """Setup PostgreSQL database with sample data"""
    engine = create_engine(POSTGRES_URL)

    # Create tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                product VARCHAR(100),
                amount DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

        # Insert sample data
        conn.execute(text("""
            INSERT INTO users (name, email, age) VALUES
            ('John Doe', 'john@example.com', 30),
            ('Jane Smith', 'jane@example.com', 25),
            ('Bob Johnson', 'bob@example.com', 35);
            
            INSERT INTO orders (user_id, product, amount) VALUES
            (1, 'Laptop', 999.99),
            (1, 'Mouse', 29.99),
            (2, 'Keyboard', 49.99),
            (3, 'Monitor', 199.99);
        """))
        conn.commit()


def setup_mongodb():
    """Setup MongoDB database with sample data"""
    client = MongoClient(MONGODB_URI)
    db = client[os.getenv('MONGODB_DB')]

    # Create collections
    users = db['users']
    orders = db['orders']

    # Insert sample data
    users.insert_many([
        {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30,
            'created_at': '2023-01-01T00:00:00Z'
        },
        {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'age': 25,
            'created_at': '2023-01-02T00:00:00Z'
        },
        {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'age': 35,
            'created_at': '2023-01-03T00:00:00Z'
        }
    ])

    orders.insert_many([
        {
            'user_id': 1,
            'product': 'Laptop',
            'amount': 999.99,
            'created_at': '2023-01-01T00:00:00Z'
        },
        {
            'user_id': 1,
            'product': 'Mouse',
            'amount': 29.99,
            'created_at': '2023-01-02T00:00:00Z'
        },
        {
            'user_id': 2,
            'product': 'Keyboard',
            'amount': 49.99,
            'created_at': '2023-01-03T00:00:00Z'
        },
        {
            'user_id': 3,
            'product': 'Monitor',
            'amount': 199.99,
            'created_at': '2023-01-04T00:00:00Z'
        }
    ])


def setup_mysql():
    """Setup MySQL database with sample data"""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            age INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            product VARCHAR(100),
            amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # Insert sample data
    cursor.execute("""
        INSERT INTO users (name, email, age) VALUES
        ('John Doe', 'john@example.com', 30),
        ('Jane Smith', 'jane@example.com', 25),
        ('Bob Johnson', 'bob@example.com', 35);
        
        INSERT INTO orders (user_id, product, amount) VALUES
        (1, 'Laptop', 999.99),
        (1, 'Mouse', 29.99),
        (2, 'Keyboard', 49.99),
        (3, 'Monitor', 199.99);
    """)

    conn.commit()
    cursor.close()
    conn.close()


def setup_sqlite():
    """Setup SQLite database with sample data"""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # Insert sample data
    cursor.execute("""
        INSERT INTO users (name, email, age) VALUES
        ('John Doe', 'john@example.com', 30),
        ('Jane Smith', 'jane@example.com', 25),
        ('Bob Johnson', 'bob@example.com', 35);
        
        INSERT INTO orders (user_id, product, amount) VALUES
        (1, 'Laptop', 999.99),
        (1, 'Mouse', 29.99),
        (2, 'Keyboard', 49.99),
        (3, 'Monitor', 199.99);
    """)

    conn.commit()
    conn.close()


def main():
    """Main function to set up test databases"""
    db_type = os.getenv('DB_TYPE', 'postgres').lower()

    print(f"Setting up {db_type} database...")

    if db_type == 'postgres':
        setup_postgres()
    elif db_type == 'mongodb':
        setup_mongodb()
    elif db_type == 'mysql':
        setup_mysql()
    elif db_type == 'sqlite':
        setup_sqlite()
    else:
        print(f"Unsupported database type: {db_type}")
        sys.exit(1)

    print("Database setup completed successfully!")


if __name__ == "__main__":
    main()
