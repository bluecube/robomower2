from .interface import Interface

class MultiInterfaceProxy:
    def __init__(self, interfaces, robonet):
        self._robonet = robonet

        self._interfaces = {}
        for addr, name, interface in interfaces:
            interface = Interface.wrap(interface)
            self._interfaces[name] = (addr, interface)

        self.broadcast = _MultiBroadcastProxy(self._interfaces, robonet)

        self.check_status()

    def __getattr__(self, name):
        if name not in self._interfaces:
            raise AttributeError("{} is not a name of an interface".format(name))
        address, interface = self._interfaces[name]
        return Proxy(interface, address, self._robonet)

    def check_status(self):
        for address, interface in self._interfaces.values():
            Proxy(interface, address, self._robonet)._check_status()


class Proxy:
    def __init__(self, interface, address, robonet):
        self._interface = Interface.wrap(interface)
        self._robonet = robonet
        self._address = address

    def __getattr__(self, name):
        if name in self._interface.broadcast:
            return _BroadcastHelper(self._robonet, broadcast)
        elif name in self._interface.request_response:
            return _RequestHelper(self._robonet, self._address, self._interface.request_response[name])
        else:
            raise AttributeError("{} is not a member of an interface".format(name))

    def _check_status(self):
        request_func = _RequestHelper(self._interface.request_response['status'], self._address, self._robonet)

        response = request_func()

        if response.interface_checksum != interface.checksum:
            raise Exception("Invalid interface checksum for device {} (local = {}, remote = {})".format(
                            name, interface_checksum, response.interface.checksum))
        if response.status != 0:
            raise Exception("Device {} reports status {}".format(name, response.status))


class _MultiBroadcastProxy:
    def __init__(self, interfaces, robonet):
        self._robonet = robonet

        self._broadcasts = {}
        broadcast_id = {}

        for addr, interface in interfaces.values():
            for broadcast_name, broadcast in interface.broadcast:
                if broadcast.id in broadcast_ids:
                    duplicate_name, duplicate_broadcast = broadcast_ids[i]
                    if duplicate_name != broadcast_name or duplicate_broadcast != broadcast:
                        raise Exception("Duplicate broadcast ({} vs {})".format(broadcast_name, duplicate_name))
                    else:
                        continue
                self._broadcasts[broadcast_name] = broadcast
                broadcast_ids[i] = (broadcast_name, broadcast)

    def __getattr__(self, name):
        if name not in self._broadcasts:
            raise AttributeError("{} is not a broadcast name".format(name))

        return _BroadcastHelper(self._robonet, self._broadcasts[name])


class _BroadcastHelper:
    def __init__(self, robonet, broadcast):
        self._robonet = robonet
        self._broadcast = broadcast
        self._address = robonet.combine_address(self.robonet.broadcast_address,
                                                broadcast.id)

    def __call__(self, *args, **kwargs):
        packed_request = self._broadcast.broadcast.pack(*args, **kwargs)
        self._robonet.broadcast_message((self._address, packed_request))


class _RequestHelper:
    def __init__(self, request_response, address, robonet):
        self._robonet = robonet
        self._request_response = request_response
        self._address = robonet.combine_address(address, request_response.id)

    def __call__(self, *args, **kwargs):
        packed_request = self._request_response.request.pack(*args, **kwargs)

        received = self._robonet.send_message([self._address, packed_request])
        return self._request_response.response.unpack(received.data)
