#!/usr/bin/python3
import logging
import logging.config
import sys
import util
import json_mod

import robonet
import layer2
import mock_hw

import differential_drive
import world_map

import datalogger
import gui as robotgui

import calibration

class Sample:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.heading = 0

with open("robomower.config", "r") as fp:
    config = json_mod.load(fp)

logging.config.dictConfig(config['logging'])

logger = logging.getLogger(__name__)
try:
    gui = robotgui.Gui(config)

    logger.info("Hello!")

    try:
        proxy = layer2.proxy.MultiInterfaceProxy(
            [
                (1, "right", "../src_avr/drive/drive.interface"),
                (2, "left", "../src_avr/drive/drive.interface"),
            ],
            robonet.RoboNet(config["robonet"]["port"], config["robonet"]["baudrate"]))
    except robonet.RoboNetException as e:
        logger.info("Initialization of real hardware failed (%s). Using mock.", str(e))
        proxy = mock_hw.MockHw()

    drive = differential_drive.DifferentialDrive(proxy.left, proxy.right, config["drive"])

    #gui._map.lines = set(zip(calibration.ground_truth[1:], calibration.ground_truth[:-1]))
    gui.world_map = world_map.WorldMap()

    gui.kP = config["drive"]["PID"]["kP"]
    gui.kI = config["drive"]["PID"]["kI"]
    gui.kD = config["drive"]["PID"]["kD"]
    gui.pid_callback = lambda: drive.set_pid(gui.kP, gui.kI, gui.kD)

    #controller = patterns.Pattern("patterns/square.json", config)
    controller = gui.controller

    data_logger = datalogger.DataLogger("/tmp")

    samples = [Sample() for i in range(1)]

    sleep_timer = util.TimeElapsed()
    while True:
        proxy.broadcast.latch_values()
        delta_t, main_loop_load = sleep_timer.tick(0.1)

        controller.update(delta_t)

        drive.update(controller.forward, controller.turn)

        data_logger.write(delta_t,
                          drive.left_command, drive.right_command,
                          drive.left_ticks, drive.right_ticks)

        gui.velocity = drive.forward_distance() / delta_t
        gui.rpm_l = abs(60e-3 * drive.left_ticks / (delta_t * 16))
        gui.rpm_r = abs(60e-3 * drive.right_ticks / (delta_t * 16))
        gui.controller = controller
        gui.load = main_loop_load
        gui.update()

        samples = [drive.update_sample(s) for s in samples]
        gui.samples = samples

        if gui.finished:
            break

except KeyboardInterrupt:
    print() # To get rid of the ^C on the current line in console
    logger.info("Keyboard interrupt, exiting")
except:
    logger.exception("Exception in main loop, exiting")

