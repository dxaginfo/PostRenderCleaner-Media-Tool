"""Archive manager for the PostRenderCleaner tool."""

import os
import shutil
import logging
import zipfile
from typing import List, Dict, Any, Optional
from pathlib import Path

class ArchiveManager:
    """Manages archiving of files to cold storage."""
    
    def __init__(self, archive_dir: Optional[str] = None):
        """Initialize the archive manager.
        
        Args:
            archive_dir: Directory for local archives
        """
        self.archive_dir = archive_dir
        self.logger = logging.getLogger("postrendercleaner.archive")
        
        if self.archive_dir and not os.path.exists(self.archive_dir):
            try:
                os.makedirs(self.archive_dir)
                self.logger.info(f"Created archive directory: {self.archive_dir}")
            except Exception as e:
                self.logger.error(f"Failed to create archive directory: {e}")
    
    def archive_files(self, files: List[Dict[str, Any]], project_id: str) -> Dict[str, Any]:
        """Archive files to cold storage.
        
        Args:
            files: List of file info dictionaries
            project_id: Project identifier for organizing archives
            
        Returns:
            Dictionary with archive results
        """
        if not self.archive_dir:
            self.logger.warning("No archive directory configured, skipping archiving")
            return {"archived": 0, "failed": 0, "bytes_archived": 0}
            
        result = {"archived": 0, "failed": 0, "bytes_archived": 0, "archive_path": None}
        
        if not files:
            return result
            
        # Create timestamped archive name
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{project_id}_{timestamp}.zip"
        archive_path = os.path.join(self.archive_dir, archive_name)
        
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files:
                    file_path = file_info['path']
                    try:
                        # Get relative path for archive structure
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname=arcname)
                        
                        result["archived"] += 1
                        result["bytes_archived"] += file_info['size']
                        self.logger.debug(f"Archived file to {archive_name}: {file_path}")
                        
                    except Exception as e:
                        result["failed"] += 1
                        self.logger.error(f"Failed to archive file {file_path}: {e}")
                        
            result["archive_path"] = archive_path
            self.logger.info(f"Created archive {archive_path} with {result['archived']} files")
            
            # For a real implementation, would also upload to cloud cold storage
            # self._upload_to_cold_storage(archive_path, project_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create archive {archive_path}: {e}")
            result["error"] = str(e)
            return result
    
    def _upload_to_cold_storage(self, archive_path: str, project_id: str) -> bool:
        """Upload archive to cloud cold storage."""
        # Placeholder for actual implementation
        self.logger.info(f"Would upload {archive_path} to cold storage for project {project_id}")
        return True
