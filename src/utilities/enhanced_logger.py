"""
Enhanced Logging Utility for a_gent_parl modules.

This module provides comprehensive logging functionality with standardized configuration,
log rotation, and sensitive data masking capabilities.
It extends the existing logging patterns established in weekly_nerd_curiosities
to create a reusable utility for all modules.
"""

import os
import logging
import logging.handlers
import re
from typing import Dict, Any, Optional


class EnhancedLogger:
    """
    Enhanced logging utility providing standardized logging configuration
    and sensitive data masking.
    
    Features:
    - Consistent log formatting across modules
    - Automatic log rotation to prevent disk space issues
    - Sensitive data masking (API keys, tokens)
    - Module-specific log file creation
    - Both console and file output
    """
    
    def __init__(self, module_name: str, log_dir: str, log_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the EnhancedLogger for a specific module.
        
        Args:
            module_name: Name of the module using this logger
            log_dir: Directory path for log files
            log_config: Optional logging configuration dictionary. If not provided, uses sensible defaults.
        """
        self.module_name = module_name
        self.log_dir = log_dir
        self.logger: Optional[logging.Logger] = None
        
        # Default logging configuration with fallbacks
        default_config = {
            'log_level': 'INFO',
            'max_log_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'console_output': True,
            'mask_sensitive_data': True
        }
        
        # Merge provided config with defaults
        self.log_config = default_config.copy()
        if log_config:
            self.log_config.update(log_config)
        
        # Sensitive data patterns for masking
        self.sensitive_patterns = [
            (r'(GEMINI_API_KEY["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1[MASKED]'),
            (r'(TELEGRAM_BOT_TOKEN["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1[MASKED]'),
            (r'(API_KEY["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1[MASKED]'),
            (r'(TOKEN["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1[MASKED]'),
            (r'(PASSWORD["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1[MASKED]'),
            (r'(SECRET["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1[MASKED]'),
            # Pattern for API keys in URLs or headers
            (r'([?&]api_key=)([^&\s]+)', r'\1[MASKED]'),
            (r'(Authorization:\s*Bearer\s+)([^\s]+)', r'\1[MASKED]'),
            # Pattern for simple key-value pairs (like in logs)
            (r'(api_key:\s*)([^\s,}]+)', r'\1[MASKED]'),
            (r'(secret\d*:\s*)([^\s,}]+)', r'\1[MASKED]'),
        ]
        
        # Sensitive key names to mask (case-insensitive)
        self.sensitive_keys = {
            'api_key', 'apikey', 'token', 'password', 'secret', 'key',
            'gemini_api_key', 'telegram_bot_token', 'auth_token'
        }
    
    def setup_logging(self) -> logging.Logger:
        """
        Configure comprehensive logging with both console and file output.
        
        Returns:
            logging.Logger: Configured logger instance for the module
        """
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create main logger
        logger_name = f"a_gent_parl.{self.module_name}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, self.log_config['log_level']))
        
        # Clear any existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if self.log_config['console_output']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.log_config['log_level']))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = os.path.join(self.log_dir, f'{self.module_name}.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.log_config['max_log_file_size'],
            backupCount=self.log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.log_config['log_level']))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        

        
        # Configure external library log levels to reduce noise
        self._configure_external_loggers()
        
        self.logger.info(f"Enhanced logging initialized for module: {self.module_name}")
        self.logger.info(f"Log directory: {self.log_dir}")
        self.logger.info(f"Log level: {self.log_config['log_level']}")
        self.logger.info(f"Max log file size: {self.log_config['max_log_file_size']} bytes")
        self.logger.info(f"Backup count: {self.log_config['backup_count']}")
        
        return self.logger
    

    
    def _configure_external_loggers(self) -> None:
        """Configure log levels for external libraries to reduce noise."""
        external_loggers = {
            'requests': logging.WARNING,
            'urllib3': logging.WARNING,
            'httpx': logging.WARNING,
            'httpcore': logging.WARNING,
            'google': logging.WARNING,
            'google.generativeai': logging.WARNING,
            'sqlite3': logging.WARNING
        }
        
        for logger_name, level in external_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    

    
    def log_api_call(self, api_name: str, endpoint: str, status: str, **kwargs) -> None:
        """
        Log API call details.
        
        Args:
            api_name: Name of the API service (e.g., 'Gemini', 'Telegram', 'Wikipedia')
            endpoint: API endpoint or method called
            status: Status of the call ('success', 'error', 'retry')
            **kwargs: Additional metadata (response_code, error_message, etc.)
        """
        if not self.logger:
            return
        
        # Mask sensitive data in kwargs
        masked_kwargs = self._mask_dict_values(kwargs) if self.log_config['mask_sensitive_data'] else kwargs
        
        log_message = f"API_CALL [{api_name}] {endpoint} - {status.upper()}"
        
        if status == 'success':
            self.logger.info(log_message)
        elif status == 'error':
            error_msg = masked_kwargs.get('error_message', 'Unknown error')
            self.logger.error(f"{log_message} - Error: {error_msg}")
        elif status == 'retry':
            attempt = masked_kwargs.get('attempt', 'N/A')
            self.logger.warning(f"{log_message} - Retry attempt: {attempt}")
    
    def mask_sensitive_data(self, data: str) -> str:
        """
        Mask sensitive information in log messages.
        
        Args:
            data: String that may contain sensitive information
            
        Returns:
            str: String with sensitive data masked
        """
        if not self.log_config['mask_sensitive_data']:
            return data
        
        masked_data = data
        
        for pattern, replacement in self.sensitive_patterns:
            masked_data = re.sub(pattern, replacement, masked_data, flags=re.IGNORECASE)
        
        return masked_data
    
    def _mask_dict_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive data in dictionary values.
        
        Args:
            data: Dictionary that may contain sensitive information
            
        Returns:
            Dict[str, Any]: Dictionary with sensitive values masked
        """
        masked_dict = {}
        
        for key, value in data.items():
            # Check if the key itself indicates sensitive data
            if key.lower() in self.sensitive_keys:
                masked_dict[key] = '[MASKED]'
            elif isinstance(value, str):
                masked_dict[key] = self.mask_sensitive_data(value)
            elif isinstance(value, dict):
                masked_dict[key] = self._mask_dict_values(value)
            elif isinstance(value, list):
                masked_dict[key] = [
                    self.mask_sensitive_data(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                masked_dict[key] = value
        
        return masked_dict
    

    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log error with detailed context information.
        
        Args:
            error: Exception that occurred
            context: Context information about when/where the error occurred
        """
        if not self.logger:
            return
        
        # Mask sensitive data in context
        masked_context = self._mask_dict_values(context) if self.log_config['mask_sensitive_data'] else context
        
        self.logger.error(f"ERROR: {str(error)}")
        self.logger.error("Error context:")
        for key, value in masked_context.items():
            self.logger.error(f"  {key}: {value}")
        
        # Log full traceback at debug level
        self.logger.debug("Full error traceback:", exc_info=True)
    

    
    def update_log_config(self, **config_updates) -> None:
        """
        Update logging configuration.
        
        Args:
            **config_updates: Configuration parameters to update
        """
        self.log_config.update(config_updates)
        
        if self.logger:
            self.logger.info(f"Updated logging configuration: {config_updates}")
    
    def log_module_start(self, **kwargs) -> None:
        """
        Log module execution start with optional context.
        
        Args:
            **kwargs: Additional context information to log
        """
        if not self.logger:
            return
        
        # Mask sensitive data in kwargs
        masked_kwargs = self._mask_dict_values(kwargs) if self.log_config['mask_sensitive_data'] else kwargs
        
        self.logger.info(f"=== MODULE START: {self.module_name} ===")
        
        if masked_kwargs:
            self.logger.info("Module context:")
            for key, value in masked_kwargs.items():
                self.logger.info(f"  {key}: {value}")
    
    def log_module_end(self, success: bool = True, **kwargs) -> None:
        """
        Log module execution end with success status and optional context.
        
        Args:
            success: Whether the module execution was successful
            **kwargs: Additional context information to log
        """
        if not self.logger:
            return
        
        # Mask sensitive data in kwargs
        masked_kwargs = self._mask_dict_values(kwargs) if self.log_config['mask_sensitive_data'] else kwargs
        
        status = "SUCCESS" if success else "FAILURE"
        self.logger.info(f"=== MODULE END: {self.module_name} - {status} ===")
        
        if masked_kwargs:
            self.logger.info("Module results:")
            for key, value in masked_kwargs.items():
                self.logger.info(f"  {key}: {value}")
    
    def get_logger(self) -> Optional[logging.Logger]:
        """
        Get the configured logger instance.
        
        Returns:
            logging.Logger: The configured logger instance, or None if not set up
        """
        return self.logger


