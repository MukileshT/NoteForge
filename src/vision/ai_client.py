import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from google import generativeai as genai
from groq import Groq
from PIL import Image
from openai import OpenAI # Keep this for OpenRouter
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class AIClient:
    def __init__(self, config, provider: str = None, model: str = None, api_key: str = None):
        self.config = config
        # Accept explicit provider/model/api_key; fall back to config if not provided
        self.provider = provider or config.get('ai_provider')
        self.api_key = api_key
        self.model = model or (config.get(f'{self.provider}_model', '') if self.provider else '')
        
        self.client: Any = None

        # If provider is still None, raise with proper error
        if not self.provider:
            raise ValueError("No AI provider configured. Set models.selected in config/app_config.json or pass provider explicitly.")
        
        # Try to get API key from parameter, then config
        if not self.api_key:
            api_key_name = f'{self.provider}_api_key'
            self.api_key = self.config.get(api_key_name)

        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            raise ValueError(f"{self.provider.capitalize()} API key not configured or is a placeholder in config.yaml")

        if self.provider == 'gemini':
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == 'openrouter':
            self.client = OpenAI(api_key=self.api_key, base_url=self.config.get('openrouter_base_url'))
        elif self.provider == 'groq':
            self.client = Groq(api_key=self.api_key)
        else:
            raise ValueError(f"Unknown AI provider or provider not supported: {self.provider}. Supported: gemini, openrouter, groq")
        
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

            if self.provider == 'openrouter': # Openrouter uses OpenAI client for images
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
                # PIL Image is required for Gemini's generate_content with image input
                # Ensure it's imported at the top of the file
                img = Image.open(image_path)
                response = self.client.generate_content(
                    contents=[prompt, img]
                )
                return response.text
            else:
                raise ValueError(f"Image calls not supported for provider: {self.provider}")
        else: # Text-only call
            if self.provider in ['openrouter', 'groq']: # Groq is text-only
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
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        response = response.strip()
        
        # Find JSON in markdown
        match = re.search(r'```(json)?\s*(\{.*\}|\[.*\])\s*```', response, re.DOTALL)
        if match:
            json_str = match.group(2)
        else:
            # Find JSON without markdown
            match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                raise ValueError("No JSON object or array found in the AI response")

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {json_str}")
            raise e

