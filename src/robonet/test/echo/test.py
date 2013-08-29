#!/usr/bin/python3
import robonet

r = robonet.RoboNet('/dev/ttyUSB1', 4800)#38400)


#while True:
#    r.send_packet(robonet.RoboNetPacket(1, bytes([0, 0, 0, 0, 0, 0])))

answer = r.send_message(robonet.RoboNetPacket(1, b'abc'))

print(answer.data)
