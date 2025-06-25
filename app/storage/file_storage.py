import os
import logging
import tempfile
import shutil
from typing import Optional
from urllib.parse import urlparse
import requests
from google.cloud import storage

class FileStorage:
    """Handles file storage and retrieval operations."""
    
    def __init__(self, use_gcs: bool = True):
        self.logger = logging.getLogger("file_storage")
        self.use_gcs = use_gcs
        
        # Initialize GCS if used
        if self.use_gcs:
            try:
                self.gcs_client = storage.Client()
                self.logger.info("Connected to Google Cloud Storage")
            except Exception as e:
                self.logger.error(f"Failed to connect to Google Cloud Storage: {str(e)}")
                self.use_gcs = False
    
    def get_local_path(self, file_uri: str) -> str:
        """Convert a file URI to a local path, downloading if necessary."""
        parsed_uri = urlparse(file_uri)
        
        # Check if it's already a local file
        if not parsed_uri.scheme or parsed_uri.scheme == "file":
            return parsed_uri.path
        
        # Handle GCS URIs
        if parsed_uri.scheme == "gs" and self.use_gcs:
            return self._download_from_gcs(parsed_uri.netloc, parsed_uri.path.lstrip('/'))
        
        # Handle HTTP/HTTPS URIs
        if parsed_uri.scheme in ["http", "https"]:
            return self._download_from_url(file_uri)
        
        raise ValueError(f"Unsupported URI scheme: {parsed_uri.scheme}")
    
    def store_file(self, local_path: str, output_location: str) -> str:
        """Store a local file to the specified location and return the URI."""
        parsed_uri = urlparse(output_location)
        
        # Handle different destination types
        if not parsed_uri.scheme or parsed_uri.scheme == "file":
            return self._store_to_local(local_path, parsed_uri.path)
        
        if parsed_uri.scheme == "gs" and self.use_gcs:
            return self._store_to_gcs(local_path, parsed_uri.netloc, parsed_uri.path.lstrip('/'))
        
        raise ValueError(f"Unsupported output location scheme: {parsed_uri.scheme}")
    
    def _download_from_gcs(self, bucket_name: str, blob_path: str) -> str:
        """Download a file from Google Cloud Storage to a local temp file."""
        try:
            # Create temp file with same extension
            _, ext = os.path.splitext(blob_path)
            temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            temp_file.close()
            
            # Download from GCS
            bucket = self.gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.download_to_filename(temp_file.name)
            
            self.logger.info(f"Downloaded GCS file gs://{bucket_name}/{blob_path} to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"Error downloading from GCS: {str(e)}")
            raise
    
    def _download_from_url(self, url: str) -> str:
        """Download a file from a URL to a local temp file."""
        try:
            # Create temp file with same extension
            parsed_url = urlparse(url)
            path = parsed_url.path
            _, ext = os.path.splitext(path)
            temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            temp_file.close()
            
            # Download from URL
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded URL {url} to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"Error downloading from URL: {str(e)}")
            raise
    
    def _store_to_local(self, local_path: str, output_path: str) -> str:
        """Store a file to a local destination."""
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Copy the file
            shutil.copy2(local_path, output_path)
            
            self.logger.info(f"Copied {local_path} to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error storing to local path: {str(e)}")
            raise
    
    def _store_to_gcs(self, local_path: str, bucket_name: str, blob_path: str) -> str:
        """Store a file to Google Cloud Storage."""
        try:
            # Upload to GCS
            bucket = self.gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            
            gcs_uri = f"gs://{bucket_name}/{blob_path}"
            self.logger.info(f"Uploaded {local_path} to {gcs_uri}")
            return gcs_uri
            
        except Exception as e:
            self.logger.error(f"Error uploading to GCS: {str(e)}")
            raise
