"""
Core implementation of the PostRenderCleaner tool.
"""

import logging
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .config import ConfigManager
from .scanner import FileScanner
from .policy import RetentionPolicy
from .executor import CleanupExecutor
from .reporting import ReportManager

logger = logging.getLogger(__name__)

@dataclass
class CleanupReport:
    """Report on cleanup results."""
    bytes_saved: int = 0
    files_removed: int = 0
    files_archived: int = 0
    files_compressed: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def summary(self) -> str:
        """Get a summary of the cleanup results."""
        mb_saved = self.bytes_saved / (1024 * 1024)
        return (
            f"Saved {mb_saved:.2f} MB by removing {self.files_removed} files, "
            f"archiving {self.files_archived} files, and compressing {self.files_compressed} files. "
            f"Errors: {len(self.errors)}"
        )

class CleanupResult:
    """Result of a cleanup operation."""
    
    def __init__(self, success: bool = True, path: str = None):
        self.success = success
        self.path = path
        self.report = CleanupReport()
        self.start_time = time.time()
        self.end_time = None
        
    def finalize(self) -> None:
        """Mark the cleanup operation as complete."""
        self.end_time = time.time()
        
    @property
    def duration(self) -> float:
        """Get the duration of the cleanup operation in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def get_report(self) -> CleanupReport:
        """Get the cleanup report."""
        return self.report

class CleanupManager:
    """Main class for managing the cleanup process."""
    
    def __init__(
        self, 
        config_path: Optional[str] = None,
        dry_run: bool = False,
        project_id: Optional[str] = None
    ):
        """Initialize the cleanup manager.
        
        Args:
            config_path: Path to configuration file. Uses default if None.
            dry_run: If True, simulate cleanup without making changes.
            project_id: Optional project ID for project-specific configuration.
        """
        self.config_manager = ConfigManager(config_path)
        self.dry_run = dry_run
        self.project_id = project_id
        
        # Initialize components
        self.scanner = FileScanner(self.config_manager)
        self.policy = RetentionPolicy(self.config_manager)
        self.executor = CleanupExecutor(self.config_manager, dry_run=dry_run)
        self.report_manager = ReportManager(self.config_manager)
        
        logger.info("CleanupManager initialized")
        if dry_run:
            logger.info("Running in DRY RUN mode - no files will be modified")
    
    def run(self, path: str) -> CleanupResult:
        """Run cleanup on the specified path.
        
        Args:
            path: Directory path to clean up.
            
        Returns:
            CleanupResult object with details of the operation.
        """
        logger.info(f"Starting cleanup of {path}")
        result = CleanupResult(path=path)
        
        try:
            # Scan for files that match cleanup patterns
            scan_results = self.scanner.scan(path)
            logger.info(f"Found {len(scan_results)} files matching cleanup patterns")
            
            # Apply retention policies
            files_to_delete, files_to_archive, files_to_compress = self.policy.apply(scan_results)
            
            logger.info(f"After policy application: {len(files_to_delete)} to delete, "
                      f"{len(files_to_archive)} to archive, {len(files_to_compress)} to compress")
            
            # Execute the cleanup operations
            delete_results = self.executor.delete_files(files_to_delete)
            archive_results = self.executor.archive_files(files_to_archive)
            compress_results = self.executor.compress_files(files_to_compress)
            
            # Update the report
            result.report.bytes_saved = delete_results['bytes_saved'] + compress_results['bytes_saved']
            result.report.files_removed = delete_results['count']
            result.report.files_archived = archive_results['count']
            result.report.files_compressed = compress_results['count']
            result.report.errors = delete_results['errors'] + archive_results['errors'] + compress_results['errors']
            
            # Generate report
            self.report_manager.generate_report(result, path)
            
            # Send notifications if configured
            if self.config_manager.get_notification_config('email_on_completion'):
                self._send_email_notification(result)
                
            if result.report.errors and self.config_manager.get_notification_config('slack_on_error'):
                self._send_slack_notification(result)
            
            result.success = True
            
        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")
            result.success = False
            if not result.report.errors:
                result.report.errors = []
            result.report.errors.append(str(e))
        
        finally:
            result.finalize()
            logger.info(f"Cleanup completed in {result.duration:.2f} seconds")
            logger.info(f"Summary: {result.report.summary}")
        
        return result
    
    def run_on_gcs(self, bucket_name: str, path: str) -> CleanupResult:
        """Run cleanup on Google Cloud Storage.
        
        Args:
            bucket_name: Name of the GCS bucket.
            path: Path within the bucket.
            
        Returns:
            CleanupResult object with details of the operation.
        """
        logger.info(f"Starting GCS cleanup of gs://{bucket_name}/{path}")
        # Implementation would use Google Cloud Storage API
        # This is a placeholder for the actual implementation
        result = CleanupResult(path=f"gs://{bucket_name}/{path}")
        
        # For now, just return a dummy result
        result.report.bytes_saved = 0
        result.report.files_removed = 0
        result.report.files_archived = 0
        result.success = True
        result.finalize()
        
        return result
    
    def _send_email_notification(self, result: CleanupResult) -> None:
        """Send email notification about the cleanup results."""
        logger.info("Sending email notification")
        # Implementation would use email service
        # This is a placeholder for the actual implementation
        
    def _send_slack_notification(self, result: CleanupResult) -> None:
        """Send Slack notification about the cleanup results."""
        logger.info("Sending Slack notification")
        # Implementation would use Slack API
        # This is a placeholder for the actual implementation