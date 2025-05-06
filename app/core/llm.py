"""LLM integration using Hugging Face Inference API"""
import os
import requests
from langchain import PromptTemplate

HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Add your token to .env


def hf_generate(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    # The response format may vary by model; adjust as needed
    if isinstance(result, list) and "generated_text" in result[0]:
        return result[0]["generated_text"]
    elif "generated_text" in result:
        return result["generated_text"]
    elif "data" in result and len(result["data"]) > 0:
        return result["data"][0]["generated_text"]
    else:
        return str(result)


class LLMManager:
    """Manager for LLM operations"""

    def __init__(self):
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

    async def generate_query(
        self,
        schema: str,
        natural_language: str,
        db_type: str
    ) -> str:
        """
        Generate a database query from natural language using the Hugging Face LLM.
        """
        prompt = self.query_prompt.format(
            schema=schema,
            natural_language=natural_language,
            db_type=db_type
        )
        # Hugging Face API is synchronous, so run in thread executor if needed
        import asyncio
        loop = asyncio.get_event_loop()
        query = await loop.run_in_executor(None, hf_generate, prompt)
        return query.strip()

    def validate_query(self, query: str, db_type: str) -> bool:
        # Optionally, you can implement validation using the LLM or regex
        return True  # For now, always return True


# Create global instance
llm_manager = LLMManager()
