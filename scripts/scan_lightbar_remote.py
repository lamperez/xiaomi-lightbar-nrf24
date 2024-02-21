#!/usr/bin/env python3

import time
import crc
from struct import unpack
import argparse
import pyrf24

# https://pyrf24.readthedocs.io/en/latest/

parser = argparse.ArgumentParser(description=

"""
Script to capture and analyze a packet of the original remote for the Xiaomi Mi Computer Monitor Lightbar (non-BLE version), 
using a nRF24L01 transceiver connected to a Raspberry Pi.

- See https://github.com/lamperez/xiaomi-lightbar-nrf24/blob/main/readme.md for the dependencies and installation.
- Modify CE_PIN and CS_PIN as needed.
- Run the script.
- Put the remote close to the nRF24L01 and operate it, turning the knob.

The script will dump detected packets. Choose a packet with correct crc. Most of the packets are not detected, so you may need 
to try long enough to capture at least one correct packet to obtain the device ID of the remote. You may also change CHANNEL to
6, 15, 43 or 68 (or even 7, 16, 44 or 69) to try to increase the detection rate.

""")

parser.add_argument("-c", "--channel", type=int,default=6, help="6 (default), 15, 43, 68 (or +1) -> 2406 MHz, 2043 MHz, 2068 MH")
parser.add_argument("-p", "--power", type=str, default="LOW", choices=["MIN", "LOW", "HIGH", "MAX"], help="Change the power level")

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

CHANNEL = args.channel # 6 (default), 15, 43, 68 (or +1) -> 2406 MHz, 2043 MHz, 2068 MHz
CE_PIN = 25
CS_PIN = 0

crc16_config = crc.Configuration(
    width=16,
    polynomial=0x1021,
    init_value=0xFFFE,
    final_xor_value=0x0000,
    reverse_input=False,
    reverse_output=False,
)
crc16 = crc.Calculator(crc16_config)


def strip_bits(num: int, msb: int, lsb: int):
    """Strip msb and lsb bits of an int"""
    
    mask = (1 << num.bit_length()-msb)-1
    return (num & mask) >> lsb


def decode_packet(raw: bytes):
    """Decode a received packet

    I captured 12 bytes = 96 bits, but:
    - The first 15 bits (MSB) are the preamble trailing ones.
      Remember that the 24 LSB from the preamble were included in the captured packet.
      Where the other 9 bits are gone, I do not know. Maybe the ether monster ate them.
    - 9 bytes = 72 bits are the good ones, the payload.
    - The remaining 9 bits (LSB) are junk.
    """ 

    # Strip the preamble and junk bits
    raw_int = int.from_bytes(raw, "big")
    data = strip_bits(raw_int, 15, 9)
    
    # Now, the payload is clean and ready to be decoded
    keys = ["id", "separator", "counter", "command", "crc"]
    values = unpack('>3s s s 2s 2s', data.to_bytes(9, 'big'))
    values = (int.from_bytes(x, "big") for x in values)
    packet = dict(zip(keys, values))
    return packet


def good_packet(packet: int):
    """Check the CRC of a packet"""
    
    x = preamble.to_bytes(8, 'big')
    x += packet["id"].to_bytes(3, 'big')
    x += packet["separator"].to_bytes(1, 'big')
    x += packet["counter"].to_bytes(1, 'big')
    x += packet["command"].to_bytes(2, 'big')
    return packet["crc"] == crc16.checksum(x)


def print_packet(packet: int):
    if good_packet(packet):
        print("Decoded packet, CRC ok")
    else:
        print("Decoded packet, wrong CRC")
    for k, v in packet.items():
        print(f"• {k}: {hex(v)}")


preamble = 0x533914DD1C493412  # 8 bytes

radio = pyrf24.RF24()
if not radio.begin(CE_PIN, CS_PIN):
    raise OSError("nRF24L01 hardware is not responding")
radio.channel = CHANNEL
radio.pa_level = POW
radio.data_rate = pyrf24.RF24_2MBPS
radio.dynamic_payloads = False
radio.crc_length = pyrf24.RF24_CRC_DISABLED
radio.payload_size = 12  # More than necessary, I will strip some bits
radio.address_width = 5
radio.listen = True
radio.open_rx_pipe(1, preamble >> 24)  # 5 first bytes of preable
radio.print_details()
print(f"CHANNEL         = {CHANNEL}")

while True:
    has_payload, pipe_number = radio.available_pipe()
    if has_payload:
        received = radio.read(radio.payload_size)
        packet = decode_packet(received)
        print()
        print_packet(packet)
    time.sleep(0.1)
