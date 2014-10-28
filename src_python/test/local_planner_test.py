from nose.tools import *

from path_planning import local_planner
from path_planning import State

def check_path(state1, state2):
    it = local_planner.plan_path(state1, state2)

    for fieldname in State._fields:
        assert_almost_equal(getattr(it, fieldname), getattr(state1, fieldname))

    it.advance(it.travel_time)
    for fieldname in State._fields:
        assert_almost_equal(getattr(it, fieldname), getattr(state2, fieldname))

    it.reset()
    for fieldname in State._fields:
        assert_almost_equal(getattr(it, fieldname), getattr(state1, fieldname))

    n = 10
    for i in range(n):
        it.advance(it.travel_time/n)

    for fieldname in State._fields:
        assert_almost_equal(getattr(it, fieldname), getattr(state2, fieldname))

def test():
    check_path(State(0, 0, 0, 1, 0, 0),
               State(1, 5, 0, 1, 0, 0))
    check_path(State(0, 0, 0, 1, 0, 0),
               State(1, 0, 0, 0, 0, 0))
