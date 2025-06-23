"""Cleanup operations executor for the PostRenderCleaner tool."""

import os
import shutil
import logging
from typing import List, Dict, Any
from pathlib import Path

from postrendercleaner.cleanup_result import CleanupResult

class CleanupExecutor:
    """Executes cleanup operations on files."""
    
    def __init__(self, config: Dict[str, bool]):
        """Initialize the executor with configuration.
        
        Args:
            config: Dictionary of action flags
        """
        self.config = config or {
            "compress_renders": True,
            "archive_to_cold_storage": True,
            "generate_report": True,
        }
        self.logger = logging.getLogger("postrendercleaner.executor")
        
    def execute(self, files: List[Dict[str, Any]], dry_run: bool = False) -> CleanupResult:
        """Execute cleanup operations on files.
        
        Args:
            files: List of file info dictionaries to process
            dry_run: If True, simulate but don't actually perform operations
            
        Returns:
            CleanupResult with statistics and outcomes
        """
        self.logger.info(f"Executing cleanup on {len(files)} files, dry_run={dry_run}")
        result = CleanupResult()
        
        for file_info in files:
            file_path = file_info['path']
            file_size = file_info['size']
            category = file_info.get('category', 'unknown')
            
            try:
                if self._should_compress(file_info) and self.config.get('compress_renders', False):
                    if not dry_run:
                        # In a real implementation, this would compress the file
                        self.logger.debug(f"Would compress file: {file_path}")
                    result.compressed_files += 1
                    
                if self._should_archive(file_info) and self.config.get('archive_to_cold_storage', False):
                    if not dry_run:
                        # In a real implementation, this would archive to cold storage
                        self.logger.debug(f"Would archive file: {file_path}")
                    result.files_archived += 1
                    
                # Delete the file
                if not dry_run:
                    os.remove(file_path)
                    self.logger.debug(f"Deleted file: {file_path}")
                    
                result.files_removed += 1
                result.bytes_saved += file_size
                
                # Track details
                if category not in result.details:
                    result.details[category] = {
                        "count": 0,
                        "bytes": 0,
                        "files": []
                    }
                
                result.details[category]["count"] += 1
                result.details[category]["bytes"] += file_size
                if len(result.details[category]["files"]) < 10:  # Limit file list
                    result.details[category]["files"].append(file_path)
                    
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                if not result.error_message:
                    result.error_message = f"Error processing {file_path}: {e}"
                result.success = False
        
        self.logger.info(f"Cleanup execution completed: {result.summary}")
        return result
    
    def _should_compress(self, file_info: Dict[str, Any]) -> bool:
        """Determine if a file should be compressed."""
        # Example logic - could be more sophisticated
        extension = file_info['extension']
        # Don't compress already compressed formats
        return extension not in [".zip", ".gz", ".rar", ".7z", ".mp4", ".jpg", ".jpeg", ".png"]
    
    def _should_archive(self, file_info: Dict[str, Any]) -> bool:
        """Determine if a file should be archived to cold storage."""
        # Example logic - in reality would be more sophisticated
        category = file_info.get('category', 'unknown')
        return category == "backups"
