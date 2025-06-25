import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
import ffmpeg

from .base import BaseOperation

class StabilizeOperation(BaseOperation):
    """Performs video stabilization to reduce camera shake."""
    
    def __init__(self):
        self.logger = logging.getLogger("stabilize_operation")
    
    def apply(self, input_path: str, output_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply stabilization to the video file.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the output file should be written
            parameters: Stabilization parameters
                - strength: Float between 0 and 1 for stabilization strength
                - crop_margin: Float between 0 and 0.25 for crop margin (default 0.1)
                - method: String 'vidstab' or 'deshake' (default 'vidstab')
            context: Additional context like scene analysis
            
        Returns:
            Dictionary with operation results and metadata
        """
        self.logger.info(f"Applying stabilization to {input_path} with parameters: {parameters}")
        
        # Check if input is a video
        try:
            probe = ffmpeg.probe(input_path)
            has_video = any(s["codec_type"] == "video" for s in probe["streams"])
            
            if not has_video:
                self.logger.warning(f"Input file {input_path} does not contain video, skipping stabilization")
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "skipped", "reason": "no_video_stream"}
                
        except Exception as e:
            self.logger.error(f"Error probing input file: {str(e)}")
            return {"status": "error", "error": str(e)}
        
        # Get parameters
        strength = parameters.get("strength", 0.5)
        crop_margin = parameters.get("crop_margin", 0.1)
        method = parameters.get("method", "vidstab")
        
        # Adjust settings based on context if available
        if context and "motion_assessment" in context:
            motion_level = context.get("motion_assessment", {}).get("camera_shake", "medium")
            
            self.logger.info(f"Adjusting stabilization based on detected motion: {motion_level}")
            
            # Adjust strength based on detected motion level
            if motion_level == "high":
                strength = min(1.0, strength * 1.3)
                crop_margin = min(0.25, crop_margin * 1.2)
            elif motion_level == "low":
                strength = max(0.1, strength * 0.7)
        
        # Apply stabilization
        if method == "deshake":
            return self._apply_deshake(input_path, output_path, strength, crop_margin)
        else:
            return self._apply_vidstab(input_path, output_path, strength, crop_margin)
    
    def _apply_vidstab(
        self, 
        input_path: str, 
        output_path: str, 
        strength: float, 
        crop_margin: float
    ) -> Dict[str, Any]:
        """Apply stabilization using FFmpeg's vidstabdetect and vidstabtransform filters."""
        try:
            temp_dir = tempfile.mkdtemp()
            transforms_file = os.path.join(temp_dir, "transforms.trf")
            
            # Step 1: Detect transforms
            shakiness = int(strength * 10)  # Scale to 1-10
            accuracy = 15 if strength > 0.8 else 10  # Higher accuracy for higher strength
            
            # Detect
            (
                ffmpeg
                .input(input_path)
                .filter("vidstabdetect", shakiness=shakiness, accuracy=accuracy, result=transforms_file)
                .output(os.devnull, f="null")
                .global_args("-nostats", "-loglevel", "error")
                .run(overwrite_output=True)
            )
            
            # Step 2: Apply transforms
            smoothing = int(strength * 100)  # Scale to 1-100
            optzoom = 1  # Optimal zoom (1 = little zoom, 2 = more zoom)
            zoom = 1 + crop_margin  # Add crop margin as zoom
            
            # Transform
            (
                ffmpeg
                .input(input_path)
                .filter("vidstabtransform", input=transforms_file, smoothing=smoothing, optzoom=optzoom, zoom=zoom)
                .filter("unsharp", 5, 5, 0.5)  # Add slight sharpening to counteract blur
                .output(output_path)
                .global_args("-nostats", "-loglevel", "error")
                .run(overwrite_output=True)
            )
            
            return {
                "status": "success",
                "parameters": {
                    "strength": strength,
                    "crop_margin": crop_margin,
                    "method": "vidstab",
                    "shakiness": shakiness,
                    "smoothing": smoothing,
                    "zoom": zoom
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in vidstab stabilization: {str(e)}")
            # Fall back to copying the file
            try:
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "error", "error": str(e), "fallback": "copy"}
            except:
                return {"status": "failed", "error": str(e)}
    
    def _apply_deshake(
        self, 
        input_path: str, 
        output_path: str, 
        strength: float, 
        crop_margin: float
    ) -> Dict[str, Any]:
        """Apply stabilization using FFmpeg's deshake filter."""
        try:
            # Map parameters to deshake filter
            # deshake uses rx, ry for edge cropping
            edge = int(crop_margin * 100)  # Convert to percentage
            
            # Apply filter
            (
                ffmpeg
                .input(input_path)
                .filter("deshake", rx=edge, ry=edge)
                .output(output_path)
                .global_args("-nostats", "-loglevel", "error")
                .run(overwrite_output=True)
            )
            
            return {
                "status": "success",
                "parameters": {
                    "strength": strength,
                    "crop_margin": crop_margin,
                    "method": "deshake",
                    "edge": edge
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in deshake stabilization: {str(e)}")
            # Fall back to copying the file
            try:
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "error", "error": str(e), "fallback": "copy"}
            except:
                return {"status": "failed", "error": str(e)}
