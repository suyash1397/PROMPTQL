"""FastAPI application entry point"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import time

from app.models.schemas import NLQueryRequest, QueryResponse, HealthResponse, SchemaResponse, MetricsResponse
from app.databases import PostgresDB, MongoDB, MySQL, SQLite
from app.core.errors import DatabaseError, ConnectionError, ValidationError, QueryError
from app.core.llm import llm_manager
from app.core.monitoring import (
    MonitoringMiddleware, log_query, log_query_duration,
    update_db_connections, log_llm_request, get_metrics
)
from app.core.security import SecurityMiddleware, setup_cors
from app.config.settings import db_settings, security_settings
import app

# Initialize FastAPI app
app = FastAPI(
    title="Natural Language Query Gateway",
    description="Convert natural language to SQL/NoSQL queries",
    version=app.__version__,
    docs_url="/docs" if security_settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if security_settings.ENABLE_DOCS else None
)

# Add middleware
app.add_middleware(MonitoringMiddleware)
app.add_middleware(SecurityMiddleware)
setup_cors(app)

# Database instances
db_instances: Dict[str, Any] = {
    "postgres": PostgresDB(),
    "mongodb": MongoDB(),
    "mysql": MySQL(),
    "sqlite": SQLite()
}


def get_db(source: str):
    """Get database instance based on source"""
    if source not in db_instances:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported database source: {source}"
        )
    return db_instances[source]


@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup"""
    for db_type, db in db_instances.items():
        try:
            db.connect()
            update_db_connections(db_type, 1)
        except ConnectionError as e:
            logger.error(f"Failed to connect to {db_type}: {str(e)}")
            update_db_connections(db_type, 0)


@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Natural Language Query Gateway",
        "version": app.__version__
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    statuses = {}
    overall_status = "healthy"

    for db_type, db in db_instances.items():
        try:
            db.connect()
            statuses[db_type] = "connected"
            update_db_connections(db_type, 1)
        except ConnectionError:
            statuses[db_type] = "disconnected"
            overall_status = "degraded"
            update_db_connections(db_type, 0)

    return HealthResponse(
        status=overall_status,
        databases=statuses,
        version=app.__version__
    )


@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics_endpoint():
    """Get application metrics"""
    return MetricsResponse(metrics=get_metrics())


@app.get("/schema/{source}", response_model=SchemaResponse, tags=["Schema"])
async def get_schema(source: str):
    """Get database schema"""
    db = get_db(source)
    try:
        schema = db.get_schema()
        metadata = db.validate_connection()
        return SchemaResponse(
            source=source,
            schema=schema,
            metadata=metadata
        )
    except DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: NLQueryRequest):
    """Process natural language query"""
    db = get_db(request.source)
    start_time = time.time()

    try:
        # Get database schema
        schema = db.get_schema()

        # Generate database query using LLM
        if request.source in ["postgres", "mysql", "sqlite"]:
            dialect = "postgresql" if request.source == "postgres" else request.source
            query = await llm_manager.generate_sql_query(schema, request.query, dialect)
            log_llm_request("claude-3-opus")
        elif request.source == "mongodb":
            query = await llm_manager.generate_mongo_query(schema, request.query)
            log_llm_request("claude-3-sonnet")
        else:
            raise ValidationError(
                f"Unsupported database type: {request.source}")

        # Validate generated query
        if not db.validate_query(query):
            log_query(request.source, query, "error")
            raise ValidationError("Generated query is invalid")

        # Execute query
        result = db.execute_query(query)
        duration = time.time() - start_time
        log_query_duration(request.source, duration)
        log_query(request.source, query)

        return QueryResponse(
            query=query,
            result=result
        )
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except QueryError as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/supported-databases", tags=["General"])
async def get_supported_databases():
    """Get list of supported databases"""
    return {
        "supported_databases": list(db_instances.keys()),
        "current_type": db_settings.DB_TYPE
    }
