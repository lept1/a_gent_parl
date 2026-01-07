"""
PathManager - Independent path resolution and directory management utility.

This module provides path management functionality that is completely independent
of configuration management. It can auto-detect project root or accept it as a
parameter, and provides utilities for directory creation and path resolution.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union


class PathManager:
    """
    Independent path management utility that handles path resolution and directory creation.
    
    This class is designed to be completely self-contained and independent of any
    configuration management system. It can auto-detect the project root or accept
    it as a parameter.
    """
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize PathManager with optional project root.
        
        Args:
            project_root: Optional project root path. If not provided, will auto-detect.
        
        Raises:
            ValueError: If project root cannot be determined or is invalid.
        """
        if project_root is not None:
            self.project_root = Path(project_root).resolve()
            if not self.project_root.exists():
                raise ValueError(f"Provided project root does not exist: {self.project_root}")
        else:
            self.project_root = self._find_project_root()
        
        # Validate that project root is actually a directory
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {self.project_root}")
    
    def _find_project_root(self) -> Path:
        """
        Auto-detect project root by looking for common project indicators.
        
        Searches upward from the current file location for indicators like:
        - .git directory
        - README.md file
        - src directory
        - setup.py or pyproject.toml
        
        Returns:
            Path: The detected project root path.
            
        Raises:
            ValueError: If project root cannot be auto-detected.
        """
        # Start from the directory containing this file
        current_path = Path(__file__).parent.resolve()
        
        # Common project root indicators
        indicators = [
            '.git',
            'README.md',
            'src',
            'setup.py',
            'pyproject.toml',
            'requirements.txt',
            'requirement.txt'  # Based on the project structure shown
        ]
        
        # Search upward through parent directories
        for parent in [current_path] + list(current_path.parents):
            # Check if any indicator exists in this directory
            for indicator in indicators:
                if (parent / indicator).exists():
                    return parent
        
        # If no indicators found, fall back to a reasonable default
        # Go up two levels from utilities (utilities -> src -> project_root)
        fallback_root = current_path.parent.parent
        if fallback_root.exists() and fallback_root.is_dir():
            return fallback_root
        
        # Last resort: use current working directory
        cwd = Path.cwd()
        if cwd.exists() and cwd.is_dir():
            return cwd
        
        raise ValueError("Unable to auto-detect project root. Please provide project_root parameter.")
    
    def ensure_directory_exists(self, path: Union[str, Path]) -> str:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure exists. Can be absolute or relative to project root.
            
        Returns:
            str: The absolute path of the ensured directory.
            
        Raises:
            OSError: If directory cannot be created.
            ValueError: If path exists but is not a directory.
        """
        path_obj = Path(path)
        
        # If path is not absolute, make it relative to project root
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj
        
        # Resolve any relative components (like ..)
        path_obj = path_obj.resolve()
        
        # Check if path already exists
        if path_obj.exists():
            if not path_obj.is_dir():
                raise ValueError(f"Path exists but is not a directory: {path_obj}")
            return str(path_obj)
        
        # Create directory and any necessary parent directories
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            return str(path_obj)
        except OSError as e:
            raise OSError(f"Failed to create directory {path_obj}: {e}")
    
    def get_database_path(self, db_name: str, db_dir: Optional[str] = None) -> str:
        """
        Get the full path for a database file.
        
        Args:
            db_name: Name of the database file.
            db_dir: Optional directory for databases. If not provided, uses project root.
            
        Returns:
            str: The full path to the database file.
        """
        if db_dir:
            db_directory = self.ensure_directory_exists(db_dir)
            return str(Path(db_directory) / db_name)
        else:
            # Default to project root for backward compatibility
            return str(self.project_root / db_name)
    
    def get_images_path(self, images_dir: str, subdir: Optional[str] = None) -> str:
        """
        Get the full path for images directory with optional subdirectory.
        
        Args:
            images_dir: Base images directory.
            subdir: Optional subdirectory within images directory.
            
        Returns:
            str: The full path to the images directory.
        """
        base_path = self.ensure_directory_exists(images_dir)
        
        if subdir:
            full_path = Path(base_path) / subdir
            return self.ensure_directory_exists(full_path)
        
        return base_path
    
    def resolve_path(self, relative_path: Union[str, Path]) -> str:
        """
        Resolve a relative path against the project root.
        
        Args:
            relative_path: Path relative to project root.
            
        Returns:
            str: The absolute resolved path.
        """
        path_obj = Path(relative_path)
        
        # If already absolute, return as-is
        if path_obj.is_absolute():
            return str(path_obj.resolve())
        
        # Resolve relative to project root
        resolved = (self.project_root / path_obj).resolve()
        return str(resolved)
    
    def get_project_root(self) -> str:
        """
        Get the project root path.
        
        Returns:
            str: The absolute path to the project root.
        """
        return str(self.project_root)
    
    def validate_path(self, path: Union[str, Path], must_exist: bool = False) -> bool:
        """
        Validate a path for basic correctness.
        
        Args:
            path: Path to validate.
            must_exist: If True, path must exist on filesystem.
            
        Returns:
            bool: True if path is valid, False otherwise.
        """
        try:
            path_obj = Path(path)
            
            # Check if path is valid (no invalid characters, etc.)
            path_obj.resolve()
            
            # If must_exist is True, check existence
            if must_exist and not path_obj.exists():
                return False
            
            return True
        except (OSError, ValueError):
            return False
    
    def get_relative_path(self, absolute_path: Union[str, Path]) -> str:
        """
        Get a path relative to the project root.
        
        Args:
            absolute_path: Absolute path to make relative.
            
        Returns:
            str: Path relative to project root.
            
        Raises:
            ValueError: If path is not within project root.
        """
        abs_path = Path(absolute_path).resolve()
        
        try:
            relative = abs_path.relative_to(self.project_root)
            return str(relative)
        except ValueError:
            raise ValueError(f"Path {abs_path} is not within project root {self.project_root}")