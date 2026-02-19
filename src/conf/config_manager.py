"""
Configuration Manager for a_gent_parl project.

This module provides centralized configuration management with:
- Configuration loading from config.ini files
- Environment variable integration
- Configuration validation and defaults
- Module-specific configuration support
- Error handling with fallback to defaults
"""

import os
import configparser
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """
    Centralized configuration manager for a_gent_parl project.
    
    Provides configuration loading, validation, and module-specific
    configuration retrieval with fallback to sensible defaults.
    """
    
    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Optional path to config.ini file. If None, auto-detects.
        """
        self._project_root = self._find_project_root()
        self._config_path = Path(config_path) if config_path else self._project_root / "src" / "conf" / "config.ini"
        self._env_path = Path(env_path) if env_path else self._project_root / "src" / "conf" / ".env"
        self._config = configparser.ConfigParser()
        self._defaults = self._get_default_config()
        
        # Load configuration with error handling
        self._load_configuration()
        # Load environment variables
        self.load_environment_variables()
    
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
    
    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default configuration values for all sections.
        
        Returns:
            Dict: Default configuration structure with all sections
        """
        return {
            'telegram': {
                'retry_attempts': 3,
                'retry_delay': 30
            },
            'logging': {
                'default_level': 'INFO',
                'sensitive_data_masking': True
            },
            'database': {
                'default_quote_db': 'quote_db.sqlite3',
                'default_news_db': 'news_db.sqlite3'
            },
            'paths': {
                'data_root': 'data',
                'images_subdir': 'images',
                'logs_subdir': 'logs',
                'cache_subdir': 'cache',
                'databases_subdir': 'databases'
            },
            'nerd_quote': {
                'nerd_categories': 'anime,manga,comics,video games,science fiction,fantasy,tabletop games,animation,japanese popular culture,superhero fiction,Role-playing games,collectible card games',
                'post_template': 'Quote of the day',
                'retry_attempts': 3
            },
            'wiki_most_viewed': {
                'country_code': 'IT',
                'top_articles_count': 5,
                'exclude_articles': 'Main Page,Wikipedia'
            },
            'ps_news': {
                'content_length_min': 800,
                'content_length_max': 1200,
                'include_free_games': True
            },
            'weekly_posting_image': {
                'image_formats': 'jpg,png,jpeg',
                'max_image_size': '5MB',
                'caption_length_max': 300
            },
            'happened_today': {
                'professions': 'comics artist,cartoonist,mangaka,fantasy writer,animator',
                'historical_period_days': 7
            },
            'nerd_curiosities': {
                'nerd_categories': 'Anime,Manga,Comics,Video_games,Science_fiction,Fantasy,Tabletop_games,Animation,Japanese_popular_culture,Superhero_fiction,Role-playing_games,Collectible_card_games',
                'content_style': 'casual',
                'hashtag_count': 5
            },
            'youtube_trend': {
                'country_code': 'IT',
                'top_videos_count': 10
            },
            'feed_store': {
                'tech_feed': 'https://www.techradar.com/rss,https://research.google/blog/rss/,https://www.marktechpost.com/feed/,https://machinelearningmastery.com/feed/,https://bair.berkeley.edu/blog/feed.xml,https://aws.amazon.com/blogs/aws/feed/,https://azure.microsoft.com/en-us/blog/feed/,https://cloud.google.com/blog/rss.xml,https://cloudcomputing-today.com/feed/,https://feeds.arstechnica.com/arstechnica/index/,https://www.theverge.com/rss/index.xml,https://news.ycombinator.com/rss,https://www.infoworld.com/category/cloud-computing/index.rss,https://www.corrierecomunicazioni.it/feed/,https://inno3.it/feed/'
            }
        }
    
    def _load_configuration(self) -> None:
        """
        Load configuration from config.ini file with error handling.
        
        If the file doesn't exist or is corrupted, creates a default one
        and uses default values.
        """
        try:
            if not self._config_path.exists():
                self._create_default_config_file()
            
            self._config.read(self._config_path)
            
            # Validate that all required sections exist
            self._validate_and_fix_config()
            
        except (configparser.Error, IOError, OSError) as e:
            logging.warning(f"Error loading configuration from {self._config_path}: {e}")
            logging.info("Using default configuration values")
            self._load_default_config()
    
    def _create_default_config_file(self) -> None:
        """
        Create a default config.ini file with all required sections and values.
        """
        try:
            # Ensure the directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create config with defaults
            config = configparser.ConfigParser()
            
            for section_name, section_data in self._defaults.items():
                config.add_section(section_name)
                for key, value in section_data.items():
                    config.set(section_name, key, str(value))
            
            # Write the configuration file
            with open(self._config_path, 'w') as config_file:
                config.write(config_file)
            
            logging.info(f"Created default configuration file at {self._config_path}")
            
        except (IOError, OSError) as e:
            logging.error(f"Failed to create default configuration file: {e}")
    
    def _load_default_config(self) -> None:
        """
        Load default configuration into the ConfigParser instance.
        """
        self._config.clear()
        
        for section_name, section_data in self._defaults.items():
            self._config.add_section(section_name)
            for key, value in section_data.items():
                self._config.set(section_name, key, str(value))
    
    def _validate_and_fix_config(self) -> None:
        """
        Validate configuration and add missing sections/keys with defaults.
        """
        config_modified = False
        
        for section_name, section_defaults in self._defaults.items():
            # Add missing sections
            if not self._config.has_section(section_name):
                self._config.add_section(section_name)
                config_modified = True
                logging.warning(f"Added missing configuration section: {section_name}")
            
            # Add missing keys within sections
            for key, default_value in section_defaults.items():
                if not self._config.has_option(section_name, key):
                    self._config.set(section_name, key, str(default_value))
                    config_modified = True
                    logging.warning(f"Added missing configuration key: {section_name}.{key}")
        
        # Save the updated configuration if modified
        if config_modified:
            try:
                with open(self._config_path, 'w') as config_file:
                    self._config.write(config_file)
                logging.info("Updated configuration file with missing sections/keys")
            except (IOError, OSError) as e:
                logging.error(f"Failed to update configuration file: {e}")
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """
        Get Telegram-specific configuration.
        
        Returns:
            Dict[str, Any]: Telegram configuration with proper type conversion
        """
        return {
            'retry_attempts': self._get_int('telegram', 'retry_attempts', 3),
            'retry_delay': self._get_int('telegram', 'retry_delay', 30)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging-specific configuration.
        
        Returns:
            Dict[str, Any]: Logging configuration with proper type conversion
        """
        return {
            'default_level': self._get_str('logging', 'default_level', 'INFO'),
            'sensitive_data_masking': self._get_bool('logging', 'sensitive_data_masking', True)
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database-specific configuration.
        
        Returns:
            Dict[str, Any]: Database configuration
        """
        return {
            'default_quote_db': self._get_str('database', 'default_quote_db', 'quote_db.sqlite3'),
            'default_news_db': self._get_str('database', 'default_news_db', 'news_db.sqlite3')
            
        }
    
    def get_paths_config(self) -> Dict[str, Any]:
        """
        Get paths-specific configuration.
        
        Returns:
            Dict[str, Any]: Paths configuration
        """
        return {
            'data_root': self._get_str('paths', 'data_root', 'data'),
            'images_subdir': self._get_str('paths', 'images_subdir', 'images'),
            'logs_subdir': self._get_str('paths', 'logs_subdir', 'logs'),
            'cache_subdir': self._get_str('paths', 'cache_subdir', 'cache'),
            'databases_subdir': self._get_str('paths', 'databases_subdir', 'databases')
        }
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """
        Get module-specific configuration.
        
        Args:
            module_name: Name of the module (e.g., 'weekly_quote')
            
        Returns:
            Dict[str, Any]: Module-specific configuration with proper type conversion
        """
        if not self.has_module_config(module_name):
            logging.warning(f"No configuration found for module: {module_name}")
            return {}
        
        config = {}
        
        # Get all options for the module section
        for key in self._config.options(module_name):
            raw_value = self._config.get(module_name, key)
            
            # Try to convert to appropriate type
            config[key] = self._convert_value(raw_value)
        
        return config
    
    def get_all_module_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all module-specific configurations.
        
        Returns:
            Dict[str, Dict[str, Any]]: All module configurations
        """
        module_configs = {}
        
        # Get all sections that are not core configuration sections
        core_sections = {'telegram', 'logging', 'database', 'paths'}
        
        for section_name in self._config.sections():
            if section_name not in core_sections:
                module_configs[section_name] = self.get_module_config(section_name)
        
        return module_configs
    
    def has_module_config(self, module_name: str) -> bool:
        """
        Check if configuration exists for a specific module.
        
        Args:
            module_name: Name of the module to check
            
        Returns:
            bool: True if module configuration exists, False otherwise
        """
        return self._config.has_section(module_name)
    
    def reload_configuration(self) -> None:
        """
        Reload configuration from the config file.
        
        Useful for picking up configuration changes without restarting.
        """
        logging.info("Reloading configuration...")
        self._load_configuration()
    
    def validate_configuration(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Check that all core sections exist
            core_sections = {'telegram', 'logging', 'database', 'paths'}
            
            for section in core_sections:
                if not self._config.has_section(section):
                    logging.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate specific configuration values
            telegram_config = self.get_telegram_config()
            if telegram_config['retry_attempts'] < 1 or telegram_config['retry_attempts'] > 10:
                logging.error("Invalid telegram retry_attempts: must be between 1 and 10")
                return False
            
            if telegram_config['retry_delay'] < 1 or telegram_config['retry_delay'] > 300:
                logging.error("Invalid telegram retry_delay: must be between 1 and 300 seconds")
                return False
            
            logging_config = self.get_logging_config()
            valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
            if logging_config['default_level'] not in valid_levels:
                logging.error(f"Invalid logging level: {logging_config['default_level']}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
            return False
    
    def _get_str(self, section: str, key: str, default: str) -> str:
        """
        Get a string configuration value with fallback to default.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            str: Configuration value or default
        """
        try:
            if self._config.has_option(section, key):
                return self._config.get(section, key)
        except (configparser.Error, ValueError):
            pass
        
        return default
    
    def _get_int(self, section: str, key: str, default: int) -> int:
        """
        Get an integer configuration value with fallback to default.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if key not found or invalid
            
        Returns:
            int: Configuration value or default
        """
        try:
            if self._config.has_option(section, key):
                return self._config.getint(section, key)
        except (configparser.Error, ValueError):
            pass
        
        return default
    
    def _get_bool(self, section: str, key: str, default: bool) -> bool:
        """
        Get a boolean configuration value with fallback to default.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if key not found or invalid
            
        Returns:
            bool: Configuration value or default
        """
        try:
            if self._config.has_option(section, key):
                return self._config.getboolean(section, key)
        except (configparser.Error, ValueError):
            pass
        
        return default
    
    def _get_float(self, section: str, key: str, default: float) -> float:
        """
        Get a float configuration value with fallback to default.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if key not found or invalid
            
        Returns:
            float: Configuration value or default
        """
        try:
            if self._config.has_option(section, key):
                return self._config.getfloat(section, key)
        except (configparser.Error, ValueError):
            pass
        
        return default
    
    def _convert_value(self, raw_value: str) -> Union[str, int, float, bool, List[str]]:
        """
        Convert a raw configuration value to the appropriate Python type.
        
        Args:
            raw_value: Raw string value from configuration
            
        Returns:
            Union[str, int, float, bool, List[str]]: Converted value
        """
        # Handle comma-separated lists
        if ',' in raw_value:
            return [item.strip() for item in raw_value.split(',')]
        
        # Handle boolean values
        if raw_value.lower() in ('true', 'false', 'yes', 'no', '1', '0'):
            return raw_value.lower() in ('true', 'yes', '1')
        
        # Try to convert to int
        try:
            return int(raw_value)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(raw_value)
        except ValueError:
            pass
        
        # Return as string
        return raw_value
    
    def get_project_root(self) -> Path:
        """
        Get the project root directory path.
        
        Returns:
            Path: Project root directory path
        """
        return self._project_root
    
    def get_config_path(self) -> Path:
        """
        Get the configuration file path.
        
        Returns:
            Path: Configuration file path
        """
        return self._config_path

    def load_environment_variables(self):
        """Load environment variables using existing project pattern."""
        # Follow the existing project pattern - utilities use '../utilities/.env'
        utilities_env_path = self._env_path
        
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