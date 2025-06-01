#!/usr/bin/env python3
"""
Image Gallery with Descriptions - Main Application
-------------------------------------------------
A tool for organizing datasets for image generating AI models.
Supports managing descriptions and dataset augmentation utilities.

Refactored version with modular architecture.
"""

# Force X11 instead of Wayland to avoid display issues
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QStatusBar, QTabWidget
)
from PyQt6.QtGui import QAction, QFont

# Import our custom modules
from ui_components import GalleryTab, UtilsTab
from event_handlers import EventHandlers
from data_manager import DataManager
from image_processor import ImageProcessor
from tag_manager import TagManager


class ImageGalleryApp(QMainWindow):
    """Main application window - coordinates between modules"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Gallery with Descriptions")
        self.resize(1200, 800)
        
        # Initialize core components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor(self)
        self.tag_manager = TagManager()  # For future tag system
        self.current_image_index = -1
        
        # Initialize event handlers (after other components)
        self.event_handlers = EventHandlers(self)
        
        # Font settings
        self.current_font_size = 14
        self.default_font = QFont("Helvetica", self.current_font_size)
        
        # Set up UI
        self.setup_ui()
        self.setup_shortcuts()
        self.update_fonts()
        
    def setup_ui(self):
        """Set up the main UI structure"""
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
        
        # Create tabs (pass self so they can access the main app)
        self.gallery_tab = GalleryTab(self)
        self.utils_tab = UtilsTab(self)
        
        self.tab_widget.addTab(self.gallery_tab, "Gallery")
        self.tab_widget.addTab(self.utils_tab, "Utils")
        
        # Initially disable Utils tab until images are loaded
        self.tab_widget.setTabEnabled(1, False)  # Utils tab is index 1
        
        # Set initial status
        self.set_status("Select a folder with images to begin • Utils will be available after loading images • Tag system enabled")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
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
        """Increase font size"""
        self.current_font_size += 1
        self.update_fonts()
        
    def decrease_font_size(self):
        """Decrease font size"""
        if self.current_font_size > 6:
            self.current_font_size -= 1
            self.update_fonts()
            
    def reset_font_size(self):
        """Reset font size to default"""
        self.current_font_size = 14
        self.update_fonts()
    
    def set_status(self, message):
        """Set status bar message"""
        self.status_bar.showMessage(message)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = ImageGalleryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()