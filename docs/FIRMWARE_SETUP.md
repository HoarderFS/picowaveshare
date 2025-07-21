# Firmware Setup for Waveshare Pico Relay B

## Step 1: Enter Bootloader Mode

1. **Disconnect** the Pico from USB
2. **Hold down the BOOTSEL button** (white button on the Pico)
3. **While holding BOOTSEL**, connect the USB cable
4. **Release BOOTSEL** after connecting
5. The Pico should appear as a mass storage device named **RPI-RP2**

## Step 2: Install MicroPython Firmware

1. Download the latest MicroPython firmware:
   ```bash
   curl -O https://micropython.org/download/rp2-pico/rp2-pico-latest.uf2
   ```

2. Copy the firmware to the Pico:
   ```bash
   cp rp2-pico-latest.uf2 /Volumes/RPI-RP2/
   ```

3. The Pico will automatically reboot with MicroPython installed

## Step 3: Verify Installation

After the Pico reboots, it should appear as a serial device. You can verify with:
```bash
ls /dev/cu.usbmodem*
```

## Step 4: Connect to REPL

Using mpremote:
```bash
source venv/bin/activate
mpremote
```

Or using screen:
```bash
screen /dev/cu.usbmodem* 115200
```

To exit screen: Press `Ctrl-A` then `K` then `Y`

## Troubleshooting

If the Pico doesn't appear:
- Try a different USB cable (must be data cable, not charge-only)
- Try a different USB port
- Make sure BOOTSEL is held while connecting

If REPL doesn't work:
- The board might be running a program - press Ctrl-C to interrupt
- Press Ctrl-D to soft reset
- Check the serial port settings (115200, 8N1)