#!/usr/bin/env python3
"""
UI Components for the Image Gallery application
Contains tab classes and custom widgets with improved tag system
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, 
    QTableWidget, QTableWidgetItem, QSplitter, QTextEdit, QHeaderView,
    QTabWidget, QGroupBox, QFrame, QRadioButton, QButtonGroup, QScrollArea,
    QApplication, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPalette, QFont, QPainter, QBrush, QPen, QColor


class FlowWidget(QWidget):
    """A widget that arranges child widgets in a flowing layout"""
    
    def __init__(self, parent=None, spacing=6):
        super().__init__(parent)
        self.spacing = spacing
        self.widgets = []
        self.setMinimumHeight(50)
        
    def addWidget(self, widget):
        """Add a widget to the flow layout"""
        widget.setParent(self)
        self.widgets.append(widget)
        self.updateLayout()
        
    def removeWidget(self, widget):
        """Remove a widget from the flow layout"""
        if widget in self.widgets:
            self.widgets.remove(widget)
            widget.setParent(None)
            self.updateLayout()
            
    def clear(self):
        """Remove all widgets"""
        for widget in self.widgets[:]:
            self.removeWidget(widget)
            
    def updateLayout(self):
        """Update the layout of all widgets"""
        if not self.widgets:
            self.setMinimumHeight(50)
            return
            
        container_width = self.width() or 400
        x, y = 0, 0
        row_height = 0
        margin = 6
        
        for widget in self.widgets:
            widget.show()
            widget_size = widget.sizeHint()
            widget_width = widget_size.width()
            widget_height = widget_size.height()
            
            # Check if widget fits on current row
            if x + widget_width > container_width - margin and x > 0:
                # Move to next row
                x = 0
                y += row_height + self.spacing
                row_height = 0
                
            # Position widget
            widget.move(x, y)
            widget.resize(widget_width, widget_height)
            
            # Update row tracking
            x += widget_width + self.spacing
            row_height = max(row_height, widget_height)
            
        # Set minimum height based on content
        total_height = y + row_height + margin * 2
        self.setMinimumHeight(max(50, total_height))
        
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.updateLayout()


class TagChip(QWidget):
    """A custom-painted tag chip widget that bypasses stylesheet issues"""
    
    tag_clicked = pyqtSignal(str)
    remove_clicked = pyqtSignal(str)
    keyword_clicked = pyqtSignal(str)
    
    def __init__(self, tag_text: str, removable: bool = True, selectable: bool = True, 
                 font_size: int = 12, is_keyword: bool = False, tag_manager=None):
        super().__init__()
        self.tag_text = tag_text
        self.removable = removable
        self.selectable = selectable
        self.selected = False
        self.font_size = font_size
        self.is_keyword = is_keyword
        self.tag_manager = tag_manager
        self.hovered = False
        self.remove_hovered = False
        
        # Calculate size based on text
        font = QFont("Arial", self.font_size, QFont.Weight.Medium)
        fm = self.fontMetrics()
        text_width = fm.boundingRect(self.tag_text).width()
        
        # Set fixed size
        padding = 20
        button_width = 20 if self.removable else 0
        total_width = text_width + padding + button_width
        height = max(32, self.font_size + 20)
        
        self.setFixedSize(total_width, height)
        self.setFont(font)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Enable context menu for keyword selection
        if self.selectable:
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """Show context menu for keyword operations"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        
        if self.is_keyword:
            action = menu.addAction("🔴 Remove as Keyword")
            action.triggered.connect(lambda: self.keyword_clicked.emit(self.tag_text))
        else:
            action = menu.addAction("⭐ Set as Keyword")
            action.triggered.connect(lambda: self.keyword_clicked.emit(self.tag_text))
        
        menu.exec(self.mapToGlobal(position))
    
    def paintEvent(self, event):
        """Custom paint the tag chip with proper colors"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Determine colors based on state
        if self.selected:
            # Green for selected
            bg_color = QColor(76, 175, 80)  # #4CAF50
            border_color = QColor(56, 142, 60)  # #388E3C
            text_color = QColor(255, 255, 255)  # White
        elif self.is_keyword:
            # Red for keyword
            bg_color = QColor(244, 67, 54)  # #F44336
            border_color = QColor(211, 47, 47)  # #D32F2F
            text_color = QColor(255, 255, 255)  # White
        else:
            # Gray for normal
            bg_color = QColor(245, 245, 245)  # #F5F5F5
            border_color = QColor(204, 204, 204)  # #CCCCCC
            text_color = QColor(51, 51, 51)  # #333333
        
        # Slightly darken if hovered
        if self.hovered and not (self.selected or self.is_keyword):
            bg_color = bg_color.darker(110)
        
        # Draw background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(rect, 16, 16)
        
        # Draw text
        painter.setPen(QPen(text_color))
        font = QFont("Arial", self.font_size, QFont.Weight.Medium)
        painter.setFont(font)
        
        text_rect = rect.adjusted(10, 0, -30 if self.removable else -10, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.tag_text)
        
        # Draw remove button if removable
        if self.removable:
            button_rect = rect.adjusted(rect.width() - 25, 6, -5, -6)
            
            # Button background
            if self.remove_hovered:
                button_bg = QColor(255, 255, 255, 128)  # Semi-transparent white
            else:
                button_bg = QColor(255, 255, 255, 77)   # More transparent
            
            painter.setBrush(QBrush(button_bg))
            painter.setPen(QPen(QColor(0, 0, 0, 0)))  # No border
            painter.drawRoundedRect(button_rect, 10, 10)
            
            # X symbol
            painter.setPen(QPen(text_color, 2))
            painter.setFont(QFont("Arial", self.font_size, QFont.Weight.Bold))
            painter.drawText(button_rect, Qt.AlignmentFlag.AlignCenter, "×")
    
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.removable and self.get_remove_button_rect().contains(event.pos()):
                # Remove button clicked
                self.remove_clicked.emit(self.tag_text)
            elif self.selectable:
                # Tag clicked for selection
                self.set_selected(not self.selected)
                self.tag_clicked.emit(self.tag_text)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects"""
        was_hovered = self.hovered
        was_remove_hovered = self.remove_hovered
        
        self.hovered = self.rect().contains(event.pos())
        
        if self.removable:
            self.remove_hovered = self.get_remove_button_rect().contains(event.pos())
        else:
            self.remove_hovered = False
        
        # Repaint if hover state changed
        if (was_hovered != self.hovered or was_remove_hovered != self.remove_hovered):
            self.update()
        
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leaving widget"""
        if self.hovered or self.remove_hovered:
            self.hovered = False
            self.remove_hovered = False
            self.update()
        super().leaveEvent(event)
    
    def get_remove_button_rect(self):
        """Get the rectangle of the remove button"""
        rect = self.rect()
        return rect.adjusted(rect.width() - 25, 6, -5, -6)
    
    def set_selected(self, selected: bool):
        """Set the selected state and repaint"""
        if self.selected != selected:
            self.selected = selected
            self.update()  # Trigger repaint
    
    def set_keyword(self, is_keyword: bool):
        """Set the keyword state and repaint"""
        if self.is_keyword != is_keyword:
            self.is_keyword = is_keyword
            self.update()  # Trigger repaint
    
    def get_tag_text(self) -> str:
        """Get the tag text"""
        return self.tag_text
    
    def sizeHint(self):
        """Provide size hint for layout calculations"""
        return self.size()


class CurrentImageTagsWidget(QWidget):
    """Improved widget for displaying tags of the currently selected image"""
    
    tag_removed = pyqtSignal(str, str)  # filename, tag_text
    keyword_toggled = pyqtSignal(str)  # tag_text
    
    def __init__(self, font_size: int = 12):
        super().__init__()
        self.current_filename = None
        self.current_tags = []
        self.font_size = font_size
        self.tag_manager = None  # Will be set by parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tags display section
        tags_group = QGroupBox("Current Image Tags")
        tags_group.setFont(QFont("Arial", self.font_size + 1, QFont.Weight.Bold))
        tags_layout = QVBoxLayout(tags_group)
        
        # Keyword info label
        self.keyword_info = QLabel("🔴 Red = Keyword tag (always first) • Right-click to set/remove keyword")
        self.keyword_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic; margin-bottom: 5px;")
        self.keyword_info.setWordWrap(True)
        tags_layout.addWidget(self.keyword_info)
        
        # Scrollable area for tag chips
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_area.setMaximumHeight(150)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Flow widget for tag chips
        self.tags_flow_widget = FlowWidget(spacing=8)
        scroll_area.setWidget(self.tags_flow_widget)
        
        tags_layout.addWidget(scroll_area)
        layout.addWidget(tags_group)
        
    def set_tag_manager(self, tag_manager):
        """Set the tag manager reference"""
        self.tag_manager = tag_manager
        
    def set_image_tags(self, filename: str, tags: list):
        """Set the current image and its tags"""
        self.current_filename = filename
        self.current_tags = tags.copy()
        self.refresh_tag_display()
        
    def clear_display(self):
        """Clear the tag display"""
        self.current_filename = None
        self.current_tags = []
        self.refresh_tag_display()
        
    def refresh_tag_display(self):
        """Refresh the visual display of tag chips"""
        # Clear existing widgets
        self.tags_flow_widget.clear()
        
        if not self.current_filename:
            # No image selected
            no_selection_label = QLabel("No image selected")
            no_selection_label.setStyleSheet("color: #666; font-style: italic; padding: 15px; font-size: 12px;")
            self.tags_flow_widget.addWidget(no_selection_label)
            return
            
        if not self.current_tags:
            # No tags for this image
            no_tags_label = QLabel(f"No tags for {self.current_filename}")
            no_tags_label.setStyleSheet("color: #666; font-style: italic; padding: 15px; font-size: 12px;")
            self.tags_flow_widget.addWidget(no_tags_label)
            return
        
        # Create tag chips with improved flow layout
        for tag in self.current_tags:
            is_keyword = self.tag_manager.is_keyword_tag(tag) if self.tag_manager else False
            chip = TagChip(tag, removable=True, selectable=False, font_size=self.font_size, 
                          is_keyword=is_keyword, tag_manager=self.tag_manager)
            chip.remove_clicked.connect(lambda t=tag: self.tag_removed.emit(self.current_filename, t))
            chip.keyword_clicked.connect(self.keyword_toggled.emit)
            self.tags_flow_widget.addWidget(chip)


class TagInputWidget(QWidget):
    """Improved widget for inputting and managing tags"""
    
    tags_changed = pyqtSignal(list)
    apply_to_selection = pyqtSignal(list)
    apply_to_all = pyqtSignal(list)
    keyword_toggled = pyqtSignal(str)  # New signal for keyword toggle
    
    def __init__(self, font_size: int = 12):
        super().__init__()
        self.available_tags = []
        self.selected_tags = []
        self.font_size = font_size
        self.tag_manager = None  # Will be set by parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tag input section
        input_group = QGroupBox("Tag Management")
        input_group.setFont(QFont("Arial", self.font_size + 1, QFont.Weight.Bold))
        input_layout = QVBoxLayout(input_group)
        
        # Text input for new tags with larger font
        input_row = QHBoxLayout()
        add_label = QLabel("Add Tags:")
        add_label.setFont(QFont("Arial", self.font_size))
        input_row.addWidget(add_label)
        
        self.tag_input = QLineEdit()
        self.tag_input.setFont(QFont("Arial", self.font_size))
        self.tag_input.setPlaceholderText("Type tags separated by commas or semicolons...")
        self.tag_input.setMinimumHeight(32)  # Taller input field
        self.tag_input.returnPressed.connect(self.add_tags_from_input)
        input_row.addWidget(self.tag_input, 1)
        
        self.add_tags_btn = QPushButton("Add Tags")
        self.add_tags_btn.setFont(QFont("Arial", self.font_size))
        self.add_tags_btn.setMinimumHeight(32)
        self.add_tags_btn.clicked.connect(self.add_tags_from_input)
        input_row.addWidget(self.add_tags_btn)
        
        input_layout.addLayout(input_row)
        
        # Available tags section with improved layout
        tags_label = QLabel("Available Tags (🟢 Green = Selected • 🔴 Red = Keyword • Right-click to set keyword):")
        tags_label.setFont(QFont("Arial", self.font_size))
        tags_label.setWordWrap(True)
        input_layout.addWidget(tags_label)
        
        # Scrollable area for tag chips
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(120)
        scroll_area.setMaximumHeight(200)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Flow widget for available tags
        self.tags_flow_widget = FlowWidget(spacing=8)
        scroll_area.setWidget(self.tags_flow_widget)
        
        input_layout.addWidget(scroll_area)
        
        # Action buttons with larger fonts
        button_layout = QHBoxLayout()
        
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.setFont(QFont("Arial", self.font_size))
        self.clear_selection_btn.setMinimumHeight(32)
        self.clear_selection_btn.clicked.connect(self.clear_tag_selection)
        button_layout.addWidget(self.clear_selection_btn)
        
        button_layout.addStretch()
        
        self.apply_to_selection_btn = QPushButton("Apply to Selection")
        self.apply_to_selection_btn.setFont(QFont("Arial", self.font_size))
        self.apply_to_selection_btn.setMinimumHeight(32)
        self.apply_to_selection_btn.clicked.connect(self.emit_apply_to_selection)
        button_layout.addWidget(self.apply_to_selection_btn)
        
        self.apply_to_all_btn = QPushButton("Apply to All")
        self.apply_to_all_btn.setFont(QFont("Arial", self.font_size))
        self.apply_to_all_btn.setMinimumHeight(32)
        self.apply_to_all_btn.clicked.connect(self.emit_apply_to_all)
        button_layout.addWidget(self.apply_to_all_btn)
        
        input_layout.addLayout(button_layout)
        
        layout.addWidget(input_group)
        
    def set_tag_manager(self, tag_manager):
        """Set the tag manager reference"""
        self.tag_manager = tag_manager
        
    def add_tags_from_input(self):
        """Add tags from the input field"""
        text = self.tag_input.text().strip()
        if not text:
            return
        
        # Parse tags from text
        tags = re.split(r'[,;]\s*', text.strip())
        new_tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Add to available tags
        for tag in new_tags:
            if tag not in self.available_tags:
                self.available_tags.append(tag)
        
        # Clear input
        self.tag_input.clear()
        
        # Refresh display
        self.refresh_tag_display()
        
        # Emit signal
        self.tags_changed.emit(self.available_tags)
    
    def set_available_tags(self, tags: list):
        """Set the list of available tags"""
        self.available_tags = tags.copy()
        self.refresh_tag_display()
    
    def refresh_tag_display(self):
        """Refresh the visual display of tag chips with flow layout"""
        # Clear existing widgets
        self.tags_flow_widget.clear()
        
        if not self.available_tags:
            no_tags_label = QLabel("No tags available. Add some tags above.")
            no_tags_label.setStyleSheet("color: #666; font-style: italic; padding: 15px; font-size: 12px;")
            self.tags_flow_widget.addWidget(no_tags_label)
            return
        
        # Create tag chips with flow layout
        for tag in sorted(self.available_tags):
            is_keyword = self.tag_manager.is_keyword_tag(tag) if self.tag_manager else False
            chip = TagChip(tag, removable=True, selectable=True, font_size=self.font_size, 
                          is_keyword=is_keyword, tag_manager=self.tag_manager)
            chip.tag_clicked.connect(self.on_tag_clicked)
            chip.remove_clicked.connect(self.remove_tag)
            chip.keyword_clicked.connect(self.keyword_toggled.emit)
            
            # Set selection state
            chip.set_selected(tag in self.selected_tags)
            self.tags_flow_widget.addWidget(chip)
    
    def on_tag_clicked(self, tag_text: str):
        """Handle tag selection/deselection"""
        if tag_text in self.selected_tags:
            self.selected_tags.remove(tag_text)
        else:
            self.selected_tags.append(tag_text)
        
        # Update all chips to reflect selection state
        self.refresh_tag_display()
    
    def remove_tag(self, tag_text: str):
        """Remove a tag from available tags"""
        if tag_text in self.available_tags:
            self.available_tags.remove(tag_text)
        if tag_text in self.selected_tags:
            self.selected_tags.remove(tag_text)
        
        self.refresh_tag_display()
        self.tags_changed.emit(self.available_tags)
    
    def clear_tag_selection(self):
        """Clear all selected tags"""
        self.selected_tags.clear()
        self.refresh_tag_display()
    
    def emit_apply_to_selection(self):
        """Emit signal to apply selected tags to selection"""
        if self.selected_tags:
            self.apply_to_selection.emit(self.selected_tags.copy())
    
    def emit_apply_to_all(self):
        """Emit signal to apply selected tags to all images"""
        if self.selected_tags:
            self.apply_to_all.emit(self.selected_tags.copy())
    
    def get_selected_tags(self) -> list:
        """Get currently selected tags"""
        return self.selected_tags.copy()


class TagDisplayWidget(QWidget):
    """Improved widget for displaying tags in table cells"""
    
    tag_removed = pyqtSignal(str, str)  # filename, tag_text
    keyword_toggled = pyqtSignal(str)  # tag_text
    
    def __init__(self, filename: str, tags: list, font_size: int = 11, tag_manager=None):
        super().__init__()
        self.filename = filename
        self.tags = tags.copy()
        self.font_size = font_size
        self.tag_manager = tag_manager
        self.setup_ui()
        
    def setup_ui(self):
        # Use flow widget for better tag arrangement in table cells
        self.flow_widget = FlowWidget(spacing=4)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.flow_widget)
        
        if not self.tags:
            # Show placeholder when no tags
            placeholder = QLabel("No tags")
            placeholder.setStyleSheet("color: #999; font-style: italic; font-size: 11px;")
            self.flow_widget.addWidget(placeholder)
        else:
            # Show tag chips with smaller font for table display
            for tag in self.tags:
                is_keyword = self.tag_manager.is_keyword_tag(tag) if self.tag_manager else False
                chip = TagChip(tag, removable=True, selectable=False, font_size=self.font_size, 
                              is_keyword=is_keyword, tag_manager=self.tag_manager)
                chip.remove_clicked.connect(lambda t=tag: self.tag_removed.emit(self.filename, t))
                chip.keyword_clicked.connect(self.keyword_toggled.emit)
                self.flow_widget.addWidget(chip)
        
        self.setMinimumHeight(40)
        self.setMaximumHeight(100)


class GalleryTab(QWidget):
    """Main gallery tab for viewing and editing images with tag system"""
    
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
        self.select_folder_btn.clicked.connect(self.parent.event_handlers.select_folder)
        
        # Add to control layout
        control_layout.addWidget(self.select_folder_btn)
        control_layout.addStretch()  # Push everything to the left
        
        # Splitter for table and tag/image view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table for image list
        self.table = QTableWidget(0, 2)  # 0 rows, 2 columns
        self.table.setHorizontalHeaderLabels(["Filename", "Tags"])
        
        # Enable multi-selection
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Make columns interactive (user-resizable)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        
        # Set initial column widths
        self.table.setColumnWidth(0, 300)  # Filename column
        self.table.setColumnWidth(1, 500)  # Tags column
        
        # Make sure the header is visible
        self.table.horizontalHeader().setVisible(True)
        
        # Allow the table to stretch horizontally
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Connect table selection signal
        self.table.itemSelectionChanged.connect(self.parent.event_handlers.on_table_select)
        
        # Add context menu to table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.parent.event_handlers.show_context_menu)
        
        # Right side panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        
        # Create bottom splitter for tag areas
        tag_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Current image tags display widget (left side of bottom) - with larger font
        try:
            self.current_image_tags_widget = CurrentImageTagsWidget(font_size=12)
            self.current_image_tags_widget.tag_removed.connect(self.parent.event_handlers.on_tag_removed_from_image)
            self.current_image_tags_widget.keyword_toggled.connect(self.parent.event_handlers.on_keyword_toggled)
            current_tags_area = self.current_image_tags_widget
            
        except Exception as e:
            print(f"Error creating CurrentImageTagsWidget: {e}")
            # Create a placeholder widget if tag system fails
            placeholder_group = QGroupBox("Tags (Error)")
            placeholder_layout = QVBoxLayout(placeholder_group)
            error_label = QLabel(f"Tag display unavailable: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            placeholder_layout.addWidget(error_label)
            current_tags_area = placeholder_group
            
            # Add dummy widget for compatibility
            self.current_image_tags_widget = type('MockWidget', (), {
                'set_image_tags': lambda self, filename, tags: None,
                'clear_display': lambda self: None,
                'set_tag_manager': lambda self, tm: None
            })()
        
        # Tag input widget (right side of bottom) - with larger font
        try:
            self.tag_input_widget = TagInputWidget(font_size=12)
            self.tag_input_widget.tags_changed.connect(self.parent.event_handlers.on_tags_changed)
            self.tag_input_widget.apply_to_selection.connect(self.parent.event_handlers.apply_tags_to_selection)
            self.tag_input_widget.apply_to_all.connect(self.parent.event_handlers.apply_tags_to_all)
            self.tag_input_widget.keyword_toggled.connect(self.parent.event_handlers.on_keyword_toggled)
            tag_input_area = self.tag_input_widget
            
        except Exception as e:
            print(f"Error creating TagInputWidget: {e}")
            # Create a placeholder widget if tag system fails
            placeholder_group = QGroupBox("Tag Input (Error)")
            placeholder_layout = QVBoxLayout(placeholder_group)
            error_label = QLabel(f"Tag input unavailable: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            placeholder_layout.addWidget(error_label)
            tag_input_area = placeholder_group
            
            # Add dummy widget for compatibility
            self.tag_input_widget = type('MockWidget', (), {
                'set_available_tags': lambda self, x: None,
                'set_tag_manager': lambda self, tm: None
            })()
        
        # Add both tag widgets to the splitter
        tag_splitter.addWidget(current_tags_area)
        tag_splitter.addWidget(tag_input_area)
        tag_splitter.setSizes([300, 400])  # Give more space to tag input
        
        # Add widgets to right panel
        right_layout.addWidget(self.image_label, 1)
        right_layout.addWidget(tag_splitter)
        
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
        
        # Left panel - Image Processing Tools
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Image Processing Section
        processing_group = QGroupBox("Image Processing")
        processing_layout = QVBoxLayout(processing_group)
        
        # Fix Images section
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
        
        # Fix Images button
        self.fix_images_btn = QPushButton("Fix Images")
        self.fix_images_btn.clicked.connect(self.parent.event_handlers.fix_images)
        fix_layout.addWidget(self.fix_images_btn)
        
        processing_layout.addWidget(fix_section)
        
        # Mass Rename Section
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
        
        # Prefix input
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("Prefix:")
        self.prefix_entry = QLineEdit()
        self.prefix_entry.setPlaceholderText("e.g., 'portrait_'")
        
        prefix_layout.addWidget(prefix_label)
        prefix_layout.addWidget(self.prefix_entry, 1)
        rename_layout.addLayout(prefix_layout)
        
        # NEW: Scramble order checkbox
        self.scramble_order_checkbox = QCheckBox("Scramble image order (adds random letters)")
        self.scramble_order_checkbox.setToolTip("Adds random letters to filenames to scramble training order\nExample: portrait_a001.jpg, portrait_m002.jpg, portrait_c003.jpg")
        rename_layout.addWidget(self.scramble_order_checkbox)
        
        # Rename button
        self.mass_rename_btn = QPushButton("Rename Images")
        self.mass_rename_btn.clicked.connect(self.parent.event_handlers.mass_rename_images)
        rename_layout.addWidget(self.mass_rename_btn)
        
        processing_layout.addWidget(rename_section)
        
        # Dataset Augmentation Section
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
        
        # Create Duplicates button
        self.create_duplicates_btn = QPushButton("Create Duplicates")
        self.create_duplicates_btn.clicked.connect(self.parent.event_handlers.create_duplicates)
        augment_layout.addWidget(self.create_duplicates_btn)
        
        processing_layout.addWidget(augment_section)
        
        # Add processing group to left layout
        left_layout.addWidget(processing_group)
        left_layout.addStretch()
        
        # Right panel - Tag Processing
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tag Scrambling Section
        scramble_group = QGroupBox("Tag Order Scrambling")
        scramble_layout = QVBoxLayout(scramble_group)
        
        # Description
        desc_label = QLabel("Randomize the order of tags in descriptions to create variety while preserving all content.")
        desc_label.setStyleSheet("QLabel { color: #666; font-size: 11px; font-style: italic; margin-bottom: 10px; }")
        desc_label.setWordWrap(True)
        scramble_layout.addWidget(desc_label)
        
        # Scope selection for Tag Scrambling
        scramble_scope_layout = QHBoxLayout()
        self.scramble_scope_group = QButtonGroup()
        self.scramble_all_radio = QRadioButton("Scramble All Descriptions")
        self.scramble_selected_radio = QRadioButton("Scramble Selected Only")
        self.scramble_all_radio.setChecked(True)
        
        self.scramble_scope_group.addButton(self.scramble_all_radio)
        self.scramble_scope_group.addButton(self.scramble_selected_radio)
        
        scramble_scope_layout.addWidget(self.scramble_all_radio)
        scramble_scope_layout.addWidget(self.scramble_selected_radio)
        scramble_layout.addLayout(scramble_scope_layout)
        
        # Options section
        options_group = QGroupBox("Scrambling Options")
        options_layout = QVBoxLayout(options_group)
        
        # Preserve first tag option
        self.preserve_first_tag = QRadioButton("Preserve first tag (keep main subject first)")
        self.preserve_first_tag.setChecked(True)
        options_layout.addWidget(self.preserve_first_tag)
        
        # Full randomization option
        self.full_randomize = QRadioButton("Fully randomize all tags")
        options_layout.addWidget(self.full_randomize)
        
        # Group the radio buttons
        self.scramble_method_group = QButtonGroup()
        self.scramble_method_group.addButton(self.preserve_first_tag)
        self.scramble_method_group.addButton(self.full_randomize)
        
        scramble_layout.addWidget(options_group)
        
        # Test section
        test_group = QGroupBox("Test Scrambling")
        test_layout = QVBoxLayout(test_group)
        
        test_input_layout = QHBoxLayout()
        test_input_layout.addWidget(QLabel("Test tags:"))
        self.test_tags_entry = QLineEdit()
        self.test_tags_entry.setPlaceholderText("Enter test tags: tag1, tag2, tag3, tag4...")
        self.test_scramble_btn = QPushButton("Test Scramble")
        self.test_scramble_btn.clicked.connect(self.parent.event_handlers.test_tag_scramble)
        
        test_input_layout.addWidget(self.test_tags_entry, 1)
        test_input_layout.addWidget(self.test_scramble_btn)
        test_layout.addLayout(test_input_layout)
        
        # Test result display
        self.test_scramble_result = QLabel("Results will appear here...")
        self.test_scramble_result.setWordWrap(True)
        self.test_scramble_result.setStyleSheet("QLabel { padding: 8px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; }")
        self.test_scramble_result.setMinimumHeight(60)
        test_layout.addWidget(self.test_scramble_result)
        
        scramble_layout.addWidget(test_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Preview button
        self.preview_scramble_btn = QPushButton("Preview Changes")
        self.preview_scramble_btn.setStyleSheet("QPushButton { background-color: #E3F2FD; border: 1px solid #2196F3; }")
        self.preview_scramble_btn.clicked.connect(self.parent.event_handlers.preview_tag_scramble)
        button_layout.addWidget(self.preview_scramble_btn)
        
        button_layout.addStretch()
        
        # Apply button
        self.scramble_tags_btn = QPushButton("Scramble Tags")
        self.scramble_tags_btn.setStyleSheet("QPushButton { background-color: #FFF3E0; border: 1px solid #FF9800; font-weight: bold; }")
        self.scramble_tags_btn.clicked.connect(self.parent.event_handlers.scramble_tags)
        button_layout.addWidget(self.scramble_tags_btn)
        
        scramble_layout.addLayout(button_layout)
        
        # Add scramble group to right layout
        right_layout.addWidget(scramble_group)
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
            self.scramble_selected_radio.setEnabled(False)
            
        elif selected_count == total_count:
            self.scope_info_label.setText(f"All {total_count} images selected")
            self.scope_info_label.setStyleSheet("QLabel { color: #0066cc; font-size: 10px; padding: 2px 6px; margin: 2px; background-color: #e6f3ff; border-radius: 2px; }")
            
            # Enable "selected only" options
            self.fix_selected_radio.setEnabled(True)
            self.rename_selected_radio.setEnabled(True)
            self.dup_selected_radio.setEnabled(True)
            self.scramble_selected_radio.setEnabled(True)
            
        else:
            self.scope_info_label.setText(f"{selected_count} of {total_count} selected")
            self.scope_info_label.setStyleSheet("QLabel { color: #009900; font-size: 10px; padding: 2px 6px; margin: 2px; background-color: #e6ffe6; border-radius: 2px; }")
            
            # Enable "selected only" options
            self.fix_selected_radio.setEnabled(True)
            self.rename_selected_radio.setEnabled(True)
            self.dup_selected_radio.setEnabled(True)
            self.scramble_selected_radio.setEnabled(True)