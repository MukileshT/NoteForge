import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import anthropic
from openai import OpenAI
from google import generativeai as genai
from groq import Groq
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class AIClient:
    def __init__(self, config):
        self.config = config
        self.provider = config.get('ai_provider')
        
        self.client: Any = None
        self.model: str = ""

        if self.provider == 'anthropic':
            api_key = self.config.get('anthropic_api_key')
            if not api_key or api_key == 'YOUR_API_KEY_HERE':
                raise ValueError("Anthropic API key not configured in config.yaml")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = self.config.get('anthropic_model')
        elif self.provider in ['openai', 'openrouter', 'deepseek']:
            api_key = self.config.get(f'{self.provider}_api_key')
            if not api_key or api_key == 'YOUR_API_KEY_HERE':
                raise ValueError(f"{self.provider.capitalize()} API key not configured in config.yaml")
            
            base_url = self.config.get(f'{self.provider}_base_url', None)
            self.client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            self.model = self.config.get(f'{self.provider}_model')
        elif self.provider == 'gemini':
            api_key = self.config.get('gemini_api_key')
            if not api_key or api_key == 'YOUR_API_KEY_HERE':
                raise ValueError("Gemini API key not configured in config.yaml")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.config.get('gemini_model'))
            self.model = self.config.get('gemini_model')
        elif self.provider == 'groq':
            api_key = self.config.get('groq_api_key')
            if not api_key or api_key == 'YOUR_API_KEY_HERE':
                raise ValueError("Groq API key not configured in config.yaml")
            self.client = Groq(api_key=api_key)
            self.model = self.config.get('groq_model')
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")
        
        if not self.model:
            raise ValueError(f"Model for provider '{self.provider}' not configured in config.yaml")

    def analyze_image(self, image_path: Path, prompt: str) -> Dict[str, Any]:
        try:
            response = self._make_api_call(prompt=prompt, image_path=image_path, is_image_call=True)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise
    
    def analyze_text(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self._make_api_call(prompt=prompt, is_image_call=False)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise

    def _encode_image(self, path: Path) -> str:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _make_api_call(self, prompt: str, image_path: Optional[Path] = None, is_image_call: bool = False) -> str:
        messages = [{"role": "user", "content": prompt}]
        if is_image_call and image_path:
            image_data = self._encode_image(image_path)

            if self.provider == 'anthropic':
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                        {"type": "text", "text": prompt}
                    ]
                }]
                msg = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.config.get('max_tokens', 1024),
                    messages=messages
                )
                return msg.content[0].text
            elif self.provider in ['openai', 'openrouter', 'deepseek']:
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                    ]
                }]
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.config.get('max_tokens', 1024)
                )
                return response.choices[0].message.content
            elif self.provider == 'gemini':
                img = Image.open(image_path) # PIL Image is required for Gemini
                response = self.client.generate_content(
                    contents=[prompt, img]
                )
                return response.text
            else:
                raise ValueError(f"Image calls not supported for provider: {self.provider}")
        else: # Text-only call
            if self.provider == 'anthropic':
                msg = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.config.get('max_tokens', 1024),
                    messages=messages
                )
                return msg.content[0].text
            elif self.provider in ['openai', 'openrouter', 'deepseek', 'groq']: # Groq is text-only
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.config.get('max_tokens', 1024)
                )
                return response.choices[0].message.content
            elif self.provider == 'gemini':
                response = self.client.generate_content(
                    contents=[prompt]
                )
                return response.text
            else:
                raise ValueError(f"Text calls not supported for provider: {self.provider}")

