#!/usr/bin/python3
import logging
import logging.config
import sys
import math
import json_mod
import xmlrpc.client
import pickle

import util
import gui as robotgui

with open("robomower.config", "r") as fp:
    config = json_mod.load(fp)

try:
    logging.config.dictConfig(config['logging'])

    logger = logging.getLogger(__name__)
    logger.info("Hello from gui viewer!")

    gui = robotgui.Gui(config)
    rpcproxy = xmlrpc.client.ServerProxy(sys.argv[1],
                                         use_builtin_types=True)
    logger.info("Connected to XML-RPC server")


    sleep_timer = util.TimeElapsed()
    last_frame = 0
    versions = {}
    while True:
        sleep_timer.tick(0.5)

        data, versions = pickle.loads(rpcproxy.request_data(versions))

        for k, v in data.items():
            setattr(gui, k, v)

        gui.update()

        if gui.finished():
            rpcproxy.send_finished()
            break

except KeyboardInterrupt:
    print() # To get rid of the ^C on the current line in console
    logger.info("Keyboard interrupt, exiting")
except:
    logger.exception("Exception in main loop, exiting")

