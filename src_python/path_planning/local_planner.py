#!/usr/bin/python3

import numpy
import math

def find_path(state1, state2):
    """ Find path from state 1 to state 2.
    State is a tuple (x, y, phi).
    Returns the polynomial (callable), does no further checks.
    The path goes with parameter from 0 to 1. """

    #                p0 q0   p1 q1   p2 q2   p3 q3
    A = numpy.array([
                     # Endpoint positions:
                     [1, 0,   0, 0,   0, 0,   0, 0],
                     [1, 0,   1, 0,   1, 0,   1, 0],
                     [0, 1,   0, 0,   0, 0,   0, 0],
                     [0, 1,   0, 1,   0, 1,   0, 1],

                     # Endpoint derivations:
                     [0, 0,   1, 0,   0, 0,   0, 0],
                     [0, 0,   0, 1,   0, 0,   0, 0],
                     [0, 0,   1, 0,   2, 0,   3, 0],
                     [0, 0,   0, 1,   0, 2,   0, 3],

                     ])

    rawdist = math.hypot(state2[0] - state1[0], state2[1] - state1[1]) * 2

    b = numpy.array([state1[0],
                     state2[0],
                     state1[1],
                     state2[1],
                     math.cos(state1[2]) * rawdist,
                     math.sin(state1[2]) * rawdist,
                     math.cos(state2[2]) * rawdist,
                     math.sin(state2[2]) * rawdist,
                     ])

    print(A)

    x = numpy.linalg.solve(A, b)

    return numpy.polynomial.Polynomial(x[::2]), numpy.polynomial.Polynomial(x[1::2])


if __name__ == "__main__":
    def p2str(poly):
        return ' + '.join("{:.2g} * t**{}".format(coef, i) for i, coef in enumerate(poly.coef) if coef != 0)

    x, y = find_path((0, 0, 0), (2, 1, math.radians(0)))
    print(p2str(x), ", ", p2str(y))
