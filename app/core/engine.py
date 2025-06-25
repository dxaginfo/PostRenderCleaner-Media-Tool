import os
import logging
import tempfile
import json
from typing import List, Dict, Any, Optional, NamedTuple
import cv2
import numpy as np
from PIL import Image
import ffmpeg
import time

from .operations.denoise import DenoiseOperation
from .operations.stabilize import StabilizeOperation
from .operations.color_correction import ColorCorrectionOperation
from .operations.artifact_removal import ArtifactRemovalOperation
from .operations.base import BaseOperation
from .gemini_client import GeminiClient

class ProcessingResult(NamedTuple):
    output_path: str
    metadata: Dict[str, Any]
    duration: float

class ProcessingEngine:
    def __init__(self):
        self.operations = {
            "denoise": DenoiseOperation(),
            "stabilize": StabilizeOperation(),
            "color_correct": ColorCorrectionOperation(),
            "artifact_removal": ArtifactRemovalOperation()
        }
        self.gemini_client = GeminiClient()
        self.logger = logging.getLogger("processing_engine")
    
    def process(
        self, 
        input_file: str, 
        operations: List[str],
        preset: str = "standard",
        parameters: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process a media file with the specified operations using the given preset.
        
        Args:
            input_file: Path to the input file
            operations: List of operations to apply
            preset: Preset name to use
            parameters: Additional parameters to override preset values
            
        Returns:
            ProcessingResult containing output path and metadata
        """
        start_time = time.time()
        self.logger.info(f"Processing {input_file} with operations: {operations} using preset: {preset}")
        
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            current_file = input_file
            
            # Get file info
            file_info = self._get_file_info(input_file)
            self.logger.info(f"File info: {file_info}")
            
            # Apply scene analysis with Gemini if needed
            if any(op in ["denoise", "color_correct"] for op in operations):
                scene_analysis = self._analyze_scene(input_file)
                self.logger.info(f"Scene analysis completed")
            else:
                scene_analysis = {}
            
            # Apply each operation in sequence
            operation_results = {}
            for op_name in operations:
                if op_name not in self.operations:
                    self.logger.warning(f"Unknown operation: {op_name}, skipping")
                    continue
                
                operation = self.operations[op_name]
                
                # Get operation parameters from preset and override with custom parameters
                op_params = self._get_operation_parameters(op_name, preset, parameters)
                
                # Apply the operation
                self.logger.info(f"Applying operation: {op_name}")
                intermediate_file = os.path.join(temp_dir, f"{op_name}_output{os.path.splitext(input_file)[1]}")
                result = operation.apply(current_file, intermediate_file, op_params, scene_analysis)
                
                # Update current file for next operation
                current_file = intermediate_file
                operation_results[op_name] = result
            
            # Create final output file
            output_file = os.path.join(temp_dir, f"final_output{os.path.splitext(input_file)[1]}")
            os.rename(current_file, output_file)
            
            # Generate processing report
            metadata = {
                "input_file": input_file,
                "operations": operation_results,
                "preset": preset,
                "file_info": file_info,
                "scene_analysis": scene_analysis
            }
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.info(f"Processing completed in {duration:.2f} seconds")
            
            # Return the final output file and metadata
            return ProcessingResult(
                output_path=output_file,
                metadata=metadata,
                duration=duration
            )
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about the media file."""
        try:
            probe = ffmpeg.probe(file_path)
            return {
                "format": probe["format"],
                "streams": probe["streams"],
                "duration": float(probe["format"].get("duration", 0)),
                "size": int(probe["format"].get("size", 0))
            }
        except Exception as e:
            self.logger.error(f"Error probing file {file_path}: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_scene(self, file_path: str) -> Dict[str, Any]:
        """Analyze the scene using Gemini API."""
        try:
            # Extract frames for analysis
            frames = self._extract_frames(file_path, num_frames=5)
            
            # Use Gemini to analyze frames
            analysis = self.gemini_client.analyze_media_content(frames, file_path)
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing scene: {str(e)}")
            return {"error": str(e)}
    
    def _extract_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Extract representative frames from the video for analysis."""
        temp_dir = tempfile.mkdtemp()
        frame_paths = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if frame_count <= 0:
                return frame_paths
            
            # Extract frames at regular intervals
            interval = max(1, frame_count // num_frames)
            
            for i in range(num_frames):
                frame_idx = min(i * interval, frame_count - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                
            cap.release()
            
        except Exception as e:
            self.logger.error(f"Error extracting frames: {str(e)}")
        
        return frame_paths
    
    def _get_operation_parameters(
        self, 
        operation_name: str, 
        preset: str, 
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get parameters for the specified operation based on preset and custom overrides.
        """
        # Define default presets
        presets = {
            "standard": {
                "denoise": {"strength": 0.5, "preserve_details": True},
                "stabilize": {"strength": 0.5, "crop_margin": 0.1},
                "color_correct": {"white_balance": "auto", "saturation": 1.0, "contrast": 1.0},
                "artifact_removal": {"compression": True, "banding": True}
            },
            "light": {
                "denoise": {"strength": 0.3, "preserve_details": True},
                "stabilize": {"strength": 0.3, "crop_margin": 0.05},
                "color_correct": {"white_balance": "auto", "saturation": 0.95, "contrast": 0.95},
                "artifact_removal": {"compression": True, "banding": False}
            },
            "heavy": {
                "denoise": {"strength": 0.8, "preserve_details": False},
                "stabilize": {"strength": 0.8, "crop_margin": 0.15},
                "color_correct": {"white_balance": "auto", "saturation": 1.1, "contrast": 1.2},
                "artifact_removal": {"compression": True, "banding": True, "moire": True}
            },
            "web": {
                "denoise": {"strength": 0.4, "preserve_details": True},
                "color_correct": {"white_balance": "auto", "saturation": 1.1, "contrast": 1.1},
                "artifact_removal": {"compression": True}
            }
        }
        
        # Get base parameters from preset
        if preset not in presets:
            self.logger.warning(f"Unknown preset: {preset}, using standard")
            preset = "standard"
            
        if operation_name not in presets[preset]:
            self.logger.warning(f"Operation {operation_name} not defined in preset {preset}")
            return {}
            
        params = presets[preset][operation_name].copy()
        
        # Override with custom parameters if provided
        if custom_params and operation_name in custom_params:
            params.update(custom_params[operation_name])
            
        return params
