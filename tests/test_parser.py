"""Query parser test suite"""
import pytest
from app.parser import QueryParser


def test_sql_parser():
    """Test SQL query parsing"""
    parser = QueryParser()

    # Test basic SELECT query
    query = "SELECT * FROM users WHERE age > 18"
    parsed = parser.parse(query)
    assert parsed["type"] == "SELECT"
    assert parsed["table"] == "users"
    assert parsed["conditions"] == ["age > 18"]

    # Test INSERT query
    query = "INSERT INTO users (name, age) VALUES ('John', 25)"
    parsed = parser.parse(query)
    assert parsed["type"] == "INSERT"
    assert parsed["table"] == "users"
    assert parsed["columns"] == ["name", "age"]
    assert parsed["values"] == ["'John'", "25"]

    # Test UPDATE query
    query = "UPDATE users SET age = 26 WHERE name = 'John'"
    parsed = parser.parse(query)
    assert parsed["type"] == "UPDATE"
    assert parsed["table"] == "users"
    assert parsed["set"] == ["age = 26"]
    assert parsed["conditions"] == ["name = 'John'"]

    # Test DELETE query
    query = "DELETE FROM users WHERE age < 18"
    parsed = parser.parse(query)
    assert parsed["type"] == "DELETE"
    assert parsed["table"] == "users"
    assert parsed["conditions"] == ["age < 18"]


def test_mongodb_parser():
    """Test MongoDB query parsing"""
    parser = QueryParser()

    # Test find query
    query = "db.users.find({age: {$gt: 18}})"
    parsed = parser.parse(query)
    assert parsed["type"] == "find"
    assert parsed["collection"] == "users"
    assert parsed["query"] == {"age": {"$gt": 18}}

    # Test insert query
    query = "db.users.insertOne({name: 'John', age: 25})"
    parsed = parser.parse(query)
    assert parsed["type"] == "insertOne"
    assert parsed["collection"] == "users"
    assert parsed["document"] == {"name": "John", "age": 25}

    # Test update query
    query = "db.users.updateOne({name: 'John'}, {$set: {age: 26}})"
    parsed = parser.parse(query)
    assert parsed["type"] == "updateOne"
    assert parsed["collection"] == "users"
    assert parsed["filter"] == {"name": "John"}
    assert parsed["update"] == {"$set": {"age": 26}}

    # Test delete query
    query = "db.users.deleteOne({age: {$lt: 18}})"
    parsed = parser.parse(query)
    assert parsed["type"] == "deleteOne"
    assert parsed["collection"] == "users"
    assert parsed["filter"] == {"age": {"$lt": 18}}


def test_invalid_queries():
    """Test invalid query handling"""
    parser = QueryParser()

    # Test invalid SQL syntax
    with pytest.raises(Exception):
        parser.parse("SELECT * FROM users WHERE")

    # Test invalid MongoDB syntax
    with pytest.raises(Exception):
        parser.parse("db.users.find({age: {$gt: 18}")

    # Test empty query
    with pytest.raises(Exception):
        parser.parse("")

    # Test unsupported query type
    with pytest.raises(Exception):
        parser.parse("CREATE TABLE users (id INT)")


def test_query_normalization():
    """Test query normalization"""
    parser = QueryParser()

    # Test SQL query normalization
    query = "SELECT * FROM users WHERE age > 18"
    normalized = parser.normalize(query)
    assert normalized == "select * from users where age > 18"

    # Test MongoDB query normalization
    query = "db.users.find({age: {$gt: 18}})"
    normalized = parser.normalize(query)
    assert normalized == "db.users.find({age:{$gt:18}})"

    # Test query with whitespace
    query = "  SELECT  *  FROM  users  WHERE  age  >  18  "
    normalized = parser.normalize(query)
    assert normalized == "select * from users where age > 18"


def test_query_validation():
    """Test query validation"""
    parser = QueryParser()

    # Test valid SQL query
    assert parser.validate("SELECT * FROM users WHERE age > 18") is True

    # Test valid MongoDB query
    assert parser.validate("db.users.find({age: {$gt: 18}})") is True

    # Test invalid SQL query
    assert parser.validate("SELECT * FROM users WHERE") is False

    # Test invalid MongoDB query
    assert parser.validate("db.users.find({age: {$gt: 18}") is False
