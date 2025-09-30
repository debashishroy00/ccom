#!/usr/bin/env python3
"""
Base Handler Class
Provides common interface for all CLI handlers
"""

from abc import ABC, abstractmethod
from typing import Any
import logging

from ...utils import ErrorHandler


class BaseHandler(ABC):
    """
    Base class for all CLI handlers

    Provides:
    - Common interface
    - Error handling
    - Logging
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_handler = ErrorHandler(self.logger)

    @abstractmethod
    def can_handle(self, args) -> bool:
        """
        Check if this handler can process the given arguments

        Args:
            args: Parsed command line arguments

        Returns:
            True if this handler can process the arguments
        """
        pass

    @abstractmethod
    def handle(self, args) -> bool:
        """
        Handle the command

        Args:
            args: Parsed command line arguments

        Returns:
            True if command executed successfully
        """
        pass

    def safe_handle(self, args, operation_name: str = "operation") -> bool:
        """
        Safely handle command with error recovery

        Args:
            args: Parsed command line arguments
            operation_name: Name of operation for error messages

        Returns:
            True if command executed successfully
        """
        return self.error_handler.safe_execute(
            lambda: self.handle(args),
            default_return=False,
            error_message=f"{operation_name} failed"
        )