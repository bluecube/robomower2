import argparse

def add_args(parser):
    parser.add_argument('--output', required=True, type=argparse.FileType('wb'),
        help='Output file')
    parser.add_argument('--target', required=True, action='append',
        help='Target')

def generate(interface, args):
    args.output.write(' '.join(args.target).encode('ascii'))
    args.output.write(': '.encode('ascii'))
    args.output.write((interface.robonet_header + ' ').encode('ascii'))
    args.output.write((args.spec + ' ').encode('ascii'))
    args.output.write(' '.join(interface.includes).encode('ascii'))
    args.output.write('\n'.encode('ascii'))
