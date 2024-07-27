Control a 
[Xiaomi My Computer Monitor Light Bar](https://www.mi.com/global/product/mi-computer-monitor-light-bar/)
MJGJD01YL, using a cheap 2.4 GHz radio transceiver module (nRF24L01 or nRF24L01+).

> [!IMPORTANT]
> There are two variants of the light bar, both of them controlled by 2.4 GHz radio signals (see the
> label on the bar for the device number).
> - Device number MJGJD01YL. It uses a TLSR8368 radio receiver and a proprietary radio format. This is
> the one that can be used with this library.
> - Device number MJGJD02YL. It uses a ESP32 and BLE (and even wifi, during the pairing process). See
> [here](https://community.home-assistant.io/t/support-for-xiaomi-mijia-1s-light-bar-mjgjd02yl-in-xiaomi-miio-integration/382276)
> or [here](https://karlquinsland.com/xaomi-s1-monitor-lamp-teardown-and-tasmota) for many details
> on how to use it with Home Assistant.

This library is inspired and based on 
[this thread](https://community.home-assistant.io/t/xiaomi-monitor-light-bar/298796/4) from the
Home Assistant community forum. My objective is to control the light bar from a Raspberry Pi where
Home Assistant is already running in a Docker container.

# Requirements

- Xiaomi My Computer Monitor Light Bar, model MJGJD01YL (without BLE or app)
- Raspberry Pi, or any other device running Linux with GPIOs and a SPI controller, and Python 3.
- nRF24L01(+) module.

# Installation

## Hardware setup

Connect the RPi to the nRF24L01 as shown
[here](https://www.laboratoriogluon.com/conectar-raspberry-pi-3-a-nrf24l01). 

In this document it
will be assumed that the SPI0 bus is used, and therefore `csn_pin=0`. The chip enable will be
connected to GPIO25 (`ce_pin=25`).
See [here](https://nrf24.github.io/RF24/md_docs_rpi_general.html) for the gory details.

## Dependencies

- `pyrf24` [pyRF24 python library](https://nrf24.github.io/pyRF24)
- `crc` [CRC python library](https://github.com/Nicoretti/crc)

Notice that `pyrf24` may need to build from source on some systems. In such case, you will need cmake and python headers (python3-dev) installed.

- Debian based OS (e.g. Raspberry Pi OS)
```sh
  sudo apt-get install python3-dev cmake
  python -m pip install pyrf24

```
- Alpine Linux (e.g. Docker container)
```sh
  apk add --no-cache cmake make g++ boost-dev
  python -m pip install pyrf24

```

# Usage

Assuming that pins are `ce_pin=25` and `csn_pin=0` and the id of the remote is `0xABCDEF` (3 byte
long), start with
```python
from xiaomi_lightbar import Lightbar
bar = Lightbar(25, 0, 0xABCDEF)
```
Then you can turn on or off:
```python
bar.on_off()
```
Notice that there is no on or off command, since both are the same for the original controller.

The id of the remote can be extracted using the [script](scripts/scan_lightbar_remote.py) provided in 
the `scripts/` folder. Alternatively, see below to use an arbitrary id.

The library uses an internal counter that is incremented on each call, required by the bar to
reject repeated consecutive packets (the radio interface has a lot of redundancy). You can use your
own counter (0 to 255) as a named argument, but if you repeat the same value twice or more it will
only work the first time.
```python
bar.on_off(counter=14)  # it works
bar.on_off(counter=15)  # it works
bar.on_off(counter=14)  # it works
bar.on_off(counter=14)  # No, repeated
```

The light bar remote has six operations:
- On/off, pressing the knob.
- Higher and lower light brightness, turning the knob.
- Colder and warmer color temperature, pressing and turning the knob.
- Reset to medium brightness and warm color, long-pressing the knob.

Therefore, the full list of commands is 
```python
bar.on_off()  # Turn on or off
bar.cooler()  # Cooler/bluer color
bar.warmer()  # Warmer/yellower color
bar.higher()  # Higher brightness
bar.lower()   # Lower brightness
bar.reset()   # Reset, medium brightness, warm color
```
The four turning operations also register the speed of change. Therefore, the four corresponding commands accept one 
optional numerical parameter, 1 to 15, that represent the change in each operation. The default value is 1, while 15 
covers the full range of brightness or color temperature in just one operation.
```python
bar.cooler(15)
bar.warmer(3)
bar.higher(5)
bar.lower(4)
```

Alternatively, the absolute value of brightness (0 lowest, 15 highest) can be set with
```python
bar.brightness(4)   # Medium-low
bar.brightness(13)  # Rather high
```
And in a similar way, for the absolute value of color temperature (0 warmest, 15 coldest)
```python
bar.color_temp(0)   # Warm white, 2700 K
bar.color_temp(8)   # Intermediate, cool white
bar.color_temp(15)  # Day light, 6500 K
```

## Controlling the bar with an arbitrary id

If you cannot/do not want to capture your remote id, you can reprogram the bar with an arbitrary one. According to the manual, you can use one remote with several bars, reprogramming them. Just unplug and plug the bar, and within 20 seconds long press the remote. The bar will briefly flash.

We can do the same thing with the library. Choose an arbitrary id,
```python
bar = Lightbar(25, 0, 0x111111)
```
unplug and plug the bar, and within 20 seconds run
```python
bar.reset()
```
Of course, now the remote will not work. You can undo everything by reprogramming the bar again (with the remote or the library).

# MQTT

Copy the following to the configuration.yaml file in your homeassistant and restart.
```python
mqtt:
  - light:
      - name: "Xiaomi Lightbar"
        command_topic: "xiaomi/lightbar/control"
        payload_on: "ON"
        payload_off: "OFF"
        max_mireds: 370
        min_mireds: 153
        brightness_command_topic: "xiaomi/lightbar/brightness/set"
        color_temp_command_topic: "xiaomi/lightbar/temperature/set"
        brightness_value_template: "{{ value_json.brightness }}"
        color_temp_value_template: "{{ value_json.temp }}"
```

To use the MQTT subscriber, you need to run the `subscriber.py` script with the appropriate arguments.
- Put correct broker, and port details
- If your mqtt broker has no password then keep username and password empty.
- Keep topic, ce_pin and csn_pin unchanged unless necessary
- Make sure you put your correct remote ID. 
```sh  
  --broker BROKER       MQTT Broker
  --port PORT           MQTT Port
  --username USERNAME   MQTT Username
  --password PASSWORD   MQTT Password
  --topic TOPIC         MQTT Topic
  --ce_pin CE_PIN       CE Pin
  --csn_pin CSN_PIN     CSN Pin
  --remote_id REMOTE_ID Remote ID
```
If everything is done correctly you should be able to see and a light entity named xaiomi_lightbar. With this you can control your light bar from Home Assistant.

# Background

If you are interested in the gory details of the radio and baseband used by the light bar, keep reading.

## Reverse engineering of the radio interface

I have analized the radio signals from the remote using a [HackRF
One](https://greatscottgadgets.com/hackrf/one/) SDR, with [Universal Radio
Hacker](https://github.com/jopohl/urh). The chipset included in the remote and the light bar
(Telink TLSR8368 or similar) are common in wireless mice and keyboards. Only the remote acts as a
transmitter, the light bar is just a receiver. Therefore, you can think of the remote as a wireless
mouse (with clicks and wheels), while the bar is like the receiver you plug in a USB port, with no
data transmission to any USB host.

The control uses at least three 2 MHz channels centered at 2406 MHz, 2043 MHz and 2068 MHz. It uses
a rather aggressive frequency-hopping scheme ([thanks, Hedy](https://en.wikipedia.org/wiki/Hedy_Lamarr#Inventor)). 
Each command is sent as a burst of ten 100 µs identical pulses, repeated each 1300 µs. 
The time between pulses is used to transmit the same burst in the other channels. 
A full burst captured by the SDR is shown here.

![Burst of RF pulses](./pics/xiaomi_lightbar_rf_burst.png) 

Here you can see not only the burst of ten pulses, but also what is leaked from other
channel in the frequency-hopping scheme (the small ten pulses before the main ones), and other
pulses of unrelated 2.4 GHz devices.

The modulation of the pulses is a simple FSK, with a frequency deviation of ±500 MHz. Below, a
demodulated pulse is shown (that is, the graph is the instant frequency of the signal in terms of
the time):

![Demodulated FSK pulse](./pics/xiaomi_lightbar_demodulated_pulse.png) 

The bit rate is 2 Mbps, and therefore the bit length is 0.5 µs. Each pulse contains a packet of 17
bytes, or 136 bits, equal to 68 µs. The remaining time up to 100 µs corresponds to a synchronization 
sequence before the bits, to allow the receiver to lock into the signal frequency. 
I suspect that the wavy shape of the frequency plot during the sync sequence is meant to help the locking process.

## Baseband packet format

A baseband packet (17 bytes) is composed of the following fields
- Preamble (8 bytes), common to all devices, `0x533914DD1C493412`
- Remote id (3 bytes), hardcoded in the remote
- Separator (1 byte), common to all devices `0xFF`
- command id (2 bytes), the 2nd one means something (?)
- sequence counter (1 byte)
- CRC16 checksum (2 bytes)

This structure is compatible with the 
[Telink baseband packet format](http://wiki.telink-semi.cn/doc/ds/DS_TLSR8368-E_Datasheet%20for%20Telink%202.4GHz%20RF%20System-On-Chip%20Solution%20TLSR8368.pdf#page=39), 
used by the TLSR8368 chip 

Before the packet, a synchronization sequence `0x5555555555` is transmitted (in binary it is just
`0b010101...` ). Notice that the four first bits in the preamble are
`0b0101 = 0x5`, they could be considered still part of the sync sequence. Doing so, the preamble
becomes `0x67229ba38926824`. However, this is clearly not a valid approach
- The `0x67...` preamble is 60 bits long, 7 bytes and a half.
- The byte alignment of the other packet fields is broken.
- There are 4 trailing zero bits in all the captured packets.
- The CRC16 checksum cannot be computed.

The [ISM](https://en.wikipedia.org/wiki/ISM_radio_band) 2.4 GHz radio interface is a battlefield
where your wireless mouse, bluetooth headset, and 2.4 GHz wifi (and your neighbour's one) are just
fighting for the spectrum with the leakage from the microwave oven. The strategy against the
corruption of the radio packets is to repeat them many times in bursts (see above), check their
integrity and drop the wrong ones. Then, the redundant ones are also dropped, using the sequence
counter to detect repeated packets.

## Command codes

The command codes that work are the ones in the following table:

| Command | Code 1         | Code 2         | Default |
|---------|----------------|----------------|---------|
| on_off  | 0x01??         | -              | 0x0100  |
| cooler  | 0x0200 + steps | 0x0300 + steps | 0x0201  |
| warmer  | 0x0300 - steps | 0x0400 - steps | 0x03FF  |
| higher  | 0x0400 + steps | 0x0500 + steps | 0x0401  |
| lower   | 0x0500 - steps | 0x0600 - steps | 0x05FF  |
| reset   | 0x06??         | 0x07??         | 0x0600  |

- `steps` is a number from 1 to 15. It encodes the turning speed of the wheel.
- The default codes are the ones sent by the original control (low turning speed).
- Wrong codes (e.g. `0x0800`) are silently ignored.
- The brightness and color temperature scales are from 0 up to 15 (16 states)
- Steps higher than 15 saturate the brightness or color temperature to its min/max value, 
  but they are not immediately applied. Instead, the bar waits for the next update in the opposite
  direction. This can be used to fix an absolute value of brightness or color temperature, without
  flicker: saturate to the minimum, and then increase to the desired level.


## CRC checksum

The integrity of a packet is check using a CRC16 checksum (the trailing two bytes in each packet).
I have reverse-engineered it using the excellent tool [reveng](https://reveng.sourceforge.io),
that I found through this
[Hackaday article](https://hackaday.com/2019/06/27/reverse-engineering-cyclic-redundancy-codes).
At least 4 captured packets are required to determine the parameters of the CRC algorithm.
Important, the packets must be correctly byte-aligned (they must start with `0x53`)

```
reveng -w 16 -s 533914DD1C49341201B960FF7901003870 \
                533914DD1C49341201B960FF1601008F2A \
                533914DD1C49341201B960FF1A0100FA4B \
                533914DD1C49341201B960FF200100F82F

width=16  poly=0x1021  init=0xfffe  refin=false  refout=false  xorout=0x0000
check=0x6e62 residue=0x0000  name=(none)
```
The validity of the checksum can be tested by changing the packets. The parameters of the CRC
checksum should be the same in all cases.

# Signal generation with the nRF24L01(+)

Both the baseband format and the radio signals are completely known. New valid packets can be
generated, and spoofed using a SDR (the HackRF, for example). However, the objective is a low cost
solution that can be permanently integrated into the Raspberry Pi or a similar device. The nRF24L01
or nRF24L01+ enters the scene.

The RF signals generated by the nRF24L01 are almost compatible with the Telink chipset inside the
Lightbar:
- 126 RF channels, covering the full 2.4 GHz IMS band (including 2406 MHz, 2043 MHz and 2068 MHz).
- Bitrate: 2 Mbps
- GFSK (Gaussian frequency shift keying), instead of plain FSK that the original signals seem to
use.
- Similar synchronization preamble (high-low transitions, `0b010101...`).

The `pyrf24` provides a closed solution for radio links between nRF24L01 devices, but the protocol
can be deactivated, giving almost full control over the radio signals. For example, a 2 to 5 long
address is mandatory, that constitute the leading bytes of each packet. This address is not
compatible with the Lightbar one (8 bytes), but it can be just filled with the sync sequence
(although after some tests I think that it is not necessary, any bit sequence works).

This is one of the spoofed pulses, captured and demodulated as before. Compare with the original
pulse shown above.

![Demodulated FSK spoofed pulse](./pics/xiaomi_lightbar_demodulated_spoofed_pulse.png) 
