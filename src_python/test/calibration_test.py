from nose.tools import *
from calibration import *
import math

def test_distances():
    l1 = ((0, 0), (10, 0))
    l2 = ((10, 0), (15, 5))
    p1 = (-1, -1)
    p2 = (5, 3)
    p3 = (13, 1)

    assert_almost_equal(squaredDistanceFromPoint(p1, l1[0]), 2)

    assert_almost_equal(squaredDistanceFromLine(p1, l1), 2)
    assert_almost_equal(squaredDistanceFromLine(p3, l1), 10)
    assert_almost_equal(squaredDistanceFromLine(p2, l1), 9)

    assert_almost_equal(squaredDistanceFromLines(p1, [l1, l2]), 2)
    assert_almost_equal(squaredDistanceFromLines(p3, [l1, l2]), 2)
