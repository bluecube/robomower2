import configparser
import collections
import os.path
import crcmod.predefined
import re
import struct

class Type:
    regexp = re.compile(r"(u?)int(\d+)(?:\((\d+)\))?")
    def __init__(self, typename):
        match = self.regexp.match(typename)
        if not match:
            raise ValueError("Invalid type name")
        self.unsigned = (match.group(1) == "u")
        self.size = int(match.group(2))
        if match.group(3) is not None:
            self.multiplier = int(match.group(3))
        else:
            self.multiplier = 1

        if self.size not in {8, 16, 32}:
            raise ValueError("Only 8, 16 or 32 bit numbers are supported")

        self._struct_arg = "<" + {
            (8, True): "B",
            (8, False): "b",
            (16, True): "H",
            (16, False): "h",
            (32, True): "I",
            (32, False): "i",
            }[(self.size, self.unsigned)]

    def __str__(self):
        if self.unsigned:
            ret = "uint"
        else:
            ret = "int"

        ret += str(self.size)

        if self.multiplier != 1:
            ret += "({})".format(int(self.multiplier))

        return ret

    def __len__(self):
        return self.size // 8

    def __eq__(self, other):
        return self.unsigned == other.unsigned and self.size == other.size and self.multiplier == other.multiplier

    def pack(self, value):
        return struct.pack(self._struct_arg, round(value * self.multiplier))

    def unpack(self, data):
        value = struct.unpack(self._struct_arg, data)[0]
        if self.multiplier != 1:
            return value / self.multiplier
        else:
            return value

class Structure:
    def __init__(self, content):
        self.members = collections.OrderedDict();

        for name, typename in content.items():
            self.members[name] = Type(typename)

    def _calc_checksum(self, init = 0):
        checksum = init
        for name, typename in self.members.items():
            checksum = Interface._string_checksum(name, checksum)
            checksum = Interface._string_checksum(str(typename), checksum)
        return checksum

    def empty(self):
        return not len(self.members)

    def __len__(self):
        return sum(len(t) for t in self.members.values())

    def __eq__(self, other):
        return all(a == b for a, b in zip(self.members.values(), other.members.values()))

    def pack(self, *args, **kwargs):
        if len(args) > len(self.members):
            raise ValueError("Too many positional arguments")
        elif len(args) + len(kwargs) > len(self.members):
            raise ValueError("Too many arguments")
        elif len(args) + len(kwargs) < len(self.members):
            raise ValueError("Too few arguments")

        packed = []
        for i, (name, member) in enumerate(self.members.items()):
            if i < len(args):
                value = args[i]
            else:
                value = kwargs[name]

            packed.append(member.pack(value))

        result = b''.join(packed);
        assert len(result) == len(self)
        return result

    def unpack(self, packed):
        result = collections.OrderedDict();
        offset = 0;
        for name, member in self.members.items():
            end_offset = offset + len(member)
            result[name] = member.unpack(packed[offset:end_offset])
            offset = end_offset
        return result

class RequestResponse:
    def __init__(self, id, automatic = False):
        self.id = id
        self.request = None
        self.response = None
        self.automatic = automatic

    def _calc_checksum(self, init = 0):
        checksum = self.request._calc_checksum(init)
        return self.response._calc_checksum(checksum)


class Broadcast:
    def __init__(self, id, automatic = False):
        self.id = id
        self.broadcast = None
        self.automatic = automatic

    def _calc_checksum(self, init = 0):
        return self.broadcast._calc_checksum(init)

    def __eq__(self, other):
        return self.id == other.id and self.broadcast == other.broadcast and self.automatic == other.automatic


class Interface:
    crc_fun = crcmod.predefined.mkPredefinedCrcFun('crc-8-maxim')

    @classmethod
    def wrap(cls, arg):
        if type(arg) == cls:
            return arg
        else:
            return cls(arg)

    def __init__(self, filename):
        self.filename = filename
        self.request_response = collections.OrderedDict();
        self.broadcast = collections.OrderedDict();
        self.constants = {}

        self.includes = []

        self._automatic_rr()
        self._parse(filename)

    def _automatic_rr(self):
        status = RequestResponse(len(self.request_response), True)
        status.request = Structure({})
        status.response = Structure(collections.OrderedDict([
            ('status', 'uint8'),
            ('interfaceChecksum', 'uint8')]))
        self.request_response['status'] = status

    def _parse(self, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.comment_prefixes = ('#',)
        parser.inline_comment_prefixes = ('#',)
        parser.optionxform = str
        with open(filename, "r") as f:
            parser.read_file(f, filename)

        if parser.has_option("interface", "include"):
            included_path = parser["interface"]["include"]
            if not os.path.isabs(included_path):
                included_path = os.path.join(os.path.dirname(filename), included_path)

            self.includes.append(included_path)

            included = Interface(included_path)
            self.request_response = included.request_response
            self.broadcast = included.broadcast

        if parser.has_option("interface", "robonet_header"):
            robonet_header = parser['interface']['robonet_header']
            if not os.path.isabs(robonet_header):
                robonet_header = os.path.join(os.path.dirname(filename), robonet_header)
            self.robonet_header = robonet_header

        if parser.has_section("constants"):
            for name, value in parser["constants"].items():
                try:
                    value = float(value)
                except ValueError:
                    pass
                else:
                    if int(value) == value:
                        value = int(value)
                if name in self.constants and value != self.constants[name]:
                    raise ValueError("Constant %s already in the list with different value" % name)
                self.constants[name] = value

        for section, content in parser.items():
            if section.startswith('request:'):
                request_response = self.request_response.setdefault(section[len('request:'):], RequestResponse(len(self.request_response)))
                if request_response.request is not None:
                    raise ValueError("Multiple occurences of " + section)
                request_response.request = Structure(content)
            elif section.startswith('response:'):
                request_response = self.request_response.setdefault(section[len('response:'):], RequestResponse(len(self.request_response)))
                if request_response.response is not None:
                    raise ValueError("Multiple occurences of " + section)
                request_response.response = Structure(content)
            elif section.startswith('broadcast:'):
                broadcast = self.broadcast.setdefault(section[len('broadcast:'):], Broadcast(len(self.broadcast)))
                if broadcast.broadcast is not None:
                    raise ValueError("Multiple occurences of " + section)
                broadcast.broadcast = Structure(content)

        for rr_name, rr in self.request_response.items():
            if rr.request is None:
                assert(rr.response is not None)
                raise ValueError("Missing request for response " + rr_name)
            if rr.response is None:
                assert(rr.request is not None)
                raise ValueError("Missing response for request " + rr_name)

        self.checksum = self._calc_checksum();

    def _calc_checksum(self):
        checksum = 0

        for name in sorted(self.constants):
            value = self.constants[name]
            checksum = self._string_checksum(name, checksum)
            checksum = self._string_checksum(repr(value), checksum)

        for rr_name in sorted(self.request_response):
            rr = self.request_response[rr_name]
            checksum = self._string_checksum(rr_name, checksum)
            checksum = rr._calc_checksum(checksum)

        for broadcast_name in sorted(self.broadcast):
            structure = self.broadcast[broadcast_name]
            checksum = self._string_checksum(broadcast_name, checksum)
            checksum = structure._calc_checksum(checksum)

        return checksum

    @classmethod
    def _string_checksum(cls, string, init):
        return cls.crc_fun(string.encode('ascii'), init)
