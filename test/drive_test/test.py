#!/usr/bin/python3

import pygame
from src_python import robonet
from src_python import layer2
import time

r = robonet.RoboNet('/dev/ttyUSB1', 38400)

proxy = layer2.proxy.MultiInterfaceProxy(
    [(1, "drive", "src_avr/drive/drive.interface")],
    robonet.RoboNet('/dev/ttyUSB1', 38400))

pygame.display.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)

joystick.init()

while True:
    pygame.event.pump()
    value = int(127 * joystick.get_axis(0))

    print(proxy.drive.update(value)['distance'])

    time.sleep(0.1)
