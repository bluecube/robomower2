#!/usr/bin/python3

import argparse
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

    def to_c_type(self):
        return str(self) + "_t"

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

    def to_c_type(self, name):
        if self.empty():
            return "/* Skipped empty struct {} */".format(name)

        ret = "struct {}\n{{\n".format(name)
        ret += "\n".join("    {} {};".format(t.to_c_type(), name) for name, t in self.members.items())
        ret += "\n};"
        return ret;

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

    def to_c_handler_func_header(self, name):
        ret = "void handle_{}(uint8_t rxStatus".format(name)
        if not self.request.empty():
            ret += ", const struct {}_request* in".format(name)
        if not self.response.empty():
            ret += ", struct {}_response* out".format(name)
        ret += ")"
        return ret

    def to_c_header(self, number, name):
        return ret


class Broadcast:
    def __init__(self):
        self.broadcast = None

    def _calc_checksum(self, init=0):
        return self.broadcast._calc_checksum(init)


class Interface:
    crc_fun = crcmod.predefined.mkPredefinedCrcFun('crc-8-maxim')

    def __init__(self, filename):
        self._filename = filename
        self.request_response = collections.OrderedDict();
        self.broadcast = collections.OrderedDict();

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

            included = Interface(included_path)
            self.request_response = included.request_response
            self.broadcast = included.broadcast

        if parser.has_option("interface", "robonet_header"):
            robonet_header = parser['interface']['robonet_header']
            if not os.path.isabs(robonet_header):
                robonet_header = os.path.join(os.path.dirname(filename), robonet_header)
            self._robonet_header = robonet_header

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

    def to_header_file(self):
        guard = re.sub("[^A-Z]", "_", os.path.basename(self._filename).upper())

        ret = """/* Automatically generated file. Do not edit. */
#ifndef {guard}
#define {guard}

#include <stdint.h>

/* Interface checksum: 0x{checksum:02x} */

""".format(guard = guard, checksum = self.checksum)

        for i, (name, rr) in enumerate(self.request_response.items()):
            ret += "/* Request id: {} */\n".format(i)
            ret += rr.request.to_c_type(name + "_request") + "\n"
            ret += rr.response.to_c_type(name + "_response") + "\n"
            ret += "void handle_{}(uint8_t rxStatus".format(name)
            if not rr.request.empty():
                ret += ",\n  const struct {}_request* in".format(name)
            if not rr.response.empty():
                ret += ",\n  struct {}_response* out".format(name)
            ret += ");\n\n"

        for i, (name, broadcast) in enumerate(self.broadcast.items()):
            ret += "/* Broadcast id: {} */\n".format(i)
            ret += broadcast.broadcast.to_c_type(name + "_broadcast") + "\n"
            ret += "void handle_{}_broadcast(uint8_t rxStatus".format(name)
            if not broadcast.broadcast.empty():
                ret += ",\n  const struct {}_broadcast* in".format(name)
            ret += ");\n\n"

        ret += "void communicate();\n"
        ret += "\n"
        ret += "#endif"
        return ret

    def to_source_file(self, own_address, header_filename):
        ret = '#include "{}"\n'.format(os.path.basename(header_filename))
        ret += '#include "{}"\n'.format(self._robonet_header)
        ret += '\n'

        ret += 'void communicate()\n'
        ret += '{\n'
        ret += '    uint8_t rxStatus = robonet_receive();\n'
        ret += '    if (rxStatus == ROBONET_BUSY)\n'
        ret += '        return;\n'

        ret += '    switch (robonetBuffer.address)\n'
        ret += '    {\n'
        for i, (name, rr) in enumerate(self.request_response.items()):
            ret += '    case 0x{:02x}:\n'.format(own_address | (i << 8))
            ret += '        if (robonetBuffer.length != {})\n'.format(len(rr.request))
            ret += '            XXX;\n'.format(len(rr.request))
            ret += '        handle_{}(rxStatus'.format(name)
            if not rr.request.empty():
                ret += ',\n          (const struct {}_request*)&(robonetBuffer.data)'.format(name)
            if not rr.response.empty():
                ret += ',\n          (struct {}_response*)&(robonetBuffer.data)'.format(name)
            ret += ');\n'
            ret += '        robonetBuffer.length = {};\n'.format(len(rr.response))
            ret += '        robonet_transmit();\n'
            ret += '        return;\n'.format(len(rr.response))
            ret += '\n'

        for i, (name, broadcast) in enumerate(self.broadcast.items()):
            ret += '    case 0x{:02x}:\n'.format(0xf | (i << 8))
            ret += '        if (robonetBuffer.length != {})\n'.format(len(rr.request))
            ret += '            XXX;\n'.format(len(rr.request))
            ret += '        handle_{}_broadcast(rxStatus'.format(name)
            if not broadcast.broadcast.empty():
                ret += ', (const struct {}_request*)&(robonetBuffer.data)'.format(name)
            ret += ');\n'
            ret += '        return;\n'.format(len(rr.response))
            ret += '\n'

        ret += '    default:\n'
        ret += '        XXX;\n'
        ret += '        break;\n'.format(len(rr.response))
        ret += '    }\n'
        ret += '}\n'

        return ret;


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate interface parser from given specification.')
    parser.add_argument('spec');
    parser.add_argument('--output', required=True,
        help='Output file name')
    args = parser.parse_args()

    interface = Interface(args.spec)
    print(interface.to_header_file())
    print()
    print(interface.to_source_file(1, "some_file.h"))
