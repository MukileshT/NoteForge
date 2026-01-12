"""Secure API Key Management with Encryption"""
import os
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# #region agent log
try:
    with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_keymgr_before_crypto", "timestamp": int(datetime.now().timestamp() * 1000), "location": "key_manager.py:10", "message": "Before importing cryptography", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
except: pass
# #endregion

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_keymgr_crypto_success", "timestamp": int(datetime.now().timestamp() * 1000), "location": "key_manager.py:14", "message": "Successfully imported cryptography", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
    except: pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_keymgr_crypto_error", "timestamp": int(datetime.now().timestamp() * 1000), "location": "key_manager.py:18", "message": "ImportError: cryptography missing", "data": {"error_type": type(e).__name__, "error_msg": str(e), "error_args": e.args}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
    except: pass
    # #endregion
    raise ImportError(f"cryptography library is required but not installed. Install with: pip install cryptography") from e

import base64
from utils.logger import get_logger

logger = get_logger(__name__)

class KeyManager:
    """Manages encrypted storage of API keys"""
    
    def __init__(self, storage_path: str = ".api_keys.enc"):
        self.storage_path = Path(storage_path)
        self.master_key_file = Path(".master.key")
        self._cipher = None
        self._initialize()
    
    def _initialize(self):
        """Initialize encryption with master key"""
        if self.master_key_file.exists():
            with open(self.master_key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new master key
            key = Fernet.generate_key()
            with open(self.master_key_file, 'wb') as f:
                f.write(key)
            # Hide master key file on Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.master_key_file), 2)
        
        self._cipher = Fernet(key)
    
    def save_key(self, provider: str, api_key: str):
        """Save encrypted API key for a provider"""
        try:
            keys = self._load_keys()
            keys[provider] = api_key
            self._save_keys(keys)
            logger.info(f"Saved API key for {provider}")
        except Exception as e:
            logger.error(f"Failed to save key for {provider}: {e}")
            raise
    
    def get_key(self, provider: str) -> Optional[str]:
        """Retrieve decrypted API key for a provider"""
        try:
            keys = self._load_keys()
            return keys.get(provider)
        except Exception as e:
            logger.error(f"Failed to retrieve key for {provider}: {e}")
            return None
    
    def delete_key(self, provider: str):
        """Delete API key for a provider"""
        try:
            keys = self._load_keys()
            if provider in keys:
                del keys[provider]
                self._save_keys(keys)
                logger.info(f"Deleted API key for {provider}")
        except Exception as e:
            logger.error(f"Failed to delete key for {provider}: {e}")
            raise
    
    def list_providers(self) -> list:
        """List all providers with stored keys"""
        try:
            keys = self._load_keys()
            return list(keys.keys())
        except:
            return []
    
    def _load_keys(self) -> Dict[str, str]:
        """Load and decrypt all keys"""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'rb') as f:
                encrypted = f.read()
            decrypted = self._cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.warning(f"Failed to load keys: {e}")
            return {}
    
    def _save_keys(self, keys: Dict[str, str]):
        """Encrypt and save all keys"""
        try:
            data = json.dumps(keys).encode()
            encrypted = self._cipher.encrypt(data)
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted)
            # Hide encrypted file on Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.storage_path), 2)
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
