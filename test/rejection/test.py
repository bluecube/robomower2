#!/usr/bin/python3
from src_python import robonet
from src_python import layer2

proxy = layer2.proxy.MultiInterfaceProxy([
    (1, "minimal", "minimal.interface"),
    (2, "other", "other.interface")
    ], robonet.RoboNet('/dev/ttyUSB1', 38400), False)


print("command to reject")
try:
    proxy.other.test(1, 2)
except robonet.RoboNetException as e:
    print(str(e))

print("Checking again")
proxy.minimal.check_status()
print("ok")
