"""Script to test the API with sample queries"""
import os
import sys
import requests
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# API configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")


def test_health_check():
    """Test health check endpoint"""
    print("\nTesting health check...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_schema():
    """Test schema endpoint"""
    print("\nTesting schema retrieval...")
    db_type = os.getenv("DB_TYPE", "postgres")
    response = requests.get(f"{API_URL}/schema/{db_type}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_natural_language_query(query: str, expected_result_count: int = None):
    """Test natural language query"""
    print(f"\nTesting query: {query}")
    db_type = os.getenv("DB_TYPE", "postgres")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    data = {
        "query": query,
        "source": db_type
    }

    response = requests.post(
        f"{API_URL}/query",
        headers=headers,
        json=data
    )

    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Generated Query: {result.get('query')}")
    print(f"Result Count: {len(result.get('result', []))}")

    if expected_result_count is not None:
        assert len(result.get('result', [])) == expected_result_count

    return response.status_code == 200


def main():
    """Main function to run tests"""
    if not API_KEY:
        print("Error: API_KEY environment variable not set")
        sys.exit(1)

    # Test basic endpoints
    if not test_health_check():
        print("Health check failed")
        sys.exit(1)

    if not test_schema():
        print("Schema retrieval failed")
        sys.exit(1)

    # Test queries
    test_queries = [
        ("Show all users", 3),
        ("Find users older than 25", 2),
        ("Show all orders", 4),
        ("Find orders with amount greater than 100", 2),
        ("Show users and their orders", 3),
        ("Find the total amount spent by each user", 3),
        ("Show the most expensive order", 1),
        ("Find users who haven't placed any orders", 0)
    ]

    for query, expected_count in test_queries:
        if not test_natural_language_query(query, expected_count):
            print(f"Query test failed: {query}")
            sys.exit(1)

    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()
