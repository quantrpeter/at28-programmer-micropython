import machine
import time
import ssd1306

# Pin mapping based on your comments
IO_PINS = [
    ('B5', 'IO0'),
    ('B8', 'IO1'),
    ('B9', 'IO2'),
    ('B2', 'IO3'),
    ('B0', 'IO4'),
    ('B1', 'IO5'),
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


def get_pin(pin_name, mode, pull=None):
    # Use string pin names directly, e.g., 'A2', 'B5'
    # print(pin_name)
    return machine.Pin(pin_name, mode, pull=pull)


# Setup address pins
# print("Setup address pins")
addr_pins = [get_pin(p[0], machine.Pin.OUT) for p in ADDR_PINS]
# Setup data pins
# print("Setup data pins")
io_pins = [get_pin(p[0], machine.Pin.IN) for p in IO_PINS]
# Setup control pins
# print("Setup control pins")
ce = get_pin(CE_PIN, machine.Pin.OUT)
oe = get_pin(OE_PIN, machine.Pin.OUT)
we = get_pin(WE_PIN, machine.Pin.OUT)


def set_address(addr):
    for i, pin in enumerate(addr_pins):
        pin.value((addr >> i) & 1)


def set_data_pins_output():
    for pin in io_pins:
        pin.init(mode=machine.Pin.OUT)


def set_data_pins_input():
    for pin in io_pins:
        pin.init(mode=machine.Pin.IN)


def set_data(value):
    for i, pin in enumerate(io_pins):
        pin.value((value >> i) & 1)


def write_byte(addr, value):
    value = value & 0xff
    set_address(addr)
    set_data_pins_output()
    set_data(value)
    oe.value(1)  # OE high (disable output)
    ce.value(0)  # CE low
    we.value(0)  # WE low (write enable)
    time.sleep_us(1)  # Write pulse width (increased)
    we.value(1)  # WE high
    ce.value(1)  # CE high
    set_data_pins_input()  # Restore data pins to input
    # time.sleep_us(10)  # Allow time for write cycle (increased)
    # Verification step: read back and compare
    # set_address(addr)
    # we.value(1)
    # ce.value(0)
    # oe.value(0)
    # time.sleep_us(50)  # Short delay to allow bus to settle

    # Verify the written value
    failTime = 0
    while True:
        # time.sleep_ms(10)
        # set_address(addr)
        we.value(1)
        ce.value(0)
        oe.value(0)
        read_val = 0
        time.sleep_us(1)  
        for i, pin in enumerate(io_pins):
            read_val |= (pin.value() << i)
        ce.value(1)
        oe.value(1)

        if read_val == value or failTime == 100:
            break
        
        if failTime > 10:
            print(f"addr: {addr:04X}, failTime: {failTime}, read_val: {read_val:02X}, expected value: {value:02X}")
        failTime += 1
        time.sleep_us(100)

    if read_val != value:
        print(
            f"Verify fail at {addr:04X}: wrote {value:02X}, read {read_val:02X}")
        # exit program
        raise Exception(
            f"Verification failed at address {addr:04X}: wrote {value:02X}, read {read_val:02X}")


def write_00_to_ff():
    i2c = machine.I2C(1)
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    display.fill(0)
    display.text("AT28 Programmer", 5, 5, 1)
    display.show()

    for addr in range(2048):
        if addr % 500 == 0:
            display.fill(0)
            display.text("AT28 Programmer", 5, 5, 1)
            display.text(f"W {addr:04X} to {addr:04X}", 5, 30, 1)
            display.show()

        print(f"W {addr:04X} to {addr:04X}")
        write_byte(addr, addr)

    display.fill(0)
    display.text("AT28 Programmer", 5, 5, 1)
    display.text(f"W {addr:04X} to {addr:04X}", 5, 30, 1)
    display.show()


def write(str):
    # Parse the input string into address-value pairs and write each value
    str = str[2:]  # Remove "w " prefix
    tokens = str.strip().split()
    if len(tokens) % 2 != 0:
        raise ValueError("Input string must contain pairs of <addr> <value>")
    i2c = machine.I2C(1)
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    display.fill(0)
    display.text("AT28 Programmer", 5, 5, 1)
    display.show()

    for i in range(0, len(tokens), 2):
        addr = int(tokens[i], 0)  # Support hex (0x...), decimal, etc.
        value = int(tokens[i+1], 0)
        write_byte(addr, value)

        if addr > 0 and addr % 500 == 0:
            print(f"Wrote {value:02X} to {addr:04X}")
            display.fill(0)
            display.text("AT28 Programmer", 5, 5, 1)
            display.text(f"W {value:02X} to {addr:04X}", 5, 30, 1)
            display.show()

    display.fill(0)
    display.text("AT28 Programmer", 5, 5, 1)
    display.text(f"W {value:02X} to {addr:04X}", 5, 30, 1)
    display.show()


def erase():
    for addr in range(2048):
        print(f"W {addr:04X}")
        write_byte(addr, 0x00)


if __name__ == "__main__":
    write_00_to_ff()
