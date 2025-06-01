#!/usr/bin/env python3
"""
Event handling logic for the Image Gallery application
Contains all button clicks, selections, and user interactions
"""

import os
import tempfile
import traceback
import random
from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QTableWidgetItem, QMenu, QDialog, 
    QProgressDialog, QApplication, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

from PIL import Image
from dialogs import ImageFixDialog, ImageDuplicateDialog


class EventHandlers:
    """Handles all user interface events and interactions"""
    
    def __init__(self, app):
        self.app = app
    
    def select_folder(self):
        """Open file dialog to select a folder with images"""
        folder_path = QFileDialog.getExistingDirectory(self.app, "Select Folder with Images")
        
        if not folder_path:
            return
            
        success, message, images_data = self.app.data_manager.load_images_from_folder(folder_path)
        
        if success:
            # Initialize tag manager with project folder
            self.app.tag_manager.set_project_folder(folder_path)
            
            # Try to migrate existing text descriptions to tags
            migrated_count = self.app.tag_manager.migrate_from_text_descriptions(images_data)
            if migrated_count > 0:
                migration_msg = f" • Migrated {migrated_count} text descriptions to tags"
            else:
                migration_msg = ""
            
            self.populate_table(images_data)
            
            # Select first image if available
            if images_data:
                self.app.gallery_tab.table.selectRow(0)
            
            # Enable Utils tab now that we have images loaded
            self.app.tab_widget.setTabEnabled(1, True)
            
            # Auto-save tags after migration
            if migrated_count > 0:
                self._auto_save_tags()
            
            self.app.set_status(f"{message} • Utils tab now available • Tag system active{migration_msg}")
            
        else:
            QMessageBox.critical(self.app, "Load Error", message)
    
    def populate_table(self, images_data):
        """Populate the table with image data using tag display widgets"""
        table = self.app.gallery_tab.table
        table.setRowCount(0)  # Clear existing data
        
        for i, img_data in enumerate(images_data):
            row_position = table.rowCount()
            table.insertRow(row_position)
            
            # Filename column
            table.setItem(row_position, 0, QTableWidgetItem(img_data['filename']))
            
            # Tags column - try to create custom widget, fallback to text
            try:
                tags = self.app.tag_manager.get_tags_for_image(img_data['filename'])
                tag_widget = self._create_tag_display_widget(img_data['filename'], tags)
                table.setCellWidget(row_position, 1, tag_widget)
            except Exception as e:
                print(f"Error creating tag widget for {img_data['filename']}: {e}")
                # Fallback to simple text display
                tags = self.app.tag_manager.get_tags_for_image(img_data['filename'])
                tag_text = ", ".join(tags) if tags else ""
                table.setItem(row_position, 1, QTableWidgetItem(tag_text))
            
            # Update row index in data
            img_data['row_index'] = row_position
        
        # Update utils tab scope info
        self.app.utils_tab.update_scope_info(0, len(images_data))
        
        # Update tag input widget with all available tags and set tag manager reference
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget') and hasattr(self.app.gallery_tab.tag_input_widget, 'set_available_tags'):
                self.app.gallery_tab.tag_input_widget.set_tag_manager(self.app.tag_manager)
                self.app.gallery_tab.tag_input_widget.set_available_tags(self.app.tag_manager.get_all_tags())
                
            if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                self.app.gallery_tab.current_image_tags_widget.set_tag_manager(self.app.tag_manager)
        except Exception as e:
            print(f"Warning: Could not update tag widgets: {e}")
    
    def _create_tag_display_widget(self, filename: str, tags: list):
        """Create a tag display widget for table cells"""
        try:
            from ui_components import TagDisplayWidget
            
            widget = TagDisplayWidget(filename, tags, tag_manager=self.app.tag_manager)
            widget.tag_removed.connect(self.on_tag_removed_from_image)
            widget.keyword_toggled.connect(self.on_keyword_toggled)
            return widget
        except Exception as e:
            print(f"Error creating TagDisplayWidget for {filename}: {e}")
            # Fallback to simple label with tag text
            from PyQt6.QtWidgets import QLabel
            label = QLabel(", ".join(tags) if tags else "No tags")
            return label
    
    def on_table_select(self):
        """Handle table selection change"""
        selected_rows = self.app.gallery_tab.table.selectionModel().selectedRows()
        
        # Update utils tab scope info
        total_images = len(self.app.data_manager.images_data)
        selected_count = len(selected_rows)
        self.app.utils_tab.update_scope_info(selected_count, total_images)
        
        # Update keyword label based on selection (with error handling)
        try:
            if hasattr(self.app.gallery_tab, 'keyword_label'):
                if selected_count == 0:
                    self.app.gallery_tab.keyword_label.setText("Add Tag to All")
                    self.app.gallery_tab.keyword_entry.setPlaceholderText("Add tag to all images...")
                else:
                    self.app.gallery_tab.keyword_label.setText("Add Tag to Selected")
                    self.app.gallery_tab.keyword_entry.setPlaceholderText("Add tag to selected images...")
        except Exception as e:
            print(f"Warning: Could not update keyword label: {e}")
        
        if not selected_rows:
            # No selection
            self.app.current_image_index = -1
            self._clear_image_display()
            self.app.set_status("No images selected")
            return
        
        # Update status with selection count
        if len(selected_rows) == 1:
            # Single selection - show the image
            row = selected_rows[0].row()
            index, img_data = self.app.data_manager.find_image_by_row_index(row)
            if index >= 0:
                self.app.current_image_index = index
                self.show_selected_image()
                self.app.set_status(f"Selected: {img_data['filename']}")
        else:
            # Multiple selection - show info but no specific image
            self.app.current_image_index = -1
            self._show_multiple_selection_display(len(selected_rows))
            self.app.set_status(f"{len(selected_rows)} images selected")
    
    def _show_multiple_selection_display(self, count):
        """Display info when multiple images are selected"""
        self.app.gallery_tab.image_label.clear()
        self.app.gallery_tab.image_label.setText(f"📋 {count} images selected\n\nUse tag system below to apply tags\nor Utils tab for operations")
        self.app.gallery_tab.image_label.setStyleSheet("QLabel { color: #666; font-size: 14px; }")
        
        # Clear current image tags display for multiple selection
        try:
            if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                self.app.gallery_tab.current_image_tags_widget.clear_display()
        except Exception as e:
            print(f"Error clearing current image tags display: {e}")
    
    def get_selected_images(self):
        """Get list of selected image data"""
        selected_rows = self.app.gallery_tab.table.selectionModel().selectedRows()
        selected_images = []
        
        for row_model in selected_rows:
            row = row_model.row()
            index, img_data = self.app.data_manager.find_image_by_row_index(row)
            if index >= 0:
                selected_images.append(img_data)
        
        return selected_images
    
    def show_selected_image(self):
        """Display the currently selected image"""
        img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
        if not img_data:
            return
        
        img_path = img_data['path']
        filename = img_data['filename']
        
        try:
            # Load and display the image
            pil_img = Image.open(img_path)
            
            # Get label dimensions for resizing
            image_label = self.app.gallery_tab.image_label
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
            
            # Update current image tags display
            tags = self.app.tag_manager.get_tags_for_image(filename)
            try:
                if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                    self.app.gallery_tab.current_image_tags_widget.set_image_tags(filename, tags)
            except Exception as e:
                print(f"Error updating current image tags display: {e}")
            
        except Exception as e:
            QMessageBox.critical(self.app, "Image Error", f"Error displaying image: {str(e)}")
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
        """Handle description updates - now disabled in tag mode"""
        # Description editing is replaced by tag system
        # This method is kept for compatibility but does nothing in tag mode
        return
    
    def _auto_save_tags(self):
        """Auto-save tags and sync with traditional descriptions"""
        try:
            # Save tags to project
            success, message = self.app.tag_manager.save_tags_to_project()
            if not success:
                self.app.set_status(f"Tag save failed: {message}")
                return
            
            # Convert tags to descriptions for backward compatibility
            self.app.tag_manager.export_to_text_descriptions(self.app.data_manager.images_data)
            
            # Save traditional descriptions
            success, message = self.app.data_manager.save_descriptions()
            if success:
                self.app.set_status("Auto-saved tags and descriptions")
            else:
                self.app.set_status(f"Description save failed: {message}")
                
        except Exception as e:
            self.app.set_status(f"Auto-save error: {str(e)}")
    
    def append_keywords(self):
        """Add keyword as tag to selected images or all images"""
        keyword = self.app.gallery_tab.keyword_entry.text().strip()
        if not keyword:
            return
        
        # Parse keywords (in case multiple are entered)
        tags = self.app.tag_manager.parse_tags_from_text(keyword)
        if not tags:
            return
        
        # Determine which images to apply to based on selection
        selected_images = self.get_selected_images()
        
        if selected_images:
            # Apply to selected images only
            for img_data in selected_images:
                self.app.tag_manager.add_tags_to_image(img_data['filename'], tags)
                self.refresh_image_row(img_data['filename'])
            
            status_msg = f"Added {len(tags)} tag(s) to {len(selected_images)} selected images and auto-saved"
        else:
            # Apply to all images
            updated_count = 0
            for img_data in self.app.data_manager.images_data:
                self.app.tag_manager.add_tags_to_image(img_data['filename'], tags)
                self.refresh_image_row(img_data['filename'])
                updated_count += 1
            
            status_msg = f"Added {len(tags)} tag(s) to all {updated_count} images and auto-saved"
        
        # Update tag input widget with new available tags
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget') and hasattr(self.app.gallery_tab.tag_input_widget, 'set_available_tags'):
                self.app.gallery_tab.tag_input_widget.set_available_tags(self.app.tag_manager.get_all_tags())
        except Exception as e:
            print(f"Warning: Could not update tag input widget: {e}")
        
        # Update current image tags display if this is the selected image
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                tags_for_current = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], tags_for_current)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        # Auto-save after keyword addition
        self._auto_save_tags()
        
        self.app.gallery_tab.keyword_entry.clear()
        self.app.set_status(status_msg)
    
    def on_tag_removed_from_image(self, filename: str, tag: str):
        """Handle removal of a tag from a specific image"""
        self.app.tag_manager.remove_tag_from_image(filename, tag)
        
        # Refresh the table row for this image
        self.refresh_image_row(filename)
        
        # If this is the currently selected image, update the current tags display
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data and current_img_data['filename'] == filename:
                tags = self.app.tag_manager.get_tags_for_image(filename)
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(filename, tags)
                except Exception as e:
                    print(f"Error updating current image tags display after removal: {e}")
        
        # Auto-save
        self._auto_save_tags()
        
        self.app.set_status(f"Removed tag '{tag}' from {filename}")
    
    def on_keyword_toggled(self, tag: str):
        """Handle keyword tag toggle"""
        self.app.tag_manager.toggle_keyword_tag(tag)
        
        # Refresh all table rows to update keyword display
        for img_data in self.app.data_manager.images_data:
            self.refresh_image_row(img_data['filename'])
        
        # Update current image tags display if applicable
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        # Update tag input widget display
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget'):
                self.app.gallery_tab.tag_input_widget.refresh_tag_display()
        except Exception as e:
            print(f"Warning: Could not refresh tag input widget: {e}")
        
        # Auto-save
        self._auto_save_tags()
        
        keyword_tag = self.app.tag_manager.get_keyword_tag()
        if keyword_tag == tag:
            self.app.set_status(f"Set '{tag}' as keyword tag (will always appear first)")
        else:
            self.app.set_status(f"Removed '{tag}' as keyword tag)")
    
    def force_refresh_all_tags(self):
        """Force refresh all tag displays to update styling"""
        # Refresh all table rows
        for img_data in self.app.data_manager.images_data:
            self.refresh_image_row(img_data['filename'])
        
        # Refresh tag input widget
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget'):
                self.app.gallery_tab.tag_input_widget.refresh_tag_display()
        except Exception as e:
            print(f"Warning: Could not refresh tag input widget: {e}")
        
        # Refresh current image tags display
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        self.app.set_status("Refreshed all tag displays")
        """Handle keyword tag toggle"""
        self.app.tag_manager.toggle_keyword_tag(tag)
        
        # Refresh all table rows to update keyword display
        for img_data in self.app.data_manager.images_data:
            self.refresh_image_row(img_data['filename'])
        
        # Update current image tags display if applicable
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        # Update tag input widget display
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget'):
                self.app.gallery_tab.tag_input_widget.refresh_tag_display()
        except Exception as e:
            print(f"Warning: Could not refresh tag input widget: {e}")
        
        # Auto-save
        self._auto_save_tags()
        
        keyword_tag = self.app.tag_manager.get_keyword_tag()
        if keyword_tag == tag:
            self.app.set_status(f"Set '{tag}' as keyword tag (will always appear first)")
        else:
            self.app.set_status(f"Removed '{tag}' as keyword tag")
    
    def refresh_image_row(self, filename: str):
        """Refresh a specific image row in the table"""
        table = self.app.gallery_tab.table
        
        # Find the row for this image
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.text() == filename:
                # Update the tags widget
                tags = self.app.tag_manager.get_tags_for_image(filename)
                try:
                    tag_widget = self._create_tag_display_widget(filename, tags)
                    table.setCellWidget(row, 1, tag_widget)
                except Exception as e:
                    print(f"Error refreshing tag widget for {filename}: {e}")
                    # Fallback to text display
                    tag_text = ", ".join(tags) if tags else ""
                    # Remove existing widget first
                    table.removeCellWidget(row, 1)
                    table.setItem(row, 1, QTableWidgetItem(tag_text))
                break
    
    def on_tags_changed(self, available_tags: list):
        """Handle changes to available tags"""
        # Update tag manager
        self.app.tag_manager.add_tags_from_list(available_tags)
        
        # Update tag input widget with tag manager reference
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget'):
                self.app.gallery_tab.tag_input_widget.set_tag_manager(self.app.tag_manager)
        except Exception as e:
            print(f"Warning: Could not update tag input widget manager: {e}")
        
        # Save tags
        self._auto_save_tags()
        
        self.app.set_status(f"Updated available tags ({len(available_tags)} total)")
    
    def apply_tags_to_selection(self, tags: list):
        """Apply tags to selected images"""
        selected_images = self.get_selected_images()
        
        if not selected_images:
            self.app.set_status("No images selected")
            return
        
        # Apply tags to each selected image
        for img_data in selected_images:
            self.app.tag_manager.add_tags_to_image(img_data['filename'], tags)
            self.refresh_image_row(img_data['filename'])
        
        # Update current image tags display if applicable
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data and current_img_data in selected_images:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        # Auto-save
        self._auto_save_tags()
        
        self.app.set_status(f"Applied {len(tags)} tags to {len(selected_images)} selected images")
    
    def apply_tags_to_all(self, tags: list):
        """Apply tags to all images"""
        if not self.app.data_manager.images_data:
            self.app.set_status("No images loaded")
            return
        
        # Apply tags to each image
        for img_data in self.app.data_manager.images_data:
            self.app.tag_manager.add_tags_to_image(img_data['filename'], tags)
            self.refresh_image_row(img_data['filename'])
        
        # Update current image tags display if applicable
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        # Auto-save
        self._auto_save_tags()
        
        self.app.set_status(f"Applied {len(tags)} tags to all {len(self.app.data_manager.images_data)} images")
    
    def show_context_menu(self, position):
        """Show context menu for table items with delete options"""
        context_menu = QMenu()
        
        # Add two delete options
        delete_from_list_action = context_menu.addAction("🗑️ Remove from List Only")
        delete_from_disk_action = context_menu.addAction("🗑️ Delete from Disk (Image + Description)")
        
        # Add separator for clarity
        context_menu.addSeparator()
        context_menu.addAction("Cancel")
        
        action = context_menu.exec(self.app.gallery_tab.table.mapToGlobal(position))
        
        if action == delete_from_list_action:
            self.delete_selected_row(from_disk=False)
        elif action == delete_from_disk_action:
            self.delete_selected_row(from_disk=True)
    
    def delete_selected_row(self, from_disk=False):
        """Delete the selected image from the list and optionally from disk"""
        current_row = self.app.gallery_tab.table.currentRow()
        if current_row < 0:
            return
        
        # Find the corresponding image data
        index, img_data = self.app.data_manager.find_image_by_row_index(current_row)
        if index < 0:
            return
        
        # Create appropriate confirmation message
        if from_disk:
            confirm_msg = f"Delete '{img_data['filename']}' from disk?\n\n"
            confirm_msg += "This will permanently delete:\n"
            confirm_msg += f"• Image file: {img_data['filename']}\n"
            confirm_msg += f"• Description file: {os.path.splitext(img_data['filename'])[0]}.txt (if exists)\n\n"
            confirm_msg += "This cannot be undone!"
            title = "Delete from Disk"
        else:
            confirm_msg = f"Remove '{img_data['filename']}' from the list?\n\n"
            confirm_msg += "The image and description files will remain on disk."
            title = "Remove from List"
        
        reply = QMessageBox.question(
            self.app, title, confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if from_disk:
                    # Delete files from disk
                    deleted_files = []
                    
                    # Delete image file
                    if os.path.exists(img_data['path']):
                        os.remove(img_data['path'])
                        deleted_files.append(img_data['filename'])
                    
                    # Delete description file
                    desc_filename = os.path.splitext(img_data['filename'])[0] + '.txt'
                    desc_path = os.path.join(os.path.dirname(img_data['path']), desc_filename)
                    if os.path.exists(desc_path):
                        os.remove(desc_path)
                        deleted_files.append(desc_filename)
                    
                    status_msg = f"Deleted from disk: {', '.join(deleted_files)}"
                else:
                    status_msg = f"Removed from list: {img_data['filename']}"
                
                # Remove from data manager and tag manager
                self.app.data_manager.remove_image(index)
                self.app.tag_manager.remove_image(img_data['filename'])
                
                # Refresh table
                self.populate_table(self.app.data_manager.images_data)
                
                # Update current selection
                if self.app.current_image_index >= index:
                    self.app.current_image_index = max(-1, self.app.current_image_index - 1)
                
                # Select next item if available
                if self.app.data_manager.images_data:
                    next_row = min(current_row, len(self.app.data_manager.images_data) - 1)
                    if next_row >= 0:
                        self.app.gallery_tab.table.selectRow(next_row)
                    else:
                        self._clear_image_display()
                else:
                    # No more images - disable Utils tab and clear display
                    self.app.tab_widget.setTabEnabled(1, False)
                    self._clear_image_display()
                    status_msg += " • No images remaining • Utils tab disabled"
                
                # Auto-save after deletion
                if from_disk:
                    self._auto_save_tags()
                
                self.app.set_status(status_msg)
                
            except Exception as e:
                error_msg = f"Error during deletion: {str(e)}"
                QMessageBox.critical(self.app, "Deletion Error", error_msg)
                self.app.set_status(error_msg)
    
    def _clear_image_display(self):
        """Clear the image display and current image tags"""
        self.app.gallery_tab.image_label.clear()
        self.app.current_image_index = -1
        
        # Clear current image tags display
        try:
            if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                self.app.gallery_tab.current_image_tags_widget.clear_display()
        except Exception as e:
            print(f"Error clearing current image tags display: {e}")
    
    def refresh_gallery(self):
        """Refresh the gallery by reloading images from the current folder"""
        if not self.app.data_manager.current_folder:
            return
            
        # Remember current selection
        current_filename = None
        if self.app.current_image_index >= 0:
            img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if img_data:
                current_filename = img_data['filename']
        
        # Reload images
        success, message, images_data = self.app.data_manager.load_images_from_folder(
            self.app.data_manager.current_folder
        )
        
        if success:
            # Re-initialize tag manager
            self.app.tag_manager.set_project_folder(self.app.data_manager.current_folder)
            
            self.populate_table(images_data)
            
            # Try to restore selection to the same image
            if current_filename:
                for i, img_data in enumerate(images_data):
                    if img_data['filename'] == current_filename:
                        self.app.gallery_tab.table.selectRow(i)
                        break
                else:
                    # Original image not found, select first item
                    if images_data:
                        self.app.gallery_tab.table.selectRow(0)
            else:
                # No previous selection, select first item
                if images_data:
                    self.app.gallery_tab.table.selectRow(0)
            
            self.app.set_status(f"Gallery refreshed • {message}")
        else:
            QMessageBox.warning(self.app, "Refresh Error", f"Could not refresh gallery: {message}")
    
    def fix_images(self):
        """Process images with user-selected options"""
        # Pass current folder as default
        dialog = ImageFixDialog(self.app, default_folder=self.app.data_manager.current_folder)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        options = dialog.result
        
        # Process images based on scope selection
        if self.app.utils_tab.fix_selected_radio.isChecked():
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self.app, "No Selection", "No images are selected. Please select images first or choose 'Fix All Images'.")
                return
            images_to_process = [img_data['filename'] for img_data in selected_images]
        else:
            images_to_process = None
        
        # Process images
        result = self.app.image_processor.fix_images(
            source_folder=options['source_folder'],
            target_size=options['size'],
            keep_aspect=options['keep_aspect'],
            output_folder=options['output_folder'],
            resize_small_images=options.get('resize_small_images', False),
            images_to_process=images_to_process,
            status_callback=self.app.set_status
        )
        
        if 'error' in result:
            QMessageBox.information(self.app, "No Images", result['error'])
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
        
        QMessageBox.information(self.app, "Processing Complete", message)
        self.app.set_status(f"Processed {result['processed']} images")
        
        # Refresh gallery if output is the same folder
        if options['output_folder'] == self.app.data_manager.current_folder:
            self.refresh_gallery()
    
    def create_duplicates(self):
        """Create duplicated images with transformations"""
        # Pass the current folder as the default input folder
        dialog = ImageDuplicateDialog(self.app, default_folder=self.app.data_manager.current_folder)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        options = dialog.result
        
        # Determine which images to process based on radio button selection
        if self.app.utils_tab.dup_selected_radio.isChecked():
            # Process only selected images
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self.app, "No Selection", "No images are selected. Please select images first or choose 'Duplicate All Images'.")
                return
            # Convert to simple filenames list for the processor
            images_to_process = [img_data['filename'] for img_data in selected_images]
        else:
            # Process all images - let the processor handle it
            images_to_process = None
        
        # Process duplicates
        result = self.app.image_processor.create_duplicates(
            input_folder=options['input_folder'],
            output_folder=options['output_folder'],
            transformations=options,
            images_to_process=images_to_process,
            status_callback=self.app.set_status
        )
        
        if 'error' in result:
            QMessageBox.information(self.app, "No Images", result['error'])
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
        
        QMessageBox.information(self.app, "Duplication Complete", message)
        self.app.set_status(f"Created {result['created_files']} files with transformations")
        
        # Refresh gallery if we're working in the same folder
        if options['output_folder'] == self.app.data_manager.current_folder:
            self.refresh_gallery()
    
    def mass_rename_images(self):
        """Rename images in the gallery folder with new prefix + numbers"""
        if not self.app.data_manager.current_folder:
            QMessageBox.information(self.app, "No Folder", "Please load images in the Gallery tab first.")
            return
            
        if not self.app.data_manager.images_data:
            QMessageBox.information(self.app, "No Images", "No images loaded to rename.")
            return
        
        # Get prefix from user
        prefix = self.app.utils_tab.prefix_entry.text().strip()
        if not prefix:
            QMessageBox.critical(self.app, "No Prefix", "Please enter a prefix for the new filenames.")
            return
        
        # Determine which images to process based on radio button selection
        if self.app.utils_tab.rename_selected_radio.isChecked():
            # Process only selected images
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self.app, "No Selection", "No images are selected. Please select images first or choose 'Rename All Images'.")
                return
            images_to_process = selected_images
            scope_text = f"{len(selected_images)} selected images"
        else:
            # Process all images
            images_to_process = self.app.data_manager.images_data
            scope_text = f"all {len(self.app.data_manager.images_data)} images"
        
        # Confirm with user
        confirm_msg = f"This will rename {scope_text} to:\n"
        confirm_msg += f"{prefix}001, {prefix}002, {prefix}003, etc.\n\n"
        confirm_msg += "Description files will also be renamed to match.\n"
        confirm_msg += "This operation cannot be undone. Continue?"
        
        reply = QMessageBox.question(
            self.app, "Confirm Mass Rename", confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform the rename operation
        result = self.app.image_processor.mass_rename_images(
            folder_path=self.app.data_manager.current_folder,
            prefix=prefix,
            images_to_process=images_to_process,
            status_callback=self.app.set_status
        )
        
        if 'error' in result:
            QMessageBox.critical(self.app, "Rename Error", result['error'])
            return
        
        # Show completion message
        message = f"Successfully renamed {result['renamed_images']} images and {result['renamed_descriptions']} description files.\n"
        if result['errors']:
            message += f"\nEncountered {len(result['errors'])} errors:\n"
            for error in result['errors'][:3]:
                message += f"  - {error}\n"
            if len(result['errors']) > 3:
                message += f"  ... and {len(result['errors']) - 3} more\n"
        
        QMessageBox.information(self.app, "Rename Complete", message)
        self.app.set_status(f"Renamed {result['renamed_images']} images with prefix '{prefix}'")
        
        # Clear the prefix field for next use
        self.app.utils_tab.prefix_entry.clear()
        
        # Refresh gallery to show new names
        self.refresh_gallery()
    
    def force_refresh_all_tags(self):
        """Force refresh all tag displays to update styling"""
        # Refresh all table rows
        for img_data in self.app.data_manager.images_data:
            self.refresh_image_row(img_data['filename'])
        
        # Refresh tag input widget
        try:
            if hasattr(self.app.gallery_tab, 'tag_input_widget'):
                self.app.gallery_tab.tag_input_widget.refresh_tag_display()
        except Exception as e:
            print(f"Warning: Could not refresh tag input widget: {e}")
        
        # Refresh current image tags display
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        self.app.set_status("Refreshed all tag displays")
    
    def test_tag_scramble(self):
        """Test tag scrambling with user input"""
        test_input = self.app.utils_tab.test_tags_entry.text().strip()
        if not test_input:
            self.app.utils_tab.test_scramble_result.setText("Please enter some test tags separated by commas.")
            return
        
        # Parse tags from input
        tags = [tag.strip() for tag in test_input.split(',') if tag.strip()]
        if len(tags) < 2:
            self.app.utils_tab.test_scramble_result.setText("Please enter at least 2 tags to see scrambling effect.")
            return
        
        # Get scrambling method
        preserve_first = self.app.utils_tab.preserve_first_tag.isChecked()
        
        # Generate multiple scrambled versions for demonstration
        original = ", ".join(tags)
        scrambled_versions = []
        
        for i in range(3):  # Show 3 different scrambled versions
            scrambled = self._scramble_tag_list(tags, preserve_first)
            scrambled_versions.append(", ".join(scrambled))
        
        result_text = f"Original: {original}\n\n"
        result_text += "Scrambled versions:\n"
        for i, version in enumerate(scrambled_versions, 1):
            result_text += f"{i}. {version}\n"
        
        self.app.utils_tab.test_scramble_result.setText(result_text)
    
    def preview_tag_scramble(self):
        """Preview tag scrambling changes without applying them"""
        if not self.app.data_manager.images_data:
            QMessageBox.information(self.app, "No Images", "Please load images in the Gallery tab first.")
            return
        
        # Determine which images to process
        if self.app.utils_tab.scramble_selected_radio.isChecked():
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self.app, "No Selection", "No images are selected. Please select images first or choose 'Scramble All Descriptions'.")
                return
            images_to_process = selected_images
            scope_text = f"{len(selected_images)} selected images"
        else:
            images_to_process = self.app.data_manager.images_data
            scope_text = f"all {len(self.app.data_manager.images_data)} images"
        
        # Filter to only images that have tags
        images_with_tags = []
        for img_data in images_to_process:
            tags = self.app.tag_manager.get_tags_for_image(img_data['filename'])
            if len(tags) > 1:  # Only include images with multiple tags
                images_with_tags.append((img_data, tags))
        
        if not images_with_tags:
            QMessageBox.information(self.app, "No Tags to Scramble", 
                                  f"No images in {scope_text} have multiple tags to scramble.\n\n"
                                  "Tag scrambling requires at least 2 tags per image.")
            return
        
        # Get scrambling method
        preserve_first = self.app.utils_tab.preserve_first_tag.isChecked()
        
        # Create preview dialog
        preview_dialog = QDialog(self.app)
        preview_dialog.setWindowTitle("Tag Scrambling Preview")
        preview_dialog.setModal(True)
        preview_dialog.resize(800, 600)
        
        layout = QVBoxLayout(preview_dialog)
        
        # Header
        header_label = QLabel(f"Preview of tag scrambling for {len(images_with_tags)} images:")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Method info
        method_text = "Method: " + ("Preserve first tag" if preserve_first else "Fully randomize all tags")
        method_label = QLabel(method_text)
        method_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(method_label)
        
        # Scrollable preview area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        preview_widget = QTextEdit()
        preview_widget.setReadOnly(True)
        preview_widget.setFont(self.app.default_font)
        
        # Generate preview content
        preview_content = ""
        sample_count = min(10, len(images_with_tags))  # Show up to 10 examples
        
        for i, (img_data, tags) in enumerate(images_with_tags[:sample_count]):
            original_tags = ", ".join(tags)
            scrambled_tags = ", ".join(self._scramble_tag_list(tags, preserve_first))
            
            preview_content += f"{i+1}. {img_data['filename']}\n"
            preview_content += f"   Original:  {original_tags}\n"
            preview_content += f"   Scrambled: {scrambled_tags}\n\n"
        
        if len(images_with_tags) > sample_count:
            preview_content += f"... and {len(images_with_tags) - sample_count} more images\n"
        
        preview_widget.setPlainText(preview_content)
        
        scroll_area.setWidget(preview_widget)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Scrambling")
        apply_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px; }")
        apply_btn.clicked.connect(lambda: (preview_dialog.accept(), self.scramble_tags()))
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(preview_dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        preview_dialog.exec()
    
    def scramble_tags(self):
        """Scramble tag order in selected images"""
        if not self.app.data_manager.images_data:
            QMessageBox.information(self.app, "No Images", "Please load images in the Gallery tab first.")
            return
        
        # Determine which images to process
        if self.app.utils_tab.scramble_selected_radio.isChecked():
            selected_images = self.get_selected_images()
            if not selected_images:
                QMessageBox.information(self.app, "No Selection", "No images are selected. Please select images first or choose 'Scramble All Descriptions'.")
                return
            images_to_process = selected_images
            scope_text = f"{len(selected_images)} selected images"
        else:
            images_to_process = self.app.data_manager.images_data
            scope_text = f"all {len(self.app.data_manager.images_data)} images"
        
        # Filter to only images that have multiple tags
        images_with_tags = []
        for img_data in images_to_process:
            tags = self.app.tag_manager.get_tags_for_image(img_data['filename'])
            if len(tags) > 1:  # Only scramble if there are multiple tags
                images_with_tags.append((img_data, tags))
        
        if not images_with_tags:
            QMessageBox.information(self.app, "No Tags to Scramble", 
                                  f"No images in {scope_text} have multiple tags to scramble.\n\n"
                                  "Tag scrambling requires at least 2 tags per image.")
            return
        
        # Get scrambling method
        preserve_first = self.app.utils_tab.preserve_first_tag.isChecked()
        method_text = "preserving first tag" if preserve_first else "fully randomizing"
        
        # Confirm with user
        confirm_msg = f"This will scramble tag order for {len(images_with_tags)} images (out of {scope_text}).\n\n"
        confirm_msg += f"Method: {method_text}\n\n"
        confirm_msg += "This operation will reorder the tags while keeping all tag content the same.\n"
        confirm_msg += "Changes will be auto-saved. Continue?"
        
        reply = QMessageBox.question(
            self.app, "Confirm Tag Scrambling", confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform scrambling
        scrambled_count = 0
        skipped_count = 0
        
        for img_data, tags in images_with_tags:
            try:
                # Scramble the tags
                scrambled_tags = self._scramble_tag_list(tags, preserve_first)
                
                # Apply the scrambled tags
                self.app.tag_manager.apply_tags_to_image(img_data['filename'], scrambled_tags)
                
                # Refresh the table row
                self.refresh_image_row(img_data['filename'])
                
                scrambled_count += 1
                
            except Exception as e:
                print(f"Error scrambling tags for {img_data['filename']}: {str(e)}")
                skipped_count += 1
        
        # Update current image tags display if needed
        if self.app.current_image_index >= 0:
            current_img_data = self.app.data_manager.get_image_data(self.app.current_image_index)
            if current_img_data:
                current_tags = self.app.tag_manager.get_tags_for_image(current_img_data['filename'])
                try:
                    if hasattr(self.app.gallery_tab, 'current_image_tags_widget'):
                        self.app.gallery_tab.current_image_tags_widget.set_image_tags(current_img_data['filename'], current_tags)
                except Exception as e:
                    print(f"Error updating current image tags display: {e}")
        
        # Auto-save all changes
        self._auto_save_tags()
        
        # Show completion message
        message = f"Tag scrambling complete!\n\n"
        message += f"Successfully scrambled: {scrambled_count} image tag sets\n"
        if skipped_count > 0:
            message += f"Skipped: {skipped_count} images (errors)\n"
        message += f"Method: {method_text}\n"
        message += f"\nTags auto-saved to disk."
        
        QMessageBox.information(self.app, "Scrambling Complete", message)
        self.app.set_status(f"Scrambled tags for {scrambled_count} images using {method_text} method")
    
    def _scramble_tag_list(self, tags, preserve_first=True):
        """
        Scramble a list of tags
        
        Args:
            tags: List of tag strings
            preserve_first: If True, keep the first tag (or keyword tag) in place
        
        Returns:
            List of scrambled tags
        """
        if len(tags) <= 1:
            return tags.copy()
        
        tags_copy = tags.copy()
        keyword_tag = self.app.tag_manager.get_keyword_tag() if self.app.tag_manager else None
        
        if preserve_first:
            # Determine which tag to preserve as first
            if keyword_tag and keyword_tag in tags_copy:
                # Preserve keyword tag as first
                first_tag = keyword_tag
                remaining_tags = [tag for tag in tags_copy if tag != keyword_tag]
            else:
                # Preserve the current first tag
                first_tag = tags_copy[0]
                remaining_tags = tags_copy[1:]
            
            # Scramble the remaining tags
            random.shuffle(remaining_tags)
            return [first_tag] + remaining_tags
        else:
            # Fully randomize, but still respect keyword tag positioning if it exists
            if keyword_tag and keyword_tag in tags_copy:
                # Even in full randomize, keyword should tend to be first more often
                other_tags = [tag for tag in tags_copy if tag != keyword_tag]
                random.shuffle(other_tags)
                # 70% chance keyword goes first even in "full randomize"
                if random.random() < 0.7:
                    return [keyword_tag] + other_tags
                else:
                    # Insert keyword at random position
                    random_pos = random.randint(0, len(other_tags))
                    other_tags.insert(random_pos, keyword_tag)
                    return other_tags
            else:
                # No keyword tag, fully scramble
                random.shuffle(tags_copy)
                return tags_copy