"""File scanner module for identifying files to clean up."""

import os
import fnmatch
import logging
from pathlib import Path
from typing import List, Dict, Any

class FileScanner:
    """Scans directories for files matching cleanup patterns."""
    
    def __init__(self, patterns: List[str]):
        """Initialize the scanner with patterns to match.
        
        Args:
            patterns: List of glob patterns to match files for cleanup
        """
        self.patterns = patterns or ["*.tmp", "*.temp", "*_scratch.*"]
        self.logger = logging.getLogger("postrendercleaner.scanner")
        
    def scan_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Scan a directory for files matching cleanup patterns.
        
        Args:
            directory: Path to directory to scan
            
        Returns:
            List of dictionaries containing file info
        """
        self.logger.info(f"Scanning directory: {directory}")
        matched_files = []
        
        try:
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                
                for filename in files:
                    file_path = root_path / filename
                    
                    # Check if file matches any pattern
                    if self._matches_pattern(file_path):
                        # Get file stats
                        stats = file_path.stat()
                        
                        file_info = {
                            "path": str(file_path),
                            "size": stats.st_size,
                            "modified_time": stats.st_mtime,
                            "creation_time": stats.st_ctime,
                            "extension": file_path.suffix.lower(),
                        }
                        
                        matched_files.append(file_info)
                        
            self.logger.info(f"Found {len(matched_files)} files matching cleanup patterns")
            return matched_files
            
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
            return []
    
    def _matches_pattern(self, file_path: Path) -> bool:
        """Check if file matches any cleanup pattern."""
        file_str = str(file_path)
        
        for pattern in self.patterns:
            # Handle directory patterns
            if '/' in pattern and fnmatch.fnmatch(file_str, pattern):
                return True
            
            # Handle filename-only patterns
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
                
        return False
