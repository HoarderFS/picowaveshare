# Waveshare Pico Relay B - ASCII Protocol Specification

## Overview

The Waveshare Pico Relay B board uses an ASCII-based protocol for serial communication over USB. The board appears as a virtual serial port (CDC) when connected via USB. This protocol provides a simple, human-readable interface for controlling the 8 relays and querying board status.

## Communication Settings

- **Interface**: USB CDC Serial (Virtual COM Port)
- **Baud Rate**: 115200 (USB CDC - rate is virtual)
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Flow Control**: None
- **Connection**: USB Type-C connector on Pico board

## Command Summary

### Relay Control
- `ON <relay>` - Turn on relay (1-8)
- `OFF <relay>` - Turn off relay (1-8)  
- `ALL ON/OFF` - Control all relays
- `SET <pattern>` - Set relay pattern (8-bit binary)
- `PULSE <relay> <ms>` - Pulse relay for duration

### Status & Info
- `STATUS` - Get relay states (8-bit binary)
- `PING` - Connection test
- `INFO` - Board information with UID
- `UID` - Get unique identifier
- `VERSION` - Get firmware version
- `HELP` - List available commands

### Configuration  
- `NAME <relay> <name>` - Set relay name
- `GET NAME <relay>` - Get relay name
- `SAVE` - Save current states
- `LOAD` - Load saved states
- `CLEAR` - Clear saved states

### Buzzer Control
- `BEEP [ms]` - Short beep
- `BUZZ ON/OFF` - Continuous buzzer
- `TONE <hz> <ms>` - Play tone

## Protocol Structure

### Command Format
```
<COMMAND> [PARAMETERS]\n
```

- Commands are **case-insensitive**
- Parameters are separated by spaces
- Commands must be terminated with newline (`\n`)
- Maximum command length: 64 characters

### Response Format
```
<RESPONSE>\n
```

- All responses are terminated with newline (`\n`)
- Success responses: `OK` or data
- Error responses: `ERROR:<ERROR_CODE>`

## Basic Commands

### 1. PING - Connection Test
Tests connection to the board.

**Command:**
```
PING\n
```

**Response:**
```
PONG\n
```

**Example:**
```
> PING
< PONG
```

### 2. ON - Turn Relay On
Turns on a specific relay.

**Command:**
```
ON <relay_number>\n
```

**Parameters:**
- `relay_number`: Integer 1-8 (relay to turn on)

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> ON 1
< OK

> ON 5
< OK

> ON 9
< ERROR:INVALID_RELAY_NUMBER
```

### 3. OFF - Turn Relay Off
Turns off a specific relay.

**Command:**
```
OFF <relay_number>\n
```

**Parameters:**
- `relay_number`: Integer 1-8 (relay to turn off)

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> OFF 1
< OK

> OFF 3
< OK

> OFF 0
< ERROR:INVALID_RELAY_NUMBER
```

### 4. STATUS - Get Relay States
Returns the current state of all relays as an 8-bit binary string.

**Command:**
```
STATUS\n
```

**Response:**
```
<8-bit_binary>\n
```

**Binary Format:**
- 8 characters: `01010101`
- Position 1 (rightmost): Relay 1 state
- Position 8 (leftmost): Relay 8 state
- `1` = ON, `0` = OFF

**Examples:**
```
> STATUS
< 00000000
(All relays off)

> STATUS
< 10101010
(Relays 2,4,6,8 are on)

> STATUS
< 11111111
(All relays on)
```

## Advanced Commands

### 5. ALL ON - Turn All Relays On
Turns on all 8 relays simultaneously.

**Command:**
```
ALL ON\n
```

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Example:**
```
> ALL ON
< OK

> STATUS
< 11111111
```

### 6. ALL OFF - Turn All Relays Off
Turns off all 8 relays simultaneously.

**Command:**
```
ALL OFF\n
```

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Example:**
```
> ALL OFF
< OK

> STATUS
< 00000000
```

### 7. SET - Set Multiple Relays
Sets the state of all 8 relays using an 8-bit binary pattern.

**Command:**
```
SET <8-bit_binary>\n
```

**Parameters:**
- `8-bit_binary`: 8-character binary string (e.g., "10110000")
- Position 1 (rightmost): Relay 1 state
- Position 8 (leftmost): Relay 8 state
- `1` = ON, `0` = OFF

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> SET 10110000
< OK

> STATUS
< 10110000
(Relays 3,4,8 are on)

> SET 11111111
< OK
(All relays on)
```

### 8. PULSE - Pulse Relay
Turns a relay on for a specified duration then returns it to OFF state.

**Command:**
```
PULSE <relay_number> <duration_ms>\n
```

**Parameters:**
- `relay_number`: Integer 1-8 (relay to pulse)
- `duration_ms`: Duration in milliseconds (1-10000)

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> PULSE 1 500
< OK
(Relay 1 turns on for 500ms then off)

> PULSE 3 1000
< OK
(Relay 3 turns on for 1 second then off)
```

### 9. INFO - Get Board Information
Returns board information including unique identifier.

**Command:**
```
INFO\n
```

**Response:**
```
<board_name>,<version>,<channels>,UID:<unique_id>\n
```

**Format:**
- `board_name`: WAVESHARE-PICO-RELAY-B
- `version`: V1.0
- `channels`: 8CH
- `unique_id`: 16-character hex string from chip UID

**Example:**
```
> INFO
< WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:E6614C311B4C5A2F
```

### 10. UID - Get Unique Identifier
Returns only the board's unique identifier.

**Command:**
```
UID\n
```

**Response:**
```
<unique_id>\n
```

**Format:**
- `unique_id`: 16-character hex string derived from RP2040/RP2350 chip ID
- Always uppercase hexadecimal
- Guaranteed unique per chip

**Example:**
```
> UID
< E6614C311B4C5A2F
```

**Implementation Notes:**
- UID is read from chip's internal unique ID registers
- UID remains constant for the lifetime of the chip
- Can be used for device identification and tracking

### 11. NAME - Set Relay Name
Sets a persistent human-readable name for a relay. Names are stored in flash memory and persist across power cycles.

**Command:**
```
NAME <relay_number> <name>\n
```

**Parameters:**
- `relay_number`: Integer 1-8 (relay to name)
- `name`: String name (1-32 characters, no spaces in command)

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> NAME 1 LIGHTS
< OK

> NAME 2 FAN
< OK

> NAME 3 PUMP
< OK
```

### 12. GET NAME - Get Relay Name
Retrieves the stored name for a specific relay.

**Command:**
```
GET NAME <relay_number>\n
```

**Parameters:**
- `relay_number`: Integer 1-8 (relay to query)

**Response:**
- Success: `<name>\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> GET NAME 1
< LIGHTS

> GET NAME 2
< FAN

> GET NAME 9
< ERROR:INVALID_RELAY_NUMBER
```

**Storage Notes:**
- Names are stored in `relay_config.json` on the device's LittleFS filesystem
- Names persist across power cycles and firmware updates
- Default names are "Relay 1", "Relay 2", etc.
- Maximum name length is 32 characters
- Names are case-sensitive

## Buzzer Control Commands

### 13. BEEP - Short Beep
Produces a short beep for notifications and alerts.

**Command:**
```
BEEP\n
```

**Command with Duration:**
```
BEEP <duration_ms>\n
```

**Parameters:**
- `duration_ms`: Duration in milliseconds (1-5000, optional)
- Default duration: 100ms
- Default frequency: 1000Hz

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> BEEP
< OK
(Short 100ms beep)

> BEEP 250
< OK
(250ms beep)

> BEEP 10000
< ERROR:INVALID_PARAMETER
(Duration too long)
```

### 14. BUZZ - Continuous Buzzer
Turns the buzzer on or off continuously for alarms and alerts.

**Command:**
```
BUZZ <state>\n
```

**Parameters:**
- `state`: ON or OFF
- Frequency: 1000Hz (default)

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> BUZZ ON
< OK
(Buzzer starts continuously)

> BUZZ OFF
< OK
(Buzzer stops)

> BUZZ INVALID
< ERROR:INVALID_PARAMETER
```

### 15. TONE - Specific Frequency and Duration
Plays a specific frequency for a specified duration.

**Command:**
```
TONE <frequency_hz> <duration_ms>\n
```

**Parameters:**
- `frequency_hz`: Frequency in Hertz (50-20000)
- `duration_ms`: Duration in milliseconds (1-10000)

**Response:**
- Success: `OK\n`
- Error: `ERROR:<ERROR_CODE>\n`

**Examples:**
```
> TONE 440 1000
< OK
(Plays musical note A4 for 1 second)

> TONE 2000 500
< OK
(High-pitched tone for 500ms)

> TONE 25000 100
< ERROR:INVALID_PARAMETER
(Frequency out of range)
```

**Musical Notes Reference:**
- A4: 440Hz
- C5: 523Hz
- E5: 659Hz
- G5: 784Hz

**Boot Behavior:**
- The buzzer produces a short beep (200ms) when the system initializes
- This indicates the board is ready and buzzer is functional

**Duration Limits:**
- Maximum duration for BEEP, TONE, and PULSE: 5000ms (5 seconds)
- This limit prevents watchdog timer timeouts
- The board uses an 8-second watchdog timer for stability

## System Commands

### 16. VERSION - Get Firmware Version
Returns the current firmware version of the board.

**Command:**
```
VERSION\n
```

**Response:**
```
<version>\n
```

**Example:**
```
> VERSION
< 1.1.0
```

### 17. HELP - List Available Commands
Returns a list of all available commands.

**Command:**
```
HELP\n
```

**Response:**
```
Commands: <command_list>\n
```

**Example:**
```
> HELP
< Commands: PING,STATUS,ON,OFF,ALL,SET,PULSE,INFO,UID,NAME,GET,BEEP,BUZZ,TONE,VERSION,HELP,SAVE,LOAD,CLEAR
```

## State Persistence Commands

### 18. SAVE - Save Current Relay States
Saves the current relay states to persistent storage. The saved states can be restored later with the LOAD command.

**Command:**
```
SAVE\n
```

**Response:**
- Success: `SAVED\n`
- Error: `ERROR:SAVE_FAILED\n`

**Example:**
```
> SET 10110011
< OK

> SAVE
< SAVED
```

### 19. LOAD - Load Saved Relay States
Restores previously saved relay states from persistent storage.

**Command:**
```
LOAD\n
```

**Response:**
- Success: `LOADED\n`
- No saved states: `ERROR:NO_SAVED_STATE\n`
- Load failed: `ERROR:LOAD_FAILED\n`

**Example:**
```
> LOAD
< LOADED

> STATUS
< 10110011
```

### 20. CLEAR - Clear Saved Relay States
Removes all saved relay states from persistent storage.

**Command:**
```
CLEAR\n
```

**Response:**
- Success: `CLEARED\n`
- Error: `ERROR:CLEAR_FAILED\n`

**Example:**
```
> CLEAR
< CLEARED

> LOAD
< ERROR:NO_SAVED_STATE
```

### Auto-Load Feature
The board supports automatic restoration of saved relay states on boot:
- When enabled (default), saved states are automatically loaded when the board powers on
- The auto-load setting is stored persistently
- Auto-load only occurs if saved states exist

**Storage Implementation:**
- States are stored in `relay_config.json` along with relay names
- File includes: relay states, names, auto-load flag, and timestamps
- Storage survives power cycles and firmware updates

## Future Implementation Commands

### TOGGLE - Toggle Relay State
```
TOGGLE <relay_number>\n
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_COMMAND` | Unknown or malformed command |
| `INVALID_RELAY_NUMBER` | Relay number not in range 1-8 |
| `INVALID_PARAMETER` | Invalid parameter value |
| `INVALID_PARAMETER_COUNT` | Wrong number of parameters |
| `HARDWARE_ERROR` | Hardware operation failed |
| `BUFFER_OVERFLOW` | Command buffer overflow |
| `TIMEOUT` | Command timeout |
| `SAVE_FAILED` | Failed to save relay states |
| `LOAD_FAILED` | Failed to load relay states |
| `NO_SAVED_STATE` | No saved states found |
| `CLEAR_FAILED` | Failed to clear saved states |

## Pin Mapping

| Relay | GPIO Pin | Description |
|-------|----------|-------------|
| 1 | GP21 | Relay 1 control |
| 2 | GP20 | Relay 2 control |
| 3 | GP19 | Relay 3 control |
| 4 | GP18 | Relay 4 control |
| 5 | GP17 | Relay 5 control |
| 6 | GP16 | Relay 6 control |
| 7 | GP15 | Relay 7 control |
| 8 | GP14 | Relay 8 control |

## Example Session

```
> PING
< PONG

> STATUS
< 00000000

> ON 1
< OK

> ON 3
< OK

> STATUS
< 00000101

> ALL ON
< OK

> STATUS
< 11111111

> ALL OFF
< OK

> STATUS
< 00000000

> ON 9
< ERROR:INVALID_RELAY_NUMBER

> VERSION
< 1.1.0

> SAVE
< SAVED

> INVALID_COMMAND
< ERROR:INVALID_COMMAND
```

## Implementation Notes

### Command Processing
1. Commands are buffered until newline is received
2. Commands are parsed and validated
3. Valid commands are executed immediately
4. Responses are sent immediately after execution
5. Invalid commands return error responses

### Performance
- Response time: < 100ms for all commands
- Command rate: Up to 100 commands/second (tested at 83 commands/second)
- Buffer size: 64 characters maximum
- Memory: Periodic garbage collection every 10 commands
- Stability: 8-second watchdog timer prevents hangs

### Safety
- All relays initialize to OFF state on startup (unless auto-load is enabled)
- Invalid commands do not affect relay states
- Hardware errors are reported immediately
- Buffer overflow protection prevents crashes
- Watchdog timer (8 seconds) automatically resets board if hung
- PWM resources properly managed to prevent exhaustion
- Command durations limited to 5 seconds for watchdog safety

## Testing

### Manual Testing
Use any serial terminal (PuTTY, screen, minicom) to connect at 115200 baud and send commands manually.

### Automated Testing
The protocol supports automated testing through scripted command sequences.

### Hardware Verification
Each command should result in:
- Audible relay click
- Visual LED indicator change
- Correct status response

## Protocol Versioning

**Current Version**: 1.0

**Board Compatibility**: Waveshare Pico Relay B v1.0

**Firmware Version**: 1.1.0

### Version History
- **1.1.0** (Current)
  - Added VERSION command
  - Added HELP command
  - Added state persistence (SAVE/LOAD/CLEAR)
  - Added auto-load on boot feature
  - Improved stability with watchdog timer
  - Fixed memory leaks
  - Reduced command duration limits to 5 seconds
  - Added heartbeat LED for health monitoring

- **1.0.0**
  - Initial release
  - Basic relay control
  - Buzzer support
  - UID and naming features

## Future Extensions

Planned features for future protocol versions:
- Timing control
- Conditional commands
- Status monitoring
- Event notifications
- Configuration management