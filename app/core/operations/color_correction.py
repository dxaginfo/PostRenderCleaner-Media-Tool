import os
import logging
import tempfile
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np
import ffmpeg

from .base import BaseOperation

class ColorCorrectionOperation(BaseOperation):
    """Performs color correction and grading on video content."""
    
    def __init__(self):
        self.logger = logging.getLogger("color_correction_operation")
    
    def apply(self, input_path: str, output_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply color correction to the media file.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the output file should be written
            parameters: Color correction parameters
                - white_balance: String 'auto' or specific temperature (e.g., '5600K')
                - saturation: Float adjustment factor (1.0 = no change)
                - contrast: Float adjustment factor (1.0 = no change)
                - brightness: Float adjustment factor (1.0 = no change)
                - gamma: Float gamma correction (1.0 = no change)
                - highlights: Float adjustment for highlights (-1.0 to 1.0)
                - shadows: Float adjustment for shadows (-1.0 to 1.0)
            context: Additional context like scene analysis
            
        Returns:
            Dictionary with operation results and metadata
        """
        self.logger.info(f"Applying color correction to {input_path} with parameters: {parameters}")
        
        # Check if input is a video
        try:
            probe = ffmpeg.probe(input_path)
            has_video = any(s["codec_type"] == "video" for s in probe["streams"])
            
            if not has_video:
                self.logger.warning(f"Input file {input_path} does not contain video, skipping color correction")
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "skipped", "reason": "no_video_stream"}
                
        except Exception as e:
            self.logger.error(f"Error probing input file: {str(e)}")
            return {"status": "error", "error": str(e)}
        
        # Get parameters with defaults
        white_balance = parameters.get("white_balance", "auto")
        saturation = parameters.get("saturation", 1.0)
        contrast = parameters.get("contrast", 1.0)
        brightness = parameters.get("brightness", 1.0)
        gamma = parameters.get("gamma", 1.0)
        highlights = parameters.get("highlights", 0.0)
        shadows = parameters.get("shadows", 0.0)
        
        # Adjust settings based on context if available
        if context and "color_characteristics" in context:
            color_temp = context.get("color_characteristics", {}).get("temperature", "neutral")
            color_cast = context.get("color_characteristics", {}).get("color_cast", None)
            
            self.logger.info(f"Adjusting color correction based on detected color: temp={color_temp}, cast={color_cast}")
            
            # Auto-adjust white balance based on detected color temperature
            if white_balance == "auto" and color_temp != "neutral":
                if color_temp == "warm":
                    # Apply cooler white balance to compensate
                    white_balance = "5600K"
                elif color_temp == "cool":
                    # Apply warmer white balance to compensate
                    white_balance = "3200K"
            
            # Auto-adjust saturation based on color cast
            if color_cast == "desaturated":
                saturation = max(1.0, saturation * 1.2)
            elif color_cast == "oversaturated":
                saturation = min(1.0, saturation * 0.8)
        
        # Apply color correction
        return self._apply_color_correction(
            input_path, 
            output_path, 
            white_balance, 
            saturation, 
            contrast, 
            brightness, 
            gamma,
            highlights,
            shadows
        )
    
    def _apply_color_correction(
        self, 
        input_path: str, 
        output_path: str, 
        white_balance: str,
        saturation: float,
        contrast: float,
        brightness: float,
        gamma: float,
        highlights: float,
        shadows: float
    ) -> Dict[str, Any]:
        """Apply color correction using FFmpeg filters."""
        try:
            filter_complex = []
            
            # Apply white balance correction if specified
            if white_balance != "none":
                if white_balance == "auto":
                    # Use autolevels for automatic white balance
                    filter_complex.append("eq=brightness=0:contrast=1.0:saturation=1.0:gamma=1.0:gamma_r=1.0:gamma_g=1.0:gamma_b=1.0:gamma_weight=1.0")
                elif white_balance == "3200K":
                    # Warm white balance (tungsten)
                    filter_complex.append("colortemperature=temperature=3200")
                elif white_balance == "5600K":
                    # Cool white balance (daylight)
                    filter_complex.append("colortemperature=temperature=5600")
            
            # Apply basic color adjustments
            eq_params = []
            if brightness != 1.0:
                # Map brightness (0.5-1.5) to FFmpeg eq filter (-0.5 to 0.5)
                brightness_adj = (brightness - 1.0) * 0.5
                eq_params.append(f"brightness={brightness_adj:.3f}")
            
            if contrast != 1.0:
                eq_params.append(f"contrast={contrast:.3f}")
            
            if gamma != 1.0:
                eq_params.append(f"gamma={gamma:.3f}")
            
            if eq_params:
                filter_complex.append("eq=" + ":".join(eq_params))
            
            # Apply saturation adjustment
            if saturation != 1.0:
                filter_complex.append(f"colorchannelmixer=rr=1:gg=1:bb=1:aa=1:rg=0:rb=0:gr=0:gb=0:br=0:bg=0:rcoeff={saturation:.3f}:gcoeff={saturation:.3f}:bcoeff={saturation:.3f}")
            
            # Apply highlights and shadows adjustments using curves filter
            if highlights != 0.0 or shadows != 0.0:
                # Create a curve string for the curves filter
                curve_points = []
                
                # Add shadow adjustment point (in the 0.0-0.3 range)
                if shadows != 0.0:
                    shadow_y = max(0.0, min(0.3, 0.15 + shadows * 0.15))
                    curve_points.append(f"0/0 0.3/{shadow_y:.3f}")
                
                # Add midpoint reference (unchanged)
                curve_points.append("0.5/0.5")
                
                # Add highlight adjustment point (in the 0.7-1.0 range)
                if highlights != 0.0:
                    highlight_y = max(0.7, min(1.0, 0.85 + highlights * 0.15))
                    curve_points.append(f"0.7/{highlight_y:.3f} 1/1")
                
                if curve_points:
                    curves_str = " ".join(curve_points)
                    filter_complex.append(f"curves=all='{curves_str}'")
            
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
                    "white_balance": white_balance,
                    "saturation": saturation,
                    "contrast": contrast,
                    "brightness": brightness,
                    "gamma": gamma,
                    "highlights": highlights,
                    "shadows": shadows,
                    "applied_filters": filter_str
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in color correction: {str(e)}")
            # Fall back to copying the file
            try:
                ffmpeg.input(input_path).output(output_path, c="copy").run(quiet=True, overwrite_output=True)
                return {"status": "error", "error": str(e), "fallback": "copy"}
            except:
                return {"status": "failed", "error": str(e)}
