"""Database adapter test suite"""
import pytest
from sqlalchemy import create_engine
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from app.databases.postgres import PostgreSQLAdapter
from app.databases.mongodb import MongoDBAdapter
from app.databases.mysql import MySQLAdapter
from app.databases.sqlite import SQLiteAdapter

# Load environment variables
load_dotenv()

# Test database connections
postgres_engine = create_engine(os.getenv("TEST_POSTGRESQL_URL"))
mongo_client = MongoClient(os.getenv("TEST_MONGODB_URL"))
mysql_engine = create_engine(os.getenv("TEST_MYSQL_URL"))
sqlite_engine = create_engine(os.getenv("TEST_SQLITE_URL"))


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test databases"""
    # Setup PostgreSQL test data
    with postgres_engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100)
            )
        """)
        conn.execute("""
            INSERT INTO test_users (name, email)
            VALUES ('Test User', 'test@example.com')
        """)

    # Setup MongoDB test data
    db = mongo_client.test_db
    collection = db.test_collection
    collection.insert_one({"name": "Test User", "email": "test@example.com"})

    # Setup MySQL test data
    with mysql_engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100)
            )
        """)
        conn.execute("""
            INSERT INTO test_users (name, email)
            VALUES ('Test User', 'test@example.com')
        """)

    # Setup SQLite test data
    with sqlite_engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT
            )
        """)
        conn.execute("""
            INSERT INTO test_users (name, email)
            VALUES ('Test User', 'test@example.com')
        """)

    yield

    # Cleanup
    with postgres_engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS test_users")
    mongo_client.drop_database("test_db")
    with mysql_engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS test_users")
    with sqlite_engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS test_users")


def test_postgresql_adapter():
    """Test PostgreSQL adapter"""
    adapter = PostgreSQLAdapter(os.getenv("TEST_POSTGRESQL_URL"))

    # Test connection
    assert adapter.validate_connection()["version"] is not None

    # Test schema
    schema = adapter.get_schema()
    assert "test_users" in schema
    assert "id" in schema["test_users"]
    assert "name" in schema["test_users"]
    assert "email" in schema["test_users"]

    # Test query
    result = adapter.execute_query("SELECT * FROM test_users")
    assert len(result) > 0
    assert "name" in result[0]
    assert "email" in result[0]


def test_mongodb_adapter():
    """Test MongoDB adapter"""
    adapter = MongoDBAdapter(os.getenv("TEST_MONGODB_URL"))

    # Test connection
    assert adapter.validate_connection()["version"] is not None

    # Test schema
    schema = adapter.get_schema()
    assert "test_db.test_collection" in schema
    assert "name" in schema["test_db.test_collection"]
    assert "email" in schema["test_db.test_collection"]

    # Test query
    result = adapter.execute_query("test_db.test_collection")
    assert len(result) > 0
    assert "name" in result[0]
    assert "email" in result[0]


def test_mysql_adapter():
    """Test MySQL adapter"""
    adapter = MySQLAdapter(os.getenv("TEST_MYSQL_URL"))

    # Test connection
    assert adapter.validate_connection()["version"] is not None

    # Test schema
    schema = adapter.get_schema()
    assert "test_users" in schema
    assert "id" in schema["test_users"]
    assert "name" in schema["test_users"]
    assert "email" in schema["test_users"]

    # Test query
    result = adapter.execute_query("SELECT * FROM test_users")
    assert len(result) > 0
    assert "name" in result[0]
    assert "email" in result[0]


def test_sqlite_adapter():
    """Test SQLite adapter"""
    adapter = SQLiteAdapter(os.getenv("TEST_SQLITE_URL"))

    # Test connection
    assert adapter.validate_connection()["version"] is not None

    # Test schema
    schema = adapter.get_schema()
    assert "test_users" in schema
    assert "id" in schema["test_users"]
    assert "name" in schema["test_users"]
    assert "email" in schema["test_users"]

    # Test query
    result = adapter.execute_query("SELECT * FROM test_users")
    assert len(result) > 0
    assert "name" in result[0]
    assert "email" in result[0]


def test_invalid_connection():
    """Test invalid connection handling"""
    adapter = PostgreSQLAdapter(
        "postgresql://invalid:invalid@localhost:5432/invalid")
    with pytest.raises(Exception):
        adapter.validate_connection()


def test_invalid_query():
    """Test invalid query handling"""
    adapter = PostgreSQLAdapter(os.getenv("TEST_POSTGRESQL_URL"))
    with pytest.raises(Exception):
        adapter.execute_query("INVALID SQL QUERY")
