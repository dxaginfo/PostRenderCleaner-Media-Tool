import os
import logging
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime
from google.cloud import firestore

class JobTracker:
    """Tracks processing jobs and their status."""
    
    def __init__(self, use_firestore: bool = True):
        self.logger = logging.getLogger("job_tracker")
        self.use_firestore = use_firestore
        
        # Initialize Firestore if used
        if self.use_firestore:
            try:
                self.db = firestore.Client()
                self.jobs_collection = self.db.collection("postrendercleaner_jobs")
                self.logger.info("Connected to Firestore for job tracking")
            except Exception as e:
                self.logger.error(f"Failed to connect to Firestore: {str(e)}")
                self.use_firestore = False
        
        # Use in-memory storage if not using Firestore
        if not self.use_firestore:
            self.jobs = {}
    
    def create_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Create a new job record."""
        if self.use_firestore:
            try:
                self.jobs_collection.document(job_id).set(job_data)
                self.logger.info(f"Created job {job_id} in Firestore")
            except Exception as e:
                self.logger.error(f"Error creating job in Firestore: {str(e)}")
                # Fall back to in-memory storage
                self.jobs[job_id] = job_data
        else:
            # Store in memory
            self.jobs[job_id] = job_data
            self.logger.info(f"Created job {job_id} in memory")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID."""
        if self.use_firestore:
            try:
                doc = self.jobs_collection.document(job_id).get()
                if doc.exists:
                    return doc.to_dict()
                return None
            except Exception as e:
                self.logger.error(f"Error getting job from Firestore: {str(e)}")
                # Fall back to in-memory storage
                return self.jobs.get(job_id)
        else:
            # Get from memory
            return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, update_data: Dict[str, Any]) -> None:
        """Update job details."""
        # Add updated timestamp
        update_data["updated_at"] = datetime.now().isoformat()
        
        if self.use_firestore:
            try:
                self.jobs_collection.document(job_id).update(update_data)
                self.logger.info(f"Updated job {job_id} in Firestore")
            except Exception as e:
                self.logger.error(f"Error updating job in Firestore: {str(e)}")
                # Fall back to in-memory storage
                if job_id in self.jobs:
                    self.jobs[job_id].update(update_data)
        else:
            # Update in memory
            if job_id in self.jobs:
                self.jobs[job_id].update(update_data)
                self.logger.info(f"Updated job {job_id} in memory")
            else:
                self.logger.warning(f"Job {job_id} not found for update")
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs, optionally filtered by status."""
        if self.use_firestore:
            try:
                query = self.jobs_collection.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
                
                if status:
                    query = query.where("status", "==", status)
                
                jobs = [doc.to_dict() for doc in query.stream()]
                return jobs
            except Exception as e:
                self.logger.error(f"Error listing jobs from Firestore: {str(e)}")
                # Fall back to in-memory storage
                return self._list_from_memory(status, limit)
        else:
            # List from memory
            return self._list_from_memory(status, limit)
    
    def _list_from_memory(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs from in-memory storage."""
        filtered_jobs = []
        
        for job_id, job_data in self.jobs.items():
            if status is None or job_data.get("status") == status:
                filtered_jobs.append(job_data)
        
        # Sort by created_at (descending)
        filtered_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply limit
        return filtered_jobs[:limit]
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up jobs older than specified days."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        count = 0
        
        if self.use_firestore:
            try:
                # Convert cutoff time to ISO format for comparison
                cutoff_date = datetime.fromtimestamp(cutoff_time).isoformat()
                
                # Query for old jobs
                old_jobs = self.jobs_collection.where("created_at", "<", cutoff_date).stream()
                
                # Delete old jobs
                for doc in old_jobs:
                    doc.reference.delete()
                    count += 1
                
                self.logger.info(f"Cleaned up {count} old jobs from Firestore")
                return count
            except Exception as e:
                self.logger.error(f"Error cleaning up old jobs from Firestore: {str(e)}")
                # Fall back to in-memory cleanup
                return self._cleanup_from_memory(cutoff_time)
        else:
            # Cleanup from memory
            return self._cleanup_from_memory(cutoff_time)
    
    def _cleanup_from_memory(self, cutoff_time: float) -> int:
        """Clean up old jobs from in-memory storage."""
        jobs_to_remove = []
        count = 0
        
        for job_id, job_data in self.jobs.items():
            created_at = job_data.get("created_at", "")
            try:
                # Parse ISO format created_at
                job_time = datetime.fromisoformat(created_at).timestamp()
                if job_time < cutoff_time:
                    jobs_to_remove.append(job_id)
            except (ValueError, TypeError):
                # Skip jobs with invalid created_at
                pass
        
        # Remove the old jobs
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            count += 1
        
        self.logger.info(f"Cleaned up {count} old jobs from memory")
        return count
