"""
NUCLEUS V1.2 - LLM Gateway
Multi-model LLM support using LiteLLM
"""

import os
from typing import List, Dict, Any, Optional
import litellm
from litellm import completion, embedding
import logging

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = False  # Set to True for debugging


class LLMGateway:
    """
    LLM Gateway for NUCLEUS.
    Supports multiple LLM providers via LiteLLM.
    """
    
    def __init__(self):
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "gemini/gemini-2.0-flash-exp")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        
        # Model fallback chain
        self.fallback_models = [
            "gemini/gemini-2.0-flash-exp",
            "gemini/gemini-1.5-flash",
            "gpt-4o-mini"
        ]
        
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional LiteLLM parameters
            
        Returns:
            Generated text
        """
        model = model or self.default_model
        
        try:
            response = await completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM completion error with {model}: {e}")
            
            # Try fallback models
            for fallback_model in self.fallback_models:
                if fallback_model != model:
                    try:
                        logger.info(f"Trying fallback model: {fallback_model}")
                        response = await completion(
                            model=fallback_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs
                        )
                        return response.choices[0].message.content
                    except Exception as fallback_error:
                        logger.error(f"Fallback model {fallback_model} failed: {fallback_error}")
                        continue
            
            raise Exception("All LLM models failed")
    
    async def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion with tool calling support.
        
        Args:
            messages: List of message dicts
            tools: List of tool definitions (OpenAI format)
            model: Model to use
            **kwargs: Additional parameters
            
        Returns:
            Full response dict with tool calls
        """
        model = model or self.default_model
        
        try:
            response = await completion(
                model=model,
                messages=messages,
                tools=tools,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM tool calling error: {e}")
            raise
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            Embedding vector
        """
        model = model or self.embedding_model
        
        try:
            response = await embedding(
                model=model,
                input=text
            )
            
            return response.data[0]["embedding"]
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        model = model or self.embedding_model
        
        try:
            response = await embedding(
                model=model,
                input=texts
            )
            
            return [item["embedding"] for item in response.data]
            
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise


# Singleton instance
_llm_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """Get or create the singleton LLM gateway"""
    global _llm_gateway
    
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
    
    return _llm_gateway
