"""Result class for the PostRenderCleaner tool."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class CleanupResult:
    """Contains results and statistics from a cleanup operation."""
    
    # Core metrics
    bytes_saved: int = 0
    files_removed: int = 0
    files_archived: int = 0
    compressed_files: int = 0
    
    # Operation details
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: bool = True
    error_message: Optional[str] = None
    
    # Additional info
    details: Dict[str, Any] = field(default_factory=dict)
    
    def get_duration(self):
        """Calculate duration of the cleanup operation."""
        if not self.end_time:
            self.end_time = datetime.now()
        return (self.end_time - self.start_time).total_seconds()
    
    def get_report(self) -> Dict[str, Any]:
        """Generate a summary report of the cleanup operation."""
        if not self.end_time:
            self.end_time = datetime.now()
            
        return {
            "bytes_saved": self.bytes_saved,
            "files_removed": self.files_removed,
            "files_archived": self.files_archived,
            "compressed_files": self.compressed_files,
            "duration_seconds": self.get_duration(),
            "success": self.success,
            "error_message": self.error_message,
            "details": self.details,
        }
    
    def merge(self, other):
        """Merge another result into this one."""
        self.bytes_saved += other.bytes_saved
        self.files_removed += other.files_removed
        self.files_archived += other.files_archived
        self.compressed_files += other.compressed_files
        
        # If any operation failed, mark the whole result as failed
        if not other.success:
            self.success = False
            if other.error_message:
                if self.error_message:
                    self.error_message += f"; {other.error_message}"
                else:
                    self.error_message = other.error_message
        
        # Merge details
        for key, value in other.details.items():
            if key in self.details and isinstance(self.details[key], list) and isinstance(value, list):
                self.details[key].extend(value)
            else:
                self.details[key] = value
    
    @property
    def summary(self) -> str:
        """Get a human-readable summary of the results."""
        return (
            f"Cleaned up {self.bytes_saved} bytes ({self.bytes_saved / (1024*1024):.2f} MB), "
            f"removed {self.files_removed} files, "
            f"archived {self.files_archived} files, "
            f"compressed {self.compressed_files} files in {self.get_duration():.2f} seconds."
        )
