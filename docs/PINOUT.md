# Waveshare Pico Relay B Pinout Documentation

## Complete GPIO Pin Assignments

### Relay Control Pins
| Relay | GPIO Pin | Pico Pin Number | Function |
|-------|----------|-----------------|----------|
| Relay 1 | GP21 | Pin 27 | Active HIGH to turn ON |
| Relay 2 | GP20 | Pin 26 | Active HIGH to turn ON |
| Relay 3 | GP19 | Pin 25 | Active HIGH to turn ON |
| Relay 4 | GP18 | Pin 24 | Active HIGH to turn ON |
| Relay 5 | GP17 | Pin 22 | Active HIGH to turn ON |
| Relay 6 | GP16 | Pin 21 | Active HIGH to turn ON |
| Relay 7 | GP15 | Pin 20 | Active HIGH to turn ON |
| Relay 8 | GP14 | Pin 19 | Active HIGH to turn ON |

### Status LED Control Pins (if separate from relay control)
| LED | GPIO Pin | Function | Notes |
|-----|----------|----------|-------|
| LED 1-8 | Same as Relay GPIO | Status indicator | LEDs are driven by relay control signals |
| RGB LED (if present) | GP6, GP7, GP8 | R, G, B channels | PWM capable for color mixing |

### Buzzer Control (if present)
| Component | GPIO Pin | Pico Pin Number | Function |
|-----------|----------|-----------------|----------|
| Buzzer | GP22 | Pin 29 | Active HIGH, PWM for tone |

### User Buttons (if present)
| Button | GPIO Pin | Pico Pin Number | Function |
|--------|----------|-----------------|----------|
| User Button | GP9 | Pin 12 | Active LOW with pull-up |

### I2C Pins (for expansion)
| Function | GPIO Pin | Pico Pin Number | Notes |
|----------|----------|-----------------|-------|
| I2C0 SDA | GP4 | Pin 6 | Data line |
| I2C0 SCL | GP5 | Pin 7 | Clock line |
| I2C1 SDA | GP2 | Pin 4 | Alternate I2C |
| I2C1 SCL | GP3 | Pin 5 | Alternate I2C |

### SPI Pins (for expansion)
| Function | GPIO Pin | Pico Pin Number | Notes |
|----------|----------|-----------------|-------|
| SPI0 MISO | GP4 | Pin 6 | Master In Slave Out |
| SPI0 CS | GP5 | Pin 7 | Chip Select |
| SPI0 SCK | GP6 | Pin 9 | Clock |
| SPI0 MOSI | GP7 | Pin 10 | Master Out Slave In |

### ADC Pins (Analog Input)
| Function | GPIO Pin | Pico Pin Number | Notes |
|----------|----------|-----------------|-------|
| ADC0 | GP26 | Pin 31 | Analog input 0 |
| ADC1 | GP27 | Pin 32 | Analog input 1 |
| ADC2 | GP28 | Pin 34 | Analog input 2 |

### Special Function Pins
| Function | GPIO Pin | Pico Pin Number | Notes |
|----------|----------|-----------------|-------|
| Onboard LED | GP25 | Internal | Pico's built-in LED |
| BOOTSEL | N/A | N/A | Hold during power-up for USB boot |

### Available GPIO Pins
| Function | GPIO Pin | Pico Pin Number | Notes |
|----------|----------|-----------------|-------|
| GP0 | GPIO 0 | Pin 1 | Available for user expansion |
| GP1 | GPIO 1 | Pin 2 | Available for user expansion |
| GND | GND | Pin 3,8,13,18,23,28,33,38 | Common ground |

### Power Pins
| Pin | Function | Voltage | Notes |
|-----|----------|---------|-------|
| VBUS | Power input | 5V | From USB or external supply |
| VSYS | System power | 5V | After protection diode |
| 3V3(OUT) | 3.3V output | 3.3V | From onboard regulator |
| GND | Ground | 0V | Multiple pins available |

## Pin Mapping Diagram

```
                    Waveshare Pico Relay B
    +--------------------------------------------------+
    |  [USB]                                           |
    |                                                  |
    |  GP0 (TX) o──o VBUS                             |
    |  GP1 (RX) o──o VSYS                             |
    |       GND o──o GND                              |
    |       GP2 o──o 3V3_EN                           |
    |       GP3 o──o 3V3(OUT)                         |
    |       GP4 o──o ADC_VREF                         |
    |       GP5 o──o GP28                             |
    |       GND o──o GND                              |
    |       GP6 o──o GP27                             |
    |       GP7 o──o GP26                             |
    |       GP8 o──o RUN                              |
    |       GP9 o──o GP22                             |
    |       GND o──o GND                              |
    |      GP10 o──o GP21 (Relay 1) ← LED1            |
    |      GP11 o──o GP20 (Relay 2) ← LED2            |
    |      GP12 o──o GP19 (Relay 3) ← LED3            |
    |      GP13 o──o GP18 (Relay 4) ← LED4            |
    |       GND o──o GND                              |
    |      GP14 (Relay 8) → LED8 o──o GP17 (Relay 5) ← LED5  |
    |      GP15 (Relay 7) → LED7 o──o GP16 (Relay 6) ← LED6  |
    |                                                  |
    |  [Relay Terminals]                               |
    |  R1: [NC][COM][NO]  R2: [NC][COM][NO] ...       |
    +--------------------------------------------------+
```

## Signal Flow

### Relay Control Signal Path
```
Pico GPIO → Current Limiting Resistor → Optocoupler LED → 
→ Optocoupler Transistor → Relay Coil Driver → Relay Coil → 
→ Relay Contacts Switch
```

### Logic Levels
- GPIO HIGH (3.3V): Relay ON, LED ON, Contact NO-COM connected
- GPIO LOW (0V): Relay OFF, LED OFF, Contact NC-COM connected

## MicroPython Pin Configuration

### Complete Pin Definitions
```python
from machine import Pin, PWM, I2C, SPI, ADC

# Relay control pins
RELAY_PINS = {
    1: 21,  # GP21
    2: 20,  # GP20
    3: 19,  # GP19
    4: 18,  # GP18
    5: 17,  # GP17
    6: 16,  # GP16
    7: 15,  # GP15
    8: 14   # GP14
}

# Peripheral pins
BUZZER_PIN = 6       # GP6 - PWM capable
USER_BUTTON_PIN = 9  # GP9 - Active LOW (if present)
ONBOARD_LED_PIN = 25 # GP25 - Pico's built-in LED

# RGB LED pin (WS2812 NeoPixel)
RGB_PIN = 13         # GP13 - Single pin control for RGB LED

# I2C pins
I2C0_PINS = {'sda': 4, 'scl': 5}  # GP4, GP5
I2C1_PINS = {'sda': 2, 'scl': 3}  # GP2, GP3

# SPI pins
SPI0_PINS = {
    'miso': 4,   # GP4
    'cs': 5,     # GP5
    'sck': 6,    # GP6
    'mosi': 7    # GP7
}

# ADC pins
ADC_PINS = {
    0: 26,  # GP26
    1: 27,  # GP27
    2: 28   # GP28
}
```

### Initialization Examples
```python
# Initialize relays
relays = {}
for relay_num, pin_num in RELAY_PINS.items():
    relays[relay_num] = Pin(pin_num, Pin.OUT)
    relays[relay_num].value(0)  # Start with all relays OFF

# Initialize buzzer with PWM
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.freq(1000)  # 1kHz tone
buzzer.duty_u16(0)  # Start silent

# Initialize user button with pull-up
button = Pin(USER_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Initialize RGB LED (if present)
rgb_leds = {}
for color, pin_num in RGB_PINS.items():
    rgb_leds[color] = PWM(Pin(pin_num))
    rgb_leds[color].freq(1000)
    rgb_leds[color].duty_u16(0)  # Start off

# Initialize onboard LED
onboard_led = Pin(ONBOARD_LED_PIN, Pin.OUT)

# Note: Communication is via USB CDC serial, not hardware UART
# GP0 and GP1 are available for user expansion

# Initialize I2C (if needed)
i2c0 = I2C(0, sda=Pin(I2C0_PINS['sda']), scl=Pin(I2C0_PINS['scl']))

# Initialize ADC (if needed)
adc_channels = {}
for channel, pin_num in ADC_PINS.items():
    adc_channels[channel] = ADC(Pin(pin_num))
```

## Important Notes

1. **Board Variations**: Not all Waveshare Pico Relay B boards include all peripherals. Verify your board version:
   - Basic version: 8 relays only
   - Enhanced version: May include buzzer, RGB LED, user button
   - Check physical board for actual components present
2. **Pin Conflicts**: Some pins serve multiple functions (e.g., GP4-7 for both I2C/SPI)
3. **Pin Direction**: All relay control pins must be configured as OUTPUTS
4. **Initial State**: Initialize all relays to OFF (LOW) on startup for safety
5. **Current Draw**: Each active relay draws ~70-80mA from the 5V supply
6. **GPIO Protection**: The optocouplers provide isolation but still use proper GPIO handling
7. **Simultaneous Switching**: Avoid switching all 8 relays simultaneously to prevent power surge
8. **PWM Channels**: Pico has 16 PWM channels (8 slices × 2 channels each), plan usage accordingly

## Available GPIO Pins
After relay allocation, the following GPIO pins remain available:
- GP2-GP13: Available for other functions
- GP22: Available (note: also connected to onboard LED on some Pico boards)
- GP26-GP28: Available (GP26-27 are ADC capable)

## Power Consumption Table
| Active Relays | Approximate Current Draw |
|---------------|-------------------------|
| 0 | 20mA |
| 1 | 90-100mA |
| 2 | 160-180mA |
| 3 | 230-260mA |
| 4 | 300-340mA |
| 5 | 370-420mA |
| 6 | 440-500mA |
| 7 | 510-580mA |
| 8 | 580-660mA |

Note: Ensure your power supply can provide at least 700mA at 5V for reliable operation with all relays active.