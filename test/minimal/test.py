#!/usr/bin/python3
from src_python import robonet
from src_python import layer2

proxy = layer2.proxy.MultiInterfaceProxy(
    [(1, "minimal", "minimal.interface")],
    robonet.RoboNet('/dev/ttyUSB1', 38400))

print("Checking again")
proxy.check_status()
print("ok")
