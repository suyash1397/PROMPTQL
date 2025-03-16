"""LLM integration with LangChain"""
from typing import Dict, Any, Optional
from langchain.chat_models import ChatAnthropic
from langchain_experimental.sql import SQLDatabaseChain
from langchain import PromptTemplate, LLMChain
from sqlalchemy import create_engine
from app.config.settings import db_settings
import os
from anthropic import Anthropic
from langchain.llms import Anthropic as LangChainAnthropic

# Initialize Claude
llm = ChatAnthropic(
    model="claude-3-opus-20240229",
    anthropic_api_key=db_settings.ANTHROPIC_API_KEY
)

# SQL prompt template
SQL_PROMPT = """Given the following database schema:
{schema}

Generate a SQL query for this request: {query}

The query should be valid for {dialect} SQL.
Return ONLY the SQL query, nothing else."""

# MongoDB prompt template
MONGO_PROMPT = """Given the following MongoDB collections and their structure:
{schema}

Generate a MongoDB query for this request: {query}

Return ONLY the MongoDB query as a valid Python dictionary, nothing else."""


class LLMManager:
    """Manager for LLM operations"""

    def __init__(self):
        """Initialize LLM chains"""
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.llm = LangChainAnthropic(model="claude-3-sonnet-20240229")

        self.query_prompt = PromptTemplate(
            input_variables=["schema", "natural_language", "db_type"],
            template="""Given the following database schema and natural language query, generate a valid {db_type} query.

Schema:
{schema}

Natural Language Query:
{natural_language}

Rules:
1. Generate only the query, no explanations
2. Ensure the query is syntactically correct for {db_type}
3. Use only tables and columns that exist in the schema
4. For MongoDB, return a valid find() or aggregate() query

Generated Query:"""
        )

        self.query_chain = LLMChain(llm=self.llm, prompt=self.query_prompt)

    async def generate_query(
        self,
        schema: str,
        natural_language: str,
        db_type: str
    ) -> str:
        """
        Generate a database query from natural language using the LLM.

        Args:
            schema: The database schema as a string
            natural_language: The natural language query
            db_type: The type of database (e.g., "PostgreSQL", "MongoDB")

        Returns:
            str: The generated database query
        """
        try:
            query = await self.query_chain.arun(
                schema=schema,
                natural_language=natural_language,
                db_type=db_type
            )
            return query.strip()
        except Exception as e:
            raise Exception(f"Error generating query: {str(e)}")

    def validate_query(self, query: str, db_type: str) -> bool:
        """
        Validate the generated query using the LLM.

        Args:
            query: The query to validate
            db_type: The type of database

        Returns:
            bool: True if the query is valid, False otherwise
        """
        try:
            validation_prompt = f"""Validate if this {db_type} query is syntactically correct:
            
{query}

Respond with only 'true' if valid or 'false' if invalid."""

            response = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": validation_prompt}]
            )

            return response.content.lower().strip() == "true"
        except Exception:
            return False


# Create global instance
llm_manager = LLMManager()
