"""Configuration parser for the PostRenderCleaner tool."""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

class ConfigParser:
    """Parses and validates configuration files."""
    
    def __init__(self):
        """Initialize the config parser."""
        self.logger = logging.getLogger("postrendercleaner.config")
        self.default_config = self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "cleanup": {
                "temp_patterns": ["*.tmp", "*.temp", "*_scratch.*", "render_cache/*"],
                "retention": {
                    "logs": 30,  # days
                    "intermediates": 7,  # days
                    "backups": 90,  # days
                },
                "actions": {
                    "compress_renders": True,
                    "archive_to_cold_storage": True,
                    "generate_report": True,
                },
                "notification": {
                    "email_on_completion": True,
                    "slack_on_error": True,
                }
            }
        }
    
    def parse(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Parse configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        if not config_path:
            self.logger.info("No config path provided, using default configuration")
            return self.default_config
        
        path = Path(config_path) if isinstance(config_path, str) else config_path
        
        if not path.exists():
            self.logger.warning(f"Config file not found: {path}, using default configuration")
            return self.default_config
        
        try:
            with open(path, 'r') as f:
                if path.suffix.lower() == '.json':
                    config = json.load(f)
                else:  # Default to YAML
                    config = yaml.safe_load(f)
                
                self.logger.info(f"Loaded configuration from {path}")
                
                # Merge with defaults for any missing values
                return self._merge_with_defaults(config)
                
        except Exception as e:
            self.logger.error(f"Failed to parse config from {path}: {e}")
            self.logger.warning("Using default configuration")
            return self.default_config
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge provided config with defaults for missing values."""
        result = self.default_config.copy()
        
        # Simple recursive merge
        def merge_dicts(default_dict, override_dict):
            for key, value in override_dict.items():
                if key in default_dict and isinstance(value, dict) and isinstance(default_dict[key], dict):
                    merge_dicts(default_dict[key], value)
                else:
                    default_dict[key] = value
        
        merge_dicts(result, config)
        return result
