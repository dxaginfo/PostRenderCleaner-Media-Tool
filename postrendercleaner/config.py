"""
Configuration management for PostRenderCleaner.
"""

import logging
import os
import pkg_resources
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config/default_config.yaml"

class ConfigManager:
    """Manages the configuration for PostRenderCleaner."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file. Uses default if None.
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dict containing the configuration.
        """
        # Start with default config
        config = self._load_default_config()
        
        # Override with custom config if provided
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    custom_config = yaml.safe_load(f)
                
                # Merge configs (custom overrides default)
                if custom_config:
                    self._merge_configs(config, custom_config)
                    logger.info(f"Loaded custom config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading custom config: {e}")
        else:
            if self.config_path:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
            else:
                logger.info("Using default configuration")
        
        return config
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load the default configuration.
        
        Returns:
            Dict containing the default configuration.
        """
        # First check if running from installed package
        try:
            default_config_text = pkg_resources.resource_string(
                __name__.split('.')[0], DEFAULT_CONFIG_PATH
            ).decode('utf-8')
            return yaml.safe_load(default_config_text)
        except (pkg_resources.DistributionNotFound, FileNotFoundError):
            pass
        
        # If not found in package, check for local file
        local_default = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            DEFAULT_CONFIG_PATH
        )
        
        if os.path.exists(local_default):
            try:
                with open(local_default, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading default config: {e}")
        
        # If all else fails, return minimal default config
        logger.warning("Could not load default config, using minimal defaults")
        return {
            "cleanup": {
                "temp_patterns": ["*.tmp", "*.temp", "*_scratch.*", "render_cache/*"],
                "retention": {
                    "logs": 30,
                    "intermediates": 7,
                    "backups": 90
                },
                "actions": {
                    "compress_renders": True,
                    "archive_to_cold_storage": False,
                    "generate_report": True
                },
                "notification": {
                    "email_on_completion": False,
                    "slack_on_error": False
                }
            }
        }
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge override config into base config.
        
        Args:
            base: Base configuration to be updated
            override: Configuration to override base values
        """
        for key, value in override.items():
            if (
                key in base and 
                isinstance(base[key], dict) and 
                isinstance(value, dict)
            ):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def get_temp_patterns(self) -> List[str]:
        """Get the temporary file patterns from config.
        
        Returns:
            List of pattern strings
        """
        return self.config.get('cleanup', {}).get('temp_patterns', [])
    
    def get_retention_policy(self, policy_type: str) -> int:
        """Get retention period in days for a specific policy type.
        
        Args:
            policy_type: Type of retention policy (logs, intermediates, backups)
            
        Returns:
            Retention period in days
        """
        return self.config.get('cleanup', {}).get('retention', {}).get(policy_type, 30)
    
    def get_action_config(self, action: str) -> bool:
        """Get configuration for a specific action.
        
        Args:
            action: Action name (compress_renders, archive_to_cold_storage, etc.)
            
        Returns:
            Boolean indicating if the action is enabled
        """
        return self.config.get('cleanup', {}).get('actions', {}).get(action, False)
    
    def get_notification_config(self, notification: str) -> bool:
        """Get configuration for a specific notification.
        
        Args:
            notification: Notification name (email_on_completion, slack_on_error)
            
        Returns:
            Boolean indicating if the notification is enabled
        """
        return self.config.get('cleanup', {}).get('notification', {}).get(notification, False)
    
    def get_gcs_config(self) -> Dict[str, Any]:
        """Get Google Cloud Storage configuration.
        
        Returns:
            Dict containing GCS configuration
        """
        return self.config.get('gcs', {})