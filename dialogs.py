#!/usr/bin/env python3
"""
Dialog classes for Image Gallery application
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QCheckBox
)


class ImageFixDialog(QDialog):
    """Dialog for configuring image processing options"""
    
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


class ImageDuplicateDialog(QDialog):
    """Dialog for configuring image duplication options"""
    
    def __init__(self, parent=None, initial_input_folder=""):
        super().__init__(parent)
        self.setWindowTitle("Create Image Duplicates")
        self.resize(450, 350)
        
        # Variables - use initial_input_folder parameter
        self.result = None
        self.input_folder = initial_input_folder
        self.output_folder = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Input folder selection
        input_group = QGroupBox("Source Folder")
        input_layout = QHBoxLayout()
        
        self.input_folder_label = QLabel("No folder selected")
        input_browse_button = QPushButton("Browse...")
        input_browse_button.clicked.connect(self.select_input_folder)
        
        # Set initial folder if provided
        if self.input_folder:
            self.input_folder_label.setText(os.path.basename(self.input_folder) or self.input_folder)
        
        input_layout.addWidget(self.input_folder_label, 1)
        input_layout.addWidget(input_browse_button)
        input_group.setLayout(input_layout)
        
        # Output folder selection
        output_group = QGroupBox("Output Folder")
        output_layout = QHBoxLayout()
        
        self.output_folder_label = QLabel("No folder selected")
        output_browse_button = QPushButton("Browse...")
        output_browse_button.clicked.connect(self.select_output_folder)
        
        output_layout.addWidget(self.output_folder_label, 1)
        output_layout.addWidget(output_browse_button)
        output_group.setLayout(output_layout)
        
        # Transformation options
        transform_group = QGroupBox("Transformations to Create")
        transform_layout = QVBoxLayout()
        
        # Add helpful note
        note_label = QLabel("Select transformations, or leave all unchecked to create simple duplicates with '_dup' suffix:")
        note_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        note_label.setWordWrap(True)
        transform_layout.addWidget(note_label)
        
        self.flip_horizontal_cb = QCheckBox("Flip Horizontally")
        self.rotate_90_left_cb = QCheckBox("Rotate 90° Left")
        self.rotate_90_right_cb = QCheckBox("Rotate 90° Right") 
        self.rotate_180_cb = QCheckBox("Rotate 180°")
        
        # Set some defaults
        self.flip_horizontal_cb.setChecked(True)
        
        transform_layout.addWidget(self.flip_horizontal_cb)
        transform_layout.addWidget(self.rotate_90_left_cb)
        transform_layout.addWidget(self.rotate_90_right_cb)
        transform_layout.addWidget(self.rotate_180_cb)
        transform_group.setLayout(transform_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        ok_button = QPushButton("Create Duplicates")
        
        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept_dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        # Add all widgets to main layout
        main_layout.addWidget(input_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(transform_group)
        main_layout.addSpacing(20)
        main_layout.addLayout(button_layout)
        
    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.input_folder = folder
            self.input_folder_label.setText(os.path.basename(folder) or folder)
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(os.path.basename(folder) or folder)
    
    def accept_dialog(self):
        if not self.input_folder:
            QMessageBox.critical(self, "Error", "Please select a source folder")
            return
            
        if not self.output_folder:
            QMessageBox.critical(self, "Error", "Please select an output folder")
            return
            
        # No need to check for transformations - if none selected, we'll just duplicate with "_dup"
            
        self.result = {
            'input_folder': self.input_folder,
            'output_folder': self.output_folder,
            'flip_horizontal': self.flip_horizontal_cb.isChecked(),
            'rotate_90_left': self.rotate_90_left_cb.isChecked(),
            'rotate_90_right': self.rotate_90_right_cb.isChecked(),
            'rotate_180': self.rotate_180_cb.isChecked()
        }
        self.accept()