"""
Configuration module for Weekly Nerd Curiosities.

This module contains all configuration constants and category selection logic
for the nerd curiosities content discovery system.
"""

import os
import random
from typing import List

# Predefined nerd-related Wikipedia categories
NERD_CATEGORIES = [
    "Anime",
    "Manga", 
    "Comics",
    "Video_games",
    "Science_fiction",
    "Fantasy",
    "Tabletop_games",
    "Animation",
    "Japanese_popular_culture",
    "Superhero_fiction",
    "Role-playing_games",
    "Collectible_card_games"
]

# Content validation constants
MIN_ARTICLE_LENGTH = 500  # Minimum characters for article content
MAX_RETRIES = 5  # Maximum attempts to find suitable article
POST_LENGTH_MIN = 200  # Minimum characters for generated post
POST_LENGTH_MAX = 500  # Maximum characters for generated post

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "nerd_curiosities.sqlite3")

# Telegram publishing configuration
TELEGRAM_RETRY_ATTEMPTS = 3
TELEGRAM_RETRY_DELAY = 30  # seconds


def select_random_category() -> str:
    """
    Select a random category from the predefined nerd categories list.
    
    Returns:
        str: A randomly selected Wikipedia category name
    """
    return random.choice(NERD_CATEGORIES)


def get_all_categories() -> List[str]:
    """
    Get the complete list of nerd-related categories.
    
    Returns:
        List[str]: List of all predefined nerd categories
    """
    return NERD_CATEGORIES.copy()


def is_valid_category(category: str) -> bool:
    """
    Check if a category is in the predefined nerd categories list.
    
    Args:
        category: Category name to validate
        
    Returns:
        bool: True if category is valid, False otherwise
    """
    return category in NERD_CATEGORIES


def get_env_path() -> str:
    """
    Get the path to the environment file following existing project pattern.
    
    Returns:
        str: Path to the .env file in utilities directory
    """
    return os.path.join(os.path.dirname(__file__), '..', 'utilities', '.env')


def get_log_directory() -> str:
    """
    Get the path to the logs directory for this module.
    
    Returns:
        str: Path to the logs directory
    """
    return os.path.join(os.path.dirname(__file__), 'logs')


def validate_configuration() -> dict:
    """
    Validate all configuration settings and return status.
    
    Returns:
        dict: Configuration validation results
    """
    validation_results = {
        'database_path_valid': os.path.exists(os.path.dirname(DATABASE_PATH)),
        'env_file_exists': os.path.exists(get_env_path()),
        'categories_count': len(NERD_CATEGORIES),
        'min_article_length': MIN_ARTICLE_LENGTH,
        'max_retries': MAX_RETRIES,
        'post_length_range': f"{POST_LENGTH_MIN}-{POST_LENGTH_MAX}",
        'telegram_retry_config': f"{TELEGRAM_RETRY_ATTEMPTS} attempts, {TELEGRAM_RETRY_DELAY}s delay"
    }
    
    return validation_results