"""
Enhanced Logging Utility for a_gent_parl modules.

This module provides comprehensive logging functionality with standardized configuration,
log rotation, performance metrics tracking, and sensitive data masking capabilities.
It extends the existing logging patterns established in weekly_nerd_curiosities
to create a reusable utility for all modules.
"""

import os
import logging
import logging.handlers
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from .config_manager import ConfigManager


class EnhancedLogger:
    """
    Enhanced logging utility providing standardized logging configuration,
    performance metrics tracking, and sensitive data masking.
    
    Features:
    - Consistent log formatting across modules
    - Automatic log rotation to prevent disk space issues
    - Performance metrics logging
    - Sensitive data masking (API keys, tokens)
    - Module-specific log file creation
    - Both console and file output
    """
    
    def __init__(self, module_name: str, config_manager: ConfigManager):
        """
        Initialize the EnhancedLogger for a specific module.
        
        Args:
            module_name: Name of the module using this logger
            config_manager: ConfigManager instance for path resolution
        """
        self.module_name = module_name
        self.config_manager = config_manager
        self.logger: Optional[logging.Logger] = None
        self.performance_logger: Optional[logging.Logger] = None
        
        # Default logging configuration
        self.log_config = {
            'log_level': 'INFO',
            'max_log_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'console_output': True,
            'performance_logging': True,
            'mask_sensitive_data': True
        }
        
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
        log_dir = self.config_manager.get_log_directory()
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
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
        log_file = os.path.join(log_dir, f'{self.module_name}.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.log_config['max_log_file_size'],
            backupCount=self.log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.log_config['log_level']))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Set up performance logger if enabled
        if self.log_config['performance_logging']:
            self._setup_performance_logger(log_dir, formatter)
        
        # Configure external library log levels to reduce noise
        self._configure_external_loggers()
        
        self.logger.info(f"Enhanced logging initialized for module: {self.module_name}")
        self.logger.info(f"Log directory: {log_dir}")
        self.logger.info(f"Log level: {self.log_config['log_level']}")
        self.logger.info(f"Max log file size: {self.log_config['max_log_file_size']} bytes")
        self.logger.info(f"Backup count: {self.log_config['backup_count']}")
        
        return self.logger
    
    def _setup_performance_logger(self, log_dir: str, formatter: logging.Formatter) -> None:
        """
        Set up dedicated performance metrics logger.
        
        Args:
            log_dir: Directory for log files
            formatter: Log formatter to use
        """
        perf_logger_name = f"a_gent_parl.{self.module_name}.performance"
        self.performance_logger = logging.getLogger(perf_logger_name)
        self.performance_logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.performance_logger.handlers.clear()
        
        # Performance log file with rotation
        perf_log_file = os.path.join(log_dir, f'{self.module_name}_performance.log')
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=self.log_config['max_log_file_size'],
            backupCount=self.log_config['backup_count'],
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(formatter)
        self.performance_logger.addHandler(perf_handler)
        
        # Prevent propagation to avoid duplicate logs
        self.performance_logger.propagate = False
    
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
    
    def log_performance_metric(self, operation: str, duration: float, **kwargs) -> None:
        """
        Log performance metrics for operations.
        
        Args:
            operation: Name of the operation being measured
            duration: Duration of the operation in seconds
            **kwargs: Additional metadata to include in the log
        """
        if not self.performance_logger:
            return
        
        metric_data = {
            'timestamp': datetime.now().isoformat(),
            'module': self.module_name,
            'operation': operation,
            'duration_seconds': round(duration, 3),
            'success': kwargs.get('success', True),
            'metadata': {k: v for k, v in kwargs.items() if k != 'success'}
        }
        
        # Log as JSON for easy parsing
        self.performance_logger.info(json.dumps(metric_data))
        
        # Also log human-readable version to main logger
        if self.logger:
            status = "SUCCESS" if metric_data['success'] else "FAILED"
            self.logger.info(f"PERFORMANCE [{operation}] {status} - {duration:.3f}s")
    
    def log_api_call(self, api_name: str, endpoint: str, status: str, 
                     duration: float, **kwargs) -> None:
        """
        Log API call details with performance metrics.
        
        Args:
            api_name: Name of the API service (e.g., 'Gemini', 'Telegram', 'Wikipedia')
            endpoint: API endpoint or method called
            status: Status of the call ('success', 'error', 'retry')
            duration: Duration of the API call in seconds
            **kwargs: Additional metadata (response_code, error_message, etc.)
        """
        if not self.logger:
            return
        
        # Mask sensitive data in kwargs
        masked_kwargs = self._mask_dict_values(kwargs) if self.log_config['mask_sensitive_data'] else kwargs
        
        log_message = f"API_CALL [{api_name}] {endpoint} - {status.upper()} ({duration:.3f}s)"
        
        if status == 'success':
            self.logger.info(log_message)
        elif status == 'error':
            error_msg = masked_kwargs.get('error_message', 'Unknown error')
            self.logger.error(f"{log_message} - Error: {error_msg}")
        elif status == 'retry':
            attempt = masked_kwargs.get('attempt', 'N/A')
            self.logger.warning(f"{log_message} - Retry attempt: {attempt}")
        
        # Log performance metric
        self.log_performance_metric(
            f"api_call_{api_name.lower()}",
            duration,
            success=(status == 'success'),
            endpoint=endpoint,
            status=status,
            **masked_kwargs
        )
    
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
    
    def log_module_start(self, **kwargs) -> None:
        """
        Log module execution start with configuration details.
        
        Args:
            **kwargs: Additional configuration details to log
        """
        if not self.logger:
            return
        
        self.logger.info("=" * 60)
        self.logger.info(f"Starting {self.module_name} module")
        self.logger.info("=" * 60)
        
        # Log configuration validation
        config_validation = self.config_manager.validate_configuration()
        self.logger.info("Configuration validation results:")
        for key, value in config_validation.items():
            if isinstance(value, dict):
                self.logger.info(f"  {key}:")
                for sub_key, sub_value in value.items():
                    self.logger.info(f"    {sub_key}: {sub_value}")
            else:
                self.logger.info(f"  {key}: {value}")
        
        # Log additional configuration details
        for key, value in kwargs.items():
            masked_value = self.mask_sensitive_data(str(value)) if isinstance(value, str) else value
            self.logger.info(f"  {key}: {masked_value}")
    
    def log_module_end(self, success: bool = True, **kwargs) -> None:
        """
        Log module execution completion.
        
        Args:
            success: Whether the module completed successfully
            **kwargs: Additional completion details to log
        """
        if not self.logger:
            return
        
        status = "successfully" if success else "with errors"
        self.logger.info("=" * 60)
        self.logger.info(f"{self.module_name} module completed {status}")
        
        # Log completion details
        for key, value in kwargs.items():
            self.logger.info(f"  {key}: {value}")
        
        self.logger.info("=" * 60)
    
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
    
    def create_execution_timer(self, operation_name: str) -> 'ExecutionTimer':
        """
        Create a context manager for timing operations.
        
        Args:
            operation_name: Name of the operation being timed
            
        Returns:
            ExecutionTimer: Context manager for timing the operation
        """
        return ExecutionTimer(self, operation_name)
    
    def update_log_config(self, **config_updates) -> None:
        """
        Update logging configuration.
        
        Args:
            **config_updates: Configuration parameters to update
        """
        self.log_config.update(config_updates)
        
        if self.logger:
            self.logger.info(f"Updated logging configuration: {config_updates}")


class ExecutionTimer:
    """
    Context manager for timing operations and automatically logging performance metrics.
    """
    
    def __init__(self, enhanced_logger: EnhancedLogger, operation_name: str):
        """
        Initialize the execution timer.
        
        Args:
            enhanced_logger: EnhancedLogger instance to use for logging
            operation_name: Name of the operation being timed
        """
        self.enhanced_logger = enhanced_logger
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.success = True
        self.metadata = {}
    
    def __enter__(self) -> 'ExecutionTimer':
        """Start timing the operation."""
        self.start_time = time.time()
        if self.enhanced_logger.logger:
            self.enhanced_logger.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End timing and log the performance metric."""
        self.end_time = time.time()
        
        if exc_type is not None:
            self.success = False
            self.metadata['error_type'] = exc_type.__name__
            self.metadata['error_message'] = str(exc_val)
        
        duration = self.end_time - self.start_time
        
        # Log performance metric
        self.enhanced_logger.log_performance_metric(
            self.operation_name,
            duration,
            success=self.success,
            **self.metadata
        )
        
        # Log completion message
        if self.enhanced_logger.logger:
            status = "completed" if self.success else "failed"
            self.enhanced_logger.logger.debug(
                f"Operation {self.operation_name} {status} in {duration:.3f}s"
            )
    
    def add_metadata(self, **metadata) -> None:
        """
        Add metadata to be included in the performance log.
        
        Args:
            **metadata: Key-value pairs to include in the performance log
        """
        self.metadata.update(metadata)