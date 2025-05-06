from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    db_type: str
    db_schema: Dict[str, List[str]]

class QueryResponse(BaseModel):
    query: str
    result: List[Dict[str, Any]]

class SchemaResponse(BaseModel):
    db_schema: Dict[str, List[str]]

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall service status")
    databases: Dict[str, str] = Field(..., description="Database connection statuses")
    version: str = Field(..., description="API version")

class MetricsResponse(BaseModel):
    metrics: Dict[str, Any] = Field(..., description="Application metrics")

class NLQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    source: str = Field(..., description="Database source (sql/mongo/mysql/sqlite)")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all users who signed up this month",
                "source": "sql"
            }
        }