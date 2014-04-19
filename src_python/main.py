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
import patterns

import datalogger
import gui

class Sample:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.heading = 0

with open("config.json", "r") as fp:
    config = json.load(fp)

logging.config.dictConfig(config['logging'])

logger = logging.getLogger(__name__)
data_logger = datalogger.DataLogger("/tmp")
try:
    logger.info("Hello!")

    try:
        proxy = layer2.proxy.MultiInterfaceProxy(
            [
                (1, "right", "../src_avr/drive/drive.interface"),
                (2, "left", "../src_avr/drive/drive.interface"),
            ],
            robonet.RoboNet(config["robonet"]["port"], config["robonet"]["baudrate"]))
    except robonet.RoboNetException:
        proxy = fake_hw.FakeHw()
    drive = differential_drive.DifferentialDrive(proxy.left, proxy.right, config)
    gui = gui.Gui(config)

    gui.kP = config["drive"]["PID"]["kP"]
    gui.kI = config["drive"]["PID"]["kI"]
    gui.kD = config["drive"]["PID"]["kD"]
    gui.pid_callback = lambda: drive.set_pid(gui.kP, gui.kI, gui.kD)

    #controller = patterns.Pattern("patterns/square.json", config)
    controller = gui.controller

    position = Sample()

    sleep_timer = util.TimeElapsed()
    while True:
        proxy.broadcast.latch_values()
        delta_t, main_loop_load = sleep_timer.tick(0.1)

        controller.update(delta_t)

        drive.update(controller.forward, controller.turn)

        data_logger.write(delta_t,
                          drive.left_command, drive.right_command,
                          drive.left_ticks, drive.right_ticks)

        gui.velocity = drive.forward_distance / delta_t
        gui.samples = [position]
        gui.controller = controller
        gui.load = main_loop_load
        gui.update()

        drive.modify_sample(position)

        if gui.finished:
            break

except KeyboardInterrupt:
    print() # To get rid of the ^C on the current line in console
    logger.info("Keyboard interrupt, exiting")
except:
    logger.exception("Exception in main loop, exiting")

