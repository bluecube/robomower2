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

# Manually selected values;
proxy.drive.params(kP = 20, kI = 1, kD = 80, integratorLimit = 1000)

try:
    prev_t = 0
    while True:
        pygame.event.pump()
        value = int(32 * joystick.get_axis(0))

        proxy.broadcast.latch_values()
        t = time.time()

        ticks = proxy.drive.update(value)['distance']
        print("{:.2f} rpm ({} ticks)                 ".format(60 * ticks / (8*(t - prev_t)), ticks), end='\r')
        prev_t = t

        time.sleep(0.1)
finally:
    print()
    proxy.drive.update(0)
