#!/usr/bin/python3

import configparser
import collections
import os.path
import crcmod.predefined
import re

class Type:
    regexp = re.compile(r"(u?)int(\d+)")
    def __init__(self, typename):
        match = self.regexp.match(typename)
        if not match:
            raise ValueError("Invalid type name")
        self.unsigned = (match.group(1) == "u")
        self.size = int(match.group(2))

        if self.size not in {8, 16, 32}:
            raise ValueError("Only 8, 16 or 32 bit numbers are supported")

    def __str__(self):
        if self.unsigned:
            ret = "uint"
        else:
            ret = "int"

        ret += str(self.size)

        return ret

    def __len__(self):
        return self.size // 8

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


class RequestResponse:
    def __init__(self):
        self.request = None
        self.response = None

    def _calc_checksum(self, init= 0):
        checksum = self.request._calc_checksum(init)
        return self.response._calc_checksum(checksum)


class Broadcast:
    def __init__(self):
        self.broadcast = None

    def _calc_checksum(self, init=0):
        return self.broadcast._calc_checksum(init)


class Interface:
    crc_fun = crcmod.predefined.mkPredefinedCrcFun('crc-8-maxim')

    def __init__(self, filename):
        self.filename = filename
        self.request_response = collections.OrderedDict();
        self.broadcast = collections.OrderedDict();

        self.includes = []

        self._parse(filename)

    def _parse(self, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.comment_prefixes = ('#',)
        parser.inline_comment_prefixes = ('#',)
        parser.optionxform = str
        parser.read(filename)

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

        for section, content in parser.items():
            if section.startswith('request:'):
                request_response = self.request_response.setdefault(section[len('request:'):], RequestResponse())
                if request_response.request is not None:
                    raise ValueError("Multiple occurences of " + section)
                request_response.request = Structure(content)
            elif section.startswith('response:'):
                request_response = self.request_response.setdefault(section[len('response:'):], RequestResponse())
                if request_response.response is not None:
                    raise ValueError("Multiple occurences of " + section)
                request_response.response = Structure(content)
            elif section.startswith('broadcast:'):
                broadcast = self.broadcast.setdefault(section[len('broadcast:'):], Broadcast())
                if broadcast.broadcast:
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
        for rr_name, rr in self.request_response.items():
            checksum = self._string_checksum(rr_name, checksum)
            checksum = rr._calc_checksum(checksum)

        for broadcast_name, structure in self.broadcast.items():
            checksum = self._string_checksum(broadcast_name, checksum)
            checksum = structure._calc_checksum(checksum)

        return checksum

    @classmethod
    def _string_checksum(cls, string, init):
        return cls.crc_fun(string.encode('ascii'), init)

