import os
import json
import logging
from typing import Dict, Any, List, Optional
import uuid
from google.cloud import firestore

class ConfigManager:
    """Manages configuration settings and presets for the PostRenderCleaner."""
    
    def __init__(self, use_firestore: bool = True):
        self.logger = logging.getLogger("config_manager")
        self.use_firestore = use_firestore
        
        # Initialize Firestore if used
        if self.use_firestore:
            try:
                self.db = firestore.Client()
                self.presets_collection = self.db.collection("postrendercleaner_presets")
                self.logger.info("Connected to Firestore for configuration storage")
            except Exception as e:
                self.logger.error(f"Failed to connect to Firestore: {str(e)}")
                self.use_firestore = False
        
        # Default presets available in the system
        self.default_presets = {
            "standard": {
                "name": "Standard",
                "description": "Balanced processing for general media",
                "denoise_strength": 0.5,
                "stabilize_strength": 0.5,
                "color_correction": {
                    "white_balance": "auto",
                    "saturation": 1.0,
                    "contrast": 1.0,
                    "brightness": 1.0
                },
                "artifact_removal": ["compression", "banding"]
            },
            "web": {
                "name": "Web Optimized",
                "description": "Settings optimized for web delivery",
                "denoise_strength": 0.4,
                "stabilize_strength": 0.3,
                "color_correction": {
                    "white_balance": "auto",
                    "saturation": 1.1,
                    "contrast": 1.1,
                    "brightness": 1.0
                },
                "artifact_removal": ["compression"]
            },
            "cinema": {
                "name": "Cinema Quality",
                "description": "High-quality settings for cinematic content",
                "denoise_strength": 0.6,
                "stabilize_strength": 0.7,
                "color_correction": {
                    "white_balance": "5600K",
                    "saturation": 1.1,
                    "contrast": 1.2,
                    "brightness": 0.95,
                    "highlights": 0.1,
                    "shadows": 0.2
                },
                "artifact_removal": ["compression", "banding", "moire"]
            },
            "archival": {
                "name": "Archival",
                "description": "Minimal processing for archival purposes",
                "denoise_strength": 0.3,
                "stabilize_strength": 0.0,
                "color_correction": {
                    "white_balance": "auto",
                    "saturation": 1.0,
                    "contrast": 1.0,
                    "brightness": 1.0
                },
                "artifact_removal": []
            }
        }
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available presets, combining default and custom presets."""
        if not self.use_firestore:
            return self.default_presets
        
        try:
            # Get custom presets from Firestore
            custom_presets = {}
            presets_docs = self.presets_collection.stream()
            
            for doc in presets_docs:
                custom_presets[doc.id] = doc.to_dict()
            
            # Combine default and custom presets, with custom taking precedence
            all_presets = {**self.default_presets, **custom_presets}
            return all_presets
            
        except Exception as e:
            self.logger.error(f"Error retrieving presets from Firestore: {str(e)}")
            return self.default_presets
    
    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset by ID."""
        # Check default presets first
        if preset_id in self.default_presets:
            return self.default_presets[preset_id]
        
        # Check custom presets if using Firestore
        if self.use_firestore:
            try:
                doc_ref = self.presets_collection.document(preset_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    return doc.to_dict()
                    
            except Exception as e:
                self.logger.error(f"Error retrieving preset {preset_id} from Firestore: {str(e)}")
        
        return None
    
    def create_preset(self, preset_data: Dict[str, Any]) -> str:
        """Create a new custom preset."""
        preset_id = preset_data.get("name", "").lower().replace(" ", "_")
        if not preset_id:
            preset_id = f"custom_{str(uuid.uuid4())[:8]}"
        
        if self.use_firestore:
            try:
                doc_ref = self.presets_collection.document(preset_id)
                doc_ref.set(preset_data)
                self.logger.info(f"Created new preset: {preset_id}")
                return preset_id
                
            except Exception as e:
                self.logger.error(f"Error creating preset in Firestore: {str(e)}")
                # Fall back to local storage if Firestore fails
                self.default_presets[preset_id] = preset_data
                return preset_id
        else:
            # Store locally if not using Firestore
            self.default_presets[preset_id] = preset_data
            return preset_id
    
    def update_preset(self, preset_id: str, preset_data: Dict[str, Any]) -> bool:
        """Update an existing preset."""
        # Don't allow updating default presets
        if preset_id in self.default_presets and preset_id not in ["custom_preset"]:
            self.logger.warning(f"Cannot update default preset: {preset_id}")
            return False
        
        if self.use_firestore:
            try:
                doc_ref = self.presets_collection.document(preset_id)
                doc = doc_ref.get()
                
                if not doc.exists:
                    self.logger.warning(f"Preset {preset_id} not found for update")
                    return False
                    
                doc_ref.update(preset_data)
                self.logger.info(f"Updated preset: {preset_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating preset in Firestore: {str(e)}")
                return False
        else:
            # Update locally if not using Firestore
            if preset_id not in self.default_presets:
                self.logger.warning(f"Preset {preset_id} not found for update")
                return False
                
            self.default_presets[preset_id].update(preset_data)
            return True
    
    def delete_preset(self, preset_id: str) -> bool:
        """Delete a custom preset."""
        # Don't allow deleting default presets
        if preset_id in self.default_presets and preset_id not in ["custom_preset"]:
            self.logger.warning(f"Cannot delete default preset: {preset_id}")
            return False
        
        if self.use_firestore:
            try:
                doc_ref = self.presets_collection.document(preset_id)
                doc = doc_ref.get()
                
                if not doc.exists:
                    self.logger.warning(f"Preset {preset_id} not found for deletion")
                    return False
                    
                doc_ref.delete()
                self.logger.info(f"Deleted preset: {preset_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error deleting preset from Firestore: {str(e)}")
                return False
        else:
            # Delete locally if not using Firestore
            if preset_id not in self.default_presets:
                self.logger.warning(f"Preset {preset_id} not found for deletion")
                return False
                
            del self.default_presets[preset_id]
            return True
