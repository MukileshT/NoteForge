"""Unified LLM Provider Interface"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: str
    model: str
    api_key: str
    max_tokens: int = 1024
    temperature: float = 0.7
    base_url: Optional[str] = None
    extra_params: Dict[str, Any] = None

@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    tokens_used: int
    finish_reason: str = "stop"
    model: str = ""

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_tokens = 0
    
    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate text completion"""
        pass
    
    @abstractmethod
    def complete_with_image(self, prompt: str, image_path: Path, 
                           system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion with image input (vision)"""
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        """Check if provider supports vision"""
        pass
    
    def get_token_usage(self) -> int:
        """Get total tokens used"""
        return self.total_tokens
    
    def reset_token_usage(self):
        """Reset token counter"""
        self.total_tokens = 0
