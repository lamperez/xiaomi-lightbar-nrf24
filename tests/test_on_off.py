#!/usr/bin/env python3

from lightbar import Lightbar
import time
import os

# Define a environment variable LIGHTBAR_ID=0x123456
# Or use dotenv and an .env file

try:
    import dotenv
except ModuleNotFoundError:
    pass
else:
    dotenv.load_dotenv()

ID = int(os.getenv("LIGHTBAR_ID"), 0)

lightbar = Lightbar(25, 0, ID)
lightbar.radio.print_pretty_details()

lightbar.on_off();
time.sleep(1)
lightbar.send(0x0100)
