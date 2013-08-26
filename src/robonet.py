import serial
import crcmod
import termios

class RoboNetException(Exception):
    pass


class RoboNetCRCException(RoboNetException):
    def __init__(self, packet, received_crc):
        super().__init__("Invalid CRC received (expected 0x{02x}, got 0x{02x})".format(
            packet.correct_crc(), received_crc))
        self.packet = packet
        self.received_crc = received_crc


class RoboNetPacket:
    _crc_fun = crcmod.mkCrcFun(0x18C, 0, False)

    def __init__(self, address, data):
        self.address = address
        self.data = data

    def address_device(self):
        return self.address & 0xf

    def address_function(self):
        return self.address >> 4

    def correct_crc(self):
        return bytes(self)[-1]

    def __bytes__(self):
        without_crc = bytes([self.address, len(self.data)]) + data
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

        cflags |= termios.PARENB # enable parity
        cflags |= self.CMSPAR # enable sticky parity
        cflags &= ~termios.PARODD # space parity by default
        iflags |= termios.IGNPAR # ignore parity on received bytes

        self._mark_attrs = (iflag,
                            oflag,
                            cflag | termios.PARODD,
                            lflag,
                            ispeed,
                            ospeed,
                            cc)
        self._space_attrs = (iflag,
                             oflag,
                             cflag,
                             lflag,
                             ispeed,
                             ospeed,
                             cc)
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
        self._set_mark();
        self._port.write(packet[0])
        self._set_space();
        self._port.write(packet[1:])
        self._port.flush()
        self._port.parity = serial.PARITY_MARK

    def receive_packet(self):
        """Receive and return a single packet."""
        address, length = self._port.read(2)
        data = self._port.read(length + 1)
        packet = RoboNetPacket(address, length, data[:-1])
        if packet.correct_crc() != data[-1]:
            raise RoboNetCRCException(packet, data[-1])
        return packet
