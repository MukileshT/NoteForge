"""LLM Provider Factory"""
from typing import Dict, Any
from llm.provider_interface import LLMProvider, LLMConfig
from llm.providers import (
    GeminiProvider, OpenRouterProvider, GroqProvider,
    OllamaProvider, HuggingFaceProvider, MistralProvider
)
from utils.logger import get_logger

logger = get_logger(__name__)

PROVIDER_MAP = {
    'gemini': GeminiProvider,
    'openrouter': OpenRouterProvider,
    'groq': GroqProvider,
    'ollama': OllamaProvider,
    'huggingface': HuggingFaceProvider,
    'mistral': MistralProvider
}

DEFAULT_MODELS = {
    'gemini': 'gemini-2.0-flash-exp',
    'openrouter': 'anthropic/claude-3.5-sonnet',
    'groq': 'llama-3.3-70b-versatile',
    'ollama': 'llama3.2',
    'huggingface': 'meta-llama/Llama-3.2-3B-Instruct',
    'mistral': 'mistral-large-latest'
}

class ProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create(provider_name: str, api_key: str, model: str = None,
               max_tokens: int = 1024, temperature: float = 0.7,
               base_url: str = None, **kwargs) -> LLMProvider:
        """Create a provider instance
        
        Args:
            provider_name: Name of provider (gemini, openrouter, groq, etc.)
            api_key: API key for the provider
            model: Model name (uses default if not provided)
            max_tokens: Maximum tokens per request
            temperature: Temperature for generation
            base_url: Base URL for provider (if applicable)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            LLMProvider instance
        """
        provider_name = provider_name.lower()
        
        if provider_name not in PROVIDER_MAP:
            raise ValueError(f"Unknown provider: {provider_name}. "
                           f"Available: {list(PROVIDER_MAP.keys())}")
        
        # Use default model if not provided
        if not model:
            model = DEFAULT_MODELS.get(provider_name)
            logger.info(f"Using default model for {provider_name}: {model}")
        
        config = LLMConfig(
            provider=provider_name,
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
            base_url=base_url,
            extra_params=kwargs
        )
        
        provider_class = PROVIDER_MAP[provider_name]
        return provider_class(config)
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available providers"""
        return list(PROVIDER_MAP.keys())
    
    @staticmethod
    def get_default_model(provider_name: str) -> str:
        """Get default model for a provider"""
        return DEFAULT_MODELS.get(provider_name.lower(), '')
