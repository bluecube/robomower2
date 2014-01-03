#!/usr/bin/python3

import pygame
from src_python import robonet
from src_python import layer2
import time

class _TunerState:
    def __init__(self, kP = 0, kI = 0, kD = 0):
        self.kP = kP
        self.kI = kI
        self.kD = kD

    def upload_params(self, proxy):
        proxy.params(kP = self.kP, kI = self.kI, kD = self.kD)
        print("setting params to " + str(self))

    def __str__(self):
        return ("kP = {}, kI = {}, kD = {}".format(self.kP, self.kI, self.kD))


class Tuner:
    def __init__(self, proxy):
        self.states = [_TunerState()]
        self._proxy = proxy
        self.upload_params()

    def upload_params(self):
        self.states[-1].upload_params(self._proxy)

    def inc(self, what):
        current = self.states[-1]
        if what == "P":
            new = _TunerState(current.kP + 1, current.kI, current.kD)
        if what == "I":
            new = _TunerState(current.kP, current.kI + 1, current.kD)
        if what == "D":
            new = _TunerState(current.kP, current.kI, current.kD + 1)
        self.states.append(new)
        self.upload_params()

    def undo(self):
        self.states.pop()
        self.upload_params()


r = robonet.RoboNet('/dev/ttyUSB1', 38400)

proxy = layer2.proxy.MultiInterfaceProxy(
    [(1, "drive", "src_avr/drive/drive.interface")],
    robonet.RoboNet('/dev/ttyUSB1', 38400))
tuner = Tuner(proxy.drive)

pygame.display.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)

joystick.init()

#value = int(32 * joystick.get_axis(0))
value = 15
max_ticks = 0

try:
    prev_t = 0
    while True:
        for ev in pygame.event.get():
            if ev.type != pygame.JOYBUTTONDOWN:
                continue
            if ev.button == 1:
                tuner.undo()
            elif ev.button == 0:
                tuner.inc("P")
            elif ev.button == 3:
                tuner.inc("D")
            elif ev.button == 2:
                tuner.inc("I")

        proxy.broadcast.latch_values()
        t = time.time()

        ticks = proxy.drive.update(value)['distance']
        max_ticks = max(max_ticks, ticks)
        print("{:.2f} rpm ({} ticks)                 ".format(60 * ticks / (8*(t - prev_t)), ticks), end='\r')
        prev_t = t

        time.sleep(0.1)
finally:
    print()
    print(max_ticks)
    proxy.drive.update(0)
