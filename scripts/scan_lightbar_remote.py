#!/usr/bin/env python3

import time
import pyrf24
import crc
from struct import unpack

# https://pyrf24.readthedocs.io/en/latest/

CE_PIN = 25
CS_PIN = 0
CHANNEL = 43  # 6, 43, 68 (or +1) -> 2406 MHz, 2043 MHz, 2068 MHz

crc16_config = crc.Configuration(
    width=16,
    polynomial=0x1021,
    init_value=0xFFFE,
    final_xor_value=0x0000,
    reverse_input=False,
    reverse_output=False,
)
crc16 = crc.Calculator(crc16_config)


def strip_bits(num, msb, lsb):
    mask = (1 << num.bit_length()-msb)-1
    return (num & mask) >> lsb


def decode_packet(raw):
    raw_int = int.from_bytes(raw, "big")
    data = strip_bits(raw_int, 15, 9)  # 3 bytes, but magic numbers otherwise
    keys = ["id", "separator", "counter", "command", "crc"]
    values = unpack('>3s s s 2s 2s', data.to_bytes(9, 'big'))  # 12-3=9
    values = (int.from_bytes(x, "big") for x in values)
    packet = dict(zip(keys, values))
    return packet


def good_packet(packet):
    x = preamble.to_bytes(8, 'big')
    x += packet["id"].to_bytes(3, 'big')
    x += packet["separator"].to_bytes(1, 'big')
    x += packet["counter"].to_bytes(1, 'big')
    x += packet["command"].to_bytes(2, 'big')
    return packet["crc"] == crc16.checksum(x)


def print_packet(packet):
    if good_packet(packet):
        print("Decoded packet, CRC ok")
    else:
        print("Decoded packet, wrong CRC")
    for k, v in packet.items():
        print(f"• {k}: {hex(v)}")


preamble = 0x533914DD1C493412

radio = pyrf24.RF24()
if not radio.begin(CE_PIN, CS_PIN):
    raise OSError("nRF24L01 hardware is not responding")
radio.channel = CHANNEL
radio.data_rate = pyrf24.RF24_2MBPS
radio.dynamic_payloads = False
radio.crc_length = pyrf24.RF24_CRC_DISABLED
radio.payload_size = 12  # More than necessary, I will strip some bits
radio.address_width = 5
radio.listen = True
radio.open_rx_pipe(1, preamble >> 24)  # 5 bytes, I remove 3 lsb
radio.print_details()

while True:
    has_payload, pipe_number = radio.available_pipe()
    if has_payload:
        received = radio.read(radio.payload_size)
        packet = decode_packet(received)
        print()
        print_packet(packet)
    time.sleep(0.1)
