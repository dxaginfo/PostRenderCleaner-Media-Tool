"""Tests for the cleanup executor module."""

import os
import tempfile
import unittest
from typing import Dict, Any, List

from postrendercleaner.executor.cleanup_operations import CleanupExecutor
from postrendercleaner.cleanup_result import CleanupResult

class TestCleanupExecutor(unittest.TestCase):
    """Test cases for the CleanupExecutor class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "compress_renders": True,
            "archive_to_cold_storage": True,
            "generate_report": True,
        }
        self.executor = CleanupExecutor(self.config)
        
        # Create test files
        self.test_files = [
            "file1.txt",
            "file2.tmp",
            "render1.exr",
            "archive1.zip"
        ]
        
        for filename in self.test_files:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write("test content")
                
        # Prepare file info records
        self.file_infos = self._create_file_infos()
    
    def tearDown(self):
        """Clean up test environment."""
        for filename in self.test_files:
            file_path = os.path.join(self.temp_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        os.rmdir(self.temp_dir)
    
    def _create_file_infos(self) -> List[Dict[str, Any]]:
        """Create test file info records."""
        files = []
        for filename in self.test_files:
            file_path = os.path.join(self.temp_dir, filename)
            file_size = os.path.getsize(file_path)
            extension = os.path.splitext(filename)[1].lower()
            
            category = "intermediates"
            if extension == ".log" or extension == ".txt":
                category = "logs"
            elif extension == ".zip" or "archive" in filename:
                category = "backups"
            
            file_info = {
                "path": file_path,
                "size": file_size,
                "extension": extension,
                "category": category,
                "modified_time": os.path.getmtime(file_path)
            }
            
            files.append(file_info)
            
        return files
    
    def test_execute_dry_run(self):
        """Test executing cleanup in dry run mode."""
        result = self.executor.execute(self.file_infos, dry_run=True)
        
        # In dry run, no files should be removed
        for filename in self.test_files:
            file_path = os.path.join(self.temp_dir, filename)
            self.assertTrue(os.path.exists(file_path))
        
        # Check result object
        self.assertIsInstance(result, CleanupResult)
        self.assertEqual(result.files_removed, len(self.file_infos))
        self.assertTrue(result.success)
    
    def test_should_compress(self):
        """Test compression decision logic."""
        # Text files should be compressed
        text_file = {"extension": ".txt"}
        self.assertTrue(self.executor._should_compress(text_file))
        
        # Already compressed files should not be compressed
        zip_file = {"extension": ".zip"}
        self.assertFalse(self.executor._should_compress(zip_file))
        
        mp4_file = {"extension": ".mp4"}
        self.assertFalse(self.executor._should_compress(mp4_file))
        
        jpg_file = {"extension": ".jpg"}
        self.assertFalse(self.executor._should_compress(jpg_file))
    
    def test_should_archive(self):
        """Test archiving decision logic."""
        # Backups should be archived
        backup_file = {"category": "backups"}
        self.assertTrue(self.executor._should_archive(backup_file))
        
        # Other categories should not be archived
        log_file = {"category": "logs"}
        self.assertFalse(self.executor._should_archive(log_file))
        
        temp_file = {"category": "intermediates"}
        self.assertFalse(self.executor._should_archive(temp_file))

if __name__ == "__main__":
    unittest.main()
