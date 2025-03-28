"""Monitoring and logging utilities"""
import logging
import time
from typing import Dict, Any
from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
QUERY_COUNTER = Counter(
    'nlq_query_total',
    'Total number of queries processed',
    ['source', 'status']
)
QUERY_DURATION = Histogram(
    'nlq_query_duration_seconds',
    'Query processing duration in seconds',
    ['source']
)
DB_CONNECTION_GAUGE = Gauge(
    'nlq_db_connections',
    'Number of active database connections',
    ['source']
)
LLM_REQUESTS = Counter(
    'nlq_llm_requests_total',
    'Total number of LLM requests',
    ['model', 'status']
)


class MonitoringMiddleware:
    """Middleware for request monitoring"""

    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.2f}s"
        )

        return response


def log_query(source: str, query: str, status: str = "success"):
    """Log query execution"""
    logger.info(f"Query executed - Source: {source}, Status: {status}")
    QUERY_COUNTER.labels(source=source, status=status).inc()


def log_query_duration(source: str, duration: float):
    """Log query duration"""
    QUERY_DURATION.labels(source=source).observe(duration)


def update_db_connections(source: str, count: int):
    """Update database connection count"""
    DB_CONNECTION_GAUGE.labels(source=source).set(count)


def log_llm_request(model: str, status: str = "success"):
    """Log LLM request"""
    logger.info(f"LLM request - Model: {model}, Status: {status}")
    LLM_REQUESTS.labels(model=model, status=status).inc()


def get_metrics() -> Dict[str, Any]:
    """Get current metrics"""
    return {
        "query_count": {
            source: QUERY_COUNTER.labels(
                source=source, status="success")._value.get()
            for source in ["postgres", "mongodb", "mysql", "sqlite"]
        },
        "error_count": {
            source: QUERY_COUNTER.labels(
                source=source, status="error")._value.get()
            for source in ["postgres", "mongodb", "mysql", "sqlite"]
        },
        "llm_requests": {
            model: LLM_REQUESTS.labels(
                model=model, status="success")._value.get()
            for model in ["claude-3-opus", "claude-3-sonnet"]
        }
    }
