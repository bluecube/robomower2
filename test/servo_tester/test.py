#!/usr/bin/python3
from src_python import robonet
import struct
import sys

r = robonet.RoboNet('/dev/ttyUSB1', 38400)
packet = robonet.RoboNetPacket(1, struct.pack('b', int(sys.argv[1])))
print("sending: " + str([hex(x) for x in bytes(packet)]))
answer = r.send_message(packet)
print("received: " + str([hex(x) for x in bytes(answer)]))
print("value: " + str(struct.unpack("h", answer.data[0:2])[0]))
#print("echo: " + str([hex(x) for x in answer.data[:-1]]))
#print("status: " + hex(answer.data[-1]))
