#!/usr/bin/env python3
"""
Image Gallery with Descriptions - Main Application
-------------------------------------------------
A tool for organizing datasets for image generating AI models.
Supports managing descriptions and dataset augmentation utilities.
"""

# Force X11 instead of Wayland to avoid display issues
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import tempfile
import traceback
import requests
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, 
    QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QSplitter,
    QTextEdit, QFileDialog, QMessageBox, QHeaderView, QStatusBar,
    QTabWidget, QGroupBox, QFrame, QMenu, QDialog, QRadioButton, QButtonGroup,
    QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QAction, QFont

from PIL import Image

# Import our custom modules
from dialogs import ImageFixDialog, ImageDuplicateDialog
from image_processor import ImageProcessor
from data_manager import DataManager


class GalleryTab(QWidget):
    """Main gallery tab for viewing and editing images"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout for gallery tab
        gallery_layout = QVBoxLayout(self)
        
        # Control layout (top row buttons and inputs)
        control_layout = QHBoxLayout()
        
        # Left side controls
        self.select_folder_btn = QPushButton("Select Folder")
        
        # Keyword entry
        keyword_label = QLabel("Key Word String:")
        self.keyword_entry = QLineEdit()
        self.keyword_entry.returnPressed.connect(self.parent.append_keywords)
        
        # Save button (right-aligned)
        self.save_btn = QPushButton("Save Descriptions")
        
        # Add to control layout
        control_layout.addWidget(self.select_folder_btn)
        control_layout.addWidget(keyword_label)
        control_layout.addWidget(self.keyword_entry, 1)  # Stretch
        control_layout.addWidget(self.save_btn)
        
        # Connect button signals
        self.select_folder_btn.clicked.connect(self.parent.select_folder)
        self.save_btn.clicked.connect(self.parent.save_descriptions)
        
        # Splitter for table and image view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table for image list
        self.table = QTableWidget(0, 2)  # 0 rows, 2 columns
        self.table.setHorizontalHeaderLabels(["Filename", "Description"])
        
        # Enable multi-selection
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
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
        self.table.itemSelectionChanged.connect(self.parent.on_table_select)
        
        # Add context menu to table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.parent.show_context_menu)
        
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
        self.description_text.textChanged.connect(self.parent.update_description)
        
        desc_layout.addWidget(self.description_text)
        
        # Add widgets to right panel
        right_layout.addWidget(self.image_label, 1)
        right_layout.addWidget(desc_group)
        
        # Add widgets to splitter
        splitter.addWidget(self.table)
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (50/50)
        splitter.setSizes([600, 600])
        
        # Add widgets to gallery layout
        gallery_layout.addLayout(control_layout)
        gallery_layout.addWidget(splitter, 1)  # Stretch


class UtilsTab(QWidget):
    """Utilities tab for image processing and augmentation"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout for utils tab
        utils_layout = QVBoxLayout(self)
        
        # Selection scope info (very compact)
        self.scope_info_label = QLabel("No images selected")
        self.scope_info_label.setStyleSheet("QLabel { color: #666; font-size: 10px; padding: 2px 6px; margin: 2px; background-color: #f8f8f8; border-radius: 2px; }")
        self.scope_info_label.setMaximumHeight(20)
        utils_layout.addWidget(self.scope_info_label)
        
        # Create horizontal splitter for left/right panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        utils_layout.addWidget(main_splitter)
        
        # Left panel - Existing Image Processing Tools
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Image Processing Section (shrunk)
        processing_group = QGroupBox("Image Processing")
        processing_layout = QVBoxLayout(processing_group)
        
        # Fix Images section (compact)
        fix_section = QGroupBox("Fix Images")
        fix_layout = QVBoxLayout(fix_section)
        
        # Scope selection for Fix Images (horizontal)
        fix_scope_layout = QHBoxLayout()
        self.fix_scope_group = QButtonGroup()
        self.fix_all_radio = QRadioButton("All")
        self.fix_selected_radio = QRadioButton("Selected")
        self.fix_all_radio.setChecked(True)
        
        self.fix_scope_group.addButton(self.fix_all_radio)
        self.fix_scope_group.addButton(self.fix_selected_radio)
        
        fix_scope_layout.addWidget(self.fix_all_radio)
        fix_scope_layout.addWidget(self.fix_selected_radio)
        fix_layout.addLayout(fix_scope_layout)
        
        # Fix Images button (smaller)
        self.fix_images_btn = QPushButton("Fix Images")
        self.fix_images_btn.clicked.connect(self.parent.fix_images)
        fix_layout.addWidget(self.fix_images_btn)
        
        processing_layout.addWidget(fix_section)
        
        # Mass Rename Section (compact)
        rename_section = QGroupBox("Mass Rename")
        rename_layout = QVBoxLayout(rename_section)
        
        # Scope selection for Mass Rename (horizontal)
        rename_scope_layout = QHBoxLayout()
        self.rename_scope_group = QButtonGroup()
        self.rename_all_radio = QRadioButton("All")
        self.rename_selected_radio = QRadioButton("Selected")
        self.rename_all_radio.setChecked(True)
        
        self.rename_scope_group.addButton(self.rename_all_radio)
        self.rename_scope_group.addButton(self.rename_selected_radio)
        
        rename_scope_layout.addWidget(self.rename_all_radio)
        rename_scope_layout.addWidget(self.rename_selected_radio)
        rename_layout.addLayout(rename_scope_layout)
        
        # Prefix input (compact)
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("Prefix:")
        self.prefix_entry = QLineEdit()
        self.prefix_entry.setPlaceholderText("e.g., 'portrait_'")
        
        prefix_layout.addWidget(prefix_label)
        prefix_layout.addWidget(self.prefix_entry, 1)
        rename_layout.addLayout(prefix_layout)
        
        # Rename button (smaller)
        self.mass_rename_btn = QPushButton("Rename Images")
        self.mass_rename_btn.clicked.connect(self.parent.mass_rename_images)
        rename_layout.addWidget(self.mass_rename_btn)
        
        processing_layout.addWidget(rename_section)
        
        # Dataset Augmentation Section (compact)
        augment_section = QGroupBox("Dataset Augmentation")
        augment_layout = QVBoxLayout(augment_section)
        
        # Scope selection for Duplicates (horizontal)
        dup_scope_layout = QHBoxLayout()
        self.dup_scope_group = QButtonGroup()
        self.dup_all_radio = QRadioButton("All")
        self.dup_selected_radio = QRadioButton("Selected")
        self.dup_all_radio.setChecked(True)
        
        self.dup_scope_group.addButton(self.dup_all_radio)
        self.dup_scope_group.addButton(self.dup_selected_radio)
        
        dup_scope_layout.addWidget(self.dup_all_radio)
        dup_scope_layout.addWidget(self.dup_selected_radio)
        augment_layout.addLayout(dup_scope_layout)
        
        # Create Duplicates button (smaller)
        self.create_duplicates_btn = QPushButton("Create Duplicates")
        self.create_duplicates_btn.clicked.connect(self.parent.create_duplicates)
        augment_layout.addWidget(self.create_duplicates_btn)
        
        processing_layout.addWidget(augment_section)
        
        # Add processing group to left layout
        left_layout.addWidget(processing_group)
        left_layout.addStretch()
        
        # Right panel - LLama Integration
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # LLama Section
        llama_group = QGroupBox("LLama Description Rephrasing")
        llama_layout = QVBoxLayout(llama_group)
        
        # Scope selection for LLama
        llama_scope_layout = QHBoxLayout()
        self.llama_scope_group = QButtonGroup()
        self.llama_all_radio = QRadioButton("Rephrase All Descriptions")
        self.llama_selected_radio = QRadioButton("Rephrase Selected Only")
        self.llama_all_radio.setChecked(True)
        
        self.llama_scope_group.addButton(self.llama_all_radio)
        self.llama_scope_group.addButton(self.llama_selected_radio)
        
        llama_scope_layout.addWidget(self.llama_all_radio)
        llama_scope_layout.addWidget(self.llama_selected_radio)
        llama_layout.addLayout(llama_scope_layout)
        
        # Server configuration
        server_layout = QHBoxLayout()
        server_label = QLabel("Server:")
        self.host_entry = QLineEdit()
        self.host_entry.setText("172.23.64.1")  # WSL to Windows host IP
        self.host_entry.setPlaceholderText("localhost or IP")
        self.host_entry.setMaximumWidth(120)
        
        # Port configuration
        port_label = QLabel("Port:")
        self.port_entry = QLineEdit()
        self.port_entry.setText("11434")  # Default oLLama port
        self.port_entry.setMaximumWidth(80)
        
        self.refresh_models_btn = QPushButton("Refresh Models")
        self.refresh_models_btn.clicked.connect(self.parent.refresh_ollama_models)
        
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.host_entry)
        server_layout.addWidget(port_label)
        server_layout.addWidget(self.port_entry)
        server_layout.addWidget(self.refresh_models_btn)
        llama_layout.addLayout(server_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_combo = QLineEdit()
        self.model_combo.setPlaceholderText("e.g., llama3.2:3b")
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo, 1)
        llama_layout.addLayout(model_layout)
        
        # Available models display
        self.available_models_label = QLabel("Available models: (Click Refresh Models)")
        self.available_models_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        self.available_models_label.setWordWrap(True)
        llama_layout.addWidget(self.available_models_label)
        
        # Prompt configuration
        prompt_label = QLabel("Rephrasing Prompt:")
        llama_layout.addWidget(prompt_label)
        
        self.llama_prompt = QTextEdit()
        self.llama_prompt.setMaximumHeight(120)
        self.llama_prompt.setPlainText(
            "Rephrase the following image description. Keep all specific names, details, and technical terms exactly the same. "
            "Only change the phrasing and sentence structure to make it sound different while preserving all information. "
            "Return only the rephrased description with no additional text:\n\n{description}"
        )
        llama_layout.addWidget(self.llama_prompt)
        
        # Test section
        test_layout = QHBoxLayout()
        self.test_description_entry = QLineEdit()
        self.test_description_entry.setPlaceholderText("Test description here...")
        self.test_rephrase_btn = QPushButton("Test Rephrase")
        self.test_rephrase_btn.clicked.connect(self.parent.test_ollama_rephrase)
        
        test_layout.addWidget(QLabel("Test:"))
        test_layout.addWidget(self.test_description_entry, 1)
        test_layout.addWidget(self.test_rephrase_btn)
        llama_layout.addLayout(test_layout)
        
        # Test result
        self.test_result_label = QLabel("")
        self.test_result_label.setWordWrap(True)
        self.test_result_label.setStyleSheet("QLabel { padding: 5px; background-color: #f9f9f9; border: 1px solid #ddd; }")
        llama_layout.addWidget(self.test_result_label)
        
        # Rephrase button
        self.rephrase_descriptions_btn = QPushButton("Rephrase Descriptions")
        self.rephrase_descriptions_btn.clicked.connect(self.parent.rephrase_descriptions)
        llama_layout.addWidget(self.rephrase_descriptions_btn)
        
        # Add llama group to right layout
        right_layout.addWidget(llama_group)
        right_layout.addStretch()
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (40% left, 60% right)
        main_splitter.setSizes([400, 600])
    
    def update_scope_info(self, selected_count, total_count):
        """Update the scope information display"""
        if selected_count == 0:
            self.scope_info_label.setText(f"No selection • {total_count} images total")
            self.scope_info_label.setStyleSheet("QLabel { color: #666; font-size: 10px; padding: 2px 6px; margin: 2px; background-color: #f8f8f8; border-radius: 2px; }")
            
            # Disable "selected only" options when nothing is selected
            self.fix_selected_radio.setEnabled(False)
            self.rename_selected_radio.setEnabled(False)
            self.dup_selected_radio.setEnabled(False)
            self.llama_selected_radio.setEnabled(False)
            
        elif selected_count == total_count:
            self.scope_info_label.setText(f"All {total_count} images selected")
            self.scope_info_label.setStyleSheet("QLabel { color: #0066cc; font-size: 10px; padding: 2px 6px; margin: 2px; background-color: #e6f3ff; border-radius: 2px; }")
            
            # Enable "selected only" options
            self.fix_selected_radio.setEnabled(True)
            self.rename_selected_radio.setEnabled(True)
            self.dup_selected_radio.setEnabled(True)
            self.llama_selected_radio.setEnabled(True)
            
        else:
            self.scope_info_label.setText(f"{selected_count} of {total_count} selected")
            self.scope_info_label.setStyleSheet("QLabel { color: #009900; font-size: 10px; padding: 2px 6px; margin: 2px; background-color: #e6ffe6; border-radius: 2px; }")
            
            # Enable "selected only" options
            self.fix_selected_radio.setEnabled(True)
            self.rename_selected_radio.setEnabled(True)
            self.dup_selected_radio.setEnabled(True)
            self.llama_selected_radio.setEnabled(True)


class ImageGalleryApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Gallery with Descriptions")
        self.resize(1200, 800)
        
        # Initialize components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor(self)
        self.current_image_index = -1
        
        # Font settings
        self.current_font_size = 14
        self.default_font = QFont("Helvetica", self.current_font_size)
        
        # Set up UI
        self.setup_ui()
        self.update_fonts()
        
    def setup_ui(self):
        # Set up central widget with tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main layout for central widget
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.gallery_tab = GalleryTab(self)
        self.utils_tab = UtilsTab(self)
        
        self.tab_widget.addTab(self.gallery_tab, "Gallery")
        self.tab_widget.addTab(self.utils_tab, "Utils")
        
        # Initially disable Utils tab until images are loaded
        self.tab_widget.setTabEnabled(1, False)  # Utils tab is index 1
        
        # Set initial status
        self.set_status("Select a folder with images to begin • Utils will be available after loading images")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Font size shortcuts
        increase_font_action = QAction(self)
        increase_font_action.setShortcut("Ctrl++")
        increase_font_action.triggered.connect(self.increase_font_size)
        self.addAction(increase_font_action)
        
        decrease_font_action = QAction(self)
        decrease_font_action.setShortcut("Ctrl+-")
        decrease_font_action.triggered.connect(self.decrease_font_size)
        self.addAction(decrease_font_action)
        
        reset_font_action = QAction(self)
        reset_font_action.setShortcut("Ctrl+0")
        reset_font_action.triggered.connect(self.reset_font_size)
        self.addAction(reset_font_action)
    
    def update_fonts(self):
        """Update all fonts in the application"""
        self.default_font = QFont("Helvetica", self.current_font_size)
        QApplication.setFont(self.default_font)
        
        # Update specific widgets if they exist
        if hasattr(self.gallery_tab, 'description_text'):
            self.gallery_tab.description_text.setFont(self.default_font)
        
        self.set_status(f"Font size: {self.current_font_size}")
        
    def increase_font_size(self):
        self.current_font_size += 1
        self.update_fonts()
        
    def decrease_font_size(self):
        if self.current_font_size > 6:
            self.current_font_size -= 1
            self.update_fonts()
            
    def reset_font_size(self):
        self.current_font_size = 14
        self.update_fonts()
    
    def set_status(self, message):
        """Set status bar message"""
        self.status_bar.showMessage(message)
    
    def select_folder(self):
        """Open file dialog to select a folder with images"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Images")
        
        if not folder_path:
            return
            
        success, message, images_data = self.data_manager.load_images_from_folder(folder_path)
        
        if success:
            self.populate_table(images_data)
            # Select first image if available
            if images_data:
                self.gallery_tab.table.selectRow(0)
            
            # Enable Utils tab now that we have images loaded
            self.tab_widget.setTabEnabled(1, True)
            self.set_status(f"{message} • Utils tab now available")
            
        else:
            QMessageBox.critical(self, "Load Error", message)
    
    def populate_table(self, images_data):
        """Populate the table with image data"""
        table = self.gallery_tab.table
        table.setRowCount(0)  # Clear existing data
        
        for i, img_data in enumerate(images_data):
            row_position = table.rowCount()
            table.insertRow(row_position)
            table.setItem(row_position, 0, QTableWidgetItem(img_data['filename']))
            table.setItem(row_position, 1, QTableWidgetItem(img_data['description']))
            
            # Update row index in data
            img_data['row_index'] = row_position
        
        # Update utils tab scope info
        self.utils_tab.update_scope_info(0, len(images_data))
    
    def on_table_select(self):
        """Handle table selection change"""
        selected_rows = self.gallery_tab.table.selectionModel().selectedRows()
        
        # Update utils tab scope info
        total_images = len(self.data_manager.images_data)
        selected_count = len(selected_rows)
        self.utils_tab.update_scope_info(selected_count, total_images)
        
        if not selected_rows:
            # No selection
            self.current_image_index = -1
            self._clear_image_display()
            self.set_status("No images selected")
            return
        
        # Update status with selection count
        if len(selected_rows) == 1:
            # Single selection - show the image
            row = selected_rows[0].row()
            index, img_data = self.data_manager.find_image_by_row_index(row)
            if index >= 0:
                self.current_image_index = index
                self.show_selected_image()
                self.set_status(f"Selected: {img_data['filename']}")
        else:
            # Multiple selection - show info but no specific image
            self.current_image_index = -1
            self._show_multiple_selection_display(len(selected_rows))
            self.set_status(f"{len(selected_rows)} images selected")
    
    def _show_multiple_selection_display(self, count):
        """Display info when multiple images are selected"""
        self.gallery_tab.image_label.clear()
        self.gallery_tab.image_label.setText(f"📋 {count} images selected\n\nUse Utils tab to perform\noperations on selection")
        self.gallery_tab.image_label.setStyleSheet("QLabel { color: #666; font-size: 14px; }")
        
        # Disable description editing for multiple selection
        self.gallery_tab.description_text.blockSignals(True)
        self.gallery_tab.description_text.setText("Multiple images selected - description editing disabled")
        self.gallery_tab.description_text.setEnabled(False)
        self.gallery_tab.description_text.blockSignals(False)
    
    def get_selected_images(self):
        """Get list of selected image data"""
        selected_rows = self.gallery_tab.table.selectionModel().selectedRows()
        selected_images = []
        
        for row_model in selected_rows:
            row = row_model.row()
            index, img_data = self.data_manager.find_image_by_row_index(row)
            if index >= 0:
                selected_images.append(img_data)
        
        return selected_images
    
    def show_selected_image(self):
        """Display the currently selected image"""
        img_data = self.data_manager.get_image_data(self.current_image_index)
        if not img_data:
            return
        
        img_path = img_data['path']
        img_description = img_data['description']
        
        try:
            # Load and display the image
            pil_img = Image.open(img_path)
            
            # Get label dimensions for resizing
            image_label = self.gallery_tab.image_label
            # Reset any styling from multi-selection display
            image_label.setStyleSheet("")
            label_width = image_label.width() or 700
            label_height = image_label.height() or 600
            
            # Calculate new size while preserving aspect ratio
            img_width, img_height = pil_img.size
            ratio = min(label_width/img_width, label_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Resize the PIL image
            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert and display
            self._display_pil_image(pil_img, image_label)
            
            # Update description text and re-enable editing
            desc_text = self.gallery_tab.description_text
            desc_text.setEnabled(True)
            desc_text.blockSignals(True)
            desc_text.setText(img_description)
            desc_text.blockSignals(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Image Error", f"Error displaying image: {str(e)}")
            traceback.print_exc()
    
    def _display_pil_image(self, pil_img, label):
        """Helper method to display PIL image in QLabel"""
        try:
            # Try saving to temp file first (more reliable)
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            pil_img.save(temp_path)
            pixmap = QPixmap(temp_path)
            label.setPixmap(pixmap)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            # Fallback to direct conversion
            pil_img = pil_img.convert("RGB")
            width, height = pil_img.size
            raw_bytes = pil_img.tobytes("raw", "RGB")
            bytes_per_line = 3 * width
            qimg = QImage(raw_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            label.setPixmap(pixmap)
    
    def update_description(self):
        """Update description when user edits text"""
        if self.current_image_index < 0:
            return
        
        new_description = self.gallery_tab.description_text.toPlainText().strip()
        
        # Update in data manager
        if self.data_manager.update_description(self.current_image_index, new_description):
            # Update the table
            img_data = self.data_manager.get_image_data(self.current_image_index)
            if img_data:
                row = img_data['row_index']
                self.gallery_tab.table.blockSignals(True)
                self.gallery_tab.table.item(row, 1).setText(new_description)
                self.gallery_tab.table.blockSignals(False)
    
    def append_keywords(self):
        """Add keyword to all descriptions"""
        keyword = self.gallery_tab.keyword_entry.text().strip()
        if not keyword:
            return
        
        updated_count = self.data_manager.append_keyword_to_all(keyword)
        
        if updated_count > 0:
            # Refresh the table
            self.populate_table(self.data_manager.images_data)
            
            # Update current description text if an image is selected
            if self.current_image_index >= 0:
                img_data = self.data_manager.get_image_data(self.current_image_index)
                if img_data:
                    desc_text = self.gallery_tab.description_text
                    desc_text.blockSignals(True)
                    desc_text.setText(img_data['description'])
                    desc_text.blockSignals(False)
        
        self.gallery_tab.keyword_entry.clear()
        self.set_status(f"Added keyword '{keyword}' to {updated_count} descriptions")
    
    def save_descriptions(self):
        """Save descriptions to text files and JSON"""
        success, message = self.data_manager.save_descriptions()
        
        if success:
            self.set_status(message)
            QMessageBox.information(self, "Save Successful", message)
        else:
            QMessageBox.critical(self, "Save Error", message)
    
    def show_context_menu(self, position):
        """Show context menu for table items"""
        context_menu = QMenu()
        delete_action = context_menu.addAction("Delete")
        
        action = context_menu.exec(self.gallery_tab.table.mapToGlobal(position))
        
        if action == delete_action:
            self.delete_selected_row()
    
    def delete_selected_row(self):
        """Delete the selected image from the list"""
        current_row = self.gallery_tab.table.currentRow()
        if current_row < 0:
            return
        
        # Find the corresponding image data
        index, img_data = self.data_manager.find_image_by_row_index(current_row)
        if index < 0:
            return
        
        if QMessageBox.question(self, "Delete", "Delete selected image from the list?",
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            
            # Remove from data manager
            self.data_manager.remove_image(index)
            
            # Refresh table
            self.populate_table(self.data_manager.images_data)
            
            # Update current selection
            if self.current_image_index >= index:
                self.current_image_index = max(-1, self.current_image_index - 1)
            
            # Select next item if available
            if self.data_manager.images_data:
                next_row = min(current_row, len(self.data_manager.images_data) - 1)
                if next_row >= 0:
                    self.gallery_tab.table.selectRow(next_row)
                else:
                    self._clear_image_display()
            else:
                # No more images - disable Utils tab and clear display
                self.tab_widget.setTabEnabled(1, False)
                self._clear_image_display()
                self.set_status("No images remaining • Utils tab disabled")
    
    def _clear_image_display(self):
        """Clear the image display and description"""
        self.gallery_tab.image_label.clear()
        self.gallery_tab.description_text.clear()
        self.current_image_index = -1
    
    def refresh_gallery(self):
        """Refresh the gallery by reloading images from the current folder"""
        if not self.data_manager.current_folder:
            return
            
        # Remember current selection
        current_filename = None
        if self.current_image_index >= 0:
            img_data = self.data_manager.get_image_data(self.current_image_index)
            if img_data:
                current_filename = img_data['filename']
        
        # Reload images
        success, message, images_data = self.data_manager.load_images_from_folder(
            self.data_manager.current_folder
        )
        
        if success:
            self.populate_table(images_data)
            
            # Try to restore selection to the same image
            if current_filename:
                for i, img_data in enumerate(images_data):
                    if img_data['filename'] == current_filename:
                        self.gallery_tab.table.selectRow(i)
                        break
                else:
                    # Original image not found, select first item
                    if images_data:
                        self.gallery_tab.table.selectRow(0)
            else:
                # No previous selection, select first item
                if images_data:
                    self.gallery_tab.table.selectRow(0)
            
            self.set_status(f"Gallery refreshed • {message}")
        else:
            QMessageBox.warning(self, "Refresh Error", f"Could not refresh gallery: {message}")
    
    def fix_images(self):
        """Process images with user-selected options"""
        dialog = ImageFixDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        # Get source folder - suggest current folder as default
        current_folder = self.data_manager.current_folder
        if current_folder:
            # Start dialog in the current folder
            source_folder = QFileDialog.getExistingDirectory(
                self, 
                "Select Source Folder with Images", 
                current_folder
            )
        else:
            source_folder = QFileDialog.getExistingDirectory(self, "Select Source Folder with Images")
            
        if not source_folder:
            return
        
        options = dialog.result
        
        # Process images
        result = self.image_processor.fix_images(
            source_folder=source_folder,
            target_size=options['size'],
            keep_aspect=options['keep_aspect'],
            output_folder=options['output_folder'],
            status_callback=self.set_status
        )
        
        if 'error' in result:
            QMessageBox.information(self, "No Images", result['error'])
            return
        
        # Show completion message
        message = f"Processed {result['processed']} images.\n"
        message += f"Skipped {result['skipped']} images (already correct size).\n"
        if result['invalid']:
            message += f"Failed to process {len(result['invalid'])} images:\n"
            for img, error in result['invalid'][:5]:
                message += f"  - {img}: {error}\n"
            if len(result['invalid']) > 5:
                message += f"  ... and {len(result['invalid']) - 5} more\n"
        message += f"Results saved to {options['output_folder']}"
        
        QMessageBox.information(self, "Processing Complete", message)
        self.set_status(f"Processed {result['processed']} images")
    
    def create_duplicates(self):
        """Create duplicated images with transformations"""
        # Pass the current folder as the default input folder
        current_folder = self.data_manager.current_folder
        dialog = ImageDuplicateDialog(self, initial_input_folder=current_folder)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        options = dialog.result
        
        # Determine which images to process based on radio button selection
        if self.utils_tab.dup_selected_radio.isChecked():
            # Process only selected images
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self, "No Selection", "No images are selected. Please select images first or choose 'Duplicate All Images'.")
                return
            # Convert to simple filenames list for the processor
            images_to_process = [img_data['filename'] for img_data in selected_images]
        else:
            # Process all images - let the processor handle it
            images_to_process = None
        
        # Process duplicates
        result = self.image_processor.create_duplicates(
            input_folder=options['input_folder'],
            output_folder=options['output_folder'],
            transformations=options,
            images_to_process=images_to_process,
            status_callback=self.set_status
        )
        
        if 'error' in result:
            QMessageBox.information(self, "No Images", result['error'])
            return
        
        # Show completion message
        if result.get('same_folder'):
            message = f"Created {result['created_files']} duplicate images in the same folder.\n"
        else:
            message = f"Created {result['created_files']} files (originals + duplicates).\n"
        
        # Check if this was simple duplication or transformations
        if not any([options['flip_horizontal'], options['rotate_90_left'], options['rotate_90_right'], options['rotate_180']]):
            message += f"Simple duplicates created (no transformations) for {result['original_images']} images.\n"
        else:
            message += f"Applied {result['transformations']} transformation(s) to {result['original_images']} images.\n"
            
        if result['errors']:
            message += f"\nEncountered {len(result['errors'])} errors:\n"
            for error in result['errors'][:3]:
                message += f"  - {error}\n"
            if len(result['errors']) > 3:
                message += f"  ... and {len(result['errors']) - 3} more\n"
        message += f"\nResults saved to {options['output_folder']}"
        
        QMessageBox.information(self, "Duplication Complete", message)
        self.set_status(f"Created {result['created_files']} files with transformations")
        
        # Refresh gallery if we're working in the same folder
        if options['output_folder'] == self.data_manager.current_folder:
            self.refresh_gallery()
    
    def refresh_ollama_models(self):
        """Refresh the list of available oLLama models"""
        host = self.utils_tab.host_entry.text().strip() or "localhost"
        port = self.utils_tab.port_entry.text().strip() or "11434"
        base_url = f"http://{host}:{port}"
        
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                if models:
                    models_text = ", ".join(models)
                    self.utils_tab.available_models_label.setText(f"Available models: {models_text}")
                    # Set first model as default if combo is empty
                    if not self.utils_tab.model_combo.text().strip():
                        self.utils_tab.model_combo.setText(models[0])
                    self.set_status(f"Found {len(models)} oLLama models at {host}:{port}")
                else:
                    self.utils_tab.available_models_label.setText("No models found. Make sure oLLama is running with models installed.")
                    self.set_status("No oLLama models found")
            else:
                raise Exception(f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.utils_tab.available_models_label.setText(f"Cannot connect to oLLama at {host}:{port}. Check server address and make sure oLLama is running.")
            QMessageBox.warning(self, "Connection Error", f"Cannot connect to oLLama at {host}:{port}.\n\nFor WSL users:\n- Use Windows host IP instead of localhost\n- Try: ip route | grep default\n\nMake sure oLLama is running:\n1. Check: ollama serve\n2. Install a model: ollama pull llama3.2:3b")
            self.set_status(f"Cannot connect to oLLama at {host}:{port}")
        except Exception as e:
            self.utils_tab.available_models_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error getting oLLama models: {str(e)}")
            self.set_status(f"oLLama error: {str(e)}")
    
    def test_ollama_rephrase(self):
        """Test rephrasing with a single description"""
        test_description = self.utils_tab.test_description_entry.text().strip()
        if not test_description:
            QMessageBox.information(self, "No Test Text", "Please enter a test description to rephrase.")
            return
        
        model = self.utils_tab.model_combo.text().strip()
        if not model:
            QMessageBox.information(self, "No Model", "Please specify an oLLama model name.")
            return
        
        self.utils_tab.test_result_label.setText("Testing... please wait")
        QApplication.processEvents()
        
        try:
            result = self._rephrase_with_ollama(test_description, model)
            if result:
                self.utils_tab.test_result_label.setText(f"Rephrased: {result}")
                self.set_status("Test rephrasing successful")
            else:
                self.utils_tab.test_result_label.setText("Error: No response from oLLama")
                self.set_status("Test rephrasing failed")
        except Exception as e:
            self.utils_tab.test_result_label.setText(f"Error: {str(e)}")
            self.set_status(f"Test rephrasing error: {str(e)}")
    
    def rephrase_descriptions(self):
        """Rephrase descriptions using oLLama"""
        if not self.data_manager.images_data:
            QMessageBox.information(self, "No Images", "Please load images in the Gallery tab first.")
            return
        
        model = self.utils_tab.model_combo.text().strip()
        if not model:
            QMessageBox.information(self, "No Model", "Please specify an oLLama model name.")
            return
        
        # Determine which images to process
        if self.utils_tab.llama_selected_radio.isChecked():
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self, "No Selection", "No images are selected. Please select images first or choose 'Rephrase All Descriptions'.")
                return
            images_to_process = selected_images
            scope_text = f"{len(selected_images)} selected images"
        else:
            images_to_process = self.data_manager.images_data
            scope_text = f"all {len(self.data_manager.images_data)} images"
        
        # Filter to only images that have descriptions
        images_with_descriptions = [img for img in images_to_process if img['description'].strip()]
        
        if not images_with_descriptions:
            QMessageBox.information(self, "No Descriptions", "No images have descriptions to rephrase.")
            return
        
        # Confirm with user
        confirm_msg = f"This will rephrase descriptions for {len(images_with_descriptions)} images (out of {scope_text}).\n\n"
        confirm_msg += f"Using model: {model}\n\n"
        confirm_msg += "This operation will replace existing descriptions. Continue?"
        
        reply = QMessageBox.question(
            self, "Confirm Rephrasing", confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create progress dialog
        progress = QProgressDialog("Rephrasing descriptions...", "Cancel", 0, len(images_with_descriptions), self)
        progress.setWindowTitle("oLLama Rephrasing")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        rephrased_count = 0
        error_count = 0
        errors = []
        
        # Process each image
        for i, img_data in enumerate(images_with_descriptions):
            if progress.wasCanceled():
                break
            
            progress.setValue(i)
            progress.setLabelText(f"Rephrasing {img_data['filename']}...")
            QApplication.processEvents()
            
            try:
                original_description = img_data['description']
                rephrased = self._rephrase_with_ollama(original_description, model)
                
                if rephrased and rephrased.strip():
                    # Update the description in data manager
                    img_index = self.data_manager.images_data.index(img_data)
                    self.data_manager.update_description(img_index, rephrased.strip())
                    
                    # Update the table
                    row = img_data['row_index']
                    self.gallery_tab.table.blockSignals(True)
                    self.gallery_tab.table.item(row, 1).setText(rephrased.strip())
                    self.gallery_tab.table.blockSignals(False)
                    
                    rephrased_count += 1
                else:
                    error_count += 1
                    errors.append(f"{img_data['filename']}: No response from oLLama")
                
            except Exception as e:
                error_count += 1
                error_msg = f"{img_data['filename']}: {str(e)}"
                errors.append(error_msg)
                print(f"Error rephrasing {img_data['filename']}: {str(e)}")
        
        progress.close()
        progress.deleteLater()
        
        # Show completion message
        message = f"Rephrasing complete!\n\n"
        message += f"Successfully rephrased: {rephrased_count} descriptions\n"
        if error_count > 0:
            message += f"Errors: {error_count}\n"
            if errors:
                message += f"First few errors:\n"
                for error in errors[:3]:
                    message += f"  - {error}\n"
                if len(errors) > 3:
                    message += f"  ... and {len(errors) - 3} more\n"
        
        QMessageBox.information(self, "Rephrasing Complete", message)
        self.set_status(f"Rephrased {rephrased_count} descriptions using {model}")
        
        # Update current description display if needed
        if self.current_image_index >= 0:
            img_data = self.data_manager.get_image_data(self.current_image_index)
            if img_data:
                desc_text = self.gallery_tab.description_text
                desc_text.blockSignals(True)
                desc_text.setText(img_data['description'])
                desc_text.blockSignals(False)
    
    def _rephrase_with_ollama(self, description, model):
        """Send description to oLLama for rephrasing"""
        host = self.utils_tab.host_entry.text().strip() or "localhost"
        port = self.utils_tab.port_entry.text().strip() or "11434"
        base_url = f"http://{host}:{port}"
        
        prompt_template = self.utils_tab.llama_prompt.toPlainText()
        full_prompt = prompt_template.replace("{description}", description)
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request timed out (30s). Try a smaller model or check oLLama status.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to oLLama at {host}:{port}. Make sure it's running.")
        except Exception as e:
            raise Exception(f"oLLama error: {str(e)}")
    
    def mass_rename_images(self):
        """Rename images in the gallery folder with new prefix + numbers"""
        if not self.data_manager.current_folder:
            QMessageBox.information(self, "No Folder", "Please load images in the Gallery tab first.")
            return
            
        if not self.data_manager.images_data:
            QMessageBox.information(self, "No Images", "No images loaded to rename.")
            return
        
        # Get prefix from user
        prefix = self.utils_tab.prefix_entry.text().strip()
        if not prefix:
            QMessageBox.critical(self, "No Prefix", "Please enter a prefix for the new filenames.")
            return
        
        # Determine which images to process based on radio button selection
        if self.utils_tab.rename_selected_radio.isChecked():
            # Process only selected images
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self, "No Selection", "No images are selected. Please select images first or choose 'Rename All Images'.")
                return
            images_to_process = selected_images
            scope_text = f"{len(selected_images)} selected images"
        else:
            # Process all images
            images_to_process = self.data_manager.images_data
            scope_text = f"all {len(self.data_manager.images_data)} images"
        
        # Confirm with user
        confirm_msg = f"This will rename {scope_text} to:\n"
        confirm_msg += f"{prefix}001, {prefix}002, {prefix}003, etc.\n\n"
        confirm_msg += "Description files will also be renamed to match.\n"
        confirm_msg += "This operation cannot be undone. Continue?"
        
        reply = QMessageBox.question(
            self, "Confirm Mass Rename", confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform the rename operation
        result = self.image_processor.mass_rename_images(
            folder_path=self.data_manager.current_folder,
            prefix=prefix,
            images_to_process=images_to_process,
            status_callback=self.set_status
        )
        
        if 'error' in result:
            QMessageBox.critical(self, "Rename Error", result['error'])
            return
        
        # Show completion message
        message = f"Successfully renamed {result['renamed_images']} images and {result['renamed_descriptions']} description files.\n"
        if result['errors']:
            message += f"\nEncountered {len(result['errors'])} errors:\n"
            for error in result['errors'][:3]:
                message += f"  - {error}\n"
            if len(result['errors']) > 3:
                message += f"  ... and {len(result['errors']) - 3} more\n"
        
        QMessageBox.information(self, "Rename Complete", message)
        self.set_status(f"Renamed {result['renamed_images']} images with prefix '{prefix}'")
        
        # Clear the prefix field for next use
        self.utils_tab.prefix_entry.clear()
        
        # Refresh gallery to show new names
        self.refresh_gallery()


def main():
    app = QApplication(sys.argv)
    window = ImageGalleryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()