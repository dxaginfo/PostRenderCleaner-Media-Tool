"""Storage utilization reporting for the PostRenderCleaner tool."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

class StorageReporter:
    """Reports on storage utilization before and after cleanup."""
    
    def __init__(self):
        """Initialize the storage reporter."""
        self.logger = logging.getLogger("postrendercleaner.storage")
    
    def analyze_directory(self, directory: Path) -> Dict[str, Any]:
        """Analyze storage utilization in a directory.
        
        Args:
            directory: Path to analyze
            
        Returns:
            Dictionary with storage statistics
        """
        self.logger.info(f"Analyzing storage in directory: {directory}")
        stats = {
            "total_size": 0,
            "file_count": 0,
            "extension_stats": {},
            "largest_files": [],
        }
        
        try:
            for root, _, files in os.walk(directory):
                for filename in files:
                    file_path = Path(root) / filename
                    
                    try:
                        # Get file size
                        size = file_path.stat().st_size
                        extension = file_path.suffix.lower() or "<no extension>"
                        
                        # Update totals
                        stats["total_size"] += size
                        stats["file_count"] += 1
                        
                        # Update extension stats
                        if extension not in stats["extension_stats"]:
                            stats["extension_stats"][extension] = {
                                "count": 0,
                                "total_size": 0
                            }
                            
                        stats["extension_stats"][extension]["count"] += 1
                        stats["extension_stats"][extension]["total_size"] += size
                        
                        # Track largest files
                        self._update_largest_files(stats["largest_files"], str(file_path), size)
                        
                    except Exception as e:
                        self.logger.warning(f"Error analyzing file {file_path}: {e}")
                        
            # Calculate percentages for extensions
            for ext, ext_stats in stats["extension_stats"].items():
                if stats["total_size"] > 0:
                    ext_stats["percentage"] = (ext_stats["total_size"] / stats["total_size"]) * 100
                else:
                    ext_stats["percentage"] = 0
            
            # Convert bytes to human-readable formats
            stats["total_size_human"] = self._format_size(stats["total_size"])
            
            for ext, ext_stats in stats["extension_stats"].items():
                ext_stats["total_size_human"] = self._format_size(ext_stats["total_size"])
                
            self.logger.info(f"Storage analysis complete: {stats['file_count']} files, {stats['total_size_human']}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing directory {directory}: {e}")
            return stats
    
    def _update_largest_files(self, largest_files: List[Dict[str, Any]], file_path: str, size: int, max_files: int = 10):
        """Update list of largest files, maintaining the top N."""
        file_entry = {"path": file_path, "size": size, "size_human": self._format_size(size)}
        
        # Add to list if not full
        if len(largest_files) < max_files:
            largest_files.append(file_entry)
            largest_files.sort(key=lambda x: x["size"], reverse=True)
            return
            
        # Check if larger than smallest entry
        if size > largest_files[-1]["size"]:
            largest_files[-1] = file_entry
            largest_files.sort(key=lambda x: x["size"], reverse=True)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes into human-readable size."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
            
        for unit in ['KB', 'MB', 'GB', 'TB']:
            size_bytes /= 1024.0
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
                
        return f"{size_bytes:.2f} PB"
    
    def generate_comparison_report(self, before: Dict[str, Any], after: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comparison report between before and after storage stats.
        
        Args:
            before: Storage stats before cleanup
            after: Storage stats after cleanup
            output_path: Optional path to write report
            
        Returns:
            Dictionary with comparison metrics
        """
        report = {
            "bytes_saved": before["total_size"] - after["total_size"],
            "files_removed": before["file_count"] - after["file_count"],
            "bytes_saved_human": self._format_size(before["total_size"] - after["total_size"]),
            "space_reduction_percent": 0,
            "before": before,
            "after": after
        }
        
        # Calculate percentage
        if before["total_size"] > 0:
            report["space_reduction_percent"] = (report["bytes_saved"] / before["total_size"]) * 100
        
        # Write to file if requested
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2)
                self.logger.info(f"Wrote comparison report to {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to write comparison report: {e}")
        
        return report
