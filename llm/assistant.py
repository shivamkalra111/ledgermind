"""
LLM Assistant using Ollama (Local Models)

This module provides a generic interface to interact with any LLM
running through Ollama. Model can be easily changed via configuration.
"""

import requests
import json
from typing import List, Dict, Optional


class LLMAssistant:
    """
    Generic LLM interface using Ollama.
    
    Supports any model available in Ollama by just changing model_name.
    Examples: qwen2.5:7b-instruct, llama3:8b, mistral:7b, etc.
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize LLM assistant.
        
        Args:
            model_name: Name of the Ollama model (e.g., 'qwen2.5:7b-instruct')
            base_url: Ollama API base URL (default: localhost)
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
        # Verify connection
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if self.model_name not in model_names:
                print(f"⚠️  Warning: Model '{self.model_name}' not found in Ollama")
                print(f"Available models: {model_names}")
                print(f"Download with: ollama pull {self.model_name}")
                raise ValueError(f"Model {self.model_name} not available")
            
            print(f"✅ Connected to Ollama (model: {self.model_name})")
            print(f"   Running locally at {self.base_url}")
            
        except requests.exceptions.ConnectionError:
            error_msg = (
                f"❌ Cannot connect to Ollama at {self.base_url}\n"
                "   Make sure Ollama is running:\n"
                "   → Terminal 1: ollama serve\n"
                f"   → Terminal 2: ollama pull {self.model_name}"
            )
            raise ConnectionError(error_msg)
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 512,
        top_p: float = 0.9,
        stream: bool = False
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: Input prompt for the model
            temperature: Sampling temperature (0.0-1.0, lower = more focused)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stream: Whether to stream response (not implemented)
        
        Returns:
            Generated text
        """
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,  # Always false for now
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "num_predict": max_tokens
                    }
                },
                timeout=120  # 2 minutes timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.Timeout:
            raise TimeoutError("LLM generation timed out (>2 minutes)")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM generation failed: {e}")
    
    def generate_with_context(
        self,
        question: str,
        context_chunks: List[Dict],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate answer based on question and context chunks.
        
        Args:
            question: User's question
            context_chunks: List of dicts with 'text', 'source', 'page' keys
            system_prompt: Optional system instruction
            **kwargs: Additional arguments passed to generate()
        
        Returns:
            Generated answer
        """
        # Build prompt
        prompt = self._build_prompt(question, context_chunks, system_prompt)
        
        # Generate
        return self.generate(prompt, **kwargs)
    
    def _build_prompt(
        self,
        question: str,
        context_chunks: List[Dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Build prompt from question and context.
        
        Format:
            [System Instruction]
            
            Context from sources:
            [Source 1] ...
            [Source 2] ...
            
            Question: ...
            
            Answer:
        """
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = (
                "You are a helpful AI assistant. "
                "Provide accurate answers based on the given context. "
                "If the context doesn't contain enough information, say so. "
                "Always cite sources when providing information."
            )
        
        # Format context chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks[:5], 1):  # Top 5 chunks
            source = chunk.get('source', 'Unknown')
            page = chunk.get('page', 'N/A')
            text = chunk.get('text', '')
            
            context_parts.append(
                f"[Source {i}: {source}, Page {page}]\n{text}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Build complete prompt
        prompt = f"""{system_prompt}

Context from documents:
{context}

User Question: {question}

Answer (based on the context provided):"""
        
        return prompt
    
    def list_available_models(self) -> List[str]:
        """
        List all models available in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def switch_model(self, new_model_name: str):
        """
        Switch to a different model.
        
        Args:
            new_model_name: Name of the new model to use
        """
        old_model = self.model_name
        self.model_name = new_model_name
        
        try:
            self._verify_connection()
            print(f"✅ Switched from {old_model} to {new_model_name}")
        except Exception as e:
            # Revert on failure
            self.model_name = old_model
            raise RuntimeError(f"Failed to switch to {new_model_name}: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize with default model
    llm = LLMAssistant()
    
    # Simple generation
    response = llm.generate("What is GST?")
    print(response)
    
    # Generation with context
    context = [
        {
            'text': 'GST stands for Goods and Services Tax...',
            'source': 'gst_guide.pdf',
            'page': 1
        }
    ]
    answer = llm.generate_with_context(
        question="What does GST stand for?",
        context_chunks=context
    )
    print(answer)
    
    # List available models
    print("Available models:", llm.list_available_models())

