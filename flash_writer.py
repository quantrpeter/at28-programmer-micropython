from machine import Pin, SoftI2C
from time import sleep,sleep_ms, sleep_us
import network
import math
import ssd1306
import os
import random

display = ssd1306.SSD1306_I2C(128, 64, SoftI2C(sda=Pin(22), scl=Pin(21)))
display.fill(0)
display.text("Peter", 10, 10, 1)
display.show() 
sleep(60)

