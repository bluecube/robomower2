#!/usr/bin/python3

import math

import mock_hw
import differential_drive
import datalogger

def squaredDistanceFromPoint(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

def squaredDistanceFromLine(point, line):
    #print(point, line)
    x, y = point
    (x1, y1), (x2, y2) = line

    dx = x2 - x1
    dy = y2 - y1

    lineLength = math.sqrt(dx * dx + dy * dy)

    t1 = (dx * (x - x1) + dy * (y - y1))
    t2 = (dx * (x2 - x) + dy * (y2 - y))

    if t1 <= 0:
        #print("t1 ", squaredDistanceFromPoint(point, line[0]))
        return squaredDistanceFromPoint(point, line[0])
    elif t2 <= 0:
        #print("t2 ", squaredDistanceFromPoint(point, line[1]))
        return squaredDistanceFromPoint(point, line[1])
    else:
        t1 /= math.sqrt(dx * dx + dy * dy)

        #print("inside ", squaredDistanceFromPoint(point, (x1 + dx * t1, y1 + dy * t1)))
        return squaredDistanceFromPoint(point, (x1 + dx * t1, y1 + dy * t1))

def squaredDistanceFromLines(p, lines):
    return min(squaredDistanceFromLine(p, line) for line in lines)

def loadRecording(path):
    return [x[2:4] for x in datalogger.load(path) if x[2] != 0 or x[3] != 0]

def objective(ticks, ground_truth, x, y, heading, **kwargs):
    """ Objective function to minimize.
    First two arguments contain the driven path and ground truth, rest are
    state vector elements.
    Returns sum of squared distances from the ground truth over the whole path. """
    class Sample:
        pass
    sample = Sample()
    sample.x = x
    sample.y = y
    sample.heading = heading

    mockHw = mock_hw.MockHw()
    drive = differential_drive.DifferentialDrive(mockHw.left,
                                                 mockHw.right,
                                                 {"drive": kwargs})

    distance = 0
    for left_ticks, right_ticks in ticks:
        drive.left_ticks = left_ticks
        drive.right_ticks = right_ticks

        distance += squaredDistanceFromLines((sample.x, sample.y), ground_truth)

        drive.modify_sample(sample);

    return distance

def optimize():
    pass

def c(x):
    return math.cos(math.radians(x))

def s(x):
    return math.sin(math.radians(x))

# The shape for calibration
#
#     p3----p4
#    /  \   /
#   /    \ /
# p1-----p2
#

p1 = (0, 0)
p2 = (5, 0)
p3 = (5 * c(60), 5 * s(60))
p4 = (5 + 5 * c(60), 5 * s(60))

ground_truth = [
    (p1, p2),
    (p2, p3),
    (p3, p4),
    (p1, p3),
    (p2, p4)]


if __name__ == "__main__":
    import json

    with open("config.json", "r") as fp:
        config = json.load(fp)

    recording = loadRecording("/tmp/robomower-recording-2014-04-19-1.txt")

    print(objective(recording, ground_truth, 0, 0, 0, **config["drive"]))
