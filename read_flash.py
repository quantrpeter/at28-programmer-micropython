import machine
import time
import ssd1306

# Pin mapping based on your comments
IO_PINS = [
    ('B5', 'IO0'),
    ('B8', 'IO1'),
    ('B9', 'IO2'),
    ('C13', 'IO3'),
    ('C14', 'IO4'),
    ('C15', 'IO5'),
    ('A0', 'IO6'),
    ('A1', 'IO7'),
]

ADDR_PINS = [
    ('B4', 'A0'),
    ('B3', 'A1'),
    ('A15', 'A2'),
    ('B15', 'A3'),
    ('B14', 'A4'),
    ('B13', 'A5'),
    ('B12', 'A6'),
    ('B10', 'A7'),
    ('A6', 'A9'),
    ('A7', 'A8'),
    ('A3', 'A10'),
]

CE_PIN = 'A2'
OE_PIN = 'A4'
WE_PIN = 'A5'

# Helper to get pin object from name
def get_pin(pin_name, mode):
    # Use string pin names directly, e.g., 'A2', 'B5'
    print(pin_name)
    return machine.Pin(pin_name, mode)

# Setup address pins
print("Setup address pins")
addr_pins = [get_pin(p[0], machine.Pin.OUT) for p in ADDR_PINS]
# Setup data pins
print("Setup data pins")
io_pins = [get_pin(p[0], machine.Pin.IN) for p in IO_PINS]
# Setup control pins
print("Setup control pins")
ce = get_pin(CE_PIN, machine.Pin.OUT)
oe = get_pin(OE_PIN, machine.Pin.OUT)
we = get_pin(WE_PIN, machine.Pin.OUT)

def set_address(addr):
    for i, pin in enumerate(addr_pins):
        pin.value((addr >> i) & 1)

def read_byte(addr):
    set_address(addr)
    ce.value(0)  # CE low
    oe.value(0)  # OE low
    we.value(1)  # WE high
    time.sleep_us(1)  # Small delay for settling
    value = 0
    for i, pin in enumerate(io_pins):
        value |= (pin.value() << i)
    ce.value(1)
    oe.value(1)
    return value

def dump_flash():
    i2c=machine.I2C(1)
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    display.fill(0)
    display.text("AT28 Programmer", 5, 5, 1)
    display.show()
    
    for base in range(0, 2048, 16):
        row = []
        for offset in range(16):
            addr = base + offset
            
            if addr % 500 == 0:
                display.fill(0)
                display.text("AT28 Programmer", 5, 5, 1)
                display.text(f"R {addr:02X} to {addr:04X}", 5, 30, 1)
                display.show()
                
            if addr >= 2048:
                break
            b = read_byte(addr)
            row.append(f"{b:02X}")
        print(' '.join(row))

if __name__ == "__main__":
    dump_flash()
