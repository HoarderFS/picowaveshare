"""
Configuration file for Waveshare Pico Relay B board.

Contains pin mappings, constants, hardware-specific settings, and persistent storage
functions for relay names and states. Supports automatic state restoration on boot.

Firmware Version: 1.2.0 - Improved HELP command with detailed descriptions
"""

import json
import time

import machine

# Board identification
BOARD_NAME = "Waveshare Pico Relay B"
BOARD_VERSION = "1.0"
FIRMWARE_VERSION = "1.2.0"

# Relay pin mappings (GPIO numbers)
# Based on hardware verification tests
RELAY_PINS = {
    1: 21,  # Relay 1: GP21
    2: 20,  # Relay 2: GP20
    3: 19,  # Relay 3: GP19
    4: 18,  # Relay 4: GP18
    5: 17,  # Relay 5: GP17
    6: 16,  # Relay 6: GP16
    7: 15,  # Relay 7: GP15
    8: 14,  # Relay 8: GP14
}

# Reverse mapping for pin to relay number lookups
PIN_TO_RELAY = {pin: relay for relay, pin in RELAY_PINS.items()}

# Peripheral pin mappings
BUZZER_PIN = 6  # GP6 - PWM capable
RGB_LED_PIN = 13  # GP13 - NeoPixel control
ONBOARD_LED_PIN = 25  # GP25 - Standard Pico onboard LED
USER_BUTTON_PIN = 9  # GP9 - User button (if present)

# Relay control constants
RELAY_ON = 1  # Logic level for relay ON
RELAY_OFF = 0  # Logic level for relay OFF
RELAY_COUNT = 8  # Total number of relays

# Timing constants (in milliseconds)
RELAY_SETTLE_TIME = 10  # Time to wait after relay state change
STARTUP_DELAY = 100  # Delay on startup before accepting commands
COMMAND_TIMEOUT = 5000  # Maximum time to wait for command completion

# PWM constants for buzzer
BUZZER_FREQ_DEFAULT = 1000  # Default buzzer frequency (Hz)
BUZZER_DUTY_ON = 32768  # 50% duty cycle for buzzer on
BUZZER_DUTY_OFF = 0  # 0% duty cycle for buzzer off

# RGB LED constants
RGB_LED_COUNT = 1  # Number of RGB LEDs
RGB_BRIGHTNESS = 0.5  # Default brightness (0.0 to 1.0)

# Status LED patterns (for debugging/status indication)
STATUS_PATTERNS = {
    "STARTUP": [(100, 100)] * 3,  # 3 quick blinks
    "READY": [(1000, 1000)],  # Slow heartbeat
    "ERROR": [(200, 200)] * 5,  # 5 fast blinks
    "COMMAND": [(50, 50)],  # Quick flash
}

# Protocol constants
PROTOCOL_VERSION = "1.0"
COMMAND_TERMINATOR = "\n"
RESPONSE_TERMINATOR = "\n"
MAX_COMMAND_LENGTH = 64
MAX_RESPONSE_LENGTH = 64

# Error codes
ERROR_CODES = {
    "INVALID_COMMAND": "ERROR:INVALID_COMMAND",
    "INVALID_RELAY_NUMBER": "ERROR:INVALID_RELAY_NUMBER",
    "INVALID_PARAMETER": "ERROR:INVALID_PARAMETER",
    "INVALID_PARAMETER_COUNT": "ERROR:INVALID_PARAMETER_COUNT",
    "RELAY_BUSY": "ERROR:RELAY_BUSY",
    "TIMEOUT": "ERROR:TIMEOUT",
    "HARDWARE_ERROR": "ERROR:HARDWARE_ERROR",
}

# Success responses
SUCCESS_RESPONSE = "OK"
PING_RESPONSE = "PONG"


# Validation functions
def is_valid_relay_number(relay_num):
    """
    Check if relay number is valid (1-8).

    Args:
        relay_num (int): Relay number to validate

    Returns:
        bool: True if relay number is between 1 and 8, False otherwise
    """
    return isinstance(relay_num, int) and 1 <= relay_num <= RELAY_COUNT


def is_valid_pin(pin_num):
    """
    Check if pin number is valid for Raspberry Pi Pico.

    Args:
        pin_num (int): GPIO pin number to validate

    Returns:
        bool: True if pin number is between 0 and 28, False otherwise
    """
    return isinstance(pin_num, int) and 0 <= pin_num <= 28


def get_relay_pin(relay_num):
    """
    Get GPIO pin number for a specific relay.

    Args:
        relay_num (int): Relay number (1-8)

    Returns:
        int or None: GPIO pin number if relay is valid, None otherwise
    """
    if is_valid_relay_number(relay_num):
        return RELAY_PINS[relay_num]
    return None


def get_relay_from_pin(pin_num):
    """
    Get relay number from GPIO pin.

    Args:
        pin_num (int): GPIO pin number

    Returns:
        int or None: Relay number (1-8) if pin is a relay pin, None otherwise
    """
    return PIN_TO_RELAY.get(pin_num)


# Debug configuration
DEBUG = False  # Enable debug output
DEBUG_SERIAL = False  # Enable serial debug messages
DEBUG_COMMANDS = False  # Enable command logging
DEBUG_TIMING = False  # Enable timing debug (verbose)

# Watchdog configuration
WATCHDOG_TIMEOUT = 10000  # Watchdog timeout in milliseconds

# Board-specific features (can be detected at runtime)
FEATURES = {
    "BUZZER": True,  # Board has buzzer
    "RGB_LED": True,  # Board has RGB LED
    "USER_BUTTON": False,  # Board has user button (varies by model)
    "STATUS_LEDS": True,  # Board has relay status LEDs
}

# Default relay states on startup
DEFAULT_RELAY_STATE = [RELAY_OFF] * RELAY_COUNT  # All relays off


def get_board_uid():
    """
    Get the unique identifier for this board.

    Uses the Raspberry Pi Pico's unique ID to generate a consistent identifier
    that can be used for device discovery and identification.

    Returns:
        str: 16-character uppercase hex string (e.g., "ECD43B7502A23159")

    Note:
        Falls back to "0000000000000000" if unique_id() fails
    """
    try:
        uid_bytes = machine.unique_id()
        return "".join([f"{b:02X}" for b in uid_bytes])
    except Exception:
        # Fallback if unique_id() fails
        return "0000000000000000"


def get_board_info():
    """
    Get complete board information including UID.

    This function is used by the INFO protocol command to return a standardized
    board identification string.

    Returns:
        str: Formatted board info string in format:
             "WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:XXXXXXXXXXXXXXXX"
    """
    uid = get_board_uid()
    return f"WAVESHARE-PICO-RELAY-B,V{BOARD_VERSION},8CH,UID:{uid}"


def load_relay_config():
    """
    Load relay configuration from persistent storage.

    Reads the relay_config.json file from flash storage. If the file doesn't exist
    or is corrupted, creates a new configuration with default values.

    Returns:
        dict: Configuration dictionary containing:
            - names: Dict mapping relay numbers (as strings) to custom names
            - settings: Dict with auto_save flag and timestamps
            - states: Dict mapping relay numbers to saved states (0 or 1)
            - auto_load: Bool indicating if states should be restored on boot
    """
    config_file = "relay_config.json"
    default_config = {
        "names": {str(i): f"Relay {i}" for i in range(1, RELAY_COUNT + 1)},
        "settings": {"auto_save": True, "created_time": 0},
        "states": {str(i): 0 for i in range(1, RELAY_COUNT + 1)},
        "auto_load": True,
    }

    try:
        with open(config_file) as f:
            config = json.load(f)
            # Ensure all required keys exist
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    except (OSError, ValueError):
        # File doesn't exist or is corrupted
        save_relay_config(default_config)
        return default_config


def save_relay_config(config):
    """
    Save relay configuration to persistent storage.

    Writes the configuration to relay_config.json in the root filesystem.
    This includes relay names, saved states, and auto-load settings.

    Args:
        config (dict): Configuration dictionary to save, must contain:
            - names: Relay name mappings
            - settings: Configuration settings
            - states: Saved relay states
            - auto_load: Auto-load enable flag

    Returns:
        bool: True if successful, False if write failed
    """
    config_file = "relay_config.json"
    try:
        with open(config_file, "w") as f:
            json.dump(config, f)
        return True
    except OSError:
        return False


def get_relay_name(relay_num):
    """
    Get the name of a specific relay

    Args:
        relay_num (int): Relay number (1-8)

    Returns:
        str: Relay name or default if not found
    """
    if not is_valid_relay_number(relay_num):
        return f"Relay {relay_num}"

    config = load_relay_config()
    return config["names"].get(str(relay_num), f"Relay {relay_num}")


def set_relay_name(relay_num, name):
    """
    Set the name of a specific relay

    Args:
        relay_num (int): Relay number (1-8)
        name (str): New name for the relay

    Returns:
        bool: True if successful, False if failed
    """
    if not is_valid_relay_number(relay_num):
        return False

    if not isinstance(name, str) or len(name) > 32:
        return False

    config = load_relay_config()
    config["names"][str(relay_num)] = name
    return save_relay_config(config)


def get_all_relay_names():
    """
    Get all relay names

    Returns:
        dict: Dictionary mapping relay numbers to names
    """
    config = load_relay_config()
    return {int(k): v for k, v in config["names"].items()}


def save_relay_states(states):
    """
    Save current relay states to persistent storage.

    Used by the SAVE protocol command to persist the current relay configuration.
    States are stored in the relay_config.json file along with a timestamp.

    Args:
        states (str): 8-character string of relay states where:
            - Character position corresponds to relay number (states[0] = relay 1)
            - '0' = relay off, '1' = relay on
            - Example: "00110101" means relays 3,4,6,8 are on

    Returns:
        bool: True if successful, False if validation or write failed
    """
    if not isinstance(states, str) or len(states) != 8:
        return False

    if not all(c in "01" for c in states):
        return False

    config = load_relay_config()
    # Store states with relay numbers as keys
    for i in range(RELAY_COUNT):
        config["states"][str(i + 1)] = int(states[i])

    # Update timestamp
    try:
        config["settings"]["last_saved"] = time.time()
    except Exception:
        pass

    return save_relay_config(config)


def load_relay_states():
    """
    Load saved relay states from persistent storage.

    Used by the LOAD protocol command and auto-load on boot feature.
    Reads the previously saved states from relay_config.json.

    Returns:
        str or None: 8-character string of relay states in same format as save_relay_states,
                     or None if no saved states exist
    """
    config = load_relay_config()

    # Check if states exist
    if "states" not in config:
        return None

    # Convert to string format
    try:
        states = ""
        for i in range(1, RELAY_COUNT + 1):
            state = config["states"].get(str(i), 0)
            states += "1" if state else "0"
        return states
    except Exception:
        return None


def clear_relay_states():
    """
    Clear saved relay states.

    Used by the CLEAR protocol command to remove all saved relay states.
    Resets all states to 0 (off) and removes the last_saved timestamp.

    Returns:
        bool: True if successful, False if write failed
    """
    config = load_relay_config()

    # Reset all states to 0
    config["states"] = {str(i): 0 for i in range(1, RELAY_COUNT + 1)}

    # Clear timestamp
    if "last_saved" in config.get("settings", {}):
        del config["settings"]["last_saved"]

    return save_relay_config(config)


def get_auto_load_enabled():
    """
    Check if auto-load is enabled.

    When enabled, saved relay states are automatically restored on boot.
    This setting persists across power cycles.

    Returns:
        bool: True if auto-load is enabled, False otherwise
    """
    config = load_relay_config()
    return config.get("auto_load", False)


def set_auto_load_enabled(enabled):
    """
    Enable or disable auto-load of saved states on boot.

    Controls whether the board automatically restores saved relay states
    when powered on. This setting is stored persistently.

    Args:
        enabled (bool): Whether to enable auto-load

    Returns:
        bool: True if setting was saved successfully, False if write failed
    """
    config = load_relay_config()
    config["auto_load"] = bool(enabled)
    return save_relay_config(config)
