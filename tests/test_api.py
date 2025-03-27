"""Test suite for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.errors import DatabaseError, ConnectionError
from unittest.mock import patch, MagicMock

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database instance"""
    with patch('app.main.db_instances') as mock:
        yield mock


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "databases" in response.json()
    assert "version" in response.json()


def test_supported_databases():
    """Test supported databases endpoint"""
    response = client.get("/supported-databases")
    assert response.status_code == 200
    assert "supported_databases" in response.json()
    assert "current_type" in response.json()


def test_get_schema(mock_db):
    """Test schema retrieval endpoint"""
    mock_db_instance = MagicMock()
    mock_db_instance.get_schema.return_value = {"tables": ["users"]}
    mock_db_instance.validate_connection.return_value = {"version": "1.0"}
    mock_db.__getitem__.return_value = mock_db_instance

    response = client.get("/schema/postgres")
    assert response.status_code == 200
    assert "source" in response.json()
    assert "schema" in response.json()
    assert "metadata" in response.json()


def test_process_query_sql(mock_db):
    """Test SQL query processing"""
    mock_db_instance = MagicMock()
    mock_db_instance.get_schema.return_value = {"tables": ["users"]}
    mock_db_instance.validate_query.return_value = True
    mock_db_instance.execute_query.return_value = [{"id": 1, "name": "test"}]
    mock_db.__getitem__.return_value = mock_db_instance

    with patch('app.core.llm.llm_manager.generate_sql_query') as mock_llm:
        mock_llm.return_value = "SELECT * FROM users"
        response = client.post(
            "/query",
            json={
                "query": "Show all users",
                "source": "postgres"
            }
        )
        assert response.status_code == 200
        assert "query" in response.json()
        assert "result" in response.json()


def test_process_query_mongodb(mock_db):
    """Test MongoDB query processing"""
    mock_db_instance = MagicMock()
    mock_db_instance.get_schema.return_value = {"collections": ["users"]}
    mock_db_instance.validate_query.return_value = True
    mock_db_instance.execute_query.return_value = [{"_id": 1, "name": "test"}]
    mock_db.__getitem__.return_value = mock_db_instance

    with patch('app.core.llm.llm_manager.generate_mongo_query') as mock_llm:
        mock_llm.return_value = {"find": "users"}
        response = client.post(
            "/query",
            json={
                "query": "Show all users",
                "source": "mongodb"
            }
        )
        assert response.status_code == 200
        assert "query" in response.json()
        assert "result" in response.json()


def test_invalid_database_source():
    """Test invalid database source"""
    response = client.get("/schema/invalid")
    assert response.status_code == 400


def test_invalid_query(mock_db):
    """Test invalid query handling"""
    mock_db_instance = MagicMock()
    mock_db_instance.get_schema.return_value = {"tables": ["users"]}
    mock_db_instance.validate_query.return_value = False
    mock_db.__getitem__.return_value = mock_db_instance

    with patch('app.core.llm.llm_manager.generate_sql_query') as mock_llm:
        mock_llm.return_value = "INVALID SQL"
        response = client.post(
            "/query",
            json={
                "query": "Invalid query",
                "source": "postgres"
            }
        )
        assert response.status_code == 400
