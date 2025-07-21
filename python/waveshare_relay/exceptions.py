"""
Custom exceptions for the Waveshare Pico Relay B library
"""


class RelayError(Exception):
    """Base exception class for relay-related errors"""

    pass


class RelayConnectionError(RelayError):
    """Raised when there are connection issues with the relay board"""

    pass


class RelayTimeoutError(RelayError):
    """Raised when a command times out waiting for response"""

    pass


class RelayCommandError(RelayError):
    """Raised when the relay board returns an error response"""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


class RelayValidationError(RelayError):
    """Raised when command parameters are invalid"""

    pass
