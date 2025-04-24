"""API test suite"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from app.main import app
from app.core.config import api_settings

# Load environment variables
load_dotenv()

# Test client
client = TestClient(app)

# Test database connections
postgres_engine = create_engine(os.getenv("TEST_POSTGRESQL_URL"))
mongo_client = MongoClient(os.getenv("TEST_MONGODB_URL"))

# Test API key
TEST_API_KEY = os.getenv("TEST_API_KEY")


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

    yield

    # Cleanup
    with postgres_engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS test_users")
    mongo_client.drop_database("test_db")


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "databases" in data
    assert "version" in data


def test_schema_endpoint():
    """Test schema endpoint"""
    response = client.get("/schema", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert "test_users" in data["schema"]  # PostgreSQL table
    assert "test_db.test_collection" in data["schema"]  # MongoDB collection


def test_query_endpoint_postgresql():
    """Test PostgreSQL query endpoint"""
    query = "SELECT * FROM test_users"
    response = client.post(
        "/query",
        json={
            "query": query,
            "db_type": "postgresql",
            "schema": {"test_users": ["id", "name", "email"]}
        },
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert len(data["result"]) > 0
    assert "name" in data["result"][0]
    assert "email" in data["result"][0]


def test_query_endpoint_mongodb():
    """Test MongoDB query endpoint"""
    query = "test_db.test_collection"
    response = client.post(
        "/query",
        json={
            "query": query,
            "db_type": "mongodb",
            "schema": {"test_db.test_collection": ["name", "email"]}
        },
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert len(data["result"]) > 0
    assert "name" in data["result"][0]
    assert "email" in data["result"][0]


def test_invalid_api_key():
    """Test invalid API key"""
    response = client.get("/schema", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403


def test_invalid_query():
    """Test invalid query"""
    response = client.post(
        "/query",
        json={
            "query": "INVALID SQL QUERY",
            "db_type": "postgresql",
            "schema": {"test_users": ["id", "name", "email"]}
        },
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 500


def test_invalid_db_type():
    """Test invalid database type"""
    response = client.post(
        "/query",
        json={
            "query": "SELECT * FROM test_users",
            "db_type": "invalid_db",
            "schema": {"test_users": ["id", "name", "email"]}
        },
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 400
