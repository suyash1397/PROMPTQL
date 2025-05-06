import requests
import json
import logging
from typing import Dict, Any
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


def test_query(query: str, source: str) -> Dict[str, Any]:
    """Test a single query and return the response"""
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"query": query, "source": source}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Query failed: {str(e)}")
        return {"error": str(e)}


def run_tests():
    """Run a series of test queries"""
    # SQL Test Queries
    sql_queries = [
        "Show me all users",
        "Find users older than 30",
        "Show me all completed orders",
        "What is the total amount of all orders?",
        "Show me users and their order counts"
    ]

    # MongoDB Test Queries
    mongo_queries = [
        "Find all users interested in coding",
        "Show me all electronics products",
        "Find products with price greater than 500",
        "Show me users between 25 and 35 years old",
        "Find products with low stock (less than 15)"
    ]

    logger.info("Running SQL Query Tests...")
    for query in sql_queries:
        logger.info(f"\nTesting SQL Query: {query}")
        result = test_query(query, "sql")
        print(json.dumps(result, indent=2))

    logger.info("\nRunning MongoDB Query Tests...")
    for query in mongo_queries:
        logger.info(f"\nTesting MongoDB Query: {query}")
        result = test_query(query, "mongo")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run_tests()
