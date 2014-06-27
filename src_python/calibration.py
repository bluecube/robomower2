#!/usr/bin/python3

import math
import functools
import scipy.optimize
import numpy

import differential_drive
import datalogger

import util.frechet_distance

def loadRecording(path):
    return [x[2:4] for x in datalogger.load(path) if x[2] != 0 or x[3] != 0]

def optimize_dimensions(ticks, ground_truth, left_resolution, right_resolution, wheel_base, **kwargs):
    """Find estimate of wheel distances per tick and wheel base dimensions.
    First two arguments contain the driven path and ground truth, resolutions and
    wheel base are the initial estimates."""

    def objective(state_vector):
        """Returns sum of squared distances from the ground truth over the whole path."""
        x, y, heading, left_resolution, right_resolution, wheel_base = state_vector
        print(x, y, heading, left_resolution, right_resolution, wheel_base)

        avg_tick_size = (left_resolution + right_resolution) / 2

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
        path = [(sample.x, sample.y)
                for sample in
                drive.update_sample_iter(initialSample, ticks)]

        dist = util.frechet_distance.frechet_distance(path, ground_truth)
        print("=>", dist)
        return dist

    initial_state = [0, 0, 0, # Initial position and orientation
                     left_resolution, right_resolution, wheel_base]

    result = scipy.optimize.minimize(objective, initial_state,
                                     options = {"disp": True, "maxiter": 1000},
                                     method =  "BFGS")#,
                                    # bounds = [(-1, 1), (-1, 1), (-2, 2),
                                    #           (0.5 * left_resolution, 1.5 * left_resolution),
                                    #           (0.5 * right_resolution, 1.5 * right_resolution),
                                    #           (0.5 * wheel_base, 1.5 * wheel_base)])
    return result['x']

#def optimize_stdevs(ticks, ground_truth, x0, y0, heading0,
#                    left_resolution, right_resolution,
#                    left_sigma, right_sigma,
#                    wheel_base, **kwargs):
#    """Find estimate of wheel standard deviations per meter. """
#
#    def objective(state_vector):
#        """Returns sum of squared distances from the ground truth over the whole path."""
#        class Sample:
#            pass
#        samples = []
#
#        for i in range(1000):
#            sample = Sample()
#            sample.x = x0
#            sample.y = y0
#            sample.heading = heading0
#            samples.append(sample)
#
#        drive = differential_drive.DifferentialDriveModel(left_resolution,
#                                                          right_resolution,
#                                                          state_vector[0],
#                                                          state_vector[1],
#                                                          wheel_base)
#
#        return squaredDistanceFromLines((x, y), ground_truth) + \
#               math.fsum(squaredDistanceFromLines((sample.x, sample.y), ground_truth)
#                         for sample in
#                         drive.update_sample_iter(initialSample, ticks))
#
#    result = scipy.optimize.minimize(functools.partial(objective, ticks, ground_truth),
#                                     [0, 0, 0, # Initial position and orientation
#                                      left_resolution, right_resolution, wheel_base],
#                                     options = {"disp": True, "maxiter": 1000},
#                                     method = "anneal",
#                                     bounds = [(0.1 * left_sigma, 10 * left_sigma),
#                                               (0.1 * right_sigma, 10 * right_sigma)])
#
#    pprint(result)
#    return result

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

ground_truth = [p1, p2, p3, p4, p2, p3, p1]

# 1 sigma distance from the ground truth
ground_truth_sigma = 5e-2

if __name__ == "__main__":
    import json
    import sys

    with open("config.json", "r") as fp:
        config = json.load(fp)

    drive_config = config["drive"]

    # just for testing
    #drive_config["left_resolution"] *= 1.014
    #drive_config["right_resolution"] *= 0.99123
    #drive_config["wheel_base"] *= 1.09123

    print("before")
    print(json.dumps(drive_config, indent=4, sort_keys=True))

    recording = loadRecording(sys.argv[1])

    x0, y0, heading0, \
        drive_config["left_resolution"], \
        drive_config["right_resolution"], \
        drive_config["wheel_base"] = \
        optimize_dimensions(recording, ground_truth, **drive_config)

    print("After dimensions optimization")
    print(json.dumps(drive_config, indent=4, sort_keys=True))

#    drive_config["left_sigma"], \
#        drive_config["right_sigma"] = \
#        optimize_stdevs(recording, ground_truth, x0, y0, heading0, **drive_config)
#
#    print("Final:")
#    print(json.dumps(drive_config, indent=4, sort_keys=True))
