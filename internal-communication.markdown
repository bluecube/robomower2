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
It is a packet based protocol operating on half duplex line.
The protocol is almost identical to [Martin Locker's 8 bit Robonet protocol](http://wiki.robotika.cz/dispatch.fcgi/KomunikacniProtokol),
the main change being that the 8 bit address space has been split into 4 bits for device
and 4 bits for message type.
Instead of master, broadcast and 254 other devices, we have
16 broadcasts, master and 14 other devices, each with 16 message types.

In the repository there is a
[client implementation for AVR]({{ site.repository_master }}/src_avr/robonet/)
and a
[server implementation in python]({{ site.repository_master }}/src_python/robonet.py).


Robonet has a single master on the bus.
The master sends either regular messages or broadcasts, regular messages require
an answer from the client, broadcasts are just silently processed.

Currently the protocol has no error corrections, all that is done is detecting
errors crashing if one appears.

### Packet Structure

Each packet contains sync byte, payload size and CRC.

A packet in the protocol consists of sync byte, address and message type byte,
payload size and payload iself, followed by a CRC.

![Robonet packet]({{ site.baseurl }}/img/2014-07/robonet_packet.svg)

The CRC is calculated from all preceding bytes of the packet including the sync byte,
polynomial is 0x107 (`crc-8-maxim` in crcmod python library, `_crc_ibutton_update()`
in avr-libc).

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

## Synchronization

To synchronize updates of all devices on the network, a sync broadcast is used.

This idea comes from the original Robonet, but logically it belongs above patcket
transmission (and above layer2 as well).

All devices have the important data double buffered and when the sync broadcast is
received, the buffers are swapped.
Since all the devices process the network messages in parallel, this causes
all reads of the update to appear (almost) simultaneously.
This mechanism doesn't take care of writing data to the devices in any way,
each device still has to wait until all the previous devices have finished their
updates before master gets to it with new commands.
