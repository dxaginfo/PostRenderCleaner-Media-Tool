import os
import logging
import base64
from typing import List, Dict, Any, Optional
import requests
import json
from PIL import Image
import io

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided and not found in environment variables")
        
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
        self.logger = logging.getLogger("gemini_client")

    def analyze_media_content(self, image_paths: List[str], media_path: str) -> Dict[str, Any]:
        """
        Analyze media content using Gemini Vision API.
        
        Args:
            image_paths: List of paths to image frames extracted from the media
            media_path: Path to the original media file for context
            
        Returns:
            Dictionary containing scene analysis data
        """
        try:
            # Prepare image data
            image_parts = []
            for img_path in image_paths[:5]:  # Limit to 5 images
                with open(img_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    image_parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": image_data
                        }
                    })
            
            # Prepare prompt
            prompt = f"""
            Analyze these frames from a media file and provide detailed information about the scene 
            that would be helpful for post-processing operations. Focus on:
            
            1. Lighting conditions (indoor/outdoor, bright/dark, consistent/inconsistent)
            2. Color characteristics (color temperature, dominant colors, color cast)
            3. Noise levels and types (grain, digital noise, etc.)
            4. Motion and stability (camera movement, subject movement)
            5. Visible artifacts (compression artifacts, banding, etc.)
            6. Scene type classification (landscape, portrait, action, etc.)
            
            Return your analysis as structured JSON with the following fields:
            - lighting_conditions: object with details about lighting
            - color_characteristics: object with color analysis
            - noise_assessment: object with noise details
            - motion_assessment: object with motion and stability details
            - artifacts: array of detected artifacts
            - scene_type: string describing the scene type
            - processing_recommendations: object with recommended processing settings
            
            Filename: {os.path.basename(media_path)}
            """
            
            # Construct request payload
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ] + image_parts
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048
                }
            }
            
            # Make API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
            
            # Parse response
            result = response.json()
            text_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            # Extract JSON from the response
            json_start = text_response.find('{')
            json_end = text_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text_response[json_start:json_end]
                try:
                    analysis_data = json.loads(json_str)
                    return analysis_data
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse JSON from Gemini response")
                    return {"error": "Failed to parse analysis data", "raw_response": text_response}
            
            # Fallback to returning the text response
            return {"error": "No structured data found", "text_analysis": text_response}
            
        except Exception as e:
            self.logger.error(f"Error in Gemini analysis: {str(e)}")
            return {"error": str(e)}
