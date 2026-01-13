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
    """Manages encrypted storage of API keys.

    Keys are stored encrypted at %APPDATA%/YourApp/keys.enc by default.
    The master key is kept alongside the encrypted file. Decryption only
    occurs in-memory. This class performs explicit permission and read-only
    checks and raises clear errors on failure.
    """

    def __init__(self, storage_path: str = None):
        appdata = os.getenv('APPDATA') or os.path.expanduser('~')
        app_folder = Path(appdata) / 'YourApp'
        app_folder.mkdir(parents=True, exist_ok=True)

        default_storage = app_folder / 'keys.enc'
        default_master = app_folder / 'master.key'

        self.storage_path = Path(storage_path) if storage_path else default_storage
        self.master_key_file = default_master
        self._cipher = None
        self._initialize()
    
    def _initialize(self):
        """Initialize encryption with master key"""
        try:
            if self.master_key_file.exists():
                # Ensure file is readable
                if not os.access(self.master_key_file, os.R_OK):
                    raise PermissionError(f"Master key file not readable: {self.master_key_file}")
                with open(self.master_key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new master key and write with restrictive permissions
                key = Fernet.generate_key()
                with open(self.master_key_file, 'wb') as f:
                    f.write(key)
                try:
                    # Attempt to set file writable only by owner where possible
                    os.chmod(self.master_key_file, 0o600)
                except Exception:
                    # Non-fatal on Windows or limited environments
                    pass

            self._cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize KeyManager: {e}")
            raise
    
    def save_key(self, provider: str, api_key: str):
        """Save encrypted API key for a provider"""
        # Save encrypted key with explicit permission checks
        try:
            # Ensure storage directory exists and writable
            storage_dir = self.storage_path.parent
            storage_dir.mkdir(parents=True, exist_ok=True)
            if not os.access(storage_dir, os.W_OK):
                raise PermissionError(f"Storage directory not writable: {storage_dir}")

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

        # Ensure the file is readable and not read-only locked
        if not os.access(self.storage_path, os.R_OK):
            logger.warning(f"Encrypted keys file not readable: {self.storage_path}")
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
            # If storage exists and is read-only, raise
            if self.storage_path.exists() and not os.access(self.storage_path, os.W_OK):
                raise PermissionError(f"Encrypted keys file is not writable: {self.storage_path}")
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted)
            try:
                os.chmod(self.storage_path, 0o600)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
