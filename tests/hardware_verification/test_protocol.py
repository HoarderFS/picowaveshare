"""
Hardware Test 3.1: Basic Protocol Testing
Tests the ASCII protocol implementation via serial terminal
"""

import sys
import time
from pathlib import Path

import serial

# Add parent directory to path for test utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import get_test_port

# Add micropython directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "micropython"))


def find_pico_port():
    """Find the Pico serial port using auto-discovery"""
    port = get_test_port()
    if not port:
        print("No relay board found via auto-discovery")
        return None

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"Found Pico at {port}")
        return ser
    except Exception as e:
        print(f"Failed to open {port}: {e}")
        return None


def upload_protocol_files(ser):
    """Upload protocol files to Pico"""
    print("Uploading protocol implementation to Pico...")

    # Files to upload
    files = [
        "../micropython/config.py",
        "../micropython/relay_controller.py",
        "../micropython/protocol.py",
        "../micropython/uart_server.py",
    ]

    for file_path in files:
        full_path = Path(__file__).parent / file_path
        if not full_path.exists():
            print("ERROR: File not found: " + str(full_path))
            return False

        print("Uploading " + full_path.name + "...")
        with full_path.open() as f:
            content = f.read()

        # Simple file upload via exec
        ser.write(("exec('''" + content + "''')").encode())
        time.sleep(0.5)

    return True


def test_protocol_commands():
    """Test protocol commands via serial"""
    print("=== HARDWARE TEST 3.1: BASIC PROTOCOL ===")

    # Find Pico
    ser = find_pico_port()
    if not ser:
        print("ERROR: Could not find Pico")
        return False

    # Send soft reset
    ser.write(b"\x04")
    time.sleep(1)
    ser.read_all()

    # Create integrated test system
    print("Setting up integrated protocol test...")

    setup_commands = [
        "from relay_controller import RelayController",
        "from protocol import ProtocolParser",
        "from uart_server import UARTServer",
        "import time",
        "",
        "# Initialize components",
        "relay_ctrl = RelayController()",
        "protocol = ProtocolParser(relay_ctrl)",
        "uart_srv = UARTServer(relay_ctrl)",
        "",
        "# Test function",
        "def test_command(cmd):",
        "    response = protocol.process_command(cmd)",
        "    print('CMD: ' + cmd + ' -> ' + response.strip())",
        "    return response.strip()",
        "",
        "print('Protocol test system ready')",
    ]

    for cmd in setup_commands:
        ser.write((cmd + "\r\n").encode())
        time.sleep(0.05)

    time.sleep(1)

    # Test commands
    test_commands = [
        ("PING", "PONG"),
        ("STATUS", "00000000"),
        ("ON 1", "OK"),
        ("STATUS", "00000001"),
        ("ON 3", "OK"),
        ("STATUS", "00000101"),
        ("OFF 1", "OK"),
        ("STATUS", "00000100"),
        ("OFF 3", "OK"),
        ("STATUS", "00000000"),
        ("ON 9", "ERROR:INVALID_RELAY_NUMBER"),
        ("INVALID", "ERROR:INVALID_COMMAND"),
    ]

    print("\nTesting protocol commands:")
    print("-" * 40)

    for cmd, expected in test_commands:
        print("\nTesting: " + cmd)
        ser.write(("test_command('" + cmd + "')\r\n").encode())
        time.sleep(0.5)

        response = ser.read_all().decode("utf-8", errors="ignore")
        print("Response: " + response.strip())

        if expected in response:
            print("✓ PASS")
        else:
            print("✗ FAIL - Expected: " + expected)

    # Cleanup
    ser.write(b"relay_ctrl.all_off()\r\n")
    time.sleep(0.2)

    ser.close()
    print("\n" + "=" * 40)
    print("Hardware Test 3.1 Complete")
    return True


if __name__ == "__main__":
    test_protocol_commands()
