import crc
# https://github.com/Nicoretti/crc
# `python -m pip install crc`

# Structure of a packet (17 bytes)
# - preamble (8 bytes), common to all devices, 0x533914DD1C493412
# - remote id (3 bytes), hardcoded in the remote
# - separator (1 byte), common to all devices 0xFF
# - command id (2 bytes), the 2nd one means something (?)
# - sequence counter (1 byte)
# - CRC16 (2 bytes)
#
# The four first bits are 0b0101 = 0x5, they can be considered part of the
# sync sequence 0x5555555555. However, this breaks the byte alignment of the
# packet fields, and produces 4 trailing zeros in the last byte.
#
# Commands:
#    on_off:   0x0100
#    cooler:   0x0201
#    warmer:   0x03FF
#    stronger: 0x0401
#    softer:   0x05FF
#    reset:    0x0600
#
# The second byte of the command has some meaning.
# - In the case of on_off and reset, it can be different than 0x00,
#   with no apparent effect
# - For the others, it is related to the step of change. The farther
#   from 0x01 or 0xFF, the longer the step.
#   Notice that 0x01 = clockwise turn, 0xFF = counterclockwise turn (?)
#
# CRC16 reverse engineered from captured packets (at least 4).
# <https://hackaday.com/2019/06/27/reverse-engineering-cyclic-redundancy-codes>
# <https://reveng.sourceforge.io>
# ```
# reveng -w 16 -s 533914DD1C49341201B960FF7901003870 \
#                 533914DD1C49341201B960FF1601008F2A \
#                 533914DD1C49341201B960FF1A0100FA4B \
#                 533914DD1C49341201B960FF200100F82F
#
# width=16  poly=0x1021  init=0xfffe  refin=false  refout=false  xorout=0x0000
# check=0x6e62 residue=0x0000  name=(none)
# ```

preamble = 0x533914DD1C493412  # 8 bytes, common to all devices
separator = 0xFF

crc16_config = crc.Configuration(
    width=16,
    polynomial=0x1021,
    init_value=0xFFFE,
    final_xor_value=0x0000,
    reverse_input=False,
    reverse_output=False,
)
crc16 = crc.Calculator(crc16_config)


def packet(id: int, command: int, counter: int) -> bytes:
    """Build a packet for the Xiaomi light bar.

    Arguments:
    id: id of the remote, as 3 byte long int (e.g. 0x5421FE)
    command: a 2 byte int code, e. g. 0x0100.
             Invalid codes are silently ignored by the bar.
    counter: int in range(0, 256), to reject repeated packets
    """
    x = preamble.to_bytes(8, 'big')
    x += id.to_bytes(3, 'big')
    x += separator.to_bytes(1, 'big')
    x += counter.to_bytes(1, 'big')
    x += command.to_bytes(2, 'big')
    x += crc16.checksum(x).to_bytes(2, 'big')
    return x
