import os
import logging
import tempfile
import subprocess
from typing import Dict, Any
import cv2
import numpy as np
import ffmpeg

from .base import BaseOperation

class DenoiseOperation(BaseOperation):
    """Performs denoising on video and audio content."""
    
    def __init__(self):
        self.logger = logging.getLogger("denoise_operation")
    
    def apply(self, input_path: str, output_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply denoising to the media file.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the output file should be written
            parameters: Denoising parameters
                - strength: Float between 0 and 1 for denoising strength
                - preserve_details: Boolean indicating whether to preserve details
                - temporal: Boolean indicating whether to use temporal denoising
            context: Additional context like scene analysis
            
        Returns:
            Dictionary with operation results and metadata
        """
        self.logger.info(f"Applying denoising to {input_path} with parameters: {parameters}")
        
        strength = parameters.get("strength", 0.5)
        preserve_details = parameters.get("preserve_details", True)
        temporal = parameters.get("temporal", True)
        
        # Adjust settings based on context if available
        if context and "noise_assessment" in context:
            noise_level = context.get("noise_assessment", {}).get("level", "medium")
            noise_type = context.get("noise_assessment", {}).get("type", "mixed")
            
            self.logger.info(f"Adjusting denoising based on detected noise: {noise_level} - {noise_type}")
            
            # Adjust strength based on detected noise level
            if noise_level == "high":
                strength = min(1.0, strength * 1.5)
            elif noise_level == "low":
                strength = max(0.1, strength * 0.7)
        
        # Determine if input is video or audio
        try:
            probe = ffmpeg.probe(input_path)
            media_type = "video" if any(s["codec_type"] == "video" for s in probe["streams"]) else "audio"
        except Exception as e:
            self.logger.error(f"Error probing media type: {str(e)}")
            media_type = "unknown"
        
        # Apply appropriate denoising based on media type
        if media_type == "video":
            return self._denoise_video(input_path, output_path, strength, preserve_details, temporal)
        elif media_type == "audio":
            return self._denoise_audio(input_path, output_path, strength)
        else:
            self.logger.warning(f"Unknown media type, copying file without denoising")
            ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
            return {"status": "skipped", "reason": "unknown_media_type"}
    
    def _denoise_video(
        self, 
        input_path: str, 
        output_path: str, 
        strength: float, 
        preserve_details: bool, 
        temporal: bool
    ) -> Dict[str, Any]:
        """Apply video denoising using FFmpeg's filters."""
        try:
            # Map strength (0-1) to FFmpeg filter parameters
            spatial_strength = int(strength * 10)  # Scale to 0-10
            temporal_strength = int(strength * 7)  # Scale to 0-7 for temporal filter
            
            filter_complex = []
            
            # Apply denoising filters
            if temporal and temporal_strength > 0:
                # Temporal denoising with TNLMeans filter
                filter_complex.append(
                    f"tnlmeans=strength={temporal_strength}:mode=fast:patch=7:search=7"
                )
            
            if spatial_strength > 0:
                # Spatial denoising
                if preserve_details:
                    # Use nlmeans for better detail preservation
                    filter_complex.append(
                        f"nlmeans=strength={spatial_strength}:patch=5:search=7"
                    )
                else:
                    # Use hqdn3d for stronger noise removal
                    luma_spatial = spatial_strength * 4
                    chroma_spatial = spatial_strength * 3
                    filter_complex.append(
                        f"hqdn3d={luma_spatial}:{luma_spatial}:{chroma_spatial}:{chroma_spatial}"
                    )
            
            # Create the filter chain
            filter_str = ",".join(filter_complex)
            
            if filter_str:
                # Apply the filter chain
                ffmpeg.input(input_path).output(
                    output_path,
                    vf=filter_str,
                    c="h264" if os.path.splitext(output_path)[1].lower() == ".mp4" else None,
                    crf=20  # Quality setting
                ).run(quiet=True, overwrite_output=True)
            else:
                # No filters to apply, just copy
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
            
            return {
                "status": "success",
                "parameters": {
                    "strength": strength,
                    "preserve_details": preserve_details,
                    "temporal": temporal,
                    "applied_filters": filter_str
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in video denoising: {str(e)}")
            # Fall back to copying the file
            try:
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "error", "error": str(e), "fallback": "copy"}
            except:
                return {"status": "failed", "error": str(e)}
    
    def _denoise_audio(
        self, 
        input_path: str, 
        output_path: str, 
        strength: float
    ) -> Dict[str, Any]:
        """Apply audio denoising using FFmpeg's filters."""
        try:
            # Map strength (0-1) to FFmpeg filter parameters
            noise_reduction = strength * 0.3  # Scale to 0-0.3 for afftdn
            
            # Apply audio denoising filter
            filter_str = f"afftdn=noise_reduction={noise_reduction:.3f}"
            
            ffmpeg.input(input_path).output(
                output_path,
                af=filter_str
            ).run(quiet=True, overwrite_output=True)
            
            return {
                "status": "success",
                "parameters": {
                    "strength": strength,
                    "applied_filter": filter_str
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in audio denoising: {str(e)}")
            # Fall back to copying the file
            try:
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "error", "error": str(e), "fallback": "copy"}
            except:
                return {"status": "failed", "error": str(e)}
