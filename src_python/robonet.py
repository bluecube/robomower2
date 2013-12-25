import serial
import crcmod.predefined
import termios

class RoboNetException(Exception):
    pass


class RoboNetCRCException(RoboNetException):
    def __init__(self, packet, received_crc):
        super().__init__("Invalid CRC received (expected 0x{:02x}, got 0x{:02x})".format(
            packet.correct_crc(), received_crc))
        self.packet = packet
        self.received_crc = received_crc


class RoboNetPacket:
    _sync_byte = 0x55
    _master_address = 0x00
    _max_data_size = 15

    @classmethod
    def wrap(cls, arg):
        if type(arg) == cls:
            return arg
        else:
            return cls(*arg)

    def __init__(self, address, data):
        self.address = address
        self.data = data
        self._crc_fun = crcmod.predefined.mkPredefinedCrcFun('crc-8-maxim')

    def address_device(self):
        return self.address & 0xf

    def address_function(self):
        return self.address >> 4

    def correct_crc(self):
        return bytes(self)[-1]

    def __bytes__(self):
        without_crc = bytes([self._sync_byte, self.address, len(self.data)]) + self.data
        return without_crc + bytes([self._crc_fun(without_crc)])


class RoboNet:
    """Master for the RoboNet protocol.
    Works around limitations of posix serial port (and of pysserial)
    by doing some black magic with termios, this makes the code incompatible with
    windows pyserial and slightly limits error checking.
    But the CRC should be strong enough by itself. """

    def __init__(self, port, baudrate):
        self._port = serial.Serial(port, baudrate)

    def send_packet(self, packet):
        """Send a single packet, don't wait for reply."""
        packet = bytes(packet)
        self._port.write(packet)
        self._port.flush()

    def receive_packet(self):
        """Receive and return a single packet."""
        sync, address, length = self._port.read(3)

        if sync != RoboNetPacket._sync_byte:
            self._port.flushInput()
            raise RoboNetException("Sync byte not found (received header: {})", str([sync, address, length]))
        if address != RoboNetPacket._master_address:
            self._port.flushInput()
            raise RoboNetException("Reply address is not 0x00 (received header: {})", str([sync, address, length]))
        if length > RoboNetPacket._max_data_size:
            self._port.flushInput()
            raise RoboNetException("Data size too large (received header: {})", str([sync, address, length]))

        data = self._port.read(length + 1)
        packet = RoboNetPacket(address, data[:-1])
        if packet.correct_crc() != data[-1]:
            raise RoboNetCRCException(packet, data[-1])
        return packet

    def broadcast_message(self, packet):
        """Higher level function for transmitting data to all devices on the wire."""

        packet = RoboNetPacket.wrap(packet)

        if packet.address_device() != 0:
            raise RoboNetException("This is not a broadcast packet")

        self.send_packet(packet)

    def send_message(self, packet):
        """Higher level function for transmitting data to a device on the wire.
        Returns the device's reply packet."""

        packet = RoboNetPacket.wrap(packet)

        if packet.address_device() == 0:
            raise RoboNetException("This is a broadcast packet")

        self._port.flushInput()
        self.send_packet(packet)
        return self.receive_packet()
