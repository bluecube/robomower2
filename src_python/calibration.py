#!/usr/bin/python3

import math
import functools
import scipy.optimize

import differential_drive
import datalogger

def squaredDistanceFromPoint(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

def squaredDistanceFromLine(point, line):
    x, y = point
    (x1, y1), (x2, y2) = line

    dx = x2 - x1
    dy = y2 - y1

    t1 = (dx * (x - x1) + dy * (y - y1))
    t2 = (dx * (x2 - x) + dy * (y2 - y))

    if t1 <= 0:
        return squaredDistanceFromPoint(point, line[0])
    elif t2 <= 0:
        return squaredDistanceFromPoint(point, line[1])
    else:
        tmp = (dy * x - dx * y - x1 * y2 + x2 * y1)
        return tmp * tmp / (dx * dx + dy * dy)

def squaredDistanceFromLines(p, lines):
    return min(squaredDistanceFromLine(p, line) for line in lines)

def loadRecording(path):
    return [x[2:4] for x in datalogger.load(path) if x[2] != 0 or x[3] != 0]

def optimize_dimensions(ticks, ground_truth, left_resolution, right_resolution, wheel_base, **kwargs):
    """Find estimate of wheel distances per tick and wheel base dimensions.
    First two arguments contain the driven path and ground truth, resolutions and
    wheel base are the initial estimates."""

    def objective(state_vector):
        """Returns sum of squared distances from the ground truth over the whole path."""
        x, y, heading, left_resolution, right_resolution, wheel_base = state_vector

        class Sample:
            pass
        initialSample = Sample()
        initialSample.x = x
        initialSample.y = y
        initialSample.heading = heading

        drive = differential_drive.DifferentialDriveModel(left_resolution,
                                                          right_resolution,
                                                          0, 0,
                                                          wheel_base)

        return squaredDistanceFromLines((x, y), ground_truth) + \
               math.fsum(squaredDistanceFromLines((sample.x, sample.y), ground_truth)
                         for sample in
                         drive.update_sample_iter(initialSample, ticks))

    result = scipy.optimize.minimize(objective,
                                     [0, 0, 0, # Initial position and orientation
                                      left_resolution, right_resolution, wheel_base],
                                     options = {"disp": True, "maxiter": 1000},
                                     method = "TNC",
                                     bounds = [(-1, 1), (-1, 1), (-2, 2),
                                               (0.1 * left_resolution, 10 * left_resolution),
                                               (0.1 * right_resolution, 10 * right_resolution),
                                               (0.1 * wheel_base, 10 * wheel_base)])

    return result['x']


# The shape for calibration
#
#     p3----p4
#    /  \   /
#   /    \ /
# p1-----p2
#

p1 = (0, 0)
p2 = (5, 0)
p3 = (5 * math.cos(math.radians(60)), 5 * math.sin(math.radians(60)))
p4 = (5 + p3[0], p3[1])

ground_truth = [
    (p1, p2),
    (p2, p3),
    (p3, p4),
    (p1, p3),
    (p2, p4)]

if __name__ == "__main__":
    import json
    import sys

    with open("config.json", "r") as fp:
        config = json.load(fp)

    drive_config = config["drive"]

    recording = loadRecording(sys.argv[1])

    x0, y0, heading0, \
        drive_config["left_resolution"], \
        drive_config["right_resolution"], \
        drive_config["wheel_base"] = \
        optimize_dimensions(recording, ground_truth, **drive_config)

    print(json.dumps(drive_config, indent=4, sort_keys=True))
