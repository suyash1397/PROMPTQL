from typing import Dict, Any, Optional
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from pymongo import MongoClient
from pymongo.errors import ConnectionError as MongoConnectionError
from app.config.settings import db_settings, get_db_url

logger = logging.getLogger(__name__)


class DatabaseValidationError(Exception):
    """Custom exception for database validation errors"""
    pass


def validate_database_connection() -> Dict[str, Any]:
    """
    Validate database connection and return connection details
    Returns:
        Dict containing connection status and details
    """
    try:
        if db_settings.DB_TYPE == "postgres":
            return validate_postgres_connection()
        elif db_settings.DB_TYPE == "mongodb":
            return validate_mongodb_connection()
        elif db_settings.DB_TYPE == "mysql":
            return validate_mysql_connection()
        elif db_settings.DB_TYPE == "sqlite":
            return validate_sqlite_connection()
        else:
            raise DatabaseValidationError(
                f"Unsupported database type: {db_settings.DB_TYPE}")
    except Exception as e:
        logger.error(f"Database validation failed: {str(e)}")
        raise DatabaseValidationError(f"Database validation failed: {str(e)}")


def validate_postgres_connection() -> Dict[str, Any]:
    """Validate PostgreSQL connection and schema"""
    try:
        engine = create_engine(get_db_url())
        with engine.connect() as conn:
            # Check if it's actually PostgreSQL
            version = conn.execute(text("SELECT version()")).scalar()
            if "PostgreSQL" not in version:
                raise DatabaseValidationError("Not a PostgreSQL database")

            # Check schema access
            inspector = inspect(engine)
            tables = inspector.get_table_names(
                schema=db_settings.POSTGRES_SCHEMA)

            return {
                "status": "connected",
                "version": version,
                "schema": db_settings.POSTGRES_SCHEMA,
                "tables": tables
            }
    except SQLAlchemyError as e:
        raise DatabaseValidationError(
            f"PostgreSQL connection failed: {str(e)}")


def validate_mongodb_connection() -> Dict[str, Any]:
    """Validate MongoDB connection and collections"""
    try:
        client = MongoClient(get_db_url())
        db = client[db_settings.DB_NAME]

        # Check connection
        db.command('ping')

        # Get collections
        collections = db.list_collection_names()

        # Check collection schemas
        collection_schemas = {}
        for collection in collections:
            sample = db[collection].find_one()
            if sample:
                collection_schemas[collection] = list(sample.keys())

        return {
            "status": "connected",
            "collections": collections,
            "schemas": collection_schemas
        }
    except MongoConnectionError as e:
        raise DatabaseValidationError(f"MongoDB connection failed: {str(e)}")


def validate_mysql_connection() -> Dict[str, Any]:
    """Validate MySQL connection and schema"""
    try:
        engine = create_engine(get_db_url())
        with engine.connect() as conn:
            # Check if it's actually MySQL
            version = conn.execute(text("SELECT version()")).scalar()
            if "MySQL" not in version:
                raise DatabaseValidationError("Not a MySQL database")

            # Get tables
            tables = conn.execute(text("SHOW TABLES")).fetchall()
            table_names = [row[0] for row in tables]

            return {
                "status": "connected",
                "version": version,
                "tables": table_names
            }
    except SQLAlchemyError as e:
        raise DatabaseValidationError(f"MySQL connection failed: {str(e)}")


def validate_sqlite_connection() -> Dict[str, Any]:
    """Validate SQLite connection and schema"""
    try:
        engine = create_engine(get_db_url())
        with engine.connect() as conn:
            # Get tables
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            table_names = [row[0] for row in tables]

            return {
                "status": "connected",
                "tables": table_names
            }
    except SQLAlchemyError as e:
        raise DatabaseValidationError(f"SQLite connection failed: {str(e)}")


def validate_query(query: str, query_type: str) -> bool:
    """
    Validate a query before execution
    Args:
        query: The query to validate
        query_type: Type of query (sql or mongo)
    Returns:
        bool indicating if query is valid
    """
    try:
        if query_type == "sql":
            return validate_sql_query(query)
        elif query_type == "mongo":
            return validate_mongo_query(query)
        else:
            raise ValueError(f"Invalid query type: {query_type}")
    except Exception as e:
        logger.error(f"Query validation failed: {str(e)}")
        return False


def validate_sql_query(query: str) -> bool:
    """Validate SQL query syntax"""
    try:
        engine = create_engine(get_db_url())
        with engine.connect() as conn:
            # Try to explain the query
            conn.execute(text("EXPLAIN " + query))
        return True
    except Exception:
        return False


def validate_mongo_query(query: str) -> bool:
    """Validate MongoDB query syntax"""
    try:
        # Basic validation - check if it's a valid Python dict
        import ast
        ast.literal_eval(query)
        return True
    except Exception:
        return False
