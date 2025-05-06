"""FastAPI application entry point"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy import create_engine, inspect, text
from pymongo import MongoClient
from typing import Dict, List, Any
import logging

from app.models.schemas import QueryRequest, QueryResponse, HealthResponse, SchemaResponse, MetricsResponse
from app.core.llm import llm_manager
from app.config.settings import api_settings, db_settings, get_db_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PromptQL API",
    description="Natural language to database query API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != api_settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


# Initialize database connections
postgres_engine = create_engine(get_db_url())
# If you have a separate MongoDB URL, you can construct it similarly:
# mongo_client = MongoClient(get_mongo_url())
# Otherwise, use the values from db_settings:
mongo_url = f"mongodb://{db_settings.DB_HOST}:27017/{db_settings.DB_NAME}"
mongo_client = MongoClient(mongo_url)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check PostgreSQL connection
        with postgres_engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        postgres_status = "connected"
    except Exception as e:
        logger.error(f"PostgreSQL connection error: {str(e)}")
        postgres_status = "disconnected"

    try:
        # Check MongoDB connection
        mongo_client.admin.command('ping')
        mongodb_status = "connected"
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        mongodb_status = "disconnected"

    return HealthResponse(
        status="healthy" if postgres_status == "connected" and mongodb_status == "connected" else "degraded",
        databases={
            "postgresql": postgres_status,
            "mongodb": mongodb_status
        },
        version="1.0.0"
    )


@app.get("/schema", response_model=SchemaResponse)
async def get_schema(api_key: str = Depends(get_api_key)):
    """Get PostgreSQL database schema only"""
    try:
        inspector = inspect(postgres_engine)
        postgres_schema = {}
        for table_name in inspector.get_table_names():
            columns = [col['name']
                       for col in inspector.get_columns(table_name)]
            postgres_schema[table_name] = columns

        return SchemaResponse(db_schema=postgres_schema)
    except Exception as e:
        logger.error(f"Error getting schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, api_key: str = Depends(get_api_key)):
    """Execute natural language query"""
    try:
        if request.db_type == "postgresql":
            # Detect if the query is not SQL (very basic check, you can improve this)
            if not request.query.strip().lower().startswith(("select", "insert", "update", "delete", "with")):
                # Get schema as a string (you may need to adjust this)
                inspector = inspect(postgres_engine)
                schema = ""
                for table_name in inspector.get_table_names():
                    columns = [col['name']
                               for col in inspector.get_columns(table_name)]
                    schema += f"{table_name}({', '.join(columns)})\n"
                # Translate NL to SQL
                request.query = await llm_manager.generate_query(
                    schema=schema,
                    natural_language=request.query,
                    db_type="PostgreSQL"
                )
            with postgres_engine.connect() as conn:
                result = conn.execute(text(request.query)).fetchall()
                return QueryResponse(
                    query=request.query,
                    result=[dict(row) for row in result]
                )
        elif request.db_type == "mongodb":
            # Execute MongoDB query
            db_name, collection_name = request.query.split(".", 1)
            collection = mongo_client[db_name][collection_name]
            result = list(collection.find())
            return QueryResponse(
                query=request.query,
                result=result
            )
        else:
            raise HTTPException(
                status_code=400, detail="Invalid database type")
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
