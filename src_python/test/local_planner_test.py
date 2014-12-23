from nose.tools import *
import math
import collections

from path_planning import local_planner
from path_planning import State

def check_it_equal_to_state(it, state):
    for fieldname in State._fields:
        assert_almost_equal(getattr(it, fieldname), getattr(state, fieldname), msg="Field " + fieldname)

def check_path(state1, state2):
    it = local_planner.plan_path(state1, state2)

    check_it_equal_to_state(it, state1)
    it.advance(it.travel_time)
    assert(it.finished())
    check_it_equal_to_state(it, state2)
    it.reset()
    check_it_equal_to_state(it, state1)

    n = 1000
    print("travel time:", it.travel_time)
    dt = it.travel_time / n
    prev = collections.deque(maxlen=2)

    prev.append((it.x, it.y, it.velocity, it.curvature))
    it.advance(dt)
    prev.append((it.x, it.y, it.velocity, it.curvature))
    it.advance(dt)

    while not it.finished():
        dv = it.velocity - prev[-1][2]
        assert_almost_equal(dv / dt, it.acceleration, delta=1e-3)

        d1x = prev[-1][0] - prev[-2][0]
        d1y = prev[-1][1] - prev[-2][1]
        d2x = it.x - prev[-1][0]
        d2y = it.y - prev[-1][1]
        # diameter of a circle defined by the last three points
        #d = math.sqrt((d1x * d1x + d1y * d1y) * (((d1x * d2x + d1y * d2y) / (d1x * d2y - d1y * d2x))**2 + 1))
        curvature = (d1x * d2y - d1y * d2x) / ((d1x * d1x + d1y * d1y) * math.hypot(d2x, d2y))
        distance = math.hypot(it.x - prev[-2][0], it.y - prev[-2][1])
        if curvature > 1e-6:
            distance = 2 * math.asin(distance * curvature / 2) / curvature
        print(d1x, d1y, d2x, d2y, "XX", curvature, distance, "XX", prev[-1][3], prev[-1][2] * (2 * dt))
        assert_almost_equal(distance / (2 * dt), prev[-1][2], delta=1e-2)
        if not math.isnan(curvature):
            assert_almost_equal(curvature, prev[-1][3], delta=1e-2)

        prev.append((it.x, it.y, it.velocity, it.curvature))

        it.advance(dt)

    assert(it.finished())
    check_it_equal_to_state(it, state2)

def test():
    yield (check_path,
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 1, 0, 0))
    yield (check_path,
           State(0, 0, 0, 1, 0, 1),
           State(0, 1, -math.radians(180), 1, 0, 1))
    yield (check_path,
           State(0, 0, 0, 1, 0, 0),
           State(1, 5, 0, 1, 0, 0))
    yield (check_path,
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 0, 0, 0))
    yield (check_path,
           State(0, 0, 0, 1, 0, 0),
           State(5, 0, 0, 2, 0.7, 1))
