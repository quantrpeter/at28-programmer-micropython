import machine
import time
import ssd1306

# AT24 EEPROM I2C configuration
# Common AT24 I2C addresses: 0x50-0x57 (depending on A0-A2 pins)
AT24_I2C_ADDR = 0x3c

# I2C bus configuration (I2C1)
# SCL and SDA pins will be auto-configured by I2C(1)
i2c = None

def init_i2c():
    global i2c
    # Initialize I2C bus (bus 1, typically SCL=B6, SDA=B7 on STM32)
    i2c = machine.I2C(1, freq=100000)
    # Scan for devices
    devices = i2c.scan()
    if AT24_I2C_ADDR not in devices:
        print(f"Warning: AT24 not found at address 0x{AT24_I2C_ADDR:02X}")
        print(f"Found devices: {[hex(d) for d in devices]}")

def read_byte(addr):
    """Read a single byte from AT24 EEPROM at given address"""
    # For AT24C256 and similar: 2-byte addressing
    addr_bytes = bytes([addr >> 8, addr & 0xFF])
    i2c.writeto(AT24_I2C_ADDR, addr_bytes, False)
    data = i2c.readfrom(AT24_I2C_ADDR, 1)
    return data[0]

def read_bytes(addr, length):
    """Read multiple bytes from AT24 EEPROM"""
    # For AT24C256 and similar: 2-byte addressing
    addr_bytes = bytes([addr >> 8, addr & 0xFF])
    i2c.writeto(AT24_I2C_ADDR, addr_bytes, False)
    return i2c.readfrom(AT24_I2C_ADDR, length)

def dump_flash(start, length):
    """Dump AT24 EEPROM contents"""
    init_i2c()
    
    # Initialize display
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    display.fill(0)
    display.text("AT24 Programmer", 5, 5, 1)
    display.show()
    
    for base in range(start, start+length, 16):
        row = []
        row.append(f"{base:04X}:")
        for offset in range(16):
            addr = base + offset
            
            if addr % 500 == 0:
                display.fill(0)
                display.text("AT24 Programmer", 5, 5, 1)
                display.text(f"R {addr:04X}", 5, 30, 1)
                display.show()
                
            if addr >= start + length:
                break
            b = read_byte(addr)
            row.append(f"{b:02X}")
        print(' '.join(row))

if __name__ == "__main__":
    # AT24C256 has 32KB (32768 bytes)
    # Change this based on your AT24 chip size
    dump_flash(0, 32768)
