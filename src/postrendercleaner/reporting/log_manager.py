"""Log management for the PostRenderCleaner tool."""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from postrendercleaner.cleanup_result import CleanupResult

class LogManager:
    """Manages logging and reporting for cleanup operations."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize the log manager.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = log_dir
        self.logger = logging.getLogger("postrendercleaner.reporting")
        
        if self.log_dir and not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
                self.logger.info(f"Created log directory: {self.log_dir}")
            except Exception as e:
                self.logger.error(f"Failed to create log directory: {e}")
    
    def log_summary(self, result: CleanupResult) -> Optional[str]:
        """Log a summary of cleanup operations.
        
        Args:
            result: CleanupResult object
            
        Returns:
            Path to log file if created, otherwise None
        """
        if not self.log_dir:
            self.logger.info(f"Log summary: {result.summary}")
            return None
            
        # Ensure end_time is set
        if not result.end_time:
            result.end_time = datetime.now()
            
        # Create log filename with timestamp
        timestamp = result.end_time.strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"cleanup_{timestamp}.json")
        
        try:
            report = result.get_report()
            
            # Add human-readable timestamps
            report["start_time_str"] = result.start_time.isoformat()
            report["end_time_str"] = result.end_time.isoformat()
            
            with open(log_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Wrote log summary to {log_file}")
            return log_file
            
        except Exception as e:
            self.logger.error(f"Failed to write log summary: {e}")
            return None
    
    def generate_report(self, result: CleanupResult, report_format: str = "json") -> Optional[str]:
        """Generate a detailed report of cleanup operations.
        
        Args:
            result: CleanupResult object
            report_format: Format of the report (json, html, csv)
            
        Returns:
            Path to report file if created, otherwise None
        """
        if not self.log_dir:
            self.logger.warning("No log directory configured, skipping report generation")
            return None
            
        # Ensure end_time is set
        if not result.end_time:
            result.end_time = datetime.now()
            
        # Create report filename with timestamp
        timestamp = result.end_time.strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.log_dir, f"cleanup_report_{timestamp}.{report_format}")
        
        try:
            report_data = result.get_report()
            
            if report_format == "json":
                with open(report_file, 'w') as f:
                    json.dump(report_data, f, indent=2)
            elif report_format == "csv":
                # Would implement CSV export here
                pass
            elif report_format == "html":
                # Would implement HTML report generation here
                pass
            else:
                self.logger.warning(f"Unsupported report format: {report_format}")
                return None
                
            self.logger.info(f"Generated {report_format} report at {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return None
