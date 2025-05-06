"""PostgreSQL database adapter"""
from typing import Dict, Any, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from .base import BaseDB
from app.core.errors import ConnectionError, ValidationError, QueryError
from app.config.settings import db_settings, get_db_url


class PostgresDB(BaseDB):
    def __init__(self):
        """Initialize PostgreSQL connection"""
        self.engine = create_engine(get_db_url())
        self.inspector = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            self.inspector = inspect(self.engine)
            return True
        except SQLAlchemyError as e:
            raise ConnectionError(f"PostgreSQL connection failed: {str(e)}")

    def validate_connection(self) -> Dict[str, Any]:
        """Validate PostgreSQL connection"""
        try:
            with self.engine.connect() as conn:
                version = conn.execute(text("SELECT version()")).scalar()
                if "PostgreSQL" not in version:
                    raise ValidationError("Not a PostgreSQL database")

                tables = self.inspector.get_table_names(
                    schema=db_settings.POSTGRES_SCHEMA)
                return {
                    "status": "connected",
                    "version": version,
                    "schema": db_settings.POSTGRES_SCHEMA,
                    "tables": tables
                }
        except SQLAlchemyError as e:
            raise ValidationError(f"PostgreSQL validation failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL schema information"""
        schema = {}
        for table in self.inspector.get_table_names():
            columns = []
            for column in self.inspector.get_columns(table):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"]
                })
            schema[table] = columns
        return schema

    def validate_query(self, query: str) -> bool:
        """Validate SQL query syntax"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("EXPLAIN " + query))
            return True
        except SQLAlchemyError:
            return False

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return [dict(row) for row in result]
        except SQLAlchemyError as e:
            raise QueryError(f"Query execution failed: {str(e)}")
