"""MySQL database adapter"""
from typing import Dict, Any, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from .base import BaseDB
from app.core.errors import ConnectionError, ValidationError, QueryError
from app.config.settings import db_settings, get_db_url


class MySQL(BaseDB):
    def __init__(self):
        """Initialize MySQL connection"""
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
            raise ConnectionError(f"MySQL connection failed: {str(e)}")

    def validate_connection(self) -> Dict[str, Any]:
        """Validate MySQL connection"""
        try:
            with self.engine.connect() as conn:
                version = conn.execute(text("SELECT VERSION()")).scalar()
                if not version or "MySQL" not in version:
                    raise ValidationError("Not a MySQL database")

                tables = self.inspector.get_table_names()
                return {
                    "status": "connected",
                    "version": version,
                    "tables": tables,
                    "charset": db_settings.MYSQL_CHARSET
                }
        except SQLAlchemyError as e:
            raise ValidationError(f"MySQL validation failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get MySQL schema information"""
        schema = {}
        for table in self.inspector.get_table_names():
            columns = []
            for column in self.inspector.get_columns(table):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True),
                    "default": str(column.get("default", "NULL")),
                    "autoincrement": column.get("autoincrement", False)
                })

            # Get primary keys
            pk_constraint = self.inspector.get_pk_constraint(table)
            if pk_constraint:
                schema[table] = {
                    "columns": columns,
                    "primary_keys": pk_constraint["constrained_columns"]
                }

            # Get foreign keys
            foreign_keys = []
            for fk in self.inspector.get_foreign_keys(table):
                foreign_keys.append({
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                    "constrained_columns": fk["constrained_columns"]
                })
            if foreign_keys:
                schema[table]["foreign_keys"] = foreign_keys

        return schema

    def validate_query(self, query: str) -> bool:
        """Validate SQL query syntax"""
        try:
            with self.engine.connect() as conn:
                # MySQL specific EXPLAIN
                conn.execute(text(f"EXPLAIN FORMAT=JSON {query}"))
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
