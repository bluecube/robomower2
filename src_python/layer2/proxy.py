class Proxy:
    def __init__(self, interface, robonet):
        self.interface = interface
        self.robonet = robonet

    def __getattr__(self, name):
        if name in self.interface.interface.broadcast:
            return _BroadcastHelper(self.robonet, self.interface.broadcasts[name])
        elif name in self.interface.request_response:
            return _RequestHelper(self.robonet, self.interface.request_response[name])
        else:
            raise AttributeError("{} is not a member of an interface".format(name))


class _BroadcastHelper:
    def __init__(self, robonet, broadcast):
        self._robonet = robonet
        self._broadcast = broadcast

    def __call__(self, *args, **kwargs):
        packed_request = self._broadcast.broadcast.pack(*args, **kwargs)
        self._robonet.broadcast_message(packed_request)

class _RequestHelper:
    def __init__(self, robonet, request_response):
        self._robonet = robonet
        self._request_response = request_response

    def __call__(self, address, *args, **kwargs):
        packed_request = self._request_response.request.pack(*args, **kwargs)

        received = self._robonet.send_message([address, packed_request])
        return self._request_response.response.unpack(received.data)
