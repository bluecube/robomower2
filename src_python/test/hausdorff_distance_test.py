from nose.tools import *
import util.hausdorff_distance as H
import math

test_data = [
    ([(0, 0), (10, 0), (20, 0)],
     [(0, 0), (10, 0), (20, 0)],
     0),
    ([(0, 0), (20, 0)],
     [(0, 0), (10, 0), (20, 0)],
     0),
    ([(0, 0), (10, 0)],
     [(0, 10), (10, 10)],
     10),
    ([(0, 0), (10, 0), (20, 0), (30, 0)],
     [(0, 10), (10, 10), (20, 10), (30, 10)],
     10),
    ([(0, 0), (10, 0), (20, 0), (30, 0)],
     [(0, 10), (10, 10), (20, 20), (30, 10)],
     20),
    ([(0, 0), (40, 0)],
     [(0, 10), (10, 10), (20, -10), (30, 10), (40, 10)],
     10),
    ([(0, 0), (10, 10), (10, -10), (0, 0)],
     [(0, 0), (10, -10), (10, 10), (0, 0)],
     0),
    ]

def distance_test1():
    pl = [(0, 0), (10, 0), (15, 5)]
    p1 = (-1, -1)
    p2 = (5, 3)
    p3 = (13, 1)

    assert_almost_equal(H._point_to_point(p1, pl[0]), 2)

    assert_almost_equal(H._point_to_line(p1, pl[:2]), 2)
    assert_almost_equal(H._point_to_line(p3, pl[:2]), 10)
    assert_almost_equal(H._point_to_line(p2, pl[:2]), 9)

    assert_almost_equal(H._point_to_polyline(p1, pl), 2)
    assert_almost_equal(H._point_to_polyline(p3, pl), 2)

def distance_test2():
    def test_func(pl1, pl2, distance):
        assert_almost_equal(H.hausdorff_distance(pl1, pl2), distance)

    for pl1, pl2, distance in test_data:
        yield (test_func, pl1, pl2, distance)
