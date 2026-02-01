"""
LLM Client - Ollama Integration
Handles all LLM interactions locally

Supports dual-model setup:
- Primary model (qwen2.5) for intent routing, knowledge, formatting
- SQL model (sqlcoder) for text-to-SQL generation
"""

import json
from typing import Optional
import ollama
from config import (
    OLLAMA_BASE_URL, 
    LLM_MODEL, 
    SQL_MODEL,
    LLM_TEMPERATURE, 
    SQL_TEMPERATURE,
    LLM_MAX_TOKENS, 
    SQL_MAX_TOKENS,
    SYSTEM_PROMPT
)


# SQL-specific system prompt
SQL_SYSTEM_PROMPT = """You are a SQL expert. Generate DuckDB-compatible SQL queries.

RULES:
1. Return ONLY the SQL query - no explanations, no markdown, no backticks
2. Use exact column names from the provided schema
3. Column names with spaces must be quoted: "Column Name"
4. For aggregations, always use aliases: SUM(x) AS total
5. Limit results to 20 unless asked for more
6. Use LIKE for text matching, not =
7. When multiple similar tables exist (e.g., data_jan, data_feb), use UNION ALL to combine them
8. Always include the table name or a source identifier when combining tables
"""

# Few-shot examples for SQL generation (generic, not data-specific)
SQL_FEW_SHOT_EXAMPLES = [
    {
        "schema": """TABLE: orders_jan (customer VARCHAR, amount DOUBLE, date DATE)
TABLE: orders_feb (customer VARCHAR, amount DOUBLE, date DATE)""",
        "question": "What is the total amount across all orders?",
        "sql": """SELECT SUM(amount) AS total_amount FROM (
    SELECT amount FROM orders_jan
    UNION ALL
    SELECT amount FROM orders_feb
) combined"""
    },
    {
        "schema": """TABLE: orders_jan (customer VARCHAR, amount DOUBLE, date DATE)
TABLE: orders_feb (customer VARCHAR, amount DOUBLE, date DATE)""",
        "question": "Show top 5 customers by total amount",
        "sql": """SELECT customer, SUM(amount) AS total_amount FROM (
    SELECT customer, amount FROM orders_jan
    UNION ALL
    SELECT customer, amount FROM orders_feb
) combined
GROUP BY customer
ORDER BY total_amount DESC
LIMIT 5"""
    },
    {
        "schema": """TABLE: sales (product VARCHAR, quantity INT, price DOUBLE, region VARCHAR)""",
        "question": "Show total sales by region",
        "sql": """SELECT region, SUM(quantity * price) AS total_sales
FROM sales
GROUP BY region
ORDER BY total_sales DESC"""
    },
    {
        "schema": """TABLE: transactions (id INT, name VARCHAR, value DOUBLE, category VARCHAR, created_date DATE)""",
        "question": "Find transactions where name contains 'Corp'",
        "sql": """SELECT * FROM transactions
WHERE name LIKE '%Corp%'
LIMIT 20"""
    },
]


def _build_few_shot_prompt(schema: str, question: str) -> str:
    """Build prompt with few-shot examples."""
    examples_text = ""
    for i, ex in enumerate(SQL_FEW_SHOT_EXAMPLES, 1):
        examples_text += f"""
--- Example {i} ---
SCHEMA:
{ex['schema']}

QUESTION: {ex['question']}

SQL:
{ex['sql']}
"""
    
    return f"""Here are examples of how to generate SQL:
{examples_text}
--- Your Task ---
SCHEMA:
{schema}

QUESTION: {question}

SQL:"""


class LLMClient:
    """
    Local LLM client using Ollama.
    
    Supports dual-model setup:
    - Primary model for general tasks
    - SQL model for text-to-SQL (optional, falls back to primary)
    """
    
    def __init__(self, model: str = LLM_MODEL, sql_model: Optional[str] = SQL_MODEL):
        self.model = model
        self.sql_model = sql_model
        self.client = ollama.Client(host=OLLAMA_BASE_URL)
        
        # Check if SQL model is available, fallback to primary if not
        if self.sql_model and not self._is_model_available(self.sql_model):
            print(f"⚠️ SQL model '{self.sql_model}' not found, using '{self.model}' for SQL")
            print(f"   Install with: ollama pull {self.sql_model}")
            self.sql_model = None
        
        # Test SQL model quality - some versions produce garbage
        if self.sql_model:
            try:
                test_result = self._quick_sql_test()
                if not test_result:
                    print(f"⚠️ SQL model '{self.sql_model}' not producing valid SQL, using '{self.model}'")
                    self.sql_model = None
            except Exception:
                self.sql_model = None
    
    def _quick_sql_test(self) -> bool:
        """Quick test to verify SQL model works correctly."""
        try:
            test_prompt = "TABLE: test (id INT, name VARCHAR)\n\nQuestion: Show all names"
            messages = [
                {"role": "system", "content": SQL_SYSTEM_PROMPT},
                {"role": "user", "content": f"DATABASE SCHEMA:\n{test_prompt}\n\nGenerate SQL:"}
            ]
            response = self.client.chat(
                model=self.sql_model,
                messages=messages,
                options={"temperature": 0.1, "num_predict": 50}
            )
            sql = response["message"]["content"].strip()
            # Check if response looks like clean SQL (starts with SELECT)
            sql_upper = sql.upper()
            # Must start with SELECT and contain FROM
            if not sql_upper.startswith("SELECT") or "FROM" not in sql_upper:
                return False
            # Should not contain garbage prefixes
            if "<s>" in sql or "#" in sql[:20]:
                return False
            return True
        except Exception:
            return False
    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        try:
            models = self.client.list()
            model_list = models.get("models", []) if isinstance(models, dict) else getattr(models, 'models', [])
            for m in model_list:
                name = m.get("model") if isinstance(m, dict) else getattr(m, 'model', None)
                if name and model_name in name:
                    return True
            return False
        except Exception:
            return False
        
    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
        json_mode: bool = False
    ) -> str:
        """Generate a response from the primary LLM."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        
        if json_mode:
            options["format"] = "json"
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options=options
        )
        
        return response["message"]["content"]
    
    def generate_sql(
        self,
        prompt: str,
        schema: str,
        temperature: float = SQL_TEMPERATURE,
        max_tokens: int = SQL_MAX_TOKENS,
        use_few_shot: bool = True
    ) -> str:
        """
        Generate SQL using few-shot learning for better accuracy.
        
        Args:
            prompt: Natural language question
            schema: Database schema (tables, columns, sample data)
            temperature: Low for deterministic SQL
            max_tokens: SQL queries are typically short
            use_few_shot: Whether to include few-shot examples (default True)
            
        Returns:
            Raw SQL query string
        """
        
        # Build prompt with or without few-shot examples
        if use_few_shot:
            full_prompt = _build_few_shot_prompt(schema, prompt)
        else:
            full_prompt = f"""DATABASE SCHEMA:
{schema}

USER QUESTION: {prompt}

Generate a DuckDB SQL query to answer this question. Return ONLY the SQL."""
        
        messages = [
            {"role": "system", "content": SQL_SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt}
        ]
        
        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        
        # Try SQL model first if available
        if self.sql_model:
            try:
                response = self.client.chat(
                    model=self.sql_model,
                    messages=messages,
                    options=options
                )
                sql = self._clean_sql(response["message"]["content"])
                
                # Validate the result - must be valid SQL
                if sql and sql.upper().startswith("SELECT") and "FROM" in sql.upper():
                    return sql
                # Invalid SQL from SQL model - fall through to primary
            except Exception:
                pass
        
        # Fallback to primary model with few-shot
        messages[0]["content"] = SQL_SYSTEM_PROMPT
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options=options
        )
        
        sql = response["message"]["content"]
        return self._clean_sql(sql)
    
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL response from LLM."""
        sql = sql.strip()
        
        # Remove markdown code blocks
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(line for line in lines if not line.startswith("```"))
            sql = sql.strip()
        
        # Remove language hints
        for prefix in ["sql", "SQL", "duckdb", "DuckDB"]:
            if sql.lower().startswith(prefix.lower()):
                sql = sql[len(prefix):].strip()
        
        # Remove backticks
        sql = sql.strip('`').strip()
        
        # Take only first statement
        if ";" in sql:
            sql = sql.split(";")[0].strip()
        
        return sql
    
    def generate_json(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> dict:
        """Generate a JSON response from the LLM."""
        response = self.generate(prompt, system_prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {response}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running and primary model is available."""
        return self._is_model_available(self.model)
    
    def get_model_info(self) -> dict:
        """Get information about configured models."""
        return {
            "primary_model": self.model,
            "primary_available": self._is_model_available(self.model),
            "sql_model": self.sql_model,
            "sql_available": self._is_model_available(self.sql_model) if self.sql_model else False,
            "using_for_sql": self.sql_model if self.sql_model else self.model
        }


# Convenience functions
def get_llm() -> LLMClient:
    """Get the default LLM client."""
    return LLMClient()


def get_sql_llm() -> LLMClient:
    """Get LLM client configured for SQL generation."""
    return LLMClient()

