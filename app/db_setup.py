import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pymongo import MongoClient
from pymongo.errors import ConnectionError as MongoConnectionError
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_postgres():
    """Setup PostgreSQL database with test data"""
    try:
        engine = create_engine(settings.DATABASE_URL)

        # Create test tables
        with engine.connect() as conn:
            # Create users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create orders table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    amount DECIMAL(10,2),
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Insert test data
            conn.execute(text("""
                INSERT INTO users (name, email, age) VALUES
                ('John Doe', 'john@example.com', 30),
                ('Jane Smith', 'jane@example.com', 25),
                ('Bob Johnson', 'bob@example.com', 35)
                ON CONFLICT DO NOTHING
            """))

            conn.execute(text("""
                INSERT INTO orders (user_id, amount, status) VALUES
                (1, 100.50, 'completed'),
                (1, 200.75, 'pending'),
                (2, 50.25, 'completed'),
                (3, 300.00, 'cancelled')
                ON CONFLICT DO NOTHING
            """))

            conn.commit()

        logger.info("PostgreSQL setup completed successfully")
        return True

    except SQLAlchemyError as e:
        logger.error(f"PostgreSQL setup failed: {str(e)}")
        return False


def setup_mongodb():
    """Setup MongoDB with test data"""
    try:
        client = MongoClient(settings.MONGO_URL)
        db = client.get_default_database()

        # Create users collection
        users = db.users
        users.insert_many([
            {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "interests": ["coding", "reading", "gaming"]
            },
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "age": 25,
                "interests": ["photography", "travel"]
            },
            {
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "age": 35,
                "interests": ["cooking", "music"]
            }
        ])

        # Create products collection
        products = db.products
        products.insert_many([
            {
                "name": "Laptop",
                "price": 999.99,
                "category": "electronics",
                "stock": 10
            },
            {
                "name": "Smartphone",
                "price": 699.99,
                "category": "electronics",
                "stock": 20
            },
            {
                "name": "Headphones",
                "price": 199.99,
                "category": "accessories",
                "stock": 15
            }
        ])

        logger.info("MongoDB setup completed successfully")
        return True

    except MongoConnectionError as e:
        logger.error(f"MongoDB setup failed: {str(e)}")
        return False


def main():
    """Main setup function"""
    logger.info("Starting database setup...")

    pg_success = setup_postgres()
    mongo_success = setup_mongodb()

    if pg_success and mongo_success:
        logger.info("All database setups completed successfully")
        return 0
    else:
        logger.error("Database setup failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
