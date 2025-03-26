"""Test configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from pymongo import MongoClient
from pathlib import Path

from app.main import app
from app.config.settings import db_settings


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def setup_sqlite():
    """Setup SQLite test database"""
    # Create test database directory
    db_path = Path(db_settings.DB_PATH).parent
    db_path.mkdir(parents=True, exist_ok=True)

    # Create engine
    engine = create_engine(f"sqlite:///{db_settings.DB_PATH}")

    # Create test tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER
            )
        """))

        # Insert test data
        conn.execute(text("""
            INSERT INTO users (name, email, age) VALUES
            ('John Doe', 'john@example.com', 30),
            ('Jane Smith', 'jane@example.com', 25)
        """))
        conn.commit()

    yield engine

    # Cleanup
    Path(db_settings.DB_PATH).unlink(missing_ok=True)


@pytest.fixture
def setup_mongodb():
    """Setup MongoDB test database"""
    client = MongoClient(db_settings.MONGO_URL)
    db = client[db_settings.DB_NAME]

    # Create test collection and insert data
    users = db.users
    users.insert_many([
        {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "interests": ["coding", "reading"]
        },
        {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 25,
            "interests": ["travel", "photography"]
        }
    ])

    yield client

    # Cleanup
    client.drop_database(db_settings.DB_NAME)
    client.close()
