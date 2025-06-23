"""Retention policy rules for the PostRenderCleaner tool."""

import time
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

class RetentionPolicy:
    """Applies retention policies to files."""
    
    def __init__(self, config: Dict[str, int]):
        """Initialize retention policy with configuration.
        
        Args:
            config: Dictionary of retention periods in days
        """
        self.config = config or {
            "logs": 30,        # days
            "intermediates": 7, # days
            "backups": 90,     # days
        }
        self.logger = logging.getLogger("postrendercleaner.policy")
        
    def apply_policy(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply retention policy to a list of files.
        
        Args:
            files: List of file info dictionaries from scanner
            
        Returns:
            Filtered list of files to be processed
        """
        self.logger.info(f"Applying retention policy to {len(files)} files")
        current_time = time.time()
        filtered_files = []
        
        for file_info in files:
            file_category = self._categorize_file(file_info)
            retention_days = self.config.get(file_category, 0)
            
            # Skip files with retention_days=0 (keep forever)
            if retention_days <= 0:
                self.logger.debug(f"Skipping file with unlimited retention: {file_info['path']}")
                continue
                
            # Calculate retention threshold timestamp
            threshold = current_time - (retention_days * 86400)  # seconds in a day
            
            # Check if file is older than retention period
            if file_info['modified_time'] < threshold:
                file_info['category'] = file_category
                file_info['retention_days'] = retention_days
                filtered_files.append(file_info)
                self.logger.debug(f"File {file_info['path']} exceeds retention period of {retention_days} days")
        
        self.logger.info(f"Retention policy filtered {len(files) - len(filtered_files)} files, {len(filtered_files)} to process")
        return filtered_files
    
    def _categorize_file(self, file_info: Dict[str, Any]) -> str:
        """Categorize a file based on its properties.
        
        Args:
            file_info: File information dictionary
            
        Returns:
            Category name matching a key in the retention config
        """
        path = file_info['path']
        extension = file_info['extension']
        
        # Categorize based on extension and path patterns
        if extension in [".log", ".txt"] or "/logs/" in path:
            return "logs"
        elif "_temp" in path or "_scratch" in path or extension in [".tmp", ".temp"]:
            return "intermediates"
        elif "backup" in path or "archive" in path:
            return "backups"
        else:
            return "intermediates"  # Default category
