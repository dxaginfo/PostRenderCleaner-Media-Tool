"""
PostRenderCleaner - An automated tool for cleaning and optimizing post-render artifacts.
"""

__version__ = "1.0.0"

from .core import CleanupManager, CleanupResult

__all__ = ["CleanupManager", "CleanupResult", "__version__"]