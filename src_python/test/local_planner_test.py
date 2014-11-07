from nose.tools import *
import math

from path_planning import local_planner
from path_planning import State

def check_it_equal_to_state(it, state):
    for fieldname in State._fields:
        assert_almost_equal(getattr(it, fieldname), getattr(state, fieldname), msg="Field " + fieldname)

def check_path(state1, state2):
    it = local_planner.plan_path(state1, state2)

    check_it_equal_to_state(it, state1)
    it.advance(it.travel_time)
    check_it_equal_to_state(it, state2)
    it.reset()
    check_it_equal_to_state(it, state1)

    n = 1000
    prev_x = it.x
    prev_y = it.y
    prev_v = it.velocity
    dt = it.travel_time / n
    for i in range(n):
        it.advance(it.travel_time/n)
        dx = it.x - prev_x
        dy = it.y - prev_y
        dv = it.velocity - prev_v

        assert_almost_equal(math.hypot(dx, dy) / dt, it.velocity, delta=0.01)
        assert_almost_equal(dv / dt, it.acceleration, delta=0.01)

        prev_x = it.x
        prev_y = it.y
        prev_v = it.velocity

    check_it_equal_to_state(it, state2)

def test():
    check_path(State(0, 0, 0, 1, 0, 0),
               State(1, 5, 0, 1, 0, 0))
    check_path(State(0, 0, 0, 1, 0, 0),
               State(1, 0, 0, 0, 0, 0))
