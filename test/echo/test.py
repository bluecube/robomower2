#!/usr/bin/python3
from src_python import robonet

r = robonet.RoboNet('/dev/ttyUSB1', 38400)
answer = r.send_message(robonet.RoboNetPacket(1, bytes(range(10)))
print("echo: " + str([hex(x) for x in answer.data[:-1]]))
print("status: " + hex(answer.data[-1]))
