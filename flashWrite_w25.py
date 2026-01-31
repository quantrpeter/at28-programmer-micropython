import machine
import time
import ssd1306
from machine import SPI, Pin

# W25Q128 SPI Flash Configuration
# W25Q128 has 16MB (16777216 bytes) = 128 Mbit
# Page size: 256 bytes
# Sector size: 4KB
# Block size: 64KB

# W25Q128 Commands
CMD_WRITE_ENABLE = 0x06
CMD_WRITE_DISABLE = 0x04
CMD_READ_STATUS = 0x05
CMD_READ_STATUS2 = 0x35
CMD_READ_STATUS3 = 0x15
CMD_WRITE_STATUS = 0x01
CMD_READ_DATA = 0x03
CMD_PAGE_PROGRAM = 0x02
CMD_SECTOR_ERASE = 0x20
CMD_BLOCK_ERASE_32K = 0x52
CMD_BLOCK_ERASE_64K = 0xD8
CMD_CHIP_ERASE = 0xC7
CMD_READ_ID = 0x9F
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

    disable_protection()
    
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

def read_status2():
    """Read status register-2"""
    cs.value(0)
    spi.write(bytes([CMD_READ_STATUS2]))
    status = spi.read(1)[0]
    cs.value(1)
    return status

def read_status3():
    """Read status register-3"""
    cs.value(0)
    spi.write(bytes([CMD_READ_STATUS3]))
    status = spi.read(1)[0]
    cs.value(1)
    return status

def write_status(sr1, sr2):
    """Write status register-1 and -2"""
    wait_busy()
    write_enable()
    cs.value(0)
    spi.write(bytes([CMD_WRITE_STATUS, sr1 & 0xFF, sr2 & 0xFF]))
    cs.value(1)
    wait_busy()

def disable_protection():
    """Clear block protection bits and SRP"""
    sr1 = read_status()
    sr2 = read_status2()
    sr3 = read_status3()
    if (sr1 & 0x1C) or (sr1 & 0x80):
        print(f"Status before: SR1={sr1:02X} SR2={sr2:02X} SR3={sr3:02X}")
        write_status(sr1 & ~0x9C, sr2 & ~0x40)
        sr1 = read_status()
        sr2 = read_status2()
        sr3 = read_status3()
        print(f"Status after:  SR1={sr1:02X} SR2={sr2:02X} SR3={sr3:02X}")

def wait_busy():
    """Wait until write operation completes"""
    while read_status() & 0x01:
        time.sleep_us(10)

def write_enable():
    """Enable write operations"""
    cs.value(0)
    spi.write(bytes([CMD_WRITE_ENABLE]))
    cs.value(1)

def write_disable():
    """Disable write operations"""
    cs.value(0)
    spi.write(bytes([CMD_WRITE_DISABLE]))
    cs.value(1)

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

def write_page(addr, data):
    """Write up to 256 bytes (one page). Address must be page-aligned."""
    if len(data) > 256:
        raise ValueError("Page write data must be <= 256 bytes")
    
    wait_busy()
    write_enable()

    # Ensure write-enable latch is set (bit 1)
    if (read_status() & 0x02) == 0:
        write_enable()
        if (read_status() & 0x02) == 0:
            raise RuntimeError("Write enable latch not set. Check /WP pin.")
    
    cs.value(0)
    spi.write(bytes([CMD_PAGE_PROGRAM, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
    spi.write(data)
    cs.value(1)
    
    wait_busy()

def write_byte(addr, value):
    """Write a single byte to address"""
    write_page(addr, bytes([value & 0xFF]))

def sector_erase(addr):
    """Erase a 4KB sector (sector address must be sector-aligned)"""
    wait_busy()
    write_enable()

    if (read_status() & 0x02) == 0:
        write_enable()
        if (read_status() & 0x02) == 0:
            raise RuntimeError("Write enable latch not set. Check /WP pin.")
    
    cs.value(0)
    spi.write(bytes([CMD_SECTOR_ERASE, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
    cs.value(1)
    
    wait_busy()

def block_erase_64k(addr):
    """Erase a 64KB block (address must be block-aligned)"""
    wait_busy()
    write_enable()
    
    cs.value(0)
    spi.write(bytes([CMD_BLOCK_ERASE_64K, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
    cs.value(1)
    
    wait_busy()

def chip_erase():
    """Erase entire chip (takes several seconds)"""
    wait_busy()
    write_enable()
    
    cs.value(0)
    spi.write(bytes([CMD_CHIP_ERASE]))
    cs.value(1)
    
    print("Chip erase started (this may take 10-30 seconds)...")
    wait_busy()
    print("Chip erase complete")

def write_00_to_ff():
    init_spi()
    
    # i2c_display = machine.I2C(1)
    # display = ssd1306.SSD1306_I2C(128, 64, i2c_display)
    # display.fill(0)
    # display.text("W25Q128 Writer", 5, 5, 1)
    # display.show()

    # Erase first 64KB (16 sectors) before writing
    # for sector in range(0, 16):
    #     sector_addr = sector * 0x1000
    #     print(f"E {sector_addr:06X}")
    #     sector_erase(sector_addr)

    # Write first 64KB for testing, page-by-page
    for page_addr in range(0, 65536, 256):
        if page_addr % 1000 == 0:
            print(f"W {page_addr:06X}")
            # display.fill(0)
            # display.text("W25Q128 Writer", 5, 5, 1)
            # display.text(f"W {page_addr:06X}", 5, 30, 1)
            # display.show()

        page = bytes([(page_addr + i) & 0xFF for i in range(256)])
        write_page(page_addr, page)

    # display.fill(0)
    # display.text("W25Q128 Writer", 5, 5, 1)
    # display.text(f"Write Complete", 5, 30, 1)
    # display.show()


def write(str):
    init_spi()
    
    # Parse the input string into address-value pairs and write each value
    str = str[2:]  # Remove "w " prefix
    tokens = str.strip().split()
    if len(tokens) % 2 != 0:
        raise ValueError("Input string must contain pairs of <addr> <value>")
    
    # i2c_display = machine.I2C(1)
    # display = ssd1306.SSD1306_I2C(128, 64, i2c_display)
    # display.fill(0)
    # display.text("W25Q128 Writer", 5, 5, 1)
    # display.show()

    for i in range(0, len(tokens), 2):
        addr = int(tokens[i], 0)  # Support hex (0x...), decimal, etc.
        value = int(tokens[i+1], 0)
        write_byte(addr, value)

        if addr > 0 and addr % 1000 == 0:
            print(f"Wrote {value:02X} to {addr:06X}")
            # display.fill(0)
            # display.text("W25Q128 Writer", 5, 5, 1)
            # display.text(f"W {value:02X} to {addr:06X}", 5, 30, 1)
            # display.show()

    # display.fill(0)
    # display.text("W25Q128 Writer", 5, 5, 1)
    # display.text(f"W {value:02X} to {addr:06X}", 5, 30, 1)
    # display.show()


def erase():
    init_spi()
    
    print("Erasing entire W25Q128 chip...")
    chip_erase()
    print("Erase complete")


def erase_sector(sector_addr):
    """Erase a specific 4KB sector"""
    init_spi()
    
    # Align to sector boundary (4KB = 0x1000)
    sector_addr = sector_addr & 0xFFFFF000
    print(f"Erasing sector at {sector_addr:06X}...")
    sector_erase(sector_addr)
    print(f"Sector at {sector_addr:06X} erased")


if __name__ == "__main__":
    write_00_to_ff()
