"""
LLM Client - Ollama Integration
Handles all LLM interactions locally

Supports dual-model setup:
- Primary model (qwen2.5) for intent routing, knowledge, formatting
- SQL model (sqlcoder) for text-to-SQL generation

Security:
- Input sanitization for prompt injection protection
- SQL validation for generated queries
"""

import json
import logging
from typing import Optional, Tuple
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
from core.security import (
    sanitize_user_input,
    validate_sql_query,
    SecurityResult,
    ThreatLevel,
    OutputSanitizer
)
from llm.secure_prompts import (
    SECURE_SYSTEM_PROMPT,
    SECURE_SQL_SYSTEM_PROMPT,
    SecurePromptBuilder,
    get_prompt_builder
)

logger = logging.getLogger(__name__)


# Use secure SQL system prompt (with injection resistance)
SQL_SYSTEM_PROMPT = SECURE_SQL_SYSTEM_PROMPT

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
    
    Security features:
    - Input sanitization for prompt injection protection
    - SQL validation before returning generated queries
    - Output sanitization to remove system artifacts
    """
    
    def __init__(
        self, 
        model: str = LLM_MODEL, 
        sql_model: Optional[str] = SQL_MODEL,
        enable_security: bool = True
    ):
        self.model = model
        self.sql_model = sql_model
        self.client = ollama.Client(host=OLLAMA_BASE_URL)
        self.enable_security = enable_security
        
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
        json_mode: bool = False,
        skip_security: bool = False,
        use_secure_framing: bool = True,
        context: str = None
    ) -> str:
        """
        Generate a response from the primary LLM.
        
        Args:
            prompt: User prompt (will be sanitized)
            system_prompt: System prompt for context
            temperature: Response randomness
            max_tokens: Maximum response length
            json_mode: Whether to request JSON output
            skip_security: Skip input sanitization (use only for internal prompts)
            use_secure_framing: Wrap prompt with defensive framing (recommended)
            context: Optional context to include with secure framing
            
        Returns:
            LLM response text
            
        Raises:
            ValueError: If prompt is blocked due to security threat
        """
        # Security: Sanitize user input
        if self.enable_security and not skip_security:
            security_result = sanitize_user_input(prompt)
            
            if security_result.blocked:
                logger.warning(
                    f"Blocked prompt injection attempt. "
                    f"Threat: {security_result.threat_level.value}, "
                    f"Issues: {security_result.threats_detected}"
                )
                raise ValueError(
                    "Your request could not be processed due to security restrictions. "
                    "Please rephrase your question."
                )
            
            # Use sanitized input
            if security_result.threats_detected:
                logger.info(f"Sanitized input. Threats detected: {security_result.threats_detected}")
                prompt = security_result.sanitized_input
        
        # Security: Use secure system prompt by default
        if self.enable_security and system_prompt == SYSTEM_PROMPT:
            system_prompt = SECURE_SYSTEM_PROMPT
        
        # Security: Apply secure framing to user prompt
        if self.enable_security and use_secure_framing and not skip_security:
            prompt_builder = get_prompt_builder()
            prompt = prompt_builder.build_query_prompt(prompt, context=context)
        
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
        
        output = response["message"]["content"]
        
        # Security: Clean output of any system artifacts
        if self.enable_security:
            output = OutputSanitizer.remove_system_artifacts(output)
        
        return output
    
    def generate_sql(
        self,
        prompt: str,
        schema: str,
        temperature: float = SQL_TEMPERATURE,
        max_tokens: int = SQL_MAX_TOKENS,
        use_few_shot: bool = True
    ) -> Tuple[str, bool]:
        """
        Generate SQL using few-shot learning for better accuracy.
        
        Security:
        - Input is sanitized for prompt injection
        - Generated SQL is validated before return
        - Only SELECT queries are allowed
        
        Args:
            prompt: Natural language question (will be sanitized)
            schema: Database schema (tables, columns, sample data)
            temperature: Low for deterministic SQL
            max_tokens: SQL queries are typically short
            use_few_shot: Whether to include few-shot examples (default True)
            
        Returns:
            Tuple of (SQL query string, is_valid)
            If security validation fails, returns ("", False)
        """
        # Security: Sanitize the user's question
        if self.enable_security:
            security_result = sanitize_user_input(prompt)
            
            if security_result.blocked:
                logger.warning(
                    f"Blocked SQL generation - prompt injection detected. "
                    f"Threat: {security_result.threat_level.value}"
                )
                return "", False
            
            if security_result.threats_detected:
                logger.info(f"SQL prompt sanitized. Threats: {security_result.threats_detected}")
                prompt = security_result.sanitized_input
        
        # Build prompt with or without few-shot examples
        # Security: Use secure prompt builder for proper framing
        if self.enable_security:
            prompt_builder = get_prompt_builder()
            few_shot_examples = None
            if use_few_shot:
                # Format few-shot examples
                examples_text = ""
                for i, ex in enumerate(SQL_FEW_SHOT_EXAMPLES, 1):
                    examples_text += f"--- Example {i} ---\nSCHEMA:\n{ex['schema']}\n\nQUESTION: {ex['question']}\n\nSQL:\n{ex['sql']}\n\n"
                few_shot_examples = examples_text
            
            full_prompt = prompt_builder.build_sql_prompt(prompt, schema, few_shot_examples)
        elif use_few_shot:
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
        
        sql = ""
        
        # Try SQL model first if available
        if self.sql_model:
            try:
                response = self.client.chat(
                    model=self.sql_model,
                    messages=messages,
                    options=options
                )
                sql = self._clean_sql(response["message"]["content"])
                
                # Basic check - must look like valid SQL
                if not (sql and sql.upper().startswith("SELECT") and "FROM" in sql.upper()):
                    sql = ""  # Invalid, try primary model
            except Exception:
                sql = ""
        
        # Fallback to primary model with few-shot
        if not sql:
            messages[0]["content"] = SQL_SYSTEM_PROMPT
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options
            )
            
            sql = self._clean_sql(response["message"]["content"])
        
        # Security: Validate the generated SQL
        if self.enable_security and sql:
            is_valid, clean_sql, issues = validate_sql_query(sql)
            
            if not is_valid:
                logger.warning(
                    f"Generated SQL failed validation. Issues: {issues}. "
                    f"SQL (truncated): {sql[:200]}"
                )
                return "", False
            
            sql = clean_sql
        
        return sql, bool(sql)
    
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
            "using_for_sql": self.sql_model if self.sql_model else self.model,
            "security_enabled": self.enable_security
        }


# Convenience functions
def get_llm() -> LLMClient:
    """Get the default LLM client."""
    return LLMClient()


def get_sql_llm() -> LLMClient:
    """Get LLM client configured for SQL generation."""
    return LLMClient()

