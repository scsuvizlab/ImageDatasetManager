#!/usr/bin/env python3
"""
Group management system for the Image Gallery application
Handles creation, storage, and management of image groups
"""

import json
import os
import uuid
from typing import List, Dict, Set, Optional, Tuple


class ImageGroup:
    """Represents a group of images"""
    
    def __init__(self, group_id: str = None, name: str = "", image_filenames: List[str] = None, expanded: bool = True):
        self.group_id = group_id or str(uuid.uuid4())
        self.name = name
        self.image_filenames = image_filenames or []
        self.expanded = expanded
        self.created_timestamp = None
        
    def add_image(self, filename: str):
        """Add an image to the group"""
        if filename not in self.image_filenames:
            self.image_filenames.append(filename)
    
    def remove_image(self, filename: str):
        """Remove an image from the group"""
        if filename in self.image_filenames:
            self.image_filenames.remove(filename)
    
    def get_image_count(self) -> int:
        """Get the number of images in the group"""
        return len(self.image_filenames)
    
    def is_empty(self) -> bool:
        """Check if the group is empty"""
        return len(self.image_filenames) == 0
    
    def to_dict(self) -> Dict:
        """Convert group to dictionary for serialization"""
        return {
            'group_id': self.group_id,
            'name': self.name,
            'image_filenames': self.image_filenames,
            'expanded': self.expanded,
            'created_timestamp': self.created_timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ImageGroup':
        """Create group from dictionary"""
        group = cls(
            group_id=data.get('group_id'),
            name=data.get('name', ''),
            image_filenames=data.get('image_filenames', []),
            expanded=data.get('expanded', True)
        )
        group.created_timestamp = data.get('created_timestamp')
        return group


class GroupManager:
    """Manages image groups and their operations"""
    
    def __init__(self):
        self.groups: Dict[str, ImageGroup] = {}  # group_id -> ImageGroup
        self.image_to_group: Dict[str, str] = {}  # filename -> group_id
        self.project_folder: Optional[str] = None
        
    def set_project_folder(self, folder_path: str):
        """Set the current project folder and load groups if they exist"""
        self.project_folder = folder_path
        self.load_groups_from_project()
    
    def create_group(self, name: str, image_filenames: List[str]) -> str:
        """Create a new group with the given images"""
        # Remove images from existing groups first
        for filename in image_filenames:
            self.remove_image_from_group(filename)
        
        # Create new group
        group = ImageGroup(name=name, image_filenames=image_filenames.copy())
        self.groups[group.group_id] = group
        
        # Update image-to-group mapping
        for filename in image_filenames:
            self.image_to_group[filename] = group.group_id
        
        return group.group_id
    
    def rename_group(self, group_id: str, new_name: str) -> bool:
        """Rename a group"""
        if group_id in self.groups:
            self.groups[group_id].name = new_name
            return True
        return False
    
    def delete_group(self, group_id: str) -> bool:
        """Delete a group (images become ungrouped) - with debugging"""
        print(f"DEBUG: GroupManager.delete_group called for {group_id}")
        
        if group_id not in self.groups:
            print(f"DEBUG: Group {group_id} not found in groups")
            return False
        
        # Remove images from image-to-group mapping
        group = self.groups[group_id]
        print(f"DEBUG: Deleting group '{group.name}' with {len(group.image_filenames)} images")
        
        for filename in group.image_filenames:
            if filename in self.image_to_group:
                print(f"DEBUG: Removing {filename} from image_to_group mapping")
                del self.image_to_group[filename]
        
        # Remove group
        del self.groups[group_id]
        print(f"DEBUG: Group {group_id} deleted. Remaining groups: {len(self.groups)}")
        return True
    
    def add_images_to_group(self, group_id: str, image_filenames: List[str]) -> bool:
        """Add images to an existing group"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        for filename in image_filenames:
            # Remove from any existing group first
            self.remove_image_from_group(filename)
            
            # Add to this group
            group.add_image(filename)
            self.image_to_group[filename] = group_id
        
        return True
    
    def remove_images_from_group(self, group_id: str, image_filenames: List[str]) -> bool:
        """Remove images from a group"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        for filename in image_filenames:
            group.remove_image(filename)
            if filename in self.image_to_group and self.image_to_group[filename] == group_id:
                del self.image_to_group[filename]
        
        return True
    
    def remove_image_from_group(self, filename: str) -> bool:
        """Remove an image from whatever group it's in - with debugging"""
        print(f"DEBUG: Attempting to remove {filename} from group")
        
        if filename not in self.image_to_group:
            print(f"DEBUG: {filename} is not in any group")
            return False
        
        group_id = self.image_to_group[filename]
        print(f"DEBUG: {filename} is in group {group_id}")
        
        if group_id in self.groups:
            group = self.groups[group_id]
            print(f"DEBUG: Removing {filename} from group '{group.name}'")
            group.remove_image(filename)
            print(f"DEBUG: Group now has {len(group.image_filenames)} images")
        else:
            print(f"DEBUG: Group {group_id} not found in groups dict")
        
        del self.image_to_group[filename]
        print(f"DEBUG: Removed {filename} from image_to_group mapping")
        return True
    
    def get_group_for_image(self, filename: str) -> Optional[ImageGroup]:
        """Get the group that contains an image"""
        if filename in self.image_to_group:
            group_id = self.image_to_group[filename]
            return self.groups.get(group_id)
        return None
    
    def get_group_by_id(self, group_id: str) -> Optional[ImageGroup]:
        """Get a group by its ID"""
        return self.groups.get(group_id)
    
    def get_all_groups(self) -> List[ImageGroup]:
        """Get all groups sorted by name"""
        return sorted(self.groups.values(), key=lambda g: g.name.lower())
    
    def get_ungrouped_images(self, all_image_filenames: List[str]) -> List[str]:
        """Get images that are not in any group"""
        return [filename for filename in all_image_filenames 
                if filename not in self.image_to_group]
    
    def toggle_group_expansion(self, group_id: str) -> bool:
        """Toggle the expanded state of a group"""
        if group_id in self.groups:
            self.groups[group_id].expanded = not self.groups[group_id].expanded
            return True
        return False
    
    def set_group_expansion(self, group_id: str, expanded: bool) -> bool:
        """Set the expanded state of a group"""
        if group_id in self.groups:
            self.groups[group_id].expanded = expanded
            return True
        return False
    
    def is_group_expanded(self, group_id: str) -> bool:
        """Check if a group is expanded"""
        if group_id in self.groups:
            return self.groups[group_id].expanded
        return True
    
    def expand_all_groups(self):
        """Expand all groups"""
        for group in self.groups.values():
            group.expanded = True
    
    def collapse_all_groups(self):
        """Collapse all groups"""
        for group in self.groups.values():
            group.expanded = False
    
    def clean_up_empty_groups(self):
        """Remove empty groups"""
        empty_group_ids = [group_id for group_id, group in self.groups.items() if group.is_empty()]
        for group_id in empty_group_ids:
            self.delete_group(group_id)
    
    def rename_image(self, old_filename: str, new_filename: str):
        """Update group mappings when an image is renamed"""
        if old_filename in self.image_to_group:
            group_id = self.image_to_group[old_filename]
            group = self.groups[group_id]
            
            # Update filename in group
            if old_filename in group.image_filenames:
                index = group.image_filenames.index(old_filename)
                group.image_filenames[index] = new_filename
            
            # Update mapping
            del self.image_to_group[old_filename]
            self.image_to_group[new_filename] = group_id
    
    def remove_image(self, filename: str):
        """Remove an image from all groups (when image is deleted)"""
        self.remove_image_from_group(filename)
        self.clean_up_empty_groups()
    
    def get_display_order(self, all_image_filenames: List[str]) -> List[Tuple[str, str, bool]]:
        """
        Get the display order for the table
        Returns list of tuples: (type, data, is_group_member)
        - type: 'group' or 'image'
        - data: group_id or filename
        - is_group_member: True if this is an image row that belongs to a group
        """
        display_order = []
        processed_images = set()
        
        # Add groups and their images
        for group in self.get_all_groups():
            # Add group header
            display_order.append(('group', group.group_id, False))
            
            # Add group images if expanded
            if group.expanded:
                for filename in group.image_filenames:
                    if filename in all_image_filenames:  # Only show if image still exists
                        display_order.append(('image', filename, True))
                        processed_images.add(filename)
        
        # Add ungrouped images
        ungrouped = self.get_ungrouped_images(all_image_filenames)
        for filename in ungrouped:
            display_order.append(('image', filename, False))
            processed_images.add(filename)
        
        return display_order
    
    def save_groups_to_project(self) -> Tuple[bool, str]:
        """Save groups to project folder - with debugging"""
        if not self.project_folder:
            return False, "No project folder set"
        
        print(f"DEBUG: Saving groups to {self.project_folder}")
        print(f"DEBUG: Total groups to save: {len(self.groups)}")
        
        try:
            groups_data = {
                'groups': {group_id: group.to_dict() for group_id, group in self.groups.items()},
                'image_to_group': self.image_to_group,
                'version': '1.0'
            }
            
            groups_file = os.path.join(self.project_folder, 'groups.json')
            print(f"DEBUG: Writing to {groups_file}")
            
            with open(groups_file, 'w', encoding='utf-8') as f:
                json.dump(groups_data, f, indent=2, ensure_ascii=False)
            
            print(f"DEBUG: Successfully saved {len(self.groups)} groups")
            return True, f"Groups saved to {groups_file}"
        
        except Exception as e:
            error_msg = f"Error saving groups: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return False, error_msg
    
    def load_groups_from_project(self) -> Tuple[bool, str]:
        """Load groups from project folder - with debugging"""
        if not self.project_folder:
            print("DEBUG: No project folder set")
            return False, "No project folder set"
        
        groups_file = os.path.join(self.project_folder, 'groups.json')
        print(f"DEBUG: Loading groups from {groups_file}")
        
        if not os.path.exists(groups_file):
            print("DEBUG: No groups file found")
            return False, "No groups file found"
        
        try:
            with open(groups_file, 'r', encoding='utf-8') as f:
                groups_data = json.load(f)
            
            # Load groups
            self.groups = {}
            for group_id, group_dict in groups_data.get('groups', {}).items():
                self.groups[group_id] = ImageGroup.from_dict(group_dict)
            
            # Load image-to-group mapping
            self.image_to_group = groups_data.get('image_to_group', {})
            
            print(f"DEBUG: Loaded {len(self.groups)} groups")
            print(f"DEBUG: Loaded {len(self.image_to_group)} image mappings")
            
            return True, f"Groups loaded from {groups_file}"
        
        except Exception as e:
            error_msg = f"Error loading groups: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return False, error_msg
    
    def get_statistics(self) -> Dict[str, int]:
        """Get group statistics"""
        total_grouped_images = len(self.image_to_group)
        return {
            'total_groups': len(self.groups),
            'total_grouped_images': total_grouped_images,
            'largest_group_size': max([group.get_image_count() for group in self.groups.values()], default=0),
            'average_group_size': total_grouped_images // len(self.groups) if self.groups else 0
        }
    
    def debug_state(self):
        """Print debug information about current group state"""
        print(f"\n=== GROUP MANAGER DEBUG ===")
        print(f"Project folder: {self.project_folder}")
        print(f"Total groups: {len(self.groups)}")
        print(f"Image mappings: {len(self.image_to_group)}")
        
        for group_id, group in self.groups.items():
            print(f"Group {group_id}: '{group.name}'")
            print(f"  Images: {group.image_filenames}")
            print(f"  Expanded: {group.expanded}")
        
        print(f"Image-to-group mapping:")
        for filename, group_id in self.image_to_group.items():
            print(f"  {filename} -> {group_id}")
        print("============================\n")
    
    def validate_consistency(self):
        """Check for consistency issues in group data"""
        issues = []
        
        # Check if all groups in image_to_group exist
        for filename, group_id in self.image_to_group.items():
            if group_id not in self.groups:
                issues.append(f"Image {filename} mapped to non-existent group {group_id}")
        
        # Check if all images in groups are in the mapping
        for group_id, group in self.groups.items():
            for filename in group.image_filenames:
                if filename not in self.image_to_group or self.image_to_group[filename] != group_id:
                    issues.append(f"Group {group_id} contains {filename} but mapping is inconsistent")
        
        if issues:
            print("DEBUG: Group consistency issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("DEBUG: Group data is consistent")
        
        return issues