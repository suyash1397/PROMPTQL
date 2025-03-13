"""MongoDB database adapter"""
from typing import Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionError as MongoConnectionError, OperationFailure
from .base import BaseDB
from app.core.errors import ConnectionError, ValidationError, QueryError
from app.config.settings import db_settings, get_db_url


class MongoDB(BaseDB):
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(get_db_url())
        self.db = self.client[db_settings.DB_NAME]

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.db.command('ping')
            return True
        except MongoConnectionError as e:
            raise ConnectionError(f"MongoDB connection failed: {str(e)}")

    def validate_connection(self) -> Dict[str, Any]:
        """Validate MongoDB connection"""
        try:
            collections = self.db.list_collection_names()
            collection_schemas = {}

            for collection in collections:
                sample = self.db[collection].find_one()
                if sample:
                    collection_schemas[collection] = list(sample.keys())

            return {
                "status": "connected",
                "collections": collections,
                "schemas": collection_schemas
            }
        except MongoConnectionError as e:
            raise ValidationError(f"MongoDB validation failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get MongoDB schema information"""
        schema = {}
        for collection in self.db.list_collection_names():
            pipeline = [
                {"$sample": {"size": 1}},
                {"$project": {"_id": 0}}
            ]
            sample = list(self.db[collection].aggregate(pipeline))
            if sample:
                schema[collection] = {
                    "fields": list(sample[0].keys()),
                    "sample": sample[0]
                }
        return schema

    def validate_query(self, query: str) -> bool:
        """Validate MongoDB query syntax"""
        try:
            import ast
            # Check if query is a valid Python dict
            query_dict = ast.literal_eval(query)
            return isinstance(query_dict, dict)
        except (ValueError, SyntaxError):
            return False

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute MongoDB query and return results"""
        try:
            import ast
            query_dict = ast.literal_eval(query)
            collection = query_dict.pop("collection", None)

            if not collection:
                raise QueryError("Query must specify a collection")

            result = list(self.db[collection].find(query_dict))
            # Convert ObjectId to string for JSON serialization
            for doc in result:
                doc["_id"] = str(doc["_id"])

            return result
        except (ValueError, SyntaxError) as e:
            raise QueryError(f"Invalid query syntax: {str(e)}")
        except OperationFailure as e:
            raise QueryError(f"Query execution failed: {str(e)}")
