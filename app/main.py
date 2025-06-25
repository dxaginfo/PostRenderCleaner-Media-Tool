from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import os
import logging
from datetime import datetime

from .core.engine import ProcessingEngine
from .core.config import ConfigManager
from .storage.file_storage import FileStorage
from .storage.job_tracker import JobTracker

app = FastAPI(
    title="PostRenderCleaner API",
    description="API for media post-processing and cleanup operations",
    version="1.0.0"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize components
config_manager = ConfigManager()
file_storage = FileStorage()
job_tracker = JobTracker()
processing_engine = ProcessingEngine()

# Models
class ProcessRequest(BaseModel):
    input_file: str
    output_location: str
    operations: List[str]
    preset: Optional[str] = "standard"
    parameters: Optional[Dict[str, Any]] = None

class PresetCreate(BaseModel):
    name: str
    denoise_strength: Optional[float] = 0.5
    stabilize_strength: Optional[float] = 0.5
    color_correction: Optional[Dict[str, Any]] = None
    artifact_removal: Optional[List[str]] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    updated_at: str
    progress: Optional[float] = None
    output_file: Optional[str] = None
    error: Optional[str] = None

# Helper functions
def validate_token(token: str = Depends(oauth2_scheme)):
    # In production, implement proper OAuth2 validation
    if token != "valid_token":  # Simplified for example
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return token

def process_job(job_id: str, request: ProcessRequest):
    try:
        # Update job status to processing
        job_tracker.update_job(job_id, {"status": "processing", "progress": 0.0})
        
        # Download file if it's a cloud URI
        local_input_path = file_storage.get_local_path(request.input_file)
        
        # Process the file
        result = processing_engine.process(
            input_file=local_input_path,
            operations=request.operations,
            preset=request.preset,
            parameters=request.parameters
        )
        
        # Upload result to output location
        output_uri = file_storage.store_file(result.output_path, request.output_location)
        
        # Update job with completion info
        job_tracker.update_job(job_id, {
            "status": "completed", 
            "progress": 1.0,
            "output_file": output_uri
        })
        
    except Exception as e:
        logging.error(f"Error processing job {job_id}: {str(e)}")
        job_tracker.update_job(job_id, {"status": "failed", "error": str(e)})

# API Endpoints
@app.post("/v1/process", response_model=JobResponse)
async def create_processing_job(
    request: ProcessRequest, 
    background_tasks: BackgroundTasks,
    token: str = Depends(validate_token)
):
    # Create a new job
    job_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "input_file": request.input_file,
        "output_location": request.output_location,
        "operations": request.operations,
        "preset": request.preset
    }
    
    job_tracker.create_job(job_id, job_data)
    
    # Start processing in background
    background_tasks.add_task(process_job, job_id, request)
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        created_at=now,
        updated_at=now
    )

@app.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, token: str = Depends(validate_token)):
    job = job_tracker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobResponse(
        job_id=job["job_id"],
        status=job["status"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        progress=job.get("progress"),
        output_file=job.get("output_file"),
        error=job.get("error")
    )

@app.delete("/v1/jobs/{job_id}")
async def cancel_job(job_id: str, token: str = Depends(validate_token)):
    job = job_tracker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status {job['status']}")
    
    job_tracker.update_job(job_id, {"status": "cancelled"})
    return {"message": f"Job {job_id} cancelled"}

@app.get("/v1/presets")
async def list_presets(token: str = Depends(validate_token)):
    presets = config_manager.get_presets()
    return {"presets": presets}

@app.post("/v1/presets")
async def create_preset(preset: PresetCreate, token: str = Depends(validate_token)):
    preset_id = config_manager.create_preset(preset.dict())
    return {"preset_id": preset_id, "name": preset.name}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
