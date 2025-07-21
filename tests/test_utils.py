"""
Test utilities for Waveshare Pico Relay B tests
Provides auto-discovery and common test helpers
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / ".." / "python"))

from waveshare_relay import RelayController, find_relay_board


def get_test_port():
    """
    Get the serial port for testing, using auto-discovery

    Returns:
        str: Serial port path or None if no board found
    """
    # First check if a port is specified in environment
    env_port = os.environ.get("RELAY_PORT")
    if env_port:
        return env_port

    # Otherwise use auto-discovery
    port = find_relay_board()
    if not port:
        print("WARNING: No relay board found via auto-discovery")
        print("You can specify a port using: export RELAY_PORT=/dev/cu.usbmodem...")
    return port


def get_test_controller(timeout=2.0):
    """
    Get a connected RelayController for testing

    Args:
        timeout: Serial timeout in seconds

    Returns:
        RelayController: Connected controller or None if no board found
    """
    port = get_test_port()
    if not port:
        return None

    try:
        controller = RelayController(port, timeout=timeout)
        controller.connect()
        return controller
    except Exception as e:
        print(f"Failed to connect to {port}: {e}")
        return None


def skip_if_no_hardware(test_func):
    """
    Decorator to skip test if no hardware is connected
    """
    import pytest

    def wrapper(*args, **kwargs):
        if not get_test_port():
            pytest.skip("No relay board hardware found")
        return test_func(*args, **kwargs)

    wrapper.__name__ = test_func.__name__
    return wrapper
