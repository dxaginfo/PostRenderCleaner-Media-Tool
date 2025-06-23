"""Tests for the integration modules."""

import unittest
from unittest.mock import patch, MagicMock

from postrendercleaner.integration.drive_connector import DriveConnector
from postrendercleaner.integration.renderfarm_monitor import RenderFarmMonitor, RenderJob

class TestDriveConnector(unittest.TestCase):
    """Test cases for the DriveConnector class."""
    
    def setUp(self):
        """Set up test environment."""
        self.connector = DriveConnector(credentials_path="fake_credentials.json")
    
    def test_initialization(self):
        """Test connector initialization."""
        # Without actual Google API, this just tests the internal logic
        result = self.connector.initialize()
        self.assertTrue(result)
    
    @patch('postrendercleaner.integration.drive_connector.DriveConnector.initialize')
    def test_upload_to_drive(self, mock_initialize):
        """Test file upload functionality."""
        mock_initialize.return_value = True
        
        # This tests the internal logic without actual Google API calls
        file_id = self.connector.upload_to_drive("fake_file.txt")
        self.assertIsNotNone(file_id)
        
        # Test with folder ID
        file_id = self.connector.upload_to_drive("fake_file.txt", folder_id="fake_folder_id")
        self.assertIsNotNone(file_id)
    
    @patch('postrendercleaner.integration.drive_connector.DriveConnector.initialize')
    def test_create_folder(self, mock_initialize):
        """Test folder creation functionality."""
        mock_initialize.return_value = True
        
        # This tests the internal logic without actual Google API calls
        folder_id = self.connector.create_folder("Test Folder")
        self.assertIsNotNone(folder_id)
        
        # Test with parent folder
        folder_id = self.connector.create_folder("Test Subfolder", parent_id="fake_parent_id")
        self.assertIsNotNone(folder_id)

class TestRenderFarmMonitor(unittest.TestCase):
    """Test cases for the RenderFarmMonitor class."""
    
    def setUp(self):
        """Set up test environment."""
        self.monitor = RenderFarmMonitor(
            api_url="https://fake-renderfarm.example.com/api",
            api_key="fake_api_key"
        )
    
    def test_get_completed_jobs(self):
        """Test retrieving completed render jobs."""
        # This tests the internal logic with simulated data
        jobs = self.monitor.get_completed_jobs()
        
        # Should return simulated jobs
        self.assertGreater(len(jobs), 0)
        self.assertIsInstance(jobs[0], RenderJob)
        
        # Test filtering by project
        project_jobs = self.monitor.get_completed_jobs(project_id="project123")
        self.assertEqual(len(project_jobs), 1)
        self.assertEqual(project_jobs[0].project_id, "project123")
    
    def test_get_job_details(self):
        """Test retrieving detailed job information."""
        # Get details for a known job ID
        job = self.monitor.get_job_details("job1")
        self.assertIsNotNone(job)
        self.assertEqual(job.job_id, "job1")
        self.assertEqual(job.project_id, "project123")
        
        # Test with unknown job ID
        job = self.monitor.get_job_details("nonexistent_job")
        self.assertIsNone(job)
    
    def test_register_cleanup_callback(self):
        """Test callback registration."""
        result = self.monitor.register_cleanup_callback(
            "https://example.com/cleanup-webhook"
        )
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
