"""Core manager class for the PostRenderCleaner tool."""

from pathlib import Path
import logging
import yaml
from typing import Optional, List, Dict, Any, Union

from postrendercleaner.scanner.file_scanner import FileScanner
from postrendercleaner.policy.retention_rules import RetentionPolicy
from postrendercleaner.executor.cleanup_operations import CleanupExecutor
from postrendercleaner.reporting.log_manager import LogManager
from postrendercleaner.cleanup_result import CleanupResult

class CleanupManager:
    """Main class for managing cleanup operations."""
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 project_id: Optional[str] = None):
        """Initialize the cleanup manager.
        
        Args:
            config_path: Path to the configuration file
            project_id: Project identifier for project-specific configs
        """
        self.logger = logging.getLogger("postrendercleaner")
        self.config = self._load_config(config_path)
        self.project_id = project_id
        
        # Initialize components
        self.scanner = FileScanner(self.config.get("cleanup", {}).get("temp_patterns", []))
        self.policy = RetentionPolicy(self.config.get("cleanup", {}).get("retention", {}))
        self.executor = CleanupExecutor(self.config.get("cleanup", {}).get("actions", {}))
        self.log_manager = LogManager()
        
        self.logger.info(f"CleanupManager initialized with project_id={project_id}")
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
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
        
        if not config_path:
            self.logger.warning("No config path provided, using default configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            self.logger.warning("Using default configuration")
            return default_config
    
    def run(self, path: Union[str, List[str]], dry_run: bool = False) -> CleanupResult:
        """Run cleanup operation on the specified path(s).
        
        Args:
            path: Directory path or list of paths to clean
            dry_run: If True, only simulate operations without actual deletion
            
        Returns:
            CleanupResult object with details of the operation
        """
        paths = [path] if isinstance(path, str) else path
        self.logger.info(f"Starting cleanup operation on {len(paths)} path(s), dry_run={dry_run}")
        
        # Initialize result tracking
        result = CleanupResult()
        
        for single_path in paths:
            path_obj = Path(single_path)
            if not path_obj.exists():
                self.logger.warning(f"Path does not exist: {single_path}")
                continue
                
            # Scan for files
            files_to_clean = self.scanner.scan_directory(path_obj)
            self.logger.info(f"Found {len(files_to_clean)} files matching cleanup patterns")
            
            # Apply retention policy
            filtered_files = self.policy.apply_policy(files_to_clean)
            self.logger.info(f"After applying retention policy, {len(filtered_files)} files will be processed")
            
            # Execute cleanup operations
            execution_result = self.executor.execute(
                filtered_files, 
                dry_run=dry_run
            )
            
            # Update result
            result.merge(execution_result)
            
        # Generate report
        self.log_manager.log_summary(result)
        
        return result
    
    def run_on_gcs(self, bucket_name: str, object_path: str, dry_run: bool = False) -> CleanupResult:
        """Run cleanup operation on Google Cloud Storage.
        
        Args:
            bucket_name: GCS bucket name
            object_path: Path within the bucket
            dry_run: If True, only simulate operations without actual deletion
            
        Returns:
            CleanupResult object with details of the operation
        """
        self.logger.info(f"Starting GCS cleanup operation on gs://{bucket_name}/{object_path}")
        
        # TODO: Implement GCS-specific cleanup logic
        # This would interact with Google Cloud Storage API to clean up files
        
        # Placeholder for actual implementation
        result = CleanupResult()
        result.bytes_saved = 0
        result.files_removed = 0
        result.files_archived = 0
        
        self.logger.info("GCS cleanup operation not fully implemented yet")
        
        return result
