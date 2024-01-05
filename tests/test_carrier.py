#!/usr/bin/env python3

from xiaomi_lightbar import Lightbar
import pyrf24
import time

# Test the radio with a constant carrier at channel 6 (2406 MHz)

lightbar = Lightbar(25, 0, 0x000000) #  Lightbar id not required
lightbar.radio.start_const_carrier(pyrf24.RF24_PA_MIN, 6)
time.sleep(5)
lightbar.radio.stop_const_carrier()
