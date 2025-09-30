#!/usr/bin/env python3
"""
Centralized error handling utilities
Eliminates code duplication and provides consistent error patterns
"""

import logging
import traceback
from typing import Callable, Any, Optional, Type
from functools import wraps


class ErrorHandler:
    """
    Centralized error handling patterns

    Replaces 10+ duplicate error handling blocks across CCOM modules
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def handle_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Optional[Callable] = None,
        error_message: str = "Operation failed",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with optional fallback

        Args:
            primary_func: Primary function to execute
            fallback_func: Fallback function if primary fails
            error_message: Custom error message
            *args: Arguments for functions
            **kwargs: Keyword arguments for functions

        Returns:
            Result from primary or fallback function
        """
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"{error_message}: {e}")

            if fallback_func:
                try:
                    self.logger.info("Attempting fallback operation")
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
                    raise fallback_error
            else:
                raise e

    def safe_execute(
        self,
        func: Callable,
        default_return=None,
        error_message: str = "Operation failed",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function safely with default return on error

        Args:
            func: Function to execute
            default_return: Value to return on error
            error_message: Custom error message
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result or default_return on error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"{error_message}: {e}")
            return default_return

    def retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        exceptions: tuple = (Exception,),
        error_message: str = "Operation failed",
        *args,
        **kwargs
    ) -> Any:
        """
        Retry function with exponential backoff

        Args:
            func: Function to execute
            max_retries: Maximum number of retries
            backoff_factor: Backoff multiplier
            exceptions: Exceptions to retry on
            error_message: Custom error message
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Last exception if all retries failed
        """
        import time

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries:
                    self.logger.error(f"{error_message} after {max_retries} retries: {e}")
                    raise e
                else:
                    wait_time = backoff_factor * (2 ** attempt)
                    self.logger.warning(f"{error_message} (attempt {attempt + 1}): {e}. Retrying in {wait_time}s")
                    time.sleep(wait_time)

    @staticmethod
    def graceful_degradation(
        fallback_message: str = "Feature unavailable",
        return_value=None
    ):
        """
        Decorator for graceful degradation on errors

        Args:
            fallback_message: Message to log on error
            return_value: Value to return on error

        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger = logging.getLogger(func.__module__)
                    logger.warning(f"{fallback_message}: {e}")
                    return return_value
            return wrapper
        return decorator

    @staticmethod
    def log_and_reraise(error_message: str = "Operation failed"):
        """
        Decorator to log errors before re-raising

        Args:
            error_message: Custom error message

        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"{error_message} in {func.__name__}: {e}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    raise
            return wrapper
        return decorator

    def validate_input(
        self,
        value: Any,
        validator: Callable[[Any], bool],
        error_message: str = "Invalid input"
    ) -> Any:
        """
        Validate input with custom validator

        Args:
            value: Value to validate
            validator: Validation function
            error_message: Error message for invalid input

        Returns:
            Validated value

        Raises:
            ValueError: If validation fails
        """
        try:
            if not validator(value):
                raise ValueError(f"{error_message}: {value}")
            return value
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            raise ValueError(f"{error_message}: {value}") from e

    def handle_file_operation(
        self,
        operation: Callable,
        file_path: str,
        error_message: str = "File operation failed",
        *args,
        **kwargs
    ) -> Any:
        """
        Handle file operations with proper error handling

        Args:
            operation: File operation function
            file_path: Path to file
            error_message: Custom error message
            *args: Arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Operation result
        """
        try:
            return operation(file_path, *args, **kwargs)
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except PermissionError:
            self.logger.error(f"Permission denied: {file_path}")
            raise
        except OSError as e:
            self.logger.error(f"{error_message} for {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"{error_message}: {e}")
            raise