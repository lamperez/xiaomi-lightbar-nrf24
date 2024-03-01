#!/usr/bin/env python3

import argparse
import pyrf24
import time
from xiaomi_lightbar import Lightbar

description = """
    Test the Xiaomi Mi Computer Monitor Lightbar with a nRF24 module.
"""

parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-c", "--channel", type=int,default=6, help="6, 15, 43, 68 (or +1) -> 2406 MHz, 2043 MHz, 2068 MH")
parser.add_argument("-p", "--power", type=str, default="LOW", choices=["MIN", "LOW", "HIGH", "MAX"], help="Change the power level.")
parser.add_argument("-i", "--id", type=lambda x: int(x, 16), default=0xABCDEF, help="ID of the remote.")

args = parser.parse_args()

# Set the power level
if args.power == "MIN":
    POW = pyrf24.RF24_PA_MIN
elif args.power == "LOW":
    POW = pyrf24.RF24_PA_LOW
elif args.power == "HIGH":
    POW = pyrf24.RF24_PA_HIGH
elif args.power == "MAX":
    POW = pyrf24.RF24_PA_MAX

CHANNEL = args.channel
ID = args.id

bar = Lightbar(25, 0, ID)
bar.radio.channel = CHANNEL
bar.radio.pa_level = POW
bar.radio.print_details()
print(f"CHANNEL         = {CHANNEL}")

print("Testing warmer")
time.sleep(3)
bar.warmer(15)

print("Testing cool white color temp")
time.sleep(3)
bar.color_temp(8)   # Intermediate, cool white

print("Testing cooler")
time.sleep(3)
bar.cooler(15)

print("Testing off and on")
time.sleep(3)
bar.on_off()
bar.on_off()

print("Done")