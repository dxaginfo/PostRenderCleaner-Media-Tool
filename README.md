# PostRenderCleaner

Media post-processing and cleanup tool for the DEN AI Media automation toolset

## Overview

PostRenderCleaner is an automated post-production tool designed to streamline the cleanup and enhancement of rendered media assets. It focuses on common post-render tasks such as denoising, stabilization, color correction, and artifact removal, making it an essential component of the media production pipeline.

## Features

- Automated denoising for video and audio content
- Frame stabilization for eliminating camera shake
- Color correction with preset support
- Artifact removal and format compliance
- Batch processing capabilities
- Integration with other media tools

## Documentation

Full documentation is available at: https://docs.google.com/document/d/18GpP-LQQJUdAFtygzjYcG_yPc3aRZv2Hw2RGdBLBbqA

## Integration Points

This tool integrates with:

- FormatNormalizer: For format standardization
- TimelineAssembler: For production timeline integration
- SceneValidator: For scene integrity validation
- SoundScaffold: For audio processing coordination

## Installation

```bash
git clone https://github.com/dxaginfo/PostRenderCleaner-Media-Tool.git
cd PostRenderCleaner-Media-Tool
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```python
from postrendercleaner import PostRenderCleaner

# Initialize cleaner with default settings
cleaner = PostRenderCleaner()

# Process a single file
cleaner.process_file(
    input_path="input_video.mp4",
    output_path="cleaned_video.mp4",
    operations=["denoise", "stabilize", "color_correct"],
    preset="standard"
)

# Process a batch of files
cleaner.process_batch(
    input_dir="input_folder",
    output_dir="output_folder",
    operations=["denoise", "color_correct"],
    preset="web"
)
```

## License

MIT License
