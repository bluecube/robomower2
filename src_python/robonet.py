import serial
import crcmod.predefined
import time
import logging

class RoboNetException(Exception):
    pass


class RoboNetCRCException(RoboNetException):
    def __init__(self, packet, received_crc):
        super().__init__("Invalid CRC received (expected 0x{:02x}, got 0x{:02x})".format(
            packet.correct_crc(), received_crc))
        self.packet = packet
        self.received_crc = received_crc


class RoboNetPacket:
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
        without_crc = bytes([RoboNet.sync_byte, self.address, len(self.data)]) + self.data
        return without_crc + bytes([self._crc_fun(without_crc)])


class RoboNet:
    """Master for the RoboNet protocol."""

    sync_byte = 0x55
    master_address = 0x0
    broadcast_address = 0xf

    timeout = 0.1

    logger = logging.getLogger(__name__)

    @staticmethod
    def combine_address(device, function):
        if device != device & 0xf:
            raise ValueError("Device ID must be between 0 and 15")
        if function != function & 0xf:
            raise ValueError("Function ID must be between 0 and 15")
        return device | (function << 4)

    def __init__(self, port, baudrate):
        self._port = serial.Serial(port, baudrate)

    def send_packet(self, packet):
        """Send a single packet, don't wait for reply."""
        packet = bytes(packet)
        self.logger.debug("sending: %s", ' '.join("{:02x}".format(x) for x in packet))
        self._port.write(packet)
        self._port.flush()

    def receive_packet(self):
        """Receive and return a single packet."""

        end_time = time.time() + self.timeout

        self._port.timeout = self.timeout
        header = self._port.read(3)
        if len(header) < 3:
            raise RoboNetException("Timed out")
        header_str = ' '.join("{:02x}".format(x) for x in header)
        sync, address, length = header

        try:
            if sync != RoboNet.sync_byte:
                self._port.flushInput()
                raise RoboNetException("Sync byte not found (received header: {})".format(header_str))
            if address != RoboNet.master_address:
                self._port.flushInput()
                raise RoboNetException("Reply address is not 0x00 (received header: {})".format(header_str))

            self._port.timeout = end_time - time.time()

            data = self._port.read(length + 1)
            if len(data) < length + 1:
                raise RoboNetException("Timed out")
        except:
            self.logger.debug("received packet header: %s", header_str)
            raise

        self.logger.debug("received packet: %s %s", header_str, ' '.join("{:02x}".format(x) for x in data))
        packet = RoboNetPacket(address, data[:-1])
        if packet.correct_crc() != data[-1]:
            raise RoboNetCRCException(packet, data[-1])
        return packet

    def broadcast_message(self, packet):
        """Higher level function for transmitting data to all devices on the wire."""

        packet = RoboNetPacket.wrap(packet)

        if packet.address_device() != self.broadcast_address:
            raise RoboNetException("This is not a broadcast packet")

        self.send_packet(packet)

    def send_message(self, packet):
        """Higher level function for transmitting data to a device on the wire.
        Returns the device's reply packet."""

        packet = RoboNetPacket.wrap(packet)

        if packet.address_device() == self.broadcast_address:
            raise RoboNetException("This is a broadcast packet")

        self._port.flushInput()
        self.send_packet(packet)
        return self.receive_packet()
