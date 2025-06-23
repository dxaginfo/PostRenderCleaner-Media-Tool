"""Pattern matching utilities for the PostRenderCleaner tool."""

import fnmatch
import re
from pathlib import Path
from typing import List, Pattern, Dict, Any, Optional

class PatternMatcher:
    """Matches files against patterns with advanced options."""
    
    def __init__(self, patterns: List[str]):
        """Initialize with patterns to match.
        
        Args:
            patterns: List of glob patterns to match
        """
        self.patterns = patterns
        self._compiled_patterns: Dict[str, Pattern] = {}
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Precompile glob patterns to regex for faster matching."""
        for pattern in self.patterns:
            regex_pattern = fnmatch.translate(pattern)
            self._compiled_patterns[pattern] = re.compile(regex_pattern)
    
    def matches(self, path: Path, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Check if the path matches any pattern.
        
        Args:
            path: File path to check
            metadata: Optional metadata for more complex matching
            
        Returns:
            True if the file matches any pattern
        """
        path_str = str(path)
        
        # First check compiled patterns for performance
        for pattern, regex in self._compiled_patterns.items():
            if regex.match(path_str) or regex.match(path.name):
                return True
        
        # Fall back to direct glob matching for complex cases
        for pattern in self.patterns:
            if '/' in pattern and fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern):
                return True
                
        # Advanced metadata matching if provided
        if metadata:
            # Example: match by file size, type, etc.
            # This could be expanded based on requirements
            pass
                
        return False
