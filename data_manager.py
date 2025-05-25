#!/usr/bin/env python3
"""
Data management for Image Gallery application
"""

import os
import json
from PyQt6.QtWidgets import QMessageBox


class DataManager:
    """Manages loading and saving of image data and descriptions"""
    
    def __init__(self):
        self.images_data = []
        self.current_folder = ""
    
    def load_images_from_folder(self, folder_path):
        """
        Load images and descriptions from the selected folder
        
        Args:
            folder_path: Path to folder containing images
            
        Returns:
            tuple: (success, message, images_data)
        """
        # Clear existing data
        self.images_data = []
        self.current_folder = folder_path
        
        # Support image formats
        image_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        
        # Check for JSON file
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        descriptions_from_json = {}
        json_message = ""
        
        if json_files:
            try:
                json_path = os.path.join(folder_path, json_files[0])
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                    # Create lookup dictionary
                    for item in json_data:
                        if 'fileName' in item and 'description' in item:
                            descriptions_from_json[item['fileName']] = item['description']
                    json_message = f"Loaded descriptions from {json_files[0]}"
            except Exception as e:
                return False, f"Error loading JSON file: {str(e)}", []
        
        # Get all image files
        image_files = [f for f in os.listdir(folder_path) 
                      if os.path.isfile(os.path.join(folder_path, f)) 
                      and f.lower().endswith(image_extensions)]
        
        if not image_files:
            return False, "No images found in the selected folder", []
            
        # Get text files for descriptions if no JSON
        text_descriptions = {}
        if not descriptions_from_json:
            for img_file in image_files:
                base_name = os.path.splitext(img_file)[0]
                txt_file = f"{base_name}.txt"
                txt_path = os.path.join(folder_path, txt_file)
                
                if os.path.isfile(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            text_descriptions[img_file] = f.read().strip()
                    except Exception as e:
                        print(f"Error reading {txt_file}: {str(e)}")
        
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
                
                # Store image data
                self.images_data.append({
                    'path': img_path,
                    'filename': img_file,
                    'description': description,
                    'row_index': i  # Will be updated by the table
                })
                
            except Exception as e:
                print(f"Error processing {img_file}: {str(e)}")
        
        success_message = f"Loaded {len(self.images_data)} images from {os.path.basename(folder_path)}"
        if json_message:
            success_message = json_message + f" • {success_message}"
            
        return True, success_message, self.images_data
    
    def save_descriptions(self, folder_path=None):
        """
        Save descriptions to text files and JSON
        
        Args:
            folder_path: Optional folder path, uses current_folder if None
            
        Returns:
            tuple: (success, message)
        """
        if not self.images_data:
            return False, "No images to save descriptions for"
        
        save_folder = folder_path or self.current_folder
        if not save_folder:
            return False, "No folder specified for saving"
        
        try:
            # Save individual text files
            for img_data in self.images_data:
                base_name = os.path.splitext(img_data['filename'])[0]
                txt_file = f"{base_name}.txt"
                txt_path = os.path.join(save_folder, txt_file)
                
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(img_data['description'])
            
            # Save JSON for future loading
            json_data = []
            for img_data in self.images_data:
                json_data.append({
                    'fileName': img_data['filename'],
                    'description': img_data['description']
                })
            
            json_filename = f"{os.path.basename(save_folder)}_descriptions.json"
            json_path = os.path.join(save_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            message = f"Saved {len(self.images_data)} descriptions to text files and {json_filename}"
            return True, message
            
        except Exception as e:
            return False, f"Error saving descriptions: {str(e)}"
    
    def update_description(self, index, new_description):
        """
        Update description for a specific image
        
        Args:
            index: Index of image in images_data
            new_description: New description text
            
        Returns:
            bool: Success status
        """
        if 0 <= index < len(self.images_data):
            self.images_data[index]['description'] = new_description.strip()
            return True
        return False
    
    def append_keyword_to_all(self, keyword):
        """
        Add a keyword to all descriptions
        
        Args:
            keyword: Keyword to append
            
        Returns:
            int: Number of descriptions updated
        """
        if not keyword or not self.images_data:
            return 0
        
        updated_count = 0
        for img_data in self.images_data:
            current_desc = img_data['description']
            separator = ' ' if current_desc else ''
            img_data['description'] = current_desc + separator + keyword
            updated_count += 1
        
        return updated_count
    
    def remove_image(self, index):
        """
        Remove an image from the dataset
        
        Args:
            index: Index of image to remove
            
        Returns:
            bool: Success status
        """
        if 0 <= index < len(self.images_data):
            self.images_data.pop(index)
            # Update row indices for remaining images
            for i in range(index, len(self.images_data)):
                if self.images_data[i]['row_index'] > index:
                    self.images_data[i]['row_index'] -= 1
            return True
        return False
    
    def get_image_data(self, index):
        """
        Get image data by index
        
        Args:
            index: Index of image
            
        Returns:
            dict or None: Image data dictionary
        """
        if 0 <= index < len(self.images_data):
            return self.images_data[index]
        return None
    
    def find_image_by_row_index(self, row_index):
        """
        Find image data by table row index
        
        Args:
            row_index: Table row index
            
        Returns:
            tuple: (found_index, image_data) or (-1, None)
        """
        for i, img_data in enumerate(self.images_data):
            if img_data['row_index'] == row_index:
                return i, img_data
        return -1, None
    
    def update_row_indices(self, table_data):
        """
        Update row indices to match table state
        
        Args:
            table_data: List of (filename, description) tuples from table
        """
        # Create a mapping from filename to new row index
        filename_to_row = {filename: i for i, (filename, _) in enumerate(table_data)}
        
        # Update row indices in images_data
        for img_data in self.images_data:
            filename = img_data['filename']
            if filename in filename_to_row:
                img_data['row_index'] = filename_to_row[filename]
    
    def get_stats(self):
        """
        Get dataset statistics
        
        Returns:
            dict: Statistics about the dataset
        """
        if not self.images_data:
            return {
                'total_images': 0,
                'with_descriptions': 0,
                'without_descriptions': 0,
                'avg_description_length': 0
            }
        
        with_desc = sum(1 for img in self.images_data if img['description'].strip())
        without_desc = len(self.images_data) - with_desc
        
        total_length = sum(len(img['description']) for img in self.images_data if img['description'].strip())
        avg_length = total_length / with_desc if with_desc > 0 else 0
        
        return {
            'total_images': len(self.images_data),
            'with_descriptions': with_desc,
            'without_descriptions': without_desc,
            'avg_description_length': round(avg_length, 1)
        }