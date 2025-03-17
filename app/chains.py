from sqlalchemy import create_engine, inspect
from pymongo import MongoClient
from langchain.chat_models import ChatAnthropic
from langchain_experimental.sql.base import SQLDatabaseChain
from langchain import LLMChain, PromptTemplate
from app.config import settings

# Relational setup
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
table_info = "\n".join(
    f"{t}({', '.join([c['name'] for c in inspector.get_columns(t)])})" 
    for t in inspector.get_table_names()
)

# Initialize Claude LLM
llm = ChatAnthropic(
    model="claude-3-opus-20240229",
    anthropic_api_key=settings.ANTHROPIC_API_KEY
)

# SQL Chain setup
sql_chain = SQLDatabaseChain.from_engine(
    llm=llm,
    engine=engine,
    prompt_template=PromptTemplate(
        input_variables=["table_info", "query"],
        template="""Given the following database schema:
{table_info}

Generate a SQL query for the following request: {query}

Return ONLY the SQL query, nothing else."""
    )
)

# MongoDB setup
client = MongoClient(settings.MONGO_URL)
db = client.get_default_database()
mongo_schema = "\n".join(
    f"{col}: {list(db[col].find_one().keys())}" 
    for col in db.list_collection_names()
)

# MongoDB Chain setup
mongo_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        input_variables=["schema", "query"],
        template="""Given the following MongoDB collections and their fields:
{schema}

Generate a MongoDB query for the following request: {query}

Return ONLY the MongoDB query as a Python dictionary, nothing else."""
    )
) 