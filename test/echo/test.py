#!/usr/bin/python3
from src_python import robonet

def hexify(data):
    return str([hex(x) for x in data])

r = robonet.RoboNet('/dev/ttyUSB1', 38400)
packet = robonet.RoboNetPacket(1, bytes(range(3)))
print("data: " + hexify(bytes(packet.data)))
print("seding: " + hexify(bytes(packet)))
answer = r.send_message(packet)
print("echo: " + hexify(answer.data[:-1]))
print("status: " + hex(answer.data[-1]))
