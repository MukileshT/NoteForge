"""LLM Provider Implementations"""
import base64
import json
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

from PIL import Image

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from llm.provider_interface import LLMProvider, LLMConfig, LLMResponse
from utils.logger import get_logger

logger = get_logger(__name__)

class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from google import genai
        from google.genai import types
        self.genai_types = types
        self.client = genai.Client(api_key=config.api_key)
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        types = self.genai_types
        parts = []
        if system_prompt:
            parts.append(types.Part(text=system_prompt))
        parts.append(types.Part(text=prompt))
        content = types.Content(role="user", parts=parts)
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=content
        )
        text = response.text or ""
        tokens = len(text.split()) * 1.3  # Rough estimate
        self.total_tokens += int(tokens)
        return LLMResponse(
            content=text,
            tokens_used=int(tokens),
            model=self.config.model
        )
    
    def complete_with_image(self, prompt: str, image_path: Path,
                           system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion with image"""
        types = self.genai_types
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        parts = []
        if system_prompt:
            parts.append(types.Part(text=system_prompt))
        parts.append(types.Part(text=prompt))
        # Use correct mime type for your image, here assumed PNG
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
        content = types.Content(role="user", parts=parts)
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=content
        )
        text = response.text or ""
        tokens = len(text.split()) * 1.3  # Rough estimate
        self.total_tokens += int(tokens)
        return LLMResponse(
            content=text,
            tokens_used=int(tokens),
            model=self.config.model
        )
    
    def supports_vision(self) -> bool:
        return True

class OpenRouterProvider(LLMProvider):
    """OpenRouter provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import OpenAI
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://openrouter.ai/api/v1"
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            finish_reason=response.choices[0].finish_reason,
            model=response.model
        )
    
    def complete_with_image(self, prompt: str, image_path: Path,
                           system_prompt: Optional[str] = None) -> LLMResponse:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ]
        })
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            model=response.model
        )
    
    def supports_vision(self) -> bool:
        # Check if model supports vision (most OpenRouter vision models have "vision" in name)
        return "vision" in self.config.model.lower() or "molmo" in self.config.model.lower()

class GroqProvider(LLMProvider):
    """Groq provider (text-only)"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from groq import Groq
        self.client = Groq(api_key=config.api_key)
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            finish_reason=response.choices[0].finish_reason,
            model=response.model
        )
    
    def complete_with_image(self, prompt: str, image_path: Path,
                           system_prompt: Optional[str] = None) -> LLMResponse:
        raise NotImplementedError("Groq does not support vision")
    
    def supports_vision(self) -> bool:
        return False

class OllamaProvider(LLMProvider):
    """Ollama local provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import OpenAI
        self.client = OpenAI(
            api_key="ollama",  # Ollama doesn't need real key
            base_url=config.base_url or "http://localhost:11434/v1"
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        tokens = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            model=self.config.model
        )
    
    def complete_with_image(self, prompt: str, image_path: Path,
                           system_prompt: Optional[str] = None) -> LLMResponse:
        # Ollama supports vision for certain models like llava
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ]
        })
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens
        )
        
        tokens = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            model=self.config.model
        )
    
    def supports_vision(self) -> bool:
        return "llava" in self.config.model.lower() or "vision" in self.config.model.lower()

class HuggingFaceProvider(LLMProvider):
    """HuggingFace Serverless Inference"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import OpenAI
        self.client = OpenAI(
            api_key=config.api_key,
            base_url="https://api-inference.huggingface.co/v1"
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            model=response.model
        )
    
    def complete_with_image(self, prompt: str, image_path: Path,
                           system_prompt: Optional[str] = None) -> LLMResponse:
        raise NotImplementedError("HuggingFace provider vision not implemented")
    
    def supports_vision(self) -> bool:
        return False

class MistralProvider(LLMProvider):
    """Mistral AI provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import OpenAI
        self.client = OpenAI(
            api_key=config.api_key,
            base_url="https://api.mistral.ai/v1"
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            finish_reason=response.choices[0].finish_reason,
            model=response.model
        )
    
    def complete_with_image(self, prompt: str, image_path: Path,
                           system_prompt: Optional[str] = None) -> LLMResponse:
        # Mistral supports vision with Pixtral
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ]
        })
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            model=response.model
        )
    
    def supports_vision(self) -> bool:
        return "pixtral" in self.config.model.lower()
