#!/usr/bin/env python3
"""
PostRenderCleaner - Main entry point for the command line interface
"""

import argparse
import logging
import os
import sys
from typing import List

from postrendercleaner import CleanupManager, __version__

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PostRenderCleaner: Clean and optimize post-render artifacts"
    )
    
    parser.add_argument(
        "--path", 
        action="append", 
        required=True,
        help="Path(s) to process. Can be specified multiple times."
    )
    
    parser.add_argument(
        "--config", 
        default=None,
        help="Path to configuration file. Uses default if not specified."
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Simulate cleanup without making changes."
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging."
    )
    
    parser.add_argument(
        "--version", 
        action="version",
        version=f"PostRenderCleaner {__version__}"
    )
    
    return parser.parse_args()

def main() -> int:
    """Main entry point for the command line interface."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logging.info("Starting PostRenderCleaner...")
    logging.info(f"Processing paths: {args.path}")
    
    try:
        # Initialize the cleanup manager
        manager = CleanupManager(
            config_path=args.config,
            dry_run=args.dry_run
        )
        
        results = []
        # Process each specified path
        for path in args.path:
            if not os.path.exists(path):
                logging.error(f"Path does not exist: {path}")
                continue
                
            logging.info(f"Processing: {path}")
            result = manager.run(path)
            results.append(result)
            
            # Print summary for this path
            report = result.get_report()
            logging.info(f"Completed processing: {path}")
            logging.info(f"  - Cleaned up: {report.bytes_saved} bytes")
            logging.info(f"  - Removed: {report.files_removed} files")
            logging.info(f"  - Archived: {report.files_archived} files")
            
        # Calculate overall stats
        total_bytes_saved = sum(r.get_report().bytes_saved for r in results)
        total_files_removed = sum(r.get_report().files_removed for r in results)
        total_files_archived = sum(r.get_report().files_archived for r in results)
        
        logging.info("=" * 50)
        logging.info("Overall cleanup summary:")
        logging.info(f"  - Total cleaned up: {total_bytes_saved} bytes")
        logging.info(f"  - Total removed: {total_files_removed} files")
        logging.info(f"  - Total archived: {total_files_archived} files")
        
        return 0
        
    except Exception as e:
        logging.exception(f"Error during cleanup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())