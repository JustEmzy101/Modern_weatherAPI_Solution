import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class APIKeyManager:
    def __init__(self, config_path: str = None):
        """Initialize API key manager with config file"""
        self.config_path = config_path or os.getenv('API_KEYS_CONFIG', 'api_keys_config.json')
        self.keys = {}
        self.load_keys()
    
    def load_keys(self):
        """Load API keys from config file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.keys = json.load(f)
                logger.info(f"Loaded {len(self.keys)} API keys from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load API keys config: {e}")
                self.keys = {}
        else:
            logger.warning(f"API keys config not found at {self.config_path}")
    
    def is_valid(self, api_key: str) -> bool:
        """Check if API key is valid and active"""
        if api_key not in self.keys:
            logger.warning(f"API key not found in whitelist")
            return False
        
        key_info = self.keys[api_key]
        
        # Check if key is active
        if not key_info.get('active', False):
            logger.warning(f"Inactive API key attempted: {key_info.get('name')}")
            return False
        
        # Check if key has expired
        if 'expires_at' in key_info:
            try:
                expiry = datetime.fromisoformat(key_info['expires_at'])
                if datetime.now() > expiry:
                    logger.warning(f"Expired API key attempted: {key_info.get('name')}")
                    return False
            except ValueError:
                logger.error(f"Invalid expiry date format for key: {key_info.get('name')}")
                return False
        
        return True
    
    def get_key_info(self, api_key: str) -> dict:
        """Get key metadata"""
        return self.keys.get(api_key, {})

# Initialize manager
key_manager = APIKeyManager()