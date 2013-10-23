import os.path
import re
import argparse

def _w(f, string):
    f.write(string.encode('ascii'))

def _type(t):
    return str(t) + "_t"

def _struct(struct, name):
    if struct.empty():
        return "/* Skipped empty struct {} */".format(name)

    ret = "struct {}\n{{\n".format(name)
    ret += "\n".join("    {} {};".format(_type(t), name) for name, t in struct.members.items())
    ret += "\n};"
    return ret;


def _generate_header(interface, header_filename, f):
    guard = re.sub("[^A-Z]", "_", os.path.basename(header_filename).upper())

    _w(f, "/* Automatically generated file. Do not edit. */\n")
    _w(f, "#ifndef {}\n".format(guard))
    _w(f, "#define {}\n".format(guard))
    _w(f, '\n')
    _w(f, "#include <stdint.h>\n")
    _w(f, '#include "{}"\n'.format(interface.robonet_header))
    _w(f, '\n')
    _w(f, '/* Interface checksum: 0x{:02x} */\n'.format(interface.checksum))
    _w(f, '\n')
    _w(f, '#define LAYER2_OK                     ROBONET_OK\n')
    _w(f, '#define LAYER2_BUSY                   ROBONET_BUSY\n')
    _w(f, '#define LAYER2_INVALID_MESSAGE_LENGTH (ROBONET_LAST_STATUS + 1)\n')
    _w(f, '#define LAYER2_UNKNOWN_MESSAGE_TYPE   (ROBONET_LAST_STATUS + 2)\n')
    _w(f, '\n')

    for i, (name, rr) in enumerate(interface.request_response.items()):
        _w(f, "/* Request id: {} */\n".format(i))
        _w(f, _struct(rr.request, name + "_request") + "\n")
        _w(f, _struct(rr.response, name + "_response") + "\n")
        _w(f, "void handle_{}(".format(name))
        if not rr.request.empty():
            _w(f, "\n    const struct {}_request* in".format(name))
            if not rr.response.empty():
                _w(f, ",")
        if not rr.response.empty():
            _w(f, "\n    struct {}_response* out".format(name))
        _w(f, ");\n")
        _w(f, '\n')

    for i, (name, broadcast) in enumerate(interface.broadcast.items()):
        _w(f, "/* Broadcast id: {} */\n".format(i))
        _w(f, _struct(broadcast.broadcast, name + "_broadcast") + "\n")
        _w(f, "void handle_{}_broadcast(".format(name))
        if not broadcast.broadcast.empty():
            _w(f, "\n    const struct {}_broadcast* in".format(name))
        _w(f, ");\n")
        _w(f, '\n')

    _w(f, "uint8_t layer2_communicate();\n")
    _w(f, "\n")
    _w(f, "#endif")

def _generate_source(interface, header_filename, f):
    _w(f, '#include "{}"\n'.format(os.path.basename(header_filename)))
    _w(f, '\n')
    _w(f, 'uint8_t layer2_communicate()\n')
    _w(f, '{\n')
    _w(f, '    uint8_t rxStatus = robonet_receive();\n')
    _w(f, '    if (rxStatus != ROBONET_OK)\n')
    _w(f, '        return rxStatus;\n')
    _w(f, '\n')
    _w(f, '    switch (robonetBuffer.address)\n')
    _w(f, '    {\n')
    for i, (name, rr) in enumerate(interface.request_response.items()):
        _w(f, '    case ROBONET_OWN_ADDRESS | 0x{:02x}:\n'.format(i << 8))
        _w(f, '        if (robonetBuffer.length != {})\n'.format(len(rr.request)))
        _w(f, '            return LAYER2_INVALID_MESSAGE_LENGTH;\n')
        _w(f, '        handle_{}('.format(name))
        if not rr.request.empty():
            _w(f, '\n            (const struct {}_request*)&(robonetBuffer.data)'.format(name))
            if not rr.response.empty():
                _w(f, ',')
        if not rr.response.empty():
            _w(f, '\n            (struct {}_response*)&(robonetBuffer.data)'.format(name))
        _w(f, ');\n')
        _w(f, '        robonetBuffer.length = {};\n'.format(len(rr.response)))
        _w(f, '        robonet_transmit();\n')
        _w(f, '        return LAYER2_OK;\n'.format(len(rr.response)))
        _w(f, '\n')

    for i, (name, broadcast) in enumerate(interface.broadcast.items()):
        _w(f, '    case ROBONET_BROADCAST_ADDRESS | 0x{:02x}:\n'.format(i << 8))
        _w(f, '        if (robonetBuffer.length != {})\n'.format(len(broadcast.broadcast)))
        _w(f, '            return LAYER2_INVALID_MESSAGE_LENGTH;\n')
        _w(f, '        handle_{}_broadcast('.format(name))
        if not broadcast.broadcast.empty():
            _w(f, '\n            (const struct {}_request*)&(robonetBuffer.data)'.format(name))
        _w(f, ');\n')
        _w(f, '        return LAYER2_OK;\n'.format(len(rr.response)))
        _w(f, '\n')

    _w(f, '    default:\n')
    _w(f, '        return LAYER2_UNKNOWN_MESSAGE_TYPE;\n')
    _w(f, '    }\n')
    _w(f, '}\n')

def add_args(parser):
    parser.add_argument('--output-header', required=True, type=argparse.FileType('wb'),
        help='Header file name')
    parser.add_argument('--output-source', required=True, type=argparse.FileType('wb'),
        help='Source file name')

def generate(interface, args):
    _generate_header(interface, args.output_header.name, args.output_header)
    _generate_source(interface, args.output_header.name, args.output_source)
