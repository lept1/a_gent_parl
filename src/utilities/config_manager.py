"""
Generic Configuration Manager for a_gent_parl modules.

This module provides a centralized configuration management system that can be
used across all modules in the project. It handles category management, path
resolution, data directory creation, and validation constants.
"""

import os
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """
    Generic configuration manager for all a_gent_parl modules.
    
    Provides centralized configuration management including:
    - Category management with validation
    - Data directory path resolution and creation
    - Module-specific configuration loading
    - Validation constants management
    - Environment path resolution
    """
    
    def __init__(self, module_name: str):
        """
        Initialize the ConfigManager for a specific module.
        
        Args:
            module_name: Name of the module using this configuration manager
        """
        self.module_name = module_name
        self._categories: List[str] = []
        self._validation_constants: Dict[str, Any] = {}
        self._project_root = self._find_project_root()
        
        # Set default validation constants
        self._set_default_validation_constants()
    
    def _find_project_root(self) -> Path:
        """
        Find the project root directory by looking for key indicators.
        
        Returns:
            Path: Path to the project root directory
        """
        current_path = Path(__file__).parent
        
        # Look for project indicators going up the directory tree
        while current_path.parent != current_path:
            if (current_path / "a_gent_parl").exists() or (current_path / "src").exists():
                return current_path
            current_path = current_path.parent
        
        # Fallback to current directory structure
        return Path(__file__).parent.parent.parent
    
    def _set_default_validation_constants(self) -> None:
        """Set default validation constants that can be overridden."""
        self._validation_constants = {
            'min_content_length': 500,
            'max_retries': 5,
            'post_length_min': 200,
            'post_length_max': 500,
            'telegram_retry_attempts': 3,
            'telegram_retry_delay': 30
        }
    
    def load_categories(self, categories: List[str]) -> None:
        """
        Load categories for this module.
        
        Args:
            categories: List of category names to load
        """
        self._categories = categories.copy()
    
    def select_random_category(self) -> str:
        """
        Select a random category from the loaded categories.
        
        Returns:
            str: A randomly selected category name
            
        Raises:
            ValueError: If no categories have been loaded
        """
        if not self._categories:
            raise ValueError("No categories loaded. Call load_categories() first.")
        
        return random.choice(self._categories)
    
    def get_all_categories(self) -> List[str]:
        """
        Get all loaded categories.
        
        Returns:
            List[str]: Copy of all loaded categories
        """
        return self._categories.copy()
    
    def is_valid_category(self, category: str) -> bool:
        """
        Check if a category is in the loaded categories list.
        
        Args:
            category: Category name to validate
            
        Returns:
            bool: True if category is valid, False otherwise
        """
        return category in self._categories
    
    def get_env_path(self) -> str:
        """
        Get the path to the environment file.
        
        Returns:
            str: Path to the .env file in utilities directory
        """
        return str(self._project_root / "src" / "utilities" / ".env")

    def load_environment_variables(self):
        """Load environment variables using existing project pattern."""
        # Follow the existing project pattern - utilities use '../utilities/.env'
        utilities_env_path = self.get_env_path()
        
        if os.path.exists(utilities_env_path):
            load_dotenv(utilities_env_path, verbose=True)
        else:
            raise FileNotFoundError(f"Environment file not found at {utilities_env_path}")
        
        # Validate required environment variables
        required_vars = ['GEMINI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'CHANNEL_ID', 'USER_WIKI', 'GITHUB_REPO', 'APP_NAME', 'VERSION']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.strip() == '':
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


    
    def get_database_path(self, db_name: str) -> str:
        """
        Get the path to a database file in the data/databases/ directory.
        
        Args:
            db_name: Name of the database file
            
        Returns:
            str: Full path to the database file
        """
        return str(self._project_root / "data" / "databases" / db_name)
    
    def get_log_directory(self) -> str:
        """
        Get the path to the logs directory for this module.
        
        Returns:
            str: Path to the module-specific logs directory
        """
        return str(self._project_root / "data" / "logs" / self.module_name)
    
    def get_cache_directory(self) -> str:
        """
        Get the path to the cache directory.
        
        Returns:
            str: Path to the cache directory
        """
        return str(self._project_root / "data" / "cache")
    
    def get_images_directory(self, subdir: Optional[str] = None) -> str:
        """
        Get the path to the images directory or a subdirectory.
        
        Args:
            subdir: Optional subdirectory name (e.g., 'posted', 'pending', 'archive')
            
        Returns:
            str: Path to the images directory or subdirectory
        """
        base_path = self._project_root / "data" / "images"
        
        if subdir:
            return str(base_path / subdir)
        
        return str(base_path)  
  
    def ensure_data_directories(self) -> None:
        """
        Create all data directories if they don't exist.
        
        Creates the following directory structure:
        - data/databases/
        - data/logs/{module_name}/
        - data/images/posted/
        - data/images/pending/
        - data/images/archive/
        - data/cache/
        """
        directories_to_create = [
            self._project_root / "data" / "databases",
            self._project_root / "data" / "logs" / self.module_name,
            self._project_root / "data" / "images" / "posted",
            self._project_root / "data" / "images" / "pending", 
            self._project_root / "data" / "images" / "archive",
            self._project_root / "data" / "cache"
        ]
        
        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    def set_validation_constants(self, **kwargs) -> None:
        """
        Set or update validation constants.
        
        Args:
            **kwargs: Key-value pairs of validation constants to set
        """
        self._validation_constants.update(kwargs)
    
    def get_validation_constant(self, key: str) -> Any:
        """
        Get a validation constant value.
        
        Args:
            key: The constant key to retrieve
            
        Returns:
            Any: The constant value
            
        Raises:
            KeyError: If the constant key doesn't exist
        """
        if key not in self._validation_constants:
            raise KeyError(f"Validation constant '{key}' not found")
        
        return self._validation_constants[key]
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate all configuration settings and return status.
        
        Returns:
            Dict[str, Any]: Configuration validation results including:
                - database_directory_exists: Whether data/databases/ exists
                - env_file_exists: Whether .env file exists
                - categories_count: Number of loaded categories
                - validation_constants: Current validation constants
                - data_directories_status: Status of data directories
        """
        validation_results = {
            'module_name': self.module_name,
            'project_root': str(self._project_root),
            'database_directory_exists': (self._project_root / "data" / "databases").exists(),
            'env_file_exists': Path(self.get_env_path()).exists(),
            'categories_count': len(self._categories),
            'categories': self._categories,
            'validation_constants': self._validation_constants.copy(),
            'data_directories_status': {
                'databases': (self._project_root / "data" / "databases").exists(),
                'logs': (self._project_root / "data" / "logs" / self.module_name).exists(),
                'images': (self._project_root / "data" / "images").exists(),
                'cache': (self._project_root / "data" / "cache").exists()
            }
        }
        
        return validation_results
    
    def get_module_database_path(self, db_name: Optional[str] = None) -> str:
        """
        Get the database path for this specific module.
        
        Args:
            db_name: Optional specific database name. If not provided,
                    uses module_name.sqlite3
                    
        Returns:
            str: Path to the module's database file
        """
        if db_name is None:
            db_name = f"{self.module_name}.sqlite3"
        
        return self.get_database_path(db_name)
    
    def get_legacy_database_path(self, db_name: str) -> str:
        """
        Get path to legacy database location for migration purposes.
        
        Args:
            db_name: Name of the legacy database file
            
        Returns:
            str: Path to the legacy database location
        """
        # Legacy databases were typically in the module directory or project root
        legacy_paths = [
            self._project_root / db_name,  # Root level (like quote_db.sqlite3)
            self._project_root / "a_gent_parl" / db_name,  # a_gent_parl level
            self._project_root / "a_gent_parl" / "src" / self.module_name / db_name  # Module level
        ]
        
        for path in legacy_paths:
            if path.exists():
                return str(path)
        
        # Return the first path as default if none exist
        return str(legacy_paths[0])