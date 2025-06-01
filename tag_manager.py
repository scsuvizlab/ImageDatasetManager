#!/usr/bin/env python3
"""
Tag management system for the Image Gallery application
Handles tag creation, storage, and application to images with keyword support
"""

import json
import os
import re
from typing import List, Dict, Set, Optional


class TagManager:
    """Manages tag definitions and their application to images"""
    
    def __init__(self):
        self.available_tags: Set[str] = set()
        self.tag_categories: Dict[str, List[str]] = {}
        self.image_tags: Dict[str, List[str]] = {}  # filename -> tags
        self.keyword_tag: Optional[str] = None  # The single keyword tag
        self.project_folder: Optional[str] = None
        
    def set_project_folder(self, folder_path: str):
        """Set the current project folder and load tags if they exist"""
        self.project_folder = folder_path
        self.load_tags_from_project()
    
    def add_tag(self, tag: str, category: str = "general"):
        """Add a new tag to the available tags"""
        if not tag.strip():
            return
        
        tag = tag.strip()
        self.available_tags.add(tag)
        
        if category not in self.tag_categories:
            self.tag_categories[category] = []
        if tag not in self.tag_categories[category]:
            self.tag_categories[category].append(tag)
    
    def add_tags_from_list(self, tags: List[str]):
        """Add multiple tags from a list"""
        for tag in tags:
            if tag.strip():
                self.add_tag(tag.strip())
    
    def remove_tag(self, tag: str):
        """Remove a tag from the system"""
        self.available_tags.discard(tag)
        for category in self.tag_categories.values():
            if tag in category:
                category.remove(tag)
        
        # Remove from all images
        for filename in self.image_tags:
            if tag in self.image_tags[filename]:
                self.image_tags[filename].remove(tag)
        
        # Clear keyword if this tag was the keyword
        if self.keyword_tag == tag:
            self.keyword_tag = None
    
    def set_keyword_tag(self, tag: str):
        """Set a tag as the keyword tag (only one can be keyword)"""
        if tag in self.available_tags:
            self.keyword_tag = tag
    
    def clear_keyword_tag(self):
        """Clear the current keyword tag"""
        self.keyword_tag = None
    
    def is_keyword_tag(self, tag: str) -> bool:
        """Check if a tag is the keyword tag"""
        return self.keyword_tag == tag
    
    def get_keyword_tag(self) -> Optional[str]:
        """Get the current keyword tag"""
        return self.keyword_tag
    
    def toggle_keyword_tag(self, tag: str):
        """Toggle a tag as keyword (set if not keyword, clear if already keyword)"""
        if self.keyword_tag == tag:
            self.keyword_tag = None
        else:
            self.keyword_tag = tag
    
    def get_tags_for_image(self, filename: str) -> List[str]:
        """Get all tags applied to an image, with keyword first if present"""
        tags = self.image_tags.get(filename, []).copy()
        return self._sort_tags_with_keyword_first(tags)
    
    def _sort_tags_with_keyword_first(self, tags: List[str]) -> List[str]:
        """Sort tags with keyword tag first, others in original order"""
        if not self.keyword_tag or self.keyword_tag not in tags:
            return tags
        
        # Put keyword first, keep others in order
        result = [self.keyword_tag]
        result.extend([tag for tag in tags if tag != self.keyword_tag])
        return result
    
    def apply_tags_to_image(self, filename: str, tags: List[str]):
        """Apply tags to an image (replaces existing tags)"""
        clean_tags = [tag.strip() for tag in tags if tag.strip()]
        # Store tags in original order - sorting happens in get_tags_for_image
        self.image_tags[filename] = clean_tags
        
        # Add tags to available tags if they don't exist
        for tag in clean_tags:
            self.add_tag(tag)
    
    def add_tags_to_image(self, filename: str, tags: List[str]):
        """Add tags to an image (keeps existing tags)"""
        existing_tags = self.image_tags.get(filename, [])
        all_tags = list(set(existing_tags + [tag.strip() for tag in tags if tag.strip()]))
        self.apply_tags_to_image(filename, all_tags)
    
    def remove_tag_from_image(self, filename: str, tag: str):
        """Remove a specific tag from an image"""
        if filename in self.image_tags and tag in self.image_tags[filename]:
            self.image_tags[filename].remove(tag)
    
    def get_all_tags(self) -> List[str]:
        """Get all available tags sorted alphabetically"""
        return sorted(list(self.available_tags))
    
    def get_tags_by_category(self) -> Dict[str, List[str]]:
        """Get tags organized by category"""
        return self.tag_categories.copy()
    
    def parse_tags_from_text(self, text: str) -> List[str]:
        """Parse tags from comma or semicolon separated text"""
        if not text.strip():
            return []
        
        # Split by comma or semicolon, handle multiple spaces
        tags = re.split(r'[,;]\s*', text.strip())
        
        # Clean up tags (strip whitespace, remove empty, normalize)
        clean_tags = []
        for tag in tags:
            tag = tag.strip()
            if tag:
                # Normalize whitespace within tags
                tag = re.sub(r'\s+', ' ', tag)
                clean_tags.append(tag)
        
        return clean_tags
    
    def format_tags_for_description(self, tags: List[str]) -> str:
        """Format tags for traditional description text, with keyword first"""
        sorted_tags = self._sort_tags_with_keyword_first(tags)
        return ", ".join(sorted_tags)
    
    def get_image_count_for_tag(self, tag: str) -> int:
        """Get the number of images that have this tag"""
        count = 0
        for tags in self.image_tags.values():
            if tag in tags:
                count += 1
        return count
    
    def get_unused_tags(self) -> List[str]:
        """Get tags that aren't applied to any images"""
        used_tags = set()
        for tags in self.image_tags.values():
            used_tags.update(tags)
        return sorted(list(self.available_tags - used_tags))
    
    def apply_tags_to_multiple_images(self, filenames: List[str], tags: List[str], replace: bool = False):
        """Apply tags to multiple images"""
        for filename in filenames:
            if replace:
                self.apply_tags_to_image(filename, tags)
            else:
                self.add_tags_to_image(filename, tags)
    
    def clear_tags_from_image(self, filename: str):
        """Remove all tags from an image"""
        if filename in self.image_tags:
            del self.image_tags[filename]
    
    def rename_image(self, old_filename: str, new_filename: str):
        """Update tag mapping when an image is renamed"""
        if old_filename in self.image_tags:
            self.image_tags[new_filename] = self.image_tags[old_filename]
            del self.image_tags[old_filename]
    
    def remove_image(self, filename: str):
        """Remove an image from tag mappings"""
        if filename in self.image_tags:
            del self.image_tags[filename]
    
    def save_tags_to_project(self):
        """Save tags and mappings to project folder"""
        if not self.project_folder:
            return False, "No project folder set"
        
        try:
            # Create tags data structure
            tags_data = {
                'available_tags': list(self.available_tags),
                'tag_categories': self.tag_categories,
                'image_tags': self.image_tags,
                'keyword_tag': self.keyword_tag,  # Save keyword tag
                'version': '2.0'  # Increment version for keyword support
            }
            
            # Save to tags.json file
            tags_file = os.path.join(self.project_folder, 'tags.json')
            with open(tags_file, 'w', encoding='utf-8') as f:
                json.dump(tags_data, f, indent=2, ensure_ascii=False)
            
            return True, f"Tags saved to {tags_file}"
        
        except Exception as e:
            return False, f"Error saving tags: {str(e)}"
    
    def load_tags_from_project(self):
        """Load tags and mappings from project folder"""
        if not self.project_folder:
            return False, "No project folder set"
        
        tags_file = os.path.join(self.project_folder, 'tags.json')
        if not os.path.exists(tags_file):
            return False, "No tags file found"
        
        try:
            with open(tags_file, 'r', encoding='utf-8') as f:
                tags_data = json.load(f)
            
            # Load data
            self.available_tags = set(tags_data.get('available_tags', []))
            self.tag_categories = tags_data.get('tag_categories', {})
            self.image_tags = tags_data.get('image_tags', {})
            self.keyword_tag = tags_data.get('keyword_tag', None)  # Load keyword tag
            
            return True, f"Tags loaded from {tags_file}"
        
        except Exception as e:
            return False, f"Error loading tags: {str(e)}"
    
    def migrate_from_text_descriptions(self, image_data_list: List[Dict]):
        """Convert text descriptions to tags for existing datasets"""
        for img_data in image_data_list:
            description = img_data.get('description', '')
            if description.strip():
                tags = self.parse_tags_from_text(description)
                if tags:
                    self.apply_tags_to_image(img_data['filename'], tags)
        
        return len([img for img in image_data_list if img.get('description', '').strip()])
    
    def export_to_text_descriptions(self, image_data_list: List[Dict]):
        """Convert tags back to text descriptions for compatibility"""
        updated_count = 0
        for img_data in image_data_list:
            filename = img_data['filename']
            tags = self.get_tags_for_image(filename)  # This will sort with keyword first
            if tags:
                img_data['description'] = self.format_tags_for_description(tags)
                updated_count += 1
            elif not img_data.get('description'):
                img_data['description'] = ""
        
        return updated_count
    
    def get_statistics(self) -> Dict[str, int]:
        """Get tag usage statistics"""
        return {
            'total_tags': len(self.available_tags),
            'total_images_with_tags': len([f for f in self.image_tags if self.image_tags[f]]),
            'total_tag_assignments': sum(len(tags) for tags in self.image_tags.values()),
            'unused_tags': len(self.get_unused_tags()),
            'has_keyword_tag': 1 if self.keyword_tag else 0
        }
    
    def clear_all_tags(self):
        """Clear all tags and tag assignments"""
        self.available_tags.clear()
        self.tag_categories.clear()
        self.image_tags.clear()
        self.keyword_tag = None