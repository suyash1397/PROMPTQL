"""Pydantic models for request/response schemas"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str
    db_type: str  # "postgresql" or "mongodb"
    schema: Dict[str, List[str]]  # Table/collection schema


class QueryResponse(BaseModel):
    """Response model for query results"""
    query: str  # Generated SQL or MongoDB query
    result: List[Dict[str, Any]]  # Query results


class SchemaResponse(BaseModel):
    """Response model for database schema"""
    schema: Dict[str, List[str]
                 ]  # Table/collection names and their columns/fields


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall service status")
    databases: Dict[str, str] = Field(...,
                                      description="Database connection statuses")
    version: str = Field(..., description="API version")


class MetricsResponse(BaseModel):
    """Metrics response"""
    metrics: Dict[str, Any] = Field(..., description="Application metrics")


class NLQueryRequest(BaseModel):
    """Natural language query request"""
    query: str = Field(..., description="Natural language query")
    source: str = Field(...,
                        description="Database source (sql/mongo/mysql/sqlite)")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all users who signed up this month",
                "source": "sql"
            }
        }


class SchemaResponse(BaseModel):
    """Database schema response"""
    source: str = Field(..., description="Database source")
    schema: Dict[str, Any] = Field(...,
                                   description="Database schema information")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata")
