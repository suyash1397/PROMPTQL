"""SQLite database adapter"""
from typing import Dict, Any, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from .base import BaseDB
from app.core.errors import ConnectionError, ValidationError, QueryError
from app.config.settings import db_settings, get_db_url


class SQLite(BaseDB):
    def __init__(self):
        """Initialize SQLite connection"""
        # Ensure the database directory exists
        db_path = Path(db_settings.DB_PATH).parent
        db_path.mkdir(parents=True, exist_ok=True)

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
            raise ConnectionError(f"SQLite connection failed: {str(e)}")

    def validate_connection(self) -> Dict[str, Any]:
        """Validate SQLite connection"""
        try:
            with self.engine.connect() as conn:
                version = conn.execute(
                    text("SELECT sqlite_version()")).scalar()

                # Get all tables excluding SQLite system tables
                tables = [t for t in self.inspector.get_table_names()
                          if not t.startswith('sqlite_')]

                return {
                    "status": "connected",
                    "version": version,
                    "tables": tables,
                    "path": db_settings.DB_PATH
                }
        except SQLAlchemyError as e:
            raise ValidationError(f"SQLite validation failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get SQLite schema information"""
        schema = {}
        for table in self.inspector.get_table_names():
            if table.startswith('sqlite_'):
                continue

            # Get table info
            table_info = []
            with self.engine.connect() as conn:
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                for row in result:
                    table_info.append({
                        "name": row.name,
                        "type": row.type,
                        "notnull": bool(row.notnull),
                        "default": row.dflt_value,
                        "pk": bool(row.pk)
                    })

            # Get foreign keys
            foreign_keys = []
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"PRAGMA foreign_key_list({table})"))
                for row in result:
                    foreign_keys.append({
                        "from": row.from_,
                        "to": row.to,
                        "table": row.table
                    })

            schema[table] = {
                "columns": table_info,
                "foreign_keys": foreign_keys
            }

        return schema

    def validate_query(self, query: str) -> bool:
        """Validate SQL query syntax"""
        try:
            with self.engine.connect() as conn:
                # SQLite EXPLAIN
                conn.execute(text(f"EXPLAIN QUERY PLAN {query}"))
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

    def create_tables(self, schema_sql: str) -> None:
        """Create tables from SQL schema"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(schema_sql))
                conn.commit()
        except SQLAlchemyError as e:
            raise QueryError(f"Failed to create tables: {str(e)}")
