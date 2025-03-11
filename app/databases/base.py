"""Base class for database adapters"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseDB(ABC):
    """Abstract base class for database adapters"""

    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass

    @abstractmethod
    def validate_connection(self) -> Dict[str, Any]:
        """Validate database connection"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        pass

    @abstractmethod
    def validate_query(self, query: str) -> bool:
        """Validate query syntax"""
        pass

    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        pass
