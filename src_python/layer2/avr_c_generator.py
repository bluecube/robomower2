import os.path
import re
import argparse
import codegen_helper
import interface

def _struct(struct, name, f):
    if struct.empty():
        f("/* Skipped empty struct {} */", name)
        return

    f("struct {}", name)
    f.open_brace()
    for name, t in struct.members.items():
        f("{}_t {};", t, name)
    f.close_brace("}};")

def _handle_function_decl(data, name, semicolon, f, extra_specifier = ""):
    if len(extra_specifier) and not extra_specifier.endswith(' '):
        extra_specifier += ' '
    if type(data) == interface.Broadcast:
        f(extra_specifier + 'void handle_{}_broadcast(', name)
        if data.broadcast.empty():
            in_struct = None
        else:
            in_struct = data.broadcast
            in_name = "{}_broadcast"
        out_struct = None
    else:
        f(extra_specifier + 'void handle_{}_request(', name)
        if data.request.empty():
            in_struct = None
        else:
            in_struct = data.request
            in_name = "{}_request"
        if data.response.empty():
            out_struct = None
        else:
            out_struct = data.response
            out_name = "{}_response"

    f.align()

    if in_struct is not None:
        f("const struct " + in_name + "* in", name)
        if out_struct is not None:
            f(",")
    if out_struct is not None:
        f("struct " + out_name + "* out", name)

    if semicolon:
        f(");")
    else:
        f(")")
    f.dedent()

def _generate_header(interface, header_filename, f):
    guard = re.sub("[^A-Z]", "_", os.path.basename(header_filename).upper())

    f("/* Automatically generated file. Do not edit. */")
    f()
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
        if rr.automatic:
            f("/* Skipped automatic request '{}', id: {} */", name, i)
            f()
            continue
        f("/* Request id: {} */", i)
        _struct(rr.request, name + "_request", f)
        _struct(rr.response, name + "_response", f)
        _handle_function_decl(rr, name, True, f)
        f()

    for i, (name, broadcast) in enumerate(interface.broadcast.items()):
        if broadcast.automatic:
            f("/* Skipped automatic broadcast '{}', id: {} */", name, i)
            f()
            continue
        f("/* Broadcast id: {} */", i)
        _struct(broadcast.broadcast, name + "_broadcast", f)
        _handle_function_decl(broadcast, name, True, f)
        f()

    f("void layer2_init();")
    f("void layer2_communicate();")
    f()
    f("#endif")

def _generate_source(interface, header_filename, f):
    f("/* Automatically generated file. Do not edit. */")
    f()
    f('#include "{}"'.format(os.path.basename(header_filename)))
    f()
    f('uint8_t layer2Status;')
    f()
    _struct(interface.request_response['status'].request, "status_request", f)
    _struct(interface.request_response['status'].response, "status_response", f)
    _handle_function_decl(interface.request_response['status'], 'status', False,
                          f, extra_specifier = "static")
    f.open_brace()
    f('out->status = layer2Status;')
    f('out->interface_checksum = 0x{:02x};', interface.checksum)
    f.close_brace()
    f()

    f('void layer2_init()')
    f.open_brace()
    f('robonet_init();')
    f.close_brace()
    f()

    f('void layer2_communicate()')
    f.open_brace()
    f('uint8_t rxStatus = robonet_receive();')
    f('if (rxStatus == ROBONET_BUSY)')
    f.indent()
    f('return;')
    f.dedent()
    f('else if (rxStatus != ROBONET_OK)')
    f.open_brace()
    f('layer2Status = rxStatus;')
    f('return;')
    f.close_brace()
    f()
    f('switch (robonetBuffer.address)')
    f.open_brace()

    for i, (name, rr) in enumerate(interface.request_response.items()):
        f('case ROBONET_OWN_ADDRESS | 0x{:02x}:', i << 4)
        f('if (robonetBuffer.length != {})', len(rr.request))
        f.open_brace()
        f('layer2Status = LAYER2_INVALID_MESSAGE_LENGTH;')
        f('return;')
        f.close_brace()
        f('handle_{}_request(', name)
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
        f('case ROBONET_BROADCAST_ADDRESS | 0x{:02x}:', i << 4)
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
