"""Tests for the retention policy module."""

import time
import unittest
from typing import Dict, Any, List

from postrendercleaner.policy.retention_rules import RetentionPolicy

class TestRetentionPolicy(unittest.TestCase):
    """Test cases for the RetentionPolicy class."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = {
            "logs": 30,  # days
            "intermediates": 7,  # days
            "backups": 90,  # days
        }
        self.policy = RetentionPolicy(self.config)
        
        # Current time
        self.current_time = time.time()
        
        # Test files
        self.files = self._create_test_files()
    
    def _create_test_files(self) -> List[Dict[str, Any]]:
        """Create test file data."""
        day_in_seconds = 86400
        files = [
            # Recent files (within retention period)
            {
                "path": "/test/logs/recent.log",
                "size": 1024,
                "modified_time": self.current_time - (15 * day_in_seconds),  # 15 days old
                "extension": ".log"
            },
            {
                "path": "/test/temp/recent_temp.tmp",
                "size": 2048,
                "modified_time": self.current_time - (3 * day_in_seconds),  # 3 days old
                "extension": ".tmp"
            },
            {
                "path": "/test/backup/recent_backup.bak",
                "size": 4096,
                "modified_time": self.current_time - (45 * day_in_seconds),  # 45 days old
                "extension": ".bak"
            },
            
            # Old files (beyond retention period)
            {
                "path": "/test/logs/old.log",
                "size": 1024,
                "modified_time": self.current_time - (45 * day_in_seconds),  # 45 days old
                "extension": ".log"
            },
            {
                "path": "/test/temp/old_temp.tmp",
                "size": 2048,
                "modified_time": self.current_time - (14 * day_in_seconds),  # 14 days old
                "extension": ".tmp"
            },
            {
                "path": "/test/backup/old_backup.bak",
                "size": 4096,
                "modified_time": self.current_time - (120 * day_in_seconds),  # 120 days old
                "extension": ".bak"
            },
        ]
        return files
    
    def test_apply_policy(self):
        """Test applying retention policy to files."""
        filtered_files = self.policy.apply_policy(self.files)
        
        # Should keep 3 files that are beyond retention period
        self.assertEqual(len(filtered_files), 3)
        
        # Check that the correct files were kept
        paths = [f["path"] for f in filtered_files]
        self.assertIn("/test/logs/old.log", paths)
        self.assertIn("/test/temp/old_temp.tmp", paths)
        self.assertIn("/test/backup/old_backup.bak", paths)
        
        # Check that files within retention period were excluded
        self.assertNotIn("/test/logs/recent.log", paths)
        self.assertNotIn("/test/temp/recent_temp.tmp", paths)
        self.assertNotIn("/test/backup/recent_backup.bak", paths)
    
    def test_categorize_file(self):
        """Test file categorization."""
        # Test log file
        log_file = {
            "path": "/test/logs/app.log",
            "extension": ".log"
        }
        self.assertEqual(self.policy._categorize_file(log_file), "logs")
        
        # Test temp file
        temp_file = {
            "path": "/test/render_scratch.tmp",
            "extension": ".tmp"
        }
        self.assertEqual(self.policy._categorize_file(temp_file), "intermediates")
        
        # Test backup file
        backup_file = {
            "path": "/test/backup/archive.zip",
            "extension": ".zip"
        }
        self.assertEqual(self.policy._categorize_file(backup_file), "backups")
        
        # Test default category
        unknown_file = {
            "path": "/test/unknown.dat",
            "extension": ".dat"
        }
        self.assertEqual(self.policy._categorize_file(unknown_file), "intermediates")

if __name__ == "__main__":
    unittest.main()
