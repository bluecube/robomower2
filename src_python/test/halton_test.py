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

def values_test():
    it = halton.HaltonSequence(2)
    for expected in [(1/2, 1/3), (1/4, 2/3), (3/4, 1/9), (1/8, 4/9), (5/8, 7/9), (3/8, 2/9)]:
        actual = next(it)

        print("actual = {}, expected = {}".format(str(actual), str(expected)))
        assert_almost_equal(actual[0], expected[0])
        assert_almost_equal(actual[1], expected[1])
