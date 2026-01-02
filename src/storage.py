import json
import os
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken
from .encryption import derive_key, generate_salt

class StorageManager:
    def __init__(self, filename: str = None):
        if filename is None:
            # Use a persistent user directory
            data_dir = os.path.expanduser("~/.iitkgp_erp_manager")
            os.makedirs(data_dir, exist_ok=True)
            self.filename = os.path.join(data_dir, "vault.json")
        else:
            self.filename = filename
            
        self.cached_creds: Optional[Dict] = None

    def exists(self) -> bool:
        return os.path.exists(self.filename)

    def init_vault(self, pin: str) -> None:
        """Initializes a new empty vault secured with the PIN."""
        salt = generate_salt()
        key = derive_key(pin, salt)
        fernet = Fernet(key)
        
        # Initial empty data
        data = {}
        encrypted_data = fernet.encrypt(json.dumps(data).encode())
        
        vault_content = {
            "salt": base64.b64encode(salt).decode('utf-8'),
            "data": base64.b64encode(encrypted_data).decode('utf-8')
        }
        
        with open(self.filename, 'w') as f:
            json.dump(vault_content, f)

    def unlock(self, pin: str) -> bool:
        """Attempts to unlock the vault with the PIN. Returns True if successful."""
        if not self.exists():
            return False
            
        try:
            with open(self.filename, 'r') as f:
                vault_content = json.load(f)
            
            salt = base64.b64decode(vault_content["salt"])
            key = derive_key(pin, salt)
            fernet = Fernet(key)
            
            encrypted_data = base64.b64decode(vault_content["data"])
            decrypted_data = fernet.decrypt(encrypted_data)
            self.cached_creds = json.loads(decrypted_data.decode())
            return True
        except (InvalidToken, KeyError, json.JSONDecodeError, ValueError):
            return False

    def save_credentials(self, pin: str, creds: Dict) -> bool:
        """Saves credentials to the vault."""
        # We need to re-encrypt everything with the PIN derived key
        # Ideally, we should already have the key if unlocked, but for safety
        # we re-derive since we don't store the key permanently in memory?
        # Actually storage manager keeps cached_creds, but not the key.
        # So we strictly need the PIN to save.
        
        try:
            with open(self.filename, 'r') as f:
                vault_content = json.load(f)
            salt = base64.b64decode(vault_content["salt"])
        except:
             # If file is corrupted or missing, start fresh
             salt = generate_salt()

        key = derive_key(pin, salt)
        fernet = Fernet(key)
        
        encrypted_data = fernet.encrypt(json.dumps(creds).encode())
        
        new_vault_content = {
            "salt": base64.b64encode(salt).decode('utf-8'),
            "data": base64.b64encode(encrypted_data).decode('utf-8')
        }
        
        with open(self.filename, 'w') as f:
            json.dump(new_vault_content, f)
            
        self.cached_creds = creds
        return True

    def get_credentials(self) -> Optional[Dict]:
        return self.cached_creds
        
import base64
