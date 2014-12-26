#!/usr/bin/python3
import logging
import logging.config
import sys
import util
import math
import json_mod

import robonet
import layer2

import mock_hw
import differential_drive
import world_map as world_map_module
import controller

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

    world_map = world_map_module.WorldMap()
    gui.world_map = world_map.polygons

    #for _, node in path_planner._nodes:
    #    for child, travel_time, cost in node.connections:
    #        p = path_planning.local_planner.plan_path(node.state, child.state)
    #        assert p is not None
    #        gui._map.lines.append(list(p.sample_intervals(1)))

    controller = controller.Controller(drive, world_map, config)
    #gui_controller = gui.get_controller(drive)

    data_logger = datalogger.DataLogger("/tmp")

    samples = [Sample() for i in range(1)]

    gui.kP = config["drive"]["PID"]["kP"]
    gui.kI = config["drive"]["PID"]["kI"]
    gui.kD = config["drive"]["PID"]["kD"]
    gui.pid_callback = lambda: drive.set_pid(gui.kP, gui.kI, gui.kD)
    #gui.path = set(zip(calibration.ground_truth[1:], calibration.ground_truth[:-1]))
    if controller._path is not None:
        gui.path = list(controller._path.sample_intervals(1))
        controller._path.reset()
        logger.info("Path length: %d s", controller._path.travel_time)
    else:
        logger.info("Path not found")
        gui.path = []

    sleep_timer = util.TimeElapsed()
    while True:
        proxy.broadcast.latch_values()
        delta_t, main_loop_load = sleep_timer.tick(0.1)

        controller.update(delta_t)
        drive.update()

        gui.velocity = drive.forward_distance() / delta_t
        gui.rpm_l = abs(60e-3 * drive.left_ticks / (delta_t * 16))
        gui.rpm_r = abs(60e-3 * drive.right_ticks / (delta_t * 16))
        gui.controller = controller
        gui.target = controller.intended_state
        gui.load = main_loop_load
        gui.update()

        samples = [drive.update_sample(s) for s in samples]
        gui.samples = samples

        data_logger.write(delta_t,
                          drive.left_command, drive.right_command,
                          drive.left_ticks, drive.right_ticks)
        if gui.finished:
            break

except KeyboardInterrupt:
    print() # To get rid of the ^C on the current line in console
    logger.info("Keyboard interrupt, exiting")
except:
    logger.exception("Exception in main loop, exiting")

