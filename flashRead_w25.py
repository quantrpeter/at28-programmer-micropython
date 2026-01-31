import machine
import time
import ssd1306
from machine import SPI, Pin

# W25Q128 SPI Flash Configuration
# W25Q128 has 16MB (16777216 bytes) = 128 Mbit

# W25Q128 Commands
CMD_READ_DATA = 0x03
CMD_READ_STATUS = 0x05
CMD_READ_ID = 0x9F
CMD_FAST_READ = 0x0B
CMD_POWER_DOWN = 0xB9
CMD_RELEASE_POWER_DOWN = 0xAB
CMD_RESET_ENABLE = 0x66
CMD_RESET_MEMORY = 0x99

# SPI Configuration
spi = None
cs = None

def init_spi():
    global spi, cs
    # Initialize SPI bus (SPI1) for WeAct BlackPill
    # SCK=PA5, MISO=PA6, MOSI=PA7
    try:
        spi = machine.SPI(
            1,
            baudrate=1000000,
            polarity=0,
            phase=0,
            bits=8,
            firstbit=machine.SPI.MSB,
            sck=machine.Pin('A5'),
            mosi=machine.Pin('A7'),
            miso=machine.Pin('A6'),
        )
    except (ValueError, TypeError):
        try:
            spi = machine.SPI(1, baudrate=1000000, polarity=0, phase=0)
        except Exception:
            spi = machine.SoftSPI(
                baudrate=500000,
                polarity=0,
                phase=0,
                sck=machine.Pin('A5'),
                mosi=machine.Pin('A7'),
                miso=machine.Pin('A6'),
            )

    # CS pin (adjust based on your wiring)
    cs = machine.Pin('A4', machine.Pin.OUT, value=1)
    time.sleep_ms(1)

    flash_wake()
    flash_reset()
    
    # Check device ID
    device_id = read_device_id()
    if device_id == 0x000000:
        time.sleep_ms(5)
        device_id = read_device_id()
    print(f"W25Q128 Device ID: {device_id:06X}")
    if device_id == 0xEF4018:
        print("W25Q128 detected successfully")
    else:
        print(f"Warning: Unexpected device ID: {device_id:06X} (expected 0xEF4018)")

def read_device_id():
    """Read W25Q128 manufacturer and device ID"""
    cs.value(0)
    spi.write(bytes([CMD_READ_ID]))
    id_data = spi.read(3)
    cs.value(1)
    return (id_data[0] << 16) | (id_data[1] << 8) | id_data[2]

def flash_wake():
    """Release from power-down (safe to call even if not asleep)"""
    cs.value(0)
    spi.write(bytes([CMD_RELEASE_POWER_DOWN]))
    cs.value(1)
    time.sleep_ms(1)

def flash_reset():
    """Reset the flash (W25Q series supports 0x66/0x99)"""
    cs.value(0)
    spi.write(bytes([CMD_RESET_ENABLE]))
    cs.value(1)
    time.sleep_us(50)
    cs.value(0)
    spi.write(bytes([CMD_RESET_MEMORY]))
    cs.value(1)
    time.sleep_ms(1)

def read_status():
    """Read status register"""
    cs.value(0)
    spi.write(bytes([CMD_READ_STATUS]))
    status = spi.read(1)[0]
    cs.value(1)
    return status

def read_byte(addr):
    """Read a single byte from address"""
    cs.value(0)
    spi.write(bytes([CMD_READ_DATA, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
    data = spi.read(1)[0]
    cs.value(1)
    return data

def read_bytes(addr, length):
    """Read multiple bytes from address"""
    cs.value(0)
    spi.write(bytes([CMD_READ_DATA, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
    data = spi.read(length)
    cs.value(1)
    return data

def dump_flash(start, length):
    """Dump W25Q128 flash contents"""
    init_spi()
    
    # Initialize display (optional)
    # i2c_display = machine.I2C(1)
    # display = ssd1306.SSD1306_I2C(128, 64, i2c_display)
    # display.fill(0)
    # display.text("W25Q128 Reader", 5, 5, 1)
    # display.show()
    
    for base in range(start, start + length, 16):
        row = [f"{base:06X}:"]

        # if base % 1000 == 0:
        #     display.fill(0)
        #     display.text("W25Q128 Reader", 5, 5, 1)
        #     display.text(f"R {base:06X}", 5, 30, 1)
        #     display.show()

        chunk_len = min(16, (start + length) - base)
        data = read_bytes(base, chunk_len)
        for b in data:
            row.append(f"{b:02X}")
        print(' '.join(row))

if __name__ == "__main__":
    # W25Q128 has 16MB (16777216 bytes)
    # Read first 64KB for testing
    dump_flash(0, 65536)
