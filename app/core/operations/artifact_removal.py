import os
import logging
import tempfile
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
import ffmpeg

from .base import BaseOperation

class ArtifactRemovalOperation(BaseOperation):
    """Performs artifact removal on video content."""
    
    def __init__(self):
        self.logger = logging.getLogger("artifact_removal_operation")
    
    def apply(self, input_path: str, output_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply artifact removal to the media file.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the output file should be written
            parameters: Artifact removal parameters
                - compression: Boolean to enable compression artifact removal
                - banding: Boolean to enable banding artifact removal
                - moire: Boolean to enable moire pattern removal
                - rolling_shutter: Boolean to enable rolling shutter correction
                - strength: Float between 0 and 1 for overall strength (default 0.5)
            context: Additional context like scene analysis
            
        Returns:
            Dictionary with operation results and metadata
        """
        self.logger.info(f"Applying artifact removal to {input_path} with parameters: {parameters}")
        
        # Check if input is a video
        try:
            probe = ffmpeg.probe(input_path)
            has_video = any(s["codec_type"] == "video" for s in probe["streams"])
            
            if not has_video:
                self.logger.warning(f"Input file {input_path} does not contain video, skipping artifact removal")
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "skipped", "reason": "no_video_stream"}
                
        except Exception as e:
            self.logger.error(f"Error probing input file: {str(e)}")
            return {"status": "error", "error": str(e)}
        
        # Get parameters with defaults
        remove_compression = parameters.get("compression", True)
        remove_banding = parameters.get("banding", False)
        remove_moire = parameters.get("moire", False)
        fix_rolling_shutter = parameters.get("rolling_shutter", False)
        strength = parameters.get("strength", 0.5)
        
        # Adjust settings based on context if available
        if context and "artifacts" in context:
            artifacts = context.get("artifacts", [])
            
            self.logger.info(f"Adjusting artifact removal based on detected artifacts: {artifacts}")
            
            # Enable specific artifact removal based on detection
            if "compression" in artifacts:
                remove_compression = True
            if "banding" in artifacts:
                remove_banding = True
            if "moire" in artifacts:
                remove_moire = True
            if "rolling_shutter" in artifacts:
                fix_rolling_shutter = True
        
        # Apply artifact removal
        return self._apply_artifact_removal(
            input_path, 
            output_path, 
            remove_compression, 
            remove_banding, 
            remove_moire,
            fix_rolling_shutter,
            strength
        )
    
    def _apply_artifact_removal(
        self, 
        input_path: str, 
        output_path: str, 
        remove_compression: bool,
        remove_banding: bool,
        remove_moire: bool,
        fix_rolling_shutter: bool,
        strength: float
    ) -> Dict[str, Any]:
        """Apply artifact removal using FFmpeg filters."""
        try:
            filter_complex = []
            
            # Apply compression artifact removal
            if remove_compression:
                # Convert strength to filter parameters
                strength_val = strength * 4  # Scale to 0-4
                filter_complex.append(f"pp=ac/a/default/ha|h/va|v/dr/tn|t|b|c")
            
            # Apply banding removal (debanding)
            if remove_banding:
                # Map strength to filter parameters
                threshold = int(strength * 4) + 1  # Scale to 1-5
                range_val = int(strength * 15) + 1  # Scale to 1-16
                filter_complex.append(f"deband=threshold={threshold}:range={range_val}:iterations=2:blendmode=average")
            
            # Apply moire pattern removal
            if remove_moire:
                # Use simple blur for moire
                radius = strength * 2  # Scale to 0-2
                filter_complex.append(f"smartblur=lr={radius:.1f}:ls=-0.5:lt=8.0:cr={radius/2:.1f}:cs=0.0:ct=0.0")
            
            # Apply rolling shutter correction
            if fix_rolling_shutter:
                # This is a simplified approach - real rolling shutter correction is complex
                filter_complex.append(f"dejudder=cycle=2")
            
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
                    "compression": remove_compression,
                    "banding": remove_banding,
                    "moire": remove_moire,
                    "rolling_shutter": fix_rolling_shutter,
                    "strength": strength,
                    "applied_filters": filter_str
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in artifact removal: {str(e)}")
            # Fall back to copying the file
            try:
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "error", "error": str(e), "fallback": "copy"}
            except:
                return {"status": "failed", "error": str(e)}
