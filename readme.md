# Image Gallery with Descriptions

A comprehensive tool for organizing, managing, and auto-generating descriptions for AI training datasets.

![Image Gallery Tool](https://via.placeholder.com/800x450.png?text=Image+Gallery+with+Descriptions)

## Overview

This application helps machine learning practitioners and AI artists manage image datasets by providing intuitive tools for:
- Viewing and organizing collections of images
- Creating and managing text descriptions for each image
- Automatically generating high-quality descriptions using Florence 2 AI
- Preprocessing images to specific dimensions and formats for AI training
- Preserving keywords across descriptions
- Batch operations for efficient dataset management

Perfect for preparing training data for image generation models like Stable Diffusion, DALL-E, and other diffusion models.

## Features

### Image Management
- 📂 Browse and load image collections from any folder
- 🖼️ Preview images with adjustable display size
- 🔍 Navigate through collections with intuitive controls
- 🗑️ Remove images from the dataset with right-click delete

### Description Management
- ✏️ Edit descriptions with real-time updates
- 💾 Auto-save to both individual text files and a consolidated JSON
- 🏷️ Add keywords to all descriptions simultaneously
- 🤖 Generate AI descriptions with Florence 2 vision model
- 🔑 Preserve common keyword prefixes between images

### Image Processing
- 📏 Resize images to standard dimensions (512, 1024, or 2048 pixels)
- 🟦 Create perfect squares with intelligent padding
- 🔄 Maintain aspect ratios if desired
- ✅ Validate images for corrupt files and minimum size
- 📁 Output to a separate folder to preserve originals

### User Interface
- 🎨 Clean, intuitive split-pane interface
- 🔤 Adjustable font sizes with keyboard shortcuts
- 📊 Progress indicators for batch operations
- 📋 Context menu for quick actions
- 🌐 Comprehensive status updates

## Requirements

- Python 3.8 or higher
- Tkinter (usually included with Python)
- PIL/Pillow for image processing
- Florence 2 for AI description generation (optional)

### Dependencies
```bash
pip install pillow
```

For AI-powered descriptions:
```bash
pip install torch transformers
```

## Installation

1. Clone or download this repository
2. Ensure Python and required dependencies are installed
3. Run the script:

```bash
python data_descriptor_exp2.py
```

## Usage Guide

### Basic Operations

#### Loading Images
1. Click "Select Folder" to choose a directory containing images
2. Images will be loaded along with any existing descriptions from .txt files or .json

#### Editing Descriptions
1. Select an image from the list
2. Edit the description in the text area on the right
3. Changes are automatically saved to memory (click "Save Descriptions" to write to disk)

#### Saving Descriptions
1. Click "Save Descriptions" to write all descriptions to:
   - Individual .txt files (one per image)
   - A consolidated JSON file for easy loading

### Image Processing

The "Fix Images" feature prepares your images for AI training by ensuring consistent dimensions and formats.

1. Click "Fix Images"
2. Configure options in the dialog:
   - Target Size: Choose 512, 1024, or 2048 pixels for the longest dimension
   - Aspect Ratio: Make square with padding or keep original aspect ratio
   - Output Folder: Choose where processed images will be saved
3. Click "OK" to process

Images that don't meet validation requirements (minimum 512x512 pixels, not corrupt) will be skipped with detailed error reporting.

### Working with Keywords

To add a common term to all descriptions:

1. Enter the keyword in the "Key Word String" field
2. Press Enter to append it to all descriptions

The system automatically maintains space separation and preserves existing description text.

### Generating AI Descriptions with Florence 2

#### Setup
1. Click "Florence Settings"
2. Browse to select your Florence 2 script location
3. Choose a prompt template:
   - General description (default)
   - Character focus (anatomy, pose, clothing)
   - Art style analysis
   - Environment/scene details
4. Or create a custom prompt
5. Click "Save"

#### Generating Descriptions
1. Click "Generate Descriptions"
2. Choose whether to replace all descriptions or only fill in missing ones
3. Monitor progress in the dialog
4. Review results when complete

#### Keyword Preservation
If all your images share a common keyword at the beginning of their descriptions (e.g., "necronomicon"), this prefix will be automatically detected and preserved when generating new descriptions.

## Florence 2 Integration

### Setting Up Florence 2

This application can integrate with Microsoft's Florence 2 vision model to generate high-quality image descriptions.

1. Install the Florence 2 requirements:
```bash
pip install torch transformers accelerate
```

2. Set up the describe_image.py script (included in this repository)
3. Configure the script path in the Florence Settings dialog

### Customizing Prompts

The quality and focus of generated descriptions can be controlled by customizing the prompt. We provide several templates:

- **General Description**: Broad descriptions of the overall image
- **Character Focus**: Detailed descriptions of characters, focusing on pose, clothing, and appearance
- **Art Style Analysis**: Analysis of artistic techniques, style, and influences
- **Environment/Scene**: Details about the setting, mood, and environment elements

These prompts can significantly improve the relevance of descriptions for your specific needs.

## Keyboard Shortcuts

- **Ctrl++**: Increase font size
- **Ctrl+-**: Decrease font size
- **Ctrl+0**: Reset font size to default

## Troubleshooting

### Image Loading Issues
- Ensure images are in supported formats (.jpg, .jpeg, .png, .webp)
- Check file permissions
- Try with a smaller batch of images first

### Florence 2 Issues
- Verify your Florence script path is correct
- Ensure all dependencies are installed
- Check console output for detailed error messages
- If generation is slow, consider using a GPU for acceleration

### Common Errors
- **"Florence 2 Error"**: Check that your Florence 2 script exists and has the correct permissions
- **"Invalid or corrupt image"**: The image file may be damaged or in an unsupported format
- **"Image too small"**: Images must be at least 512x512 pixels for processing

## Future Improvements

Planned enhancements include:
- Multi-select image operations
- Advanced filtering and sorting
- Batch renaming capabilities
- Integration with other vision models
- Export to various dataset formats
- Cloud storage integration

## Contributing

Contributions are welcome! Feel free to submit pull requests or suggest improvements.

## License

This project is open source and available under the MIT License.

---

*This tool was developed to streamline the process of preparing high-quality datasets for image generation AI models.*