from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseOperation(ABC):
    """Base class for all processing operations."""
    
    @abstractmethod
    def apply(self, input_path: str, output_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the operation to the input file and generate the output file.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the output file should be written
            parameters: Operation-specific parameters
            context: Additional context like scene analysis
            
        Returns:
            Dictionary with operation results and metadata
        """
        pass
