import xmlrpc.server
import logging
import threading
import pickle
import traceback
import pprint

class Gui:
    def __init__(self, config):
        self._config = config
        self._data = {}
        self._finished = False
        self._logger = logging.getLogger(__name__)

        self._thread = threading.Thread(target = self._serve_thread,
                                        daemon = True)
        self._thread.start()

    def _serve_thread(self):
        rpc_config = self._config["gui"]["xmlrpc"]
        address = (rpc_config["bind_address"], rpc_config["port"])

        rpc_server = xmlrpc.server.SimpleXMLRPCServer(address,
                                                      use_builtin_types = True)
        rpc_server.register_function(self._request_data, "request_data")
        rpc_server.register_function(self._set_finished, "set_finished")

        addr, port = rpc_server.server_address
        self._logger.info("Serving XML-RPC for gui on %s:%d", addr, port)

        rpc_server.serve_forever()

    def _request_data(self):
        pprint.pprint(self._data)
        return bytes(pickle.dumps(self._data))

    def _set_finished(self):
        self._finished = True

    def update(self):
        self._data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def finished(self):
        return self._finished
