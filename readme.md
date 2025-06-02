# Image Gallery with Descriptions

A comprehensive tool for organizing, managing, and AI-enhancing image datasets for machine learning training.

## Overview

This application provides a complete workflow for dataset preparation, combining manual organization tools with AI-powered description enhancement. Built with a clean tabbed interface, it supports multi-selection operations and integrates with oLLama for intelligent description rephrasing.

**Perfect for preparing training data for image generation models like Stable Diffusion, DALL-E, and other diffusion models.**


![GUI Screenshot](ig_gui1.png)
![GUI Screenshot](ig_gui2.png)

## Features

### 🖼️ **Gallery Management**
- **Multi-Selection Support**: Ctrl+click and Shift+click for batch operations
- **Real-time Preview**: Large image display with instant description editing
- **Smart Loading**: Automatically loads descriptions from .txt files or consolidated JSON
- **Flexible Save Options**: Individual .txt files + consolidated JSON export
- **Context Menu**: Right-click to remove images from dataset

### 🛠️ **Image Processing (Utils Tab - Left Panel)**
- **Fix Images**: Resize, pad, and standardize image dimensions (512/1024/2048px)
- **Mass Rename**: Batch rename with custom prefixes and sequential numbering
- **🆕 Order Scrambling**: Randomize training order with alpha characters (e.g., `name_a001.jpg`, `name_m002.jpg`, `name_c003.jpg`)
- **Dataset Augmentation**: Create duplicates with transformations:
  - Simple duplication (`_dup` suffix)
  - Horizontal flip (`_flipHor`)
  - 90° rotations (`_rotLeft`, `_rotRight`)
  - 180° rotation (`_flipVert`)

### 🤖 **AI Description Enhancement (Utils Tab - Right Panel)**
-
- **Custom Prompts**: Full control over AI rephrasing instructions
- **Test Interface**: Preview AI output before batch processing
- **Batch Processing**: Rephrase descriptions while preserving names and details
- **WSL Support**: Configurable server/port for cross-platform development

### 🏷️ **Advanced Tag System**
- **Tag Scrambling**: Randomize tag order to create training variety
- **Keyword Tags**: Mark important tags to always appear first
- **Visual Tag Chips**: Color-coded tags (red=keyword, green=selected)
- **Batch Tag Operations**: Apply tags to multiple images at once
- **Tag Migration**: Converts existing descriptions to tag format

### 🎯 **Scope-Aware Operations**
Every utility respects your selection:
- **"All Images"**: Process entire dataset
- **"Selected Only"**: Process only highlighted images
- **Smart UI**: Options auto-enable/disable based on selection state

## Requirements

- **Python 3.8+**
- **PyQt6**: Modern GUI framework
- **PIL/Pillow**: Image processing
-

### Installation
```bash
pip install PyQt6 pillow requests
```



## Quick Start

```bash
# Clone and run
git clone https://github.com/scsuvizlab/ImageDatasetManager.git
cd image-gallery
python image_gallery.py
```

## Usage Guide

### Basic Workflow

1. **Load Dataset**: Gallery tab → "Select Folder"
2. **Review & Edit**: Browse images, edit descriptions manually
3. **Process Images**: Utils tab → Fix dimensions, rename, or duplicate
4. **AI Enhancement**: Utils tab → Rephrase descriptions with oLLama
5. **Save Results**: Gallery tab → "Save Descriptions"

### Multi-Selection Operations

- **Select Multiple**: `Ctrl+Click` individual images or `Shift+Click` ranges
- **Scope Selection**: Choose "All" or "Selected Only" for each operation
- **Visual Feedback**: Green status bar shows current selection

### 🆕 **Order Scrambling for Training**

The new order scrambling feature helps randomize training order by adding random letters to filenames:

**Standard Naming:**
```
portrait_001.jpg
portrait_002.jpg
portrait_003.jpg
```

**With Order Scrambling:**
```
portrait_a001.jpg
portrait_m002.jpg
portrait_c003.jpg
```

This prevents models from learning filename-based patterns and ensures truly random training order.

**How to Use:**
1. Go to Utils tab → Mass Rename section
2. Enter your desired prefix
3. ✅ Check "Scramble image order (adds random letters)"
4. Click "Rename Images"



### File Format Support

**Input Formats:**
- **Images**: .jpg, .jpeg, .png, .webp
- **Descriptions**: Individual .txt files or consolidated .json

**Output Formats:**
- **Individual**: `imagename.txt` per image
- **Consolidated**: `foldername_descriptions.json`
- **Processed Images**: Same format as input, optimized for training

## Advanced Features


**Customize for your needs:**
- Art style analysis
- Character-focused descriptions  
- Technical specifications
- Creative variations

### Tag System Features

**Keyword Tags**: Mark critical tags to always appear first in descriptions
**Tag Scrambling**: Randomize tag order while preserving content:
- Preserve first tag (recommended)
- Fully randomize all tags

**Visual Indicators**:
- 🔴 Red chips = Keyword tags
- 🟢 Green chips = Selected tags
- Right-click chips to set/remove keywords

### Batch Keywords

Add common elements to all descriptions:
1. Enter keyword in "Key Word String" field
2. Press Enter to append to all descriptions
3. Maintains proper spacing automatically

### Image Validation

**Automatically detects and reports:**
- Corrupt or unreadable images
- Images below minimum size (512x512)
- Format compatibility issues

## Architecture

### Modular Design
```
image_gallery/
├── image_gallery.py      # Main application (300 lines)
├── data_manager.py       # Data loading/saving (200 lines)  
├── image_processor.py    # Image processing (400 lines)
├── dialogs.py           # UI dialogs (150 lines)
├── ui_components.py     # UI widgets and layout (800 lines)
├── event_handlers.py    # Event handling logic (500 lines)
├── tag_manager.py       # Tag system management (300 lines)
└── README.md            # Documentation
```

### Key Benefits
- **Clean Separation**: UI, data, and processing logic separated
- **Easy Extension**: Add new features without complexity
- **Robust Error Handling**: Comprehensive validation and reporting
- **Cross-Platform**: Works on Windows, Linux, and WSL

## Keyboard Shortcuts

- **Ctrl + +**: Increase font size
- **Ctrl + -**: Decrease font size
- **Ctrl + 0**: Reset font size to default
- **F5**: Refresh gallery

## Common Workflows

### Small Dataset Expansion
1. Load 10-20 base images with descriptions
2. Use "Create Duplicates" with horizontal flip
3. Optionally add rotations for abstract content
4. Result: 20-80 images with preserved descriptions

### Training Order Randomization
1. Load your dataset with any naming convention
2. Go to Utils → Mass Rename
3. Enter a training-friendly prefix (e.g., "train_")
4. ✅ Enable "Scramble image order"
5. Rename to get randomized training order


### Tag System Migration
1. Load dataset with comma-separated descriptions
2. App automatically converts to tag format
3. Set keyword tags for important subjects
4. Use tag scrambling to create variety

### Dataset Standardization
1. Load mixed-size images
2. Use "Fix Images" with 1024px target
3. Choose square padding for training consistency
4. Export to separate folder for training

## Troubleshooting

### Common Issues

**Images not loading**: Check file permissions and formats
**Description encoding**: Files saved with UTF-8 encoding
**Memory usage**: Close application between large datasets
**WSL networking**: Use Windows host IP instead of localhost
**Scrambling conflicts**: Existing files with same scrambled names

## Best Practices

### Dataset Organization
- Use consistent naming conventions before mass operations
- Keep original images separate from processed versions
- Backup description files before AI processing
- Test operations on small batches first

### Training Optimization
- Use order scrambling for datasets larger than 100 images
- Combine with tag scrambling for maximum variety
- Test training with scrambled vs sequential naming
- Monitor model performance with different orderings

### AI Enhancement
- Always test prompts with sample descriptions
- Review AI output before accepting batch changes
- Keep prompt instructions specific and clear
- Consider different models for different content types

### Performance Tips
- Process images in batches of 50-100 for large datasets
- Use "Selected Only" for targeted operations
- Close other applications during intensive processing
- Save work frequently during long sessions

## What's New

### Version 2.1 - Order Scrambling Update
- **🆕 Image Order Scrambling**: Randomize training order with alpha characters
- **Enhanced Mass Rename**: New checkbox option for scrambling
- **Improved Training Workflows**: Better support for ML training pipelines
- **Conflict Detection**: Prevents naming conflicts during scrambling
- **Progress Feedback**: Real-time status updates during renaming

## Future Enhancements

## Contributing

Contributions welcome! Areas of interest:
- Additional image transformations
- New AI model integrations
- Export format support
- UI/UX improvements
- Performance optimizations
- Training pipeline integrations

## License

Open source under the MIT License.

---

**Built for the AI training community** - streamlining the dataset preparation process with intelligent tools, flexible workflows, and optimized training pipelines.
