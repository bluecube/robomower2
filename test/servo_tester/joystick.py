#!/usr/bin/python3

import pygame
from src_python import robonet
import struct
import time

r = robonet.RoboNet('/dev/ttyUSB1', 38400)

pygame.display.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)

joystick.init()

while True:
    pygame.event.pump()
    value = 127 * joystick.get_axis(0)

    packet = robonet.RoboNetPacket(1, struct.pack('b', int(value)))
    print("sending: " + str([hex(x) for x in bytes(packet)]))
    answer = r.send_message(packet)

    time.sleep(0.1)
