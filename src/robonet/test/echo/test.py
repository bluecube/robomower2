#!/usr/bin/python3
import robonet

r = robonet.RoboNet('/dev/ttyUSB1', 38400)
answer = r.send_message(robonet.RoboNetPacket(1, b'abc'))
print("echo: " + str([hex(x) for x in answer.data[:-1]]))
print("status: " + hex(answer.data[-1]))
