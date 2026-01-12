# Fix Gemini API call in ai_client.py

@"
import json
import base64
from pathlib import Path
from typing import Dict, Any
import anthropic
import openai
from google import genai
from google.genai import types
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
            self.model_name = config.get('gemini_model', 'gemini-2.5-flash')
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
    
    def _call_gemini(self, image_path: Path, prompt: str) -> str:
        from PIL import Image
        img = Image.open(image_path)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_text(prompt),
                types.Part.from_image(img)
            ]
        )
        return response.text
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)
        return json.loads(response)
"@ | Out-File -FilePath "src/vision/ai_client.py" -Encoding UTF8

Write-Host "✅ Fixed Gemini API call" -ForegroundColor Green
Write-Host ""
Write-Host "Make sure your Gemini API key is set in config.yaml" -ForegroundColor Yellow
Write-Host "Then run: python main.py" -ForegroundColor Cyan
