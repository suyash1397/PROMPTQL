# Natural Language Query Gateway

A FastAPI service that converts natural language queries to SQL/NoSQL queries using LangChain and Claude.

## Features

- Support for multiple databases:
  - PostgreSQL
  - MongoDB
  - MySQL
  - SQLite
- Natural language to SQL/NoSQL query conversion
- Automatic schema introspection
- Query validation and error handling
- Health check endpoints
- Comprehensive test suite
- API documentation with Swagger UI
- **New**: Monitoring and metrics
- **New**: Rate limiting and security features
- **New**: Enhanced error handling and logging

## Prerequisites

- Python 3.10+
- One or more of the following databases:
  - PostgreSQL
  - MongoDB
  - MySQL
  - SQLite
- Anthropic API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROMPTQL
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv .env
.env\Scripts\activate

# Linux/macOS
python -m venv .env
source .env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Configure your environment variables in `.env`:
```env
# Database Type (required)
DB_TYPE=postgres  # Options: postgres, mongodb, mysql, sqlite

# Database Settings
DB_HOST=localhost
DB_PORT=5432  # Default ports: PostgreSQL=5432, MongoDB=27017, MySQL=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database

# SQLite Specific
DB_PATH=./data/database.db  # Only for SQLite

# API Settings
ANTHROPIC_API_KEY=your_api_key

# Security Settings
API_KEY=your_api_key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
ALLOWED_ORIGINS=["http://localhost:3000"]
ENABLE_DOCS=true
```

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation:
```
http://localhost:8000/docs
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Metrics
```bash
GET /metrics
```

### Schema Information
```bash
GET /schema/{source}
```

### Query Execution
```bash
POST /query
Content-Type: application/json
X-API-Key: your_api_key

{
    "query": "Show me all users who signed up this month",
    "source": "sql"
}
```

### Supported Databases
```bash
GET /supported-databases
```

## Security Features

- API key authentication
- Rate limiting
- CORS protection
- Security headers
- Input validation
- Error handling

## Monitoring

The application provides the following monitoring capabilities:

- Request logging
- Query execution metrics
- Database connection status
- LLM request tracking
- Performance metrics

## Testing

1. Run all tests:
```bash
pytest
```

2. Run specific test file:
```bash
pytest tests/test_api.py
```

3. Run with coverage:
```bash
pytest --cov=app tests/
```

## Example Queries

### SQL (PostgreSQL/MySQL/SQLite)
```json
{
    "query": "Find all users older than 25",
    "source": "sql"
}
```

### MongoDB
```json
{
    "query": {
        "collection": "users",
        "age": {"$gt": 25},
        "interests": "coding"
    },
    "source": "mongodb"
}
```

## Development

### Project Structure
```
PROMPTQL/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── llm.py
│   │   ├── monitoring.py
│   │   ├── security.py
│   │   └── validation.py
│   ├── databases/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── postgres.py
│   │   ├── mongodb.py
│   │   ├── mysql.py
│   │   └── sqlite.py
│   └── models/
│       ├── __init__.py
│       └── schemas.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_api.py
├── .env.example
├── requirements.txt
└── README.md
```

### Adding a New Database

1. Create a new adapter in `app/databases/`
2. Implement the `BaseDB` interface
3. Add database-specific settings to `app/config/settings.py`
4. Update the database instances in `app/main.py`
5. Add test cases in `tests/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT 