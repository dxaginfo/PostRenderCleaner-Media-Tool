"""Tests for the file scanner module."""

import os
import tempfile
import unittest
from pathlib import Path

from postrendercleaner.scanner.file_scanner import FileScanner

class TestFileScanner(unittest.TestCase):
    """Test cases for the FileScanner class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.patterns = ["*.tmp", "*.temp", "*_scratch.*"]
        self.scanner = FileScanner(self.patterns)
        
        # Create test files
        self.test_files = [
            "file1.txt",
            "file2.tmp",
            "file3.temp",
            "file4_scratch.txt",
            "file5.mp4"
        ]
        
        for filename in self.test_files:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write("test content")
    
    def tearDown(self):
        """Clean up test environment."""
        for filename in self.test_files:
            file_path = os.path.join(self.temp_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        os.rmdir(self.temp_dir)
    
    def test_scan_directory(self):
        """Test scanning a directory for cleanup candidates."""
        results = self.scanner.scan_directory(Path(self.temp_dir))
        
        # Should find 3 files matching patterns
        self.assertEqual(len(results), 3)
        
        # Check that the correct files were found
        found_files = [os.path.basename(f["path"]) for f in results]
        self.assertIn("file2.tmp", found_files)
        self.assertIn("file3.temp", found_files)
        self.assertIn("file4_scratch.txt", found_files)
        
        # Check that non-matching files were excluded
        self.assertNotIn("file1.txt", found_files)
        self.assertNotIn("file5.mp4", found_files)
    
    def test_matches_pattern(self):
        """Test pattern matching functionality."""
        file1 = Path(os.path.join(self.temp_dir, "file1.txt"))
        file2 = Path(os.path.join(self.temp_dir, "file2.tmp"))
        file3 = Path(os.path.join(self.temp_dir, "file3.temp"))
        file4 = Path(os.path.join(self.temp_dir, "file4_scratch.txt"))
        file5 = Path(os.path.join(self.temp_dir, "file5.mp4"))
        
        # Check pattern matching
        self.assertFalse(self.scanner._matches_pattern(file1))
        self.assertTrue(self.scanner._matches_pattern(file2))
        self.assertTrue(self.scanner._matches_pattern(file3))
        self.assertTrue(self.scanner._matches_pattern(file4))
        self.assertFalse(self.scanner._matches_pattern(file5))

if __name__ == "__main__":
    unittest.main()
