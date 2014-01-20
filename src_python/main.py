#!/usr/bin/python3
from __future__ import division, print_function, unicode_literals

import robonet
import layer2
import gui
import time
import logging
import logging.config
import sys
import util
import json

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
    #proxy.right.params(kP = 20, kI = 1, kD = 80)
    #proxy.left.params(kP = 20, kI = 1, kD = 80)
    gui = gui.Gui(config)

    integration_timer = util.TimeElapsed()
    sleep_timer = util.TimeElapsed()
    while True:
        #proxy.broadcast.latch_values()
        delta_t = integration_timer()

        #ticksLeft = proxy.left.update(value)['distance']
        #ticksRight = proxy.right.update(value)['distance']

        gui.update()
        if gui.finished:
            break

        sleep_timer.tick(0.1)

except KeyboardInterrupt:
    print() # To get rid of the ^C on the current line in console
    logger.info("Keyboard interrupt, exiting")
except:
    logger.exception("Exception in main loop, exiting")

