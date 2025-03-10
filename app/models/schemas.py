"""Pydantic models for request/response schemas"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


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


class QueryResponse(BaseModel):
    """Query response"""
    query: str = Field(..., description="Generated database query")
    result: List[Dict[str, Any]] = Field(
        default_list=[], description="Query results")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall service status")
    databases: Dict[str, str] = Field(...,
                                      description="Database connection statuses")
    version: str = Field(..., description="API version")


class SchemaResponse(BaseModel):
    """Database schema response"""
    source: str = Field(..., description="Database source")
    schema: Dict[str, Any] = Field(...,
                                   description="Database schema information")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata")
