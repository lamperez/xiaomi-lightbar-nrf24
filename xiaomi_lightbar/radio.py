import time
import pyrf24
from . import baseband

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
        self.radio.channel = 6  # 6, 15, 43, 68 (or +1) -> 2406 MHz, 2015 MHz, 2043 MHz, 2068 MHz
        self.radio.pa_level = pyrf24.RF24_PA_LOW
        self.radio.data_rate = pyrf24.RF24_2MBPS
        self.radio.set_retries(0, 0)  # no repetitions, done manually in method send
        self.radio.listen = False
        self.radio.dynamic_payloads = False
        self.radio.payload_size = 17
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

    @property
    def is_available(self):
        return self.radio.is_chip_connected

    def on_off(self, counter: int = None):
        self.send(0x0100, counter)

    def reset(self, counter: int = None):
        self.send(0x0600, counter)

    def cooler(self, step: int = 1, counter: int = None):
        self.send(0x0200 + clamp(step), counter)

    def warmer(self, step: int = 1, counter: int = None):
        self.send(0x0300 - clamp(step), counter)

    def higher(self, step: int = 1, counter: int = None):
        self.send(0x0400 + clamp(step), counter)

    def lower(self, step: int = 1, counter: int = None):
        self.send(0x0500 - clamp(step), counter)

    def brightness(self, value: int, counter: int = None):
        """Set the brightness (≤0 lowest, ≥15 highest 270 lm)"""

        # Beware, counter increases by two, two operations
        counter2 = None if counter is None else counter+1

        # Saturate lowest sending an out-of-range step >15.
        # This delays the change until next update! Then adjust.
        self.send(0x0500-16, counter)
        self.higher(value, counter2)

    def color_temp(self, value: int, counter: int = None):
        """Set the color temperature (≤0 ~2700K, ≥15 ~6500K)"""

        # Beware, counter increases by two, two operations
        counter2 = None if counter is None else counter+1

        # Saturate warmest sending an out-of-range step >15.
        # This delays the change until next update! Then adjust.
        self.send(0x0300-16, counter)
        self.cooler(value, counter2)
