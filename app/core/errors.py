"""Custom exceptions for the application"""


class DatabaseError(Exception):
    """Base class for database-related exceptions"""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


class ValidationError(DatabaseError):
    """Raised when validation fails"""
    pass


class QueryError(DatabaseError):
    """Raised when query execution fails"""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass
