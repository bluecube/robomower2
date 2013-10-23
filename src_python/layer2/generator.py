#!/usr/bin/python3
import argparse
import interface

import avr_c_generator
import avr_dependency_generator

formats = {
    'avr_c': avr_c_generator,
    'avr_dependency': avr_dependency_generator
}

parser = argparse.ArgumentParser(description='Generate interface parser from given specification.')
parser.add_argument('spec');
parser.add_argument('--format', '-f', required=True, choices=formats.keys(),
    help='Format in wich to output')
args = parser.parse_known_args()[0]

formats[args.format].add_args(parser)
args = parser.parse_args()

iface = interface.Interface(args.spec)
formats[args.format].generate(iface, args)
