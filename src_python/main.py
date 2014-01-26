#!/usr/bin/python3
import logging
import logging.config
import sys
import util
import json

import robonet
import layer2
import fake_hw

import differential_drive

import gui

with open("config.json", "r") as fp:
    config = json.load(fp)

logging.config.dictConfig(config['logging'])

logger = logging.getLogger(__name__)
try:
    logger.info("Hello!")

    #proxy = layer2.proxy.MultiInterfaceProxy(
    #    [
    #        (1, "right", "src_avr/drive/drive.interface"),
    #        (2, "left", "src_avr/drive/drive.interface"),
    #    ],
    #    robonet.RoboNet('/dev/ttyUSB1', 38400))
    proxy = fake_hw.FakeHw()
    proxy.right.params(kP = 20, kI = 1, kD = 80)
    proxy.left.params(kP = 20, kI = 1, kD = 80)
    drive = differential_drive.DifferentialDrive(proxy.left, proxy.right, config)
    gui = gui.Gui(config)

    integration_timer = util.TimeElapsed()
    sleep_timer = util.TimeElapsed()
    while True:
        proxy.broadcast.latch_values()
        delta_t = integration_timer()

        gui.update(delta_t)
        drive.update(gui.forward, gui.turn)
        gui.velocity = drive.forward_distance / delta_t

        if gui.finished:
            break

        sleep_timer.tick(0.1)

except KeyboardInterrupt:
    print() # To get rid of the ^C on the current line in console
    logger.info("Keyboard interrupt, exiting")
except:
    logger.exception("Exception in main loop, exiting")

