# PostRenderCleaner

A tool for cleaning and optimizing post-render artifacts in media production workflows. It identifies and removes temporary files, optimizes final renders, and organizes output directories according to predefined standards.

## Overview

PostRenderCleaner is designed to be a flexible and powerful tool for managing the cleanup of post-render artifacts in media production environments. It helps studios and creators manage disk space, organize assets, and ensure compliance with retention policies.

## Features

- Automatic detection and removal of temporary render files
- Configurable retention policies for different file types
- Compression of final renders for optimized storage
- Integration with Google Cloud Storage for archiving
- Detailed logging and reporting of cleanup operations
- API for integration with existing media production pipelines

## Installation

```bash
pip install postrendercleaner
```

Or install from source:

```bash
git clone https://github.com/dxaginfo/PostRenderCleaner-Media-Tool.git
cd PostRenderCleaner-Media-Tool
pip install -e .
```

## Usage

### Basic Usage

```bash
# Basic cleanup with default config
python -m postrendercleaner --path /render/project123

# Specify custom configuration
python -m postrendercleaner --path /render/project123 --config my_config.yaml

# Dry run mode (no actual deletion)
python -m postrendercleaner --path /render/project123 --dry-run

# Apply to multiple paths
python -m postrendercleaner --path /render/project123 --path /render/project124
```

### Python API

```python
from postrendercleaner import CleanupManager

# Initialize the cleaner
cleaner = CleanupManager(config_path="config/project_specific.yaml")

# Run cleanup operation
result = cleaner.run("/render/project123")

# Get report
report = result.get_report()
print(f"Cleaned up {report.bytes_saved} bytes of disk space")
print(f"Removed {report.files_removed} temporary files")
print(f"Archived {report.files_archived} files to cold storage")
```

## Configuration

PostRenderCleaner uses YAML configuration files. Here's an example:

```yaml
# Example configuration
cleanup:
  temp_patterns:
    - "*.tmp"
    - "*.temp"
    - "*_scratch.*"
    - "render_cache/*"
  
  retention:
    logs: 30  # days
    intermediates: 7  # days
    backups: 90  # days
  
  actions:
    compress_renders: true
    archive_to_cold_storage: true
    generate_report: true
  
  notification:
    email_on_completion: true
    slack_on_error: true
```

## Cloud Deployment

PostRenderCleaner can be deployed as a Cloud Function that triggers on storage events:

```python
def trigger_cleanup(event, context):
    """Cloud Function to trigger cleanup on GCS render bucket events."""
    from postrendercleaner import CleanupManager
    
    render_bucket = event['bucket']
    render_path = event['name']
    
    # Extract project info from path
    project_id = render_path.split('/')[0]
    
    # Initialize cleanup with project-specific config
    cleaner = CleanupManager(project_id=project_id)
    
    # Run cleanup
    result = cleaner.run_on_gcs(render_bucket, render_path)
    
    # Log results
    print(f"Cleanup completed for {project_id}: {result.summary}")
    
    return result.success
```

## Integration with Other Tools

PostRenderCleaner is designed to work with other media automation tools including:

- **SceneValidator**: Ensures only validated scenes are retained
- **TimelineAssembler**: Cleans up intermediates when a timeline is finalized
- **LoopOptimizer**: Removes unoptimized loops after optimization

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.