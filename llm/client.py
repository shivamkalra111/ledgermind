"""
LLM Client - Ollama/Qwen Integration
Handles all LLM interactions locally
"""

import json
from typing import Optional
import ollama
from config import OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, SYSTEM_PROMPT


class LLMClient:
    """Local LLM client using Ollama."""
    
    def __init__(self, model: str = LLM_MODEL):
        self.model = model
        self.client = ollama.Client(host=OLLAMA_BASE_URL)
        
    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
        json_mode: bool = False
    ) -> str:
        """Generate a response from the LLM."""
        
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
        """Check if Ollama is running and model is available."""
        try:
            models = self.client.list()
            # Handle both dict and object responses from ollama library
            model_list = models.get("models", []) if isinstance(models, dict) else getattr(models, 'models', [])
            model_names = []
            for m in model_list:
                # Handle both dict and Model object
                name = m.get("model") if isinstance(m, dict) else getattr(m, 'model', None)
                if name:
                    model_names.append(name)
            return any(self.model in name for name in model_names)
        except Exception:
            return False


# Convenience function
def get_llm() -> LLMClient:
    """Get the default LLM client."""
    return LLMClient()

