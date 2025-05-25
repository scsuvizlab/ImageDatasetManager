#!/usr/bin/env python3
"""
Image Gallery with Descriptions - PyQt6 Version
----------------------------------------------
A tool for organizing datasets for image generating AI models.
Supports managing descriptions and fixing image dimensions.
"""

# Force X11 instead of Wayland to avoid display issues
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"
import json
import sys
import shutil
import traceback
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, 
    QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QSplitter,
    QTextEdit, QFileDialog, QMessageBox, QHeaderView, QProgressDialog,
    QDialog, QRadioButton, QButtonGroup, QGroupBox, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QAction, QColor, QFont, QFontMetrics

from PIL import Image


class ImageFixDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fix Images Options")
        self.resize(450, 420)
        
        # Variables
        self.result = None
        self.size = 1024
        self.keep_aspect = False
        self.output_folder = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Size selection
        size_group = QGroupBox("Target Size (longest dimension)")
        size_layout = QVBoxLayout()
        
        self.size_512_radio = QRadioButton("512 pixels")
        self.size_1024_radio = QRadioButton("1024 pixels")
        self.size_2048_radio = QRadioButton("2048 pixels")
        
        # Set initial selection
        self.size_1024_radio.setChecked(True)
        
        size_layout.addWidget(self.size_512_radio)
        size_layout.addWidget(self.size_1024_radio)
        size_layout.addWidget(self.size_2048_radio)
        size_group.setLayout(size_layout)
        
        # Aspect ratio option
        aspect_group = QGroupBox("Aspect Ratio")
        aspect_layout = QVBoxLayout()
        
        self.aspect_square_radio = QRadioButton("Make square (pad with white)")
        self.aspect_original_radio = QRadioButton("Keep original aspect ratio")
        
        # Set initial selection
        self.aspect_square_radio.setChecked(True)
        
        aspect_layout.addWidget(self.aspect_square_radio)
        aspect_layout.addWidget(self.aspect_original_radio)
        aspect_group.setLayout(aspect_layout)
        
        # Output folder selection
        folder_group = QGroupBox("Output Folder")
        folder_layout = QHBoxLayout()
        
        self.folder_label = QLabel("No folder selected")
        folder_browse_button = QPushButton("Browse...")
        folder_browse_button.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(folder_browse_button)
        folder_group.setLayout(folder_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        ok_button = QPushButton("OK")
        
        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept_dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        # Add all widgets to main layout
        main_layout.addWidget(size_group)
        main_layout.addWidget(aspect_group)
        main_layout.addWidget(folder_group)
        main_layout.addSpacing(20)
        main_layout.addLayout(button_layout)
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.folder_label.setText(os.path.basename(folder) or folder)
    
    def accept_dialog(self):
        if not self.output_folder:
            QMessageBox.critical(self, "Error", "Please select an output folder")
            return
            
        # Get selected size
        if self.size_512_radio.isChecked():
            self.size = 512
        elif self.size_1024_radio.isChecked():
            self.size = 1024
        elif self.size_2048_radio.isChecked():
            self.size = 2048
            
        # Get aspect ratio setting
        self.keep_aspect = self.aspect_original_radio.isChecked()
            
        self.result = {
            'size': self.size,
            'keep_aspect': self.keep_aspect,
            'output_folder': self.output_folder
        }
        self.accept()


class ImageGalleryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Gallery with Descriptions")
        self.resize(1200, 800)
        
        # Data storage
        self.images_data = []
        self.current_folder = ""
        self.current_image_index = -1
        
        # Font settings
        self.current_font_size = 14
        self.default_font = QFont("Helvetica", self.current_font_size)
        
        # Set up central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create status bar before setup_ui
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Set up UI
        self.setup_ui()
        
        # Update fonts after UI is set up
        self.update_fonts()
        
    def update_fonts(self):
        """Update all fonts in the application"""
        self.default_font = QFont("Helvetica", self.current_font_size)
        
        # Apply to the whole application
        QApplication.setFont(self.default_font)
        
        # Force update any existing widgets if needed
        if hasattr(self, 'description_text'):
            self.description_text.setFont(self.default_font)
        
        if hasattr(self, 'keyword_entry'):
            self.keyword_entry.setFont(self.default_font)
            
        if hasattr(self, 'table'):
            self.table.setFont(self.default_font)
            
        if hasattr(self, 'status_bar'):
            self.status_bar.setFont(self.default_font)
        
        # Only set status if status_bar exists
        if hasattr(self, 'status_bar'):
            self.set_status(f"Font size changed to {self.current_font_size}")
        
    def increase_font_size(self):
        """Increase the font size in the application"""
        self.current_font_size += 1
        self.update_fonts()
        
    def decrease_font_size(self):
        """Decrease the font size in the application"""
        if self.current_font_size > 6:  # Don't go too small
            self.current_font_size -= 1
            self.update_fonts()
            
    def reset_font_size(self):
        """Reset font size to default"""
        self.current_font_size = 14
        self.update_fonts()
    
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        
        # Control layout (top row buttons and inputs)
        control_layout = QHBoxLayout()
        
        # Left side controls
        self.select_folder_btn = QPushButton("Select Folder")
        self.fix_images_btn = QPushButton("Fix Images")
        
        # Keyword entry
        keyword_label = QLabel("Key Word String:")
        self.keyword_entry = QLineEdit()
        self.keyword_entry.returnPressed.connect(self.append_keywords)
        
        # Save button (right-aligned)
        self.save_btn = QPushButton("Save Descriptions")
        
        # Add to control layout
        control_layout.addWidget(self.select_folder_btn)
        control_layout.addWidget(self.fix_images_btn)
        control_layout.addWidget(keyword_label)
        control_layout.addWidget(self.keyword_entry, 1)  # Stretch
        control_layout.addWidget(self.save_btn)
        
        # Connect button signals
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.fix_images_btn.clicked.connect(self.fix_images)
        self.save_btn.clicked.connect(self.save_descriptions)
        
        # Splitter for table and image view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table for image list
        self.table = QTableWidget(0, 2)  # 0 rows, 2 columns
        self.table.setHorizontalHeaderLabels(["Filename", "Description"])
        
        # Make columns interactive (user-resizable)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        
        # Set initial column widths
        self.table.setColumnWidth(0, 300)  # Filename column
        self.table.setColumnWidth(1, 500)  # Description column
        
        # Make sure the header is visible
        self.table.horizontalHeader().setVisible(True)
        
        # Allow the table to stretch horizontally
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Connect table selection signal
        self.table.itemSelectionChanged.connect(self.on_table_select)
        
        # Add context menu to table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Right side panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        
        # Description editor
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_text = QTextEdit()
        self.description_text.setFont(self.default_font)
        self.description_text.textChanged.connect(self.update_description)
        
        desc_layout.addWidget(self.description_text)
        
        # Add widgets to right panel
        right_layout.addWidget(self.image_label, 1)
        right_layout.addWidget(desc_group)
        
        # Add widgets to splitter
        splitter.addWidget(self.table)
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (50/50)
        splitter.setSizes([600, 600])
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add widgets to main layout
        main_layout.addLayout(control_layout)
        main_layout.addWidget(splitter, 1)  # Stretch
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Ctrl++ to increase font size
        increase_font_action = QAction(self)
        increase_font_action.setShortcut("Ctrl++")
        increase_font_action.triggered.connect(self.increase_font_size)
        self.addAction(increase_font_action)
        
        # Ctrl+- to decrease font size
        decrease_font_action = QAction(self)
        decrease_font_action.setShortcut("Ctrl+-")
        decrease_font_action.triggered.connect(self.decrease_font_size)
        self.addAction(decrease_font_action)
        
        # Ctrl+0 to reset font size
        reset_font_action = QAction(self)
        reset_font_action.setShortcut("Ctrl+0")
        reset_font_action.triggered.connect(self.reset_font_size)
        self.addAction(reset_font_action)
    
    def set_status(self, message):
        """Set status bar message"""
        self.status_bar.showMessage(message)
    
    def select_folder(self):
        """Open file dialog to select a folder with images"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Images")
        
        if not folder_path:
            return
            
        self.current_folder = folder_path
        self.load_images_from_folder(folder_path)
    
    def load_images_from_folder(self, folder_path):
        """Load images and descriptions from the selected folder"""
        # Clear existing data
        self.images_data = []
        self.table.setRowCount(0)
        
        # Support image formats
        image_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        
        # Check for JSON file
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        descriptions_from_json = {}
        
        if json_files:
            try:
                json_path = os.path.join(folder_path, json_files[0])
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                    # Create lookup dictionary
                    for item in json_data:
                        if 'fileName' in item and 'description' in item:
                            descriptions_from_json[item['fileName']] = item['description']
                    self.set_status(f"Loaded descriptions from {json_files[0]}")
            except Exception as e:
                QMessageBox.critical(self, "JSON Error", f"Error loading JSON file: {str(e)}")
        
        # Get all image files
        image_files = [f for f in os.listdir(folder_path) 
                      if os.path.isfile(os.path.join(folder_path, f)) 
                      and f.lower().endswith(image_extensions)]
        
        if not image_files:
            self.set_status("No images found in the selected folder")
            return
            
        # Get text files for descriptions if no JSON
        text_descriptions = {}
        if not descriptions_from_json:
            for img_file in image_files:
                base_name = os.path.splitext(img_file)[0]
                txt_file = f"{base_name}.txt"
                txt_path = os.path.join(folder_path, txt_file)
                
                if os.path.isfile(txt_path):
                    try:
                        with open(txt_path, 'r') as f:
                            text_descriptions[img_file] = f.read()
                    except Exception:
                        pass
        
        # Process image files
        for i, img_file in enumerate(sorted(image_files)):
            img_path = os.path.join(folder_path, img_file)
            
            try:
                # Get description from JSON or text file
                description = ""
                if img_file in descriptions_from_json:
                    description = descriptions_from_json[img_file]
                elif img_file in text_descriptions:
                    description = text_descriptions[img_file]
                
                # Insert into table
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(img_file))
                self.table.setItem(row_position, 1, QTableWidgetItem(description))
                
                # Store image data
                self.images_data.append({
                    'path': img_path,
                    'filename': img_file,
                    'description': description,
                    'row_index': row_position
                })
                
            except Exception as e:
                print(f"Error processing {img_file}: {str(e)}")
        
        if self.images_data:
            # Select first image
            self.table.selectRow(0)
            self.set_status(f"Loaded {len(self.images_data)} images from {os.path.basename(folder_path)}")
    
    def on_table_select(self):
        """Handle table selection change"""
        selected_rows = self.table.selectedItems()
        if selected_rows:
            current_row = self.table.currentRow()
            
            # Find the corresponding image data using row index
            for i, img_data in enumerate(self.images_data):
                if img_data['row_index'] == current_row:
                    self.current_image_index = i
                    self.show_selected_image()
                    break
    
    def show_selected_image(self):
        """Display the currently selected image"""
        if self.current_image_index < 0 or self.current_image_index >= len(self.images_data):
            return
        
        # Get image metadata
        image_metadata = self.images_data[self.current_image_index]
        img_path = image_metadata['path']
        img_description = image_metadata['description']
        
        # Load and display the image
        try:
            # Use PIL to open the image
            pil_img = Image.open(img_path)
            
            # Get label dimensions to resize properly
            label_width = self.image_label.width()
            label_height = self.image_label.height()
            
            # Make sure we have valid dimensions
            if label_width <= 0:
                label_width = 700
            if label_height <= 0:
                label_height = 600
            
            # Calculate new size while preserving aspect ratio
            img_width, img_height = pil_img.size
            ratio = min(label_width/img_width, label_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Resize the PIL image
            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try the direct method first
            try:
                # Save to temporary file and load with QPixmap directly
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                pil_img.save(temp_path)
                pixmap = QPixmap(temp_path)
                self.image_label.setPixmap(pixmap)
                
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
            except Exception as e:
                # If temp file approach fails, try QImage conversion
                print(f"Fallback to QImage method: {str(e)}")
                # Convert to RGB first (safer)
                pil_img = pil_img.convert("RGB")
                
                # Convert PIL image to QImage
                raw_bytes = pil_img.tobytes("raw", "RGB")
                bytes_per_line = 3 * new_width  # 3 bytes per pixel for RGB
                qimg = QImage(raw_bytes, new_width, new_height, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Create pixmap from QImage
                pixmap = QPixmap.fromImage(qimg)
                
                # Display the image
                self.image_label.setPixmap(pixmap)
            
            # Update description text
            self.description_text.blockSignals(True)  # Block signals to prevent recursive updates
            self.description_text.setText(img_description)
            self.description_text.blockSignals(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Image Error", f"Error displaying image: {str(e)}")
            traceback.print_exc()  # Print traceback for debugging
    
    def update_description(self):
        """Update description when user edits text"""
        if self.current_image_index < 0:
            return
        
        # Get the current description
        new_description = self.description_text.toPlainText().strip()
        
        # Update the data
        self.images_data[self.current_image_index]['description'] = new_description
        
        # Update the table
        row = self.images_data[self.current_image_index]['row_index']
        self.table.blockSignals(True)  # Block signals to prevent recursive updates
        self.table.item(row, 1).setText(new_description)
        self.table.blockSignals(False)
    
    def append_keywords(self):
        """Add keyword to all descriptions"""
        keyword = self.keyword_entry.text().strip()
        
        if not keyword or not self.images_data:
            return
        
        for i, img_data in enumerate(self.images_data):
            current_desc = img_data['description']
            separator = ' ' if current_desc else ''
            new_desc = current_desc + separator + keyword
            
            # Update data
            self.images_data[i]['description'] = new_desc
            
            # Update table
            row = img_data['row_index']
            self.table.item(row, 1).setText(new_desc)
        
        # Update current description text if an image is selected
        if self.current_image_index >= 0:
            self.description_text.blockSignals(True)
            self.description_text.setText(self.images_data[self.current_image_index]['description'])
            self.description_text.blockSignals(False)
        
        self.keyword_entry.clear()
        self.set_status(f"Added keyword '{keyword}' to all descriptions")
    
    def save_descriptions(self):
        """Save descriptions to text files and JSON"""
        if not self.images_data:
            QMessageBox.information(self, "No Data", "No images to save descriptions for")
            return
        
        try:
            # Save individual text files
            for img_data in self.images_data:
                base_name = os.path.splitext(img_data['filename'])[0]
                txt_file = f"{base_name}.txt"
                txt_path = os.path.join(self.current_folder, txt_file)
                
                with open(txt_path, 'w') as f:
                    f.write(img_data['description'])
            
            # Save JSON for future loading
            json_data = []
            for img_data in self.images_data:
                json_data.append({
                    'fileName': img_data['filename'],
                    'description': img_data['description']
                })
            
            json_path = os.path.join(self.current_folder, f"{os.path.basename(self.current_folder)}_descriptions.json")
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            self.set_status(f"Saved {len(self.images_data)} descriptions to text files and JSON")
            QMessageBox.information(self, "Save Successful", 
                                  f"Saved {len(self.images_data)} individual text files and descriptions.json")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving descriptions: {str(e)}")
    
    def show_context_menu(self, position):
        """Show context menu for table items"""
        context_menu = QMenu()
        delete_action = context_menu.addAction("Delete")
        
        # Get the action that was selected
        action = context_menu.exec(self.table.mapToGlobal(position))
        
        if action == delete_action:
            self.delete_selected_row()
    
    def delete_selected_row(self):
        """Delete the selected image from the list"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
            
        current_row = self.table.currentRow()
        
        # Find the corresponding image data
        data_index = -1
        for i, img_data in enumerate(self.images_data):
            if img_data['row_index'] == current_row:
                data_index = i
                break
        
        if data_index >= 0:
            if QMessageBox.question(self, "Delete", "Delete selected image from the list?",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                                  
                # Remove from table
                self.table.removeRow(current_row)
                
                # Remove from data
                self.images_data.pop(data_index)
                
                # Update row indices for remaining images
                for i in range(data_index, len(self.images_data)):
                    if self.images_data[i]['row_index'] > current_row:
                        self.images_data[i]['row_index'] -= 1
                
                # Update current_image_index
                if self.current_image_index >= data_index:
                    self.current_image_index = max(-1, self.current_image_index - 1)
                
                # Select next item if available
                if self.images_data:
                    next_row = min(current_row, self.table.rowCount() - 1)
                    if next_row >= 0:
                        self.table.selectRow(next_row)
                    else:
                        # Clear image display if no more images
                        self.image_label.clear()
                        self.description_text.clear()
                        self.current_image_index = -1
                else:
                    # Clear image display if no more images
                    self.image_label.clear()
                    self.description_text.clear()
                    self.current_image_index = -1
    
    def validate_image(self, img_path):
        """Validate that an image is not corrupt and meets minimum size requirements"""
        try:
            with Image.open(img_path) as img:
                # Check if image can be loaded and verify
                img.verify()
                
            # Need to reopen after verify()
            with Image.open(img_path) as img:
                width, height = img.size
                # Check minimum size requirement (512x512)
                if width < 512 or height < 512:
                    return False, f"Image too small: {width}x{height} (minimum 512x512)"
                
            return True, "Valid"
            
        except Exception as e:
            return False, f"Invalid or corrupt image: {str(e)}"
    
    def fix_images(self):
        """Process images with user-selected options"""
        if not self.current_folder:
            QMessageBox.information(self, "No Folder Selected", "Please select a folder with images first.")
            return
            
        # Show options dialog
        dialog = ImageFixDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return  # User cancelled
            
        target_size = dialog.result['size']
        keep_aspect = dialog.result['keep_aspect']
        output_folder = dialog.result['output_folder']
        
        # Get all image files in the current folder
        image_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        image_files = [f for f in os.listdir(self.current_folder) 
                      if os.path.isfile(os.path.join(self.current_folder, f)) 
                      and f.lower().endswith(image_extensions)]
        
        if not image_files:
            QMessageBox.information(self, "No Images", "No images found in the selected folder.")
            return
        
        # Create progress dialog
        progress = QProgressDialog("Processing images...", "Cancel", 0, len(image_files), self)
        progress.setWindowTitle("Fix Images")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Track progress
        total_images = len(image_files)
        processed_images = 0
        skipped_images = 0
        invalid_images = []
        
        # Process each image
        for i, img_file in enumerate(image_files):
            # Update progress
            progress.setValue(i)
            if progress.wasCanceled():
                break
                
            img_path = os.path.join(self.current_folder, img_file)
            
            # Validate image first
            is_valid, validation_message = self.validate_image(img_path)
            if not is_valid:
                invalid_images.append((img_file, validation_message))
                self.set_status(f"Skipping {img_file}: {validation_message}")
                QApplication.processEvents()
                continue
            
            try:
                # Open the image
                img = Image.open(img_path)
                width, height = img.size
                
                # Check if already correct size and format
                is_correct_size = False
                if keep_aspect:
                    # For aspect ratio mode, just check if longest dimension matches
                    is_correct_size = max(width, height) == target_size
                else:
                    # For square mode, check if already square and correct size
                    is_correct_size = (width == height == target_size)
                
                if is_correct_size:
                    # Already good, just copy
                    fixed_img_path = os.path.join(output_folder, img_file)
                    shutil.copy2(img_path, fixed_img_path)
                    skipped_images += 1
                else:
                    # Need to process
                    # Convert to RGB mode if it's not (needed for padding)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    # Determine scaling
                    if width >= height:
                        # Width is longer or equal
                        new_width = target_size
                        new_height = int((height / width) * target_size)
                    else:
                        # Height is longer
                        new_height = target_size
                        new_width = int((width / height) * target_size)
                    
                    # Resize image while maintaining aspect ratio
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    if keep_aspect:
                        # Just save the resized image
                        result_img = img
                    else:
                        # Create a white background for padding
                        padded_img = Image.new('RGB', (target_size, target_size), (255, 255, 255))
                        
                        # Calculate position to paste resized image (center it)
                        paste_x = (target_size - new_width) // 2
                        paste_y = (target_size - new_height) // 2
                        
                        # Paste the resized image onto the padded background
                        padded_img.paste(img, (paste_x, paste_y))
                        result_img = padded_img
                    
                    # Save the processed image
                    fixed_img_path = os.path.join(output_folder, img_file)
                    result_img.save(fixed_img_path, quality=95)
                
                # Copy associated text file if it exists
                base_name = os.path.splitext(img_file)[0]
                txt_file = f"{base_name}.txt"
                txt_path = os.path.join(self.current_folder, txt_file)
                
                if os.path.isfile(txt_path):
                    fixed_txt_path = os.path.join(output_folder, txt_file)
                    shutil.copy2(txt_path, fixed_txt_path)
                
                processed_images += 1
                
                # Update status
                self.set_status(f"Processing images: {processed_images}/{total_images}")
                QApplication.processEvents()
                
            except Exception as e:
                print(f"Error processing {img_file}: {str(e)}")
                invalid_images.append((img_file, str(e)))
        
        # Copy JSON file if it exists
        json_files = [f for f in os.listdir(self.current_folder) if f.endswith('.json')]
        for json_file in json_files:
            src_path = os.path.join(self.current_folder, json_file)
            dst_path = os.path.join(output_folder, json_file)
            try:
                shutil.copy2(src_path, dst_path)
            except Exception as e:
                print(f"Error copying JSON file: {str(e)}")
        
        # Close progress dialog
        progress.setValue(len(image_files))
        
        # Show completion message
        message = f"Processed {processed_images} images.\n"
        message += f"Skipped {skipped_images} images (already correct size).\n"
        if invalid_images:
            message += f"Failed to process {len(invalid_images)} images:\n"
            for img, error in invalid_images[:5]:  # Show first 5 errors
                message += f"  - {img}: {error}\n"
            if len(invalid_images) > 5:
                message += f"  ... and {len(invalid_images) - 5} more\n"
        message += f"Results saved to {output_folder}"
        
        QMessageBox.information(self, "Processing Complete", message)
        
        self.set_status(f"Processed {processed_images} images. Results saved to selected folder.")


def main():
    app = QApplication(sys.argv)
    window = ImageGalleryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()