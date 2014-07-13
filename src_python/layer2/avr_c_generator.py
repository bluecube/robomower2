import os.path
import re
import argparse
import codegen_helper
import interface
import string

def _type(t):
    ret = "int" + str(t.size) + "_t"
    if t.unsigned:
        ret = "u" + ret
    return ret

def _array(t):
    if not t.array:
        return ""
    else:
        return "[" + str(t.array) + "]"

def _string(s):
    ret = ['"']
    for char in s:
        if char not in string.printable or char in '"\\':
            ret.append("\\u{:04x}".format(ord(char)))
        else:
            ret.append(char)
    ret.append('"')
    return ''.join(ret)

def _struct(struct, name, f):
    if struct.empty():
        f("/* Skipped empty struct {} */", name)
        return

    f("struct {}", name)
    f.open_brace()
    for field_name, t in struct.members.items():
        f("{} {}{};", _type(t), field_name, _array(t))
        if t.multiplier != 1:
            f("#define {}_{}_MULTIPLIER {}", name.upper(), field_name.upper(), t.multiplier)
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

def _generate_header(interface, header_filename, robonet_header, f):
    guard = re.sub("[^A-Z]", "_", os.path.basename(header_filename).upper())

    f("/* Automatically generated file. Do not edit. */")
    f()
    f("#ifndef {}", guard)
    f("#define {}", guard)
    f()
    f("#include <stdint.h>")
    f('#include "{}"', robonet_header)
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
    f('/* Interface constants */')
    for name, value in interface.constants.items():
        if isinstance(value, str):
            value = _string(value)
        else:
            value = repr(value)
        f('#define {} {}', name, value)
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
    f('out->interfaceChecksum = 0x{:02x};', interface.checksum)
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

    for name, rr in interface.request_response.items():
        f('case ROBONET_OWN_ADDRESS | 0x{:02x}:', rr.id << 4)
        f.indent()
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
        f('robonetBuffer.address = ROBONET_MASTER_ADDRESS;')
        f('robonet_transmit();')
        f('break;')
        f.dedent()
        f()

    for name, broadcast in interface.broadcast.items():
        f('case ROBONET_BROADCAST_ADDRESS | 0x{:02x}:', broadcast.id << 4)
        f.indent()
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
        f('break;')
        f.dedent()
        f()

    f('default:')
    f.indent()
    f('layer2Status = LAYER2_UNKNOWN_MESSAGE_TYPE;')
    f('return;')
    f.dedent()

    f.close_brace()

    f('layer2Status = robonet_receive_complete();')

    f.close_brace()

def add_args(parser):
    parser.add_argument('--output-header', required=True, type=argparse.FileType('wb'),
        help='Header file name')
    parser.add_argument('--output-source', required=True, type=argparse.FileType('wb'),
        help='Source file name')
    parser.add_argument('--robonet-header', required=True,
        help='Path for including the robonet header file from the generated code')

def generate(interface, args):
    robonet_header = args.robonet_header
    if not os.path.isabs(robonet_header):
        robonet_header = os.path.join(os.path.dirname(args.spec), robonet_header)

    header = codegen_helper.CodegenHelper(args.output_header)
    _generate_header(interface, args.output_header.name, robonet_header, header)
    source = codegen_helper.CodegenHelper(args.output_source)
    _generate_source(interface, args.output_header.name, source)
