from pathlib import Path
from typing import Any, Dict, List
import json
import os

from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Centralized config manager for single-source JSON config.

    Uses `config/app_config.json` as the single source of truth. Provides
    accessors and mutators for models and other settings. Fails fast on
    invalid model selections to enforce deterministic behavior.
    """

    DEFAULT_PATH = Path('config') / 'app_config.json'

    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_PATH
        self._ensure_config_exists()
        self.config = self._load_config()
        self._validate_models()

    def _ensure_config_exists(self):
        if not self.config_path.exists():
            # Create parent folders and write defaults
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._default_config(), f, indent=2)
            logger.info(f"Created default config at {self.config_path}")

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _default_config(self) -> Dict[str, Any]:
        return {
            "ocr": {"mode": "local", "confidence_threshold": 0.6},
            "models": {"selected": "", "available": []},
            "image": {"max_width": 1200, "quality": 70},
            "security": {"keys_path": ""},
            "vault": {"notes_folder": "Notes", "assets_folder": "assets"}
        }

    def _save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any):
        keys = key.split('.')
        node = self.config
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value
        self._save()

    # Model registry helpers
    def list_models(self) -> List[Dict[str, str]]:
        return self.config.get('models', {}).get('available', [])

    def get_selected_model(self) -> str:
        return self.config.get('models', {}).get('selected', '')

    def add_model(self, name: str, provider: str, mtype: str = 'api'):
        available = self.config.setdefault('models', {}).setdefault('available', [])
        # Prevent duplicates
        for m in available:
            if m.get('name') == name:
                # Update provider/type if changed
                m['provider'] = provider
                m['type'] = mtype
                break
        else:
            available.append({'name': name, 'provider': provider, 'type': mtype})
        # Set as selected
        self.config['models']['selected'] = name
        self._save()

    def set_selected_model(self, name: str):
        available = [m.get('name') for m in self.list_models()]
        if name not in available:
            raise ValueError(f"Selected model '{name}' is not present in available models")
        self.config['models']['selected'] = name
        self._save()

    def _validate_models(self):
        selected = self.get_selected_model()
        available = [m.get('name') for m in self.list_models()]
        if selected and selected not in available:
            raise ValueError("Config validation failed: 'models.selected' must reference exactly one entry in 'models.available'")

    def load_symbols(self) -> Dict[str, Any]:
        symbols_path = Path('config') / 'symbols.json'
        if symbols_path.exists():
            with open(symbols_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'symbols': {}, 'rendering': {}}
