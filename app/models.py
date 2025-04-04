from pydantic import BaseModel
from typing import List, Dict, Any

class QueryRequest(BaseModel):
    query: str
    source: str  # "sql" or "mongo"

class QueryResponse(BaseModel):
    result: List[Dict[str, Any]] 