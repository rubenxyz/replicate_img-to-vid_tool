"""
Custom exceptions for video generation tool.

This module defines a hierarchy of exceptions for different error scenarios:
- VideoGenerationError: Base exception for all video generation errors
- AuthenticationError: API authentication failures
- InputValidationError: Invalid input data or missing files
- ProfileValidationError: Invalid profile configuration
- APIError: General API communication errors

All exceptions inherit from VideoGenerationError for consistent error handling.
"""


class VideoGenerationError(Exception):
    """Base exception for video generation errors."""
    pass


class AuthenticationError(VideoGenerationError):
    """Raised when authentication fails."""
    pass


class InputValidationError(VideoGenerationError):
    """Raised when input validation fails."""
    pass


class ProfileValidationError(VideoGenerationError):
    """Raised when profile validation fails."""
    pass


class APIError(VideoGenerationError):
    """Raised when API calls fail."""
    pass


