import math
from nose.tools import *
import util.frechet_distance as F

test_data = [
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
     10 * math.sqrt(2)),
    ([(0, 0), (1, 1), (11, 1), (12, 2)],
     [(1, 0), (11, 0), (1, 2), (11, 2)],
     math.sqrt(5 * 5 + 1))
    ]

def decision_test():
    def test_func(pl1, pl2, epsilon):
        assert_false(F.frechet_distance_decision(pl1, pl2, epsilon - 1))
        assert_true(F.frechet_distance_decision(pl1, pl2, epsilon * (1 + 1e-8))) # to prevent rounding errors
        assert_true(F.frechet_distance_decision(pl1, pl2, epsilon + 1))
        assert_true(F.frechet_distance_decision(pl1, pl2, epsilon + 1000))

    assert_true(F.frechet_distance_decision([(0, 0), (10, 0), (20, 0)],
                                            [(0, 0), (10, 0), (20, 0)],
                                            0))
    assert_true(F.frechet_distance_decision([(0, 0), (20, 0)],
                                            [(0, 0), (10, 0), (20, 0)],
                                            0))

    for pl1, pl2, epsilon in test_data:
        yield (test_func, pl1, pl2, epsilon)

def pass_test():
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (5, 0), 2), (0.3, 0.7))
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (5, 5), 5), (0.5, 0.5))
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (10, 0), 5), (0.5, 1))
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (10, 0), 5), (0.5, 1))
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (20, 0), 5), (1.5, 1))
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (-10, 0), 5), (0, -0.5))
    assert_equal(F._calc_pass(((0, 0), (10, 0)), (5, 4), 5), (0.2, 0.8))

def distance_test():
    def test_func(pl1, pl2, epsilon):
        assert_almost_equal(F.frechet_distance(pl1, pl2), epsilon)

    assert_almost_equal(F.frechet_distance([(0, 0), (10, 0), (20, 0)],
                                           [(0, 0), (10, 0), (20, 0)]),
                        0)
    assert_almost_equal(F.frechet_distance([(0, 0), (20, 0)],
                                           [(0, 0), (10, 0), (20, 0)]),
                        0)

    for pl1, pl2, epsilon in test_data:
        yield (test_func, pl1, pl2, epsilon)
