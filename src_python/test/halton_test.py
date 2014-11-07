from nose.tools import *

from util import halton

def uniqueness_test():
    values = set()
    sequence = halton.HaltonSequence(1)
    for i in range(1000):
        values.add(tuple(next(sequence)))
    assert_equal(len(values), 1000)

    values = set()
    sequence = halton.HaltonSequence(len(halton.HaltonSequence.primes))
    for i in range(1000):
        values.add(tuple(next(sequence)))
    assert_equal(len(values), 1000)
