import time
import pyrf24
from . import baseband
import functools

# https://nrf24.github.io/RF24/
# https://pyrf24.readthedocs.io/en/latest/rf24_api.html


def clamp(x: int):
    """Clamp value to [0, 15]"""
    return min(max(x, 0), 15)

class Lightbar:
    """Implements a Xiaomi light bar controller with a nRF24L01 module"""

    def __init__(self, ce_pin: int, csn_pin: int, remote_id: int):
        self.radio = pyrf24.RF24()
        if not self.radio.begin(ce_pin, csn_pin):
            raise OSError("nRF24L01 hardware is not responding")
        self.radio.channel = 6  # 6, 43, 68 (or +1) -> 2406 MHz, 2043 MHz, 2068 MHz
        self.radio.pa_level = pyrf24.RF24_PA_LOW
        self.radio.data_rate = pyrf24.RF24_2MBPS
        self.radio.set_retries(0, 0)  # no repetitions, done manually in method send
        self.radio.listen = False
        self.radio.open_tx_pipe(bytes(5*[0x55]))  # Address, really sync sequence
        self.repetitions = 20
        self.delay_s = 0.01
        self.counter = 0
        self.id = remote_id  # Xiaomi remote id, 3-byte int (0x112233)

    def send(self, code: int, counter: int = None):
        """Send a command to the Xiaomi light bar.

        Arguments:
        code: 2 byte int (e.g. 0x0100)
        counter: int in range(0, 256) to reject repeated packets.
                 If None, use an internal counter that increments one.
        """
        if counter is None:
            counter = self.counter
            self.counter += 1
            if self.counter > 255:
                self.counter = 0
        pkt = baseband.packet(self.id, code, counter)
        for _ in range(self.repetitions):
            self.radio.write(pkt)
            time.sleep(self.delay_s)

    def on_off(self, counter: int = None):
        self.send(0x0100, counter)

    def reset(self, counter: int = None):
        self.send(0x0600, counter)

    def cooler(self, step: int = 1, counter: int = None):
        step = clamp(step)
        self.send(0x0200 + step, counter)

    def warmer(self, step: int = 1, counter: int = None):
        step = clamp(step)
        self.send(0x0300 - step, counter)

    def higher(self, step: int = 1, counter: int = None):
        step = clamp(step)
        self.send(0x0400 + step, counter)

    def lower(self, step: int = 1, counter: int = None):
        step = clamp(step)
        self.send(0x0500 - step, counter)

    def set_intensity(self, intensity: int, counter: int = None):
        """Set the intensity (≤0 lowest, ≥15 highest)"""

        intensity = clamp(intensity)
        if intensity < 8:  # Full scale lowest, then adjust
            self.lower(15)
            self.higher(intensity)
        else:              # Full scale highest, then adjust
            self.higher(15)
            self.lower(15-intensity)

    def set_color(self, color: int, counter: int = None):
        """Set the color (≤0 warmest, ≥15 coolest)"""

        color = clamp(color)
        if color < 8:  # Full scale warmest, then adjust
            self.warmer(15)
            self.cooler(color)
        else:          # Full scale coolest, then adjust
            self.cooler(15)
            self.warmer(15-color)
