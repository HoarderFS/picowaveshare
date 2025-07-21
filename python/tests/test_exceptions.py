"""
Tests for custom exceptions
"""

from waveshare_relay.exceptions import (
    RelayCommandError,
    RelayConnectionError,
    RelayError,
    RelayTimeoutError,
    RelayValidationError,
)


class TestExceptions:
    """Test cases for custom exceptions"""

    def test_relay_error_base(self):
        """Test base RelayError exception"""
        error = RelayError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_relay_connection_error(self):
        """Test RelayConnectionError exception"""
        error = RelayConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, RelayError)
        assert isinstance(error, Exception)

    def test_relay_timeout_error(self):
        """Test RelayTimeoutError exception"""
        error = RelayTimeoutError("Command timed out")
        assert str(error) == "Command timed out"
        assert isinstance(error, RelayError)
        assert isinstance(error, Exception)

    def test_relay_command_error_without_code(self):
        """Test RelayCommandError without error code"""
        error = RelayCommandError("Command failed")
        assert str(error) == "Command failed"
        assert error.error_code is None
        assert isinstance(error, RelayError)
        assert isinstance(error, Exception)

    def test_relay_command_error_with_code(self):
        """Test RelayCommandError with error code"""
        error = RelayCommandError("Command failed", "INVALID_COMMAND")
        assert str(error) == "Command failed"
        assert error.error_code == "INVALID_COMMAND"
        assert isinstance(error, RelayError)
        assert isinstance(error, Exception)

    def test_relay_validation_error(self):
        """Test RelayValidationError exception"""
        error = RelayValidationError("Invalid parameter")
        assert str(error) == "Invalid parameter"
        assert isinstance(error, RelayError)
        assert isinstance(error, Exception)

    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from RelayError"""
        exceptions = [
            RelayConnectionError("test"),
            RelayTimeoutError("test"),
            RelayCommandError("test"),
            RelayValidationError("test"),
        ]

        for exception in exceptions:
            assert isinstance(exception, RelayError)
            assert isinstance(exception, Exception)
