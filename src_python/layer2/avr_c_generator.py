import os.path
import re
import argparse
import codegen_helper

def _struct(struct, name, f):
    if struct.empty():
        f("/* Skipped empty struct {} */", name)
        return

    f("struct {}", name)
    f.open_brace()
    for name, t in struct.members.items():
        f("{}_t {};", t, name)
    f.close_brace("}};")
    f()

def _generate_header(interface, header_filename, f):
    guard = re.sub("[^A-Z]", "_", os.path.basename(header_filename).upper())

    f("/* Automatically generated file. Do not edit. */")
    f("#ifndef {}", guard)
    f("#define {}", guard)
    f()
    f("#include <stdint.h>")
    f('#include "{}"', interface.robonet_header)
    f()
    f('/* Interface checksum: 0x{:02x} */', interface.checksum)
    f()
    f('#define LAYER2_OK                     ROBONET_OK')
    f('#define LAYER2_BUSY                   ROBONET_BUSY')
    f('#define LAYER2_INVALID_MESSAGE_LENGTH (ROBONET_LAST_STATUS + 1)')
    f('#define LAYER2_UNKNOWN_MESSAGE_TYPE   (ROBONET_LAST_STATUS + 2)')
    f()
    f('extern uint8_t layer2Status;')
    f()

    for i, (name, rr) in enumerate(interface.request_response.items()):
        f("/* Request id: {} */", i)
        _struct(rr.request, name + "_request", f)
        _struct(rr.response, name + "_response", f)
        f("void handle_{}(", name)
        f.align()
        if not rr.request.empty():
            f("const struct {}_request* in", name)
            if not rr.response.empty():
                f(",")
        if not rr.response.empty():
            f("struct {}_response* out", name)
        f(");")
        f.dedent();
        f()

    for i, (name, broadcast) in enumerate(interface.broadcast.items()):
        f("/* Broadcast id: {} */", i)
        _struct(broadcast.broadcast, name + "_broadcast", f)
        f("void handle_{}_broadcast(", name)
        f.align()
        if not broadcast.broadcast.empty():
            f("const struct {}_broadcast* in", name)
        f(");")
        f.dedent()
        f()

    f("void layer2_communicate();")
    f()
    f("#endif")

def _generate_source(interface, header_filename, f):
    f('#include "{}"'.format(os.path.basename(header_filename)))
    f()
    f('uint8_t layer2Status;')
    f()
    f('void layer2_communicate()')
    f.open_brace()
    f('uint8_t rxStatus = robonet_receive();')
    f('if (rxStatus != ROBONET_OK)')
    f.open_brace()
    f('layer2Status = rxStatus;')
    f('return;')
    f.close_brace()
    f()
    f('switch (robonetBuffer.address)')
    f.open_brace()

    for i, (name, rr) in enumerate(interface.request_response.items()):
        f('case ROBONET_OWN_ADDRESS | 0x{:02x}:', i << 8)
        f('if (robonetBuffer.length != {})', len(rr.request))
        f.open_brace()
        f('layer2Status = LAYER2_INVALID_MESSAGE_LENGTH;')
        f('return;')
        f.close_brace()
        f('handle_{}(', name)
        f.align()
        if not rr.request.empty():
            f('(const struct {}_request*)&(robonetBuffer.data)', name)
            if not rr.response.empty():
                f(',')
        if not rr.response.empty():
            f('(struct {}_response*)&(robonetBuffer.data)', name)
        f(');')
        f.dedent()
        f('robonetBuffer.length = {};', len(rr.response))
        f('robonet_transmit();')
        f('layer2Status = LAYER2_OK;')
        f('return;')
        f()

    for i, (name, broadcast) in enumerate(interface.broadcast.items()):
        f('case ROBONET_BROADCAST_ADDRESS | 0x{:02x}:', i << 8)
        f('if (robonetBuffer.length != {})', len(broadcast.broadcast))
        f.open_brace()
        f('layer2Status = LAYER2_INVALID_MESSAGE_LENGTH;')
        f('return;')
        f.close_brace()
        f('handle_{}_broadcast(', name)
        f.align()
        if not broadcast.broadcast.empty():
            f('(const struct {}_request*)&(robonetBuffer.data)', name)
        f(');')
        f.dedent();
        f('layer2Status = LAYER2_OK;')
        f('return;')
        f()

    f('default:')
    f('layer2Status = LAYER2_UNKNOWN_MESSAGE_TYPE;')
    f('return;')

    f.close_brace()
    f.close_brace()

def add_args(parser):
    parser.add_argument('--output-header', required=True, type=argparse.FileType('wb'),
        help='Header file name')
    parser.add_argument('--output-source', required=True, type=argparse.FileType('wb'),
        help='Source file name')

def generate(interface, args):
    header = codegen_helper.CodegenHelper(args.output_header)
    _generate_header(interface, args.output_header.name, header)
    source = codegen_helper.CodegenHelper(args.output_source)
    _generate_source(interface, args.output_header.name, source)
