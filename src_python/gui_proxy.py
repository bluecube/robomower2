import xmlrpc.server
import logging
import threading
import pickle
import pprint

class _Server:
    def __init__(self, config):
        self._data = {}
        self._finished = False

        self._versions = {}
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._current_version = 0

        self._thread = threading.Thread(target = self._serve_thread,
                                        daemon = True)
        self._thread.start()

    def _serve_thread(self):
        rpc_config = self._config["gui"]["xmlrpc"]
        address = (rpc_config["bind_address"], rpc_config["port"])

        rpc_server = xmlrpc.server.SimpleXMLRPCServer(address,
                                                      use_builtin_types = True,
                                                      logRequests = False)
        rpc_server.register_function(self._request_data, "request_data")
        rpc_server.register_function(self._set_finished, "set_finished")

        addr, port = rpc_server.server_address
        self._logger.info("Serving XML-RPC for gui on %s:%d", addr, port)

        rpc_server.serve_forever()

    def _request_data(self, versions = {}):
        data = {k: v for k, v in self._data.items()
                if k not in versions or versions[k] < self._versions[k]}
        ret = data, self._versions
        return pickle.dumps(ret)

    def _set_finished(self):
        self._finished = True

    def set(self, key, value):
        self._data[key] = value
        self._versions[key] = self._current_version

    def step(self):
        complete_data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        for k in complete_data:
            if (k not in self._complete_data) or (self._complete_data[k] != complete_data[k]):
                self._data[k] = complete_data[k]
        self._complete_data = complete_data

        self._current_version += 1

    def finished(self):
        return self._finished

class Gui:
    """ This is mainly a proxy object. Most of the work is done in _Server """
    def __init__(self, config):
        self._server = _Server(config)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self._server.set(key, value)

    def update(self):
        self._server.step()

    def finished(self):
        return self._server.finished()
