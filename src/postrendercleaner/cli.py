"""Command-line interface for the PostRenderCleaner tool."""

import click
import logging
from typing import List
from pathlib import Path

from postrendercleaner.cleanup_manager import CleanupManager

@click.command()
@click.option(
    "--path", "-p", 
    multiple=True, 
    required=True, 
    help="Directory path(s) containing rendered media"
)
@click.option(
    "--config", "-c", 
    help="Path to configuration file"
)
@click.option(
    "--dry-run", "-d", 
    is_flag=True, 
    help="Simulate cleanup without actually deleting files"
)
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Enable verbose output"
)
@click.version_option()
def main(path: List[str], config: str, dry_run: bool, verbose: bool):
    """Clean and optimize post-render artifacts in media production workflows."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger("postrendercleaner")
    logger.info("Starting PostRenderCleaner")
    
    # Initialize the cleanup manager
    manager = CleanupManager(config_path=config)
    
    # Run cleanup on all specified paths
    result = manager.run(path, dry_run=dry_run)
    
    # Print summary
    click.echo(f"Cleanup {'simulation' if dry_run else 'operation'} completed:")
    click.echo(result.summary)
    
    if not result.success:
        click.echo(f"Error: {result.error_message}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()
