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

#Ziegler nichols: kU = 60, tU = 0.22s
#proxy.drive.params(kP = 36, kI = 11, kD = 82, integratorLimit = 100)
proxy.drive.params(kP = 36, kI = 1, kD = 82, integratorLimit = 100)

try:
    prev_t = 0
    while True:
        pygame.event.pump()
        value = int(32 * joystick.get_axis(0))
        value = 5

        proxy.broadcast.latch_values()
        t = time.time()

        ticks = proxy.drive.update(value)['distance']
        print("{:.2f} rpm ({} ticks)".format(60 * ticks / (8*(t - prev_t)), ticks))
        prev_t = t

        time.sleep(0.1)
finally:
    proxy.drive.update(0)
