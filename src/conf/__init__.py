"""
Configuration management module for a_gent_parl.

This module provides centralized configuration management with:
- Configuration loading from config.ini files
- Environment variable integration
- Configuration validation and defaults
- Module-specific configuration support
"""

from .config_manager import ConfigManager

__all__ = ['ConfigManager']