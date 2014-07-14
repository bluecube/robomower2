---
title: Internal Communication
layout: default
---

For communication between the modules the robot uses RS485.
RS485 was chosen because it should be reliable (I imagined hunting down a bug
caused by motors interfering with the communication and almost fainted) and because
it can use the UART module on my favorite ATMega mcu.

On top of the RS485 are two layers.

## Robonet
Robonet is the lower layer.
It is almost identical to [Martin Locker's 8 bit Robonet protocol](http://wiki.robotika.cz/dispatch.fcgi/KomunikacniProtokol)

The protocol works in half-duplex mode.
Master sends simple packets that must be answered, or broadcasts which don't have any answer.
Each packet contains sync byte, payload size and CRC.

As a difference from the original protocol, each physical device has 16 addresses instead of 256
(the lower 4 bits of address determine physical device, upper 4 bits have application
specific meaning). There are also 16 broadcast addresses instead of only one.

In the repository there is a
[client implementation for AVR]({{ site.repository_master }}/src_avr/robonet/)
and a
[server implementation in python]({{ site.repository_master }}/src_python/robonet.py).

## Layer 2
Layer 2 builds on top of Robonet and provides a very simple remote procedure call
functions.
Layer2 uses interface files (eg.
[the drive interface]({{ site.repository_master }}/src_avr/drive/drive.interface))
to define requests and broadcasts for communication with a device and structures that
pass as its arguments and return values.
Then it either generates C code for AVR client, or directly creates python proxy
objects for the server.

Values in layer2 can be of signed or unsigned integer type or an array,
optionaly with a (compile time constant) multiplier.
The interface files can also contain constants that are `#define`d in the generated
code.

To make sure that everything works correctly, there is a enumeration step in the server
which checks that every expected client is responding and that the interface crc
matches.

