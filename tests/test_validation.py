import pytest
from app.core.validation import (
    validate_database_connection,
    validate_query,
    DatabaseValidationError
)
from app.config.settings import db_settings


def test_database_connection():
    """Test database connection validation"""
    try:
        result = validate_database_connection()
        assert result["status"] == "connected"

        if db_settings.DB_TYPE == "postgres":
            assert "version" in result
            assert "tables" in result
        elif db_settings.DB_TYPE == "mongodb":
            assert "collections" in result
            assert "schemas" in result
        elif db_settings.DB_TYPE == "mysql":
            assert "version" in result
            assert "tables" in result
        elif db_settings.DB_TYPE == "sqlite":
            assert "tables" in result

    except DatabaseValidationError as e:
        pytest.fail(f"Database validation failed: {str(e)}")


def test_sql_query_validation():
    """Test SQL query validation"""
    if db_settings.DB_TYPE in ["postgres", "mysql", "sqlite"]:
        # Valid query
        assert validate_query("SELECT 1", "sql") is True

        # Invalid query
        assert validate_query("SELECT FROM", "sql") is False


def test_mongo_query_validation():
    """Test MongoDB query validation"""
    if db_settings.DB_TYPE == "mongodb":
        # Valid query
        assert validate_query('{"name": "test"}', "mongo") is True

        # Invalid query
        assert validate_query("invalid json", "mongo") is False


if __name__ == "__main__":
    pytest.main([__file__])
