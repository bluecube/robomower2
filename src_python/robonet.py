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
        without_crc = bytes([self.address, len(self.data)]) + self.data
        return without_crc + bytes([self._crc_fun(without_crc)])


class RoboNet:
    """Master for the RoboNet protocol.
    Works around limitations of posix serial port (and of pysserial)
    by doing some black magic with termios, this makes the code incompatible with
    windows pyserial and slightly limits error checking.
    But the CRC should be strong enough by itself. """

    CMSPAR = 0o010000000000

    def __init__(self, port, baudrate):
        self._port = serial.Serial(port, baudrate)

        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self._port.fd)

        cflag |= termios.PARENB # enable parity
        cflag |= self.CMSPAR # enable sticky parity
        cflag &= ~termios.PARODD # space parity by default
        iflag |= termios.IGNPAR # ignore parity on received bytes

        self._mark_attrs = [iflag,
                            oflag,
                            cflag | termios.PARODD,
                            lflag,
                            ispeed,
                            ospeed,
                            cc]
        self._space_attrs = [iflag,
                             oflag,
                             cflag,
                             lflag,
                             ispeed,
                             ospeed,
                             cc]
        self._set_space();

    def _set_mark(self):
        self._port.flush() #maybe flush isn't necessary with TCSADRAIN?
        termios.tcsetattr(self._port.fd, termios.TCSADRAIN, self._mark_attrs)

    def _set_space(self):
        self._port.flush()
        termios.tcsetattr(self._port.fd, termios.TCSADRAIN, self._space_attrs)

    def send_packet(self, packet):
        """Send a single packet, don't wait for reply."""
        packet = bytes(packet)

        #self._port.setDTR(False)
        #self._port.setRTS(True)
        self._set_mark()
        self._port.write(packet[0:1])
        self._set_space()
        self._port.write(packet[1:])
        self._port.flush()
        #self._port.setDTR(True)
        #self._port.setRTS(False)

    def receive_packet(self):
        """Receive and return a single packet."""
        address = self._port.read(1)[0]
        length = self._port.read(1)[0]
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
