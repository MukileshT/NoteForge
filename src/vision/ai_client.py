import json
import base64
from pathlib import Path
from typing import Dict, Any
import anthropic
import openai
from google import genai
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class AIClient:
    def __init__(self, config):
        self.config = config
        self.provider = config.get('ai_provider')
        api_key = config.get('ai_api_key')
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            raise ValueError("API key not configured in config.yaml")
        if self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = config.get('anthropic_model')
        elif self.provider == 'openai':
            openai.api_key = api_key
            self.model = config.get('openai_model')
        elif self.provider == 'gemini':
            self.client = genai.Client(api_key=api_key)
            self.model_name = config.get('gemini_model', 'gemini-2.0-flash-exp')
            logger.info(f"Initialized Gemini AIClient with model: {self.model_name}")
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def analyze_image(self, image_path: Path, prompt: str) -> Dict[str, Any]:
        try:
            if self.provider == 'anthropic':
                image_data = self._encode_image(image_path)
                response = self._call_anthropic(image_data, prompt)
            elif self.provider == 'openai':
                image_data = self._encode_image(image_path)
                response = self._call_openai(image_data, prompt)
            else:
                response = self._call_gemini(image_path, prompt)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise
    
    def analyze_text(self, prompt: str) -> Dict[str, Any]:
        try:
            if self.provider == 'anthropic':
                response = self._call_anthropic_text(prompt)
            elif self.provider == 'openai':
                response = self._call_openai_text(prompt)
            else:
                response = self._call_gemini_text(prompt)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise
    
    def _encode_image(self, path: Path) -> str:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _call_anthropic(self, image_data: str, prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        return msg.content[0].text

    def _call_anthropic_text(self, prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }]
        )
        return msg.content[0].text
    
    def _call_openai(self, image_data: str, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }],
            max_tokens=1024
        )
        return response.choices[0].message.content

    def _call_openai_text(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }],
            max_tokens=1024
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, image_path: Path, prompt: str) -> str:
        from PIL import Image
        img = Image.open(image_path)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt, img]
        )
        return response.text

    def _call_gemini_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt]
        )
        return response.text
    
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
