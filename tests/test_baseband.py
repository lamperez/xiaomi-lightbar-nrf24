from xiaomi_lightbar.baseband import packet

x_bytes = packet(id=0xABCDEF, command=0x0100, counter=0x72)
x = int.from_bytes(x_bytes, "big")
assert x == 0x533914dd1c493412abcdefff720100fad4
