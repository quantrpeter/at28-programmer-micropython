import machine
import time
import ssd1306
from machine import I2C, Pin

# AT24 EEPROM I2C configuration
# Common AT24 I2C addresses: 0x50-0x57 (depending on A0-A2 pins)
AT24_I2C_ADDR = 0x50

# I2C bus configuration (I2C1)
# WeAct STM32F411 BlackPill I2C pins
i2c = None

def init_i2c():
    global i2c
    # Initialize I2C bus with explicit pin configuration for WeAct BlackPill
    # Using I2C2 with SCL=PB10, SDA=PB9
    i2c = machine.I2C(2, freq=100000)
    # Scan for devices
    devices = i2c.scan()
    print(f"I2C scan found {len(devices)} device(s): {[hex(d) for d in devices]}")
    if AT24_I2C_ADDR not in devices:
        print(f"Warning: AT24 not found at address 0x{AT24_I2C_ADDR:02X}")

def write_byte(addr, value):
    """Write a single byte to AT24 EEPROM at given address"""
    value = value & 0xff
    # For AT24C256 and similar: 2-byte addressing + data byte
    addr_bytes = bytes([addr >> 8, addr & 0xFF, value])
    i2c.writeto(AT24_I2C_ADDR, addr_bytes)
    # AT24 requires 5ms write cycle time
    time.sleep_ms(5)

def write_bytes(addr, data):
    """Write multiple bytes to AT24 EEPROM (page write)"""
    # For AT24C256: 64-byte page write
    # Note: writes must not cross page boundaries
    addr_bytes = bytes([addr >> 8, addr & 0xFF]) + bytes(data)
    i2c.writeto(AT24_I2C_ADDR, addr_bytes)
    # AT24 requires 5ms write cycle time
    time.sleep_ms(5)


def write_00_to_ff():
    init_i2c()
    
    # i2c_display = machine.I2C(1)
    # display = ssd1306.SSD1306_I2C(128, 64, i2c_display)
    # display.fill(0)
    # display.text("AT24 Programmer", 5, 5, 1)
    # display.show()

    for addr in range(32768):  # AT24C256 has 32KB
        if addr % 500 == 0:
            print(f"Writing 00 to {addr:04X}")
        #     display.fill(0)
        #     display.text("AT24 Programmer", 5, 5, 1)
        #     display.text(f"W {addr:04X}", 5, 30, 1)
        #     display.show()
        #     print(f"W {addr:04X}")

        write_byte(addr, addr & 0xFF)

    # display.fill(0)
    # display.text("AT24 Programmer", 5, 5, 1)
    # display.text(f"W Complete", 5, 30, 1)
    # display.show()


def write(str):
    init_i2c()
    
    # Parse the input string into address-value pairs and write each value
    str = str[2:]  # Remove "w " prefix
    tokens = str.strip().split()
    if len(tokens) % 2 != 0:
        raise ValueError("Input string must contain pairs of <addr> <value>")
    
    # i2c_display = machine.I2C(1)
    # display = ssd1306.SSD1306_I2C(128, 64, i2c_display)
    # display.fill(0)
    # display.text("AT28 Programmer", 5, 5, 1)
    # display.show()

    for i in range(0, len(tokens), 2):
        addr = int(tokens[i], 0)  # Support hex (0x...), decimal, etc.
        value = int(tokens[i+1], 0)
        write_byte(addr, value)

        if addr > 0 and addr % 500 == 0:
            print(f"Wrote {value:02X} to {addr:04X}")
            # display.fill(0)
            # display.text("AT28 Programmer", 5, 5, 1)
            # display.text(f"W {value:02X} to {addr:04X}", 5, 30, 1)
            # display.show()

    # display.fill(0)
    # display.text("AT28 Programmer", 5, 5, 1)
    # display.text(f"W {value:02X} to {addr:04X}", 5, 30, 1)
    # display.show()


def erase():
    init_i2c()
    
    for addr in range(32768):  # AT24C256 has 32KB
        if addr % 500 == 0:
            print(f"Erasing {addr:04X}")
        write_byte(addr, 0xFF)  # EEPROM erase value is typically 0xFF


if __name__ == "__main__":
    write_00_to_ff()
