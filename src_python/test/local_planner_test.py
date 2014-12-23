from path_planning import local_planner
from path_planning import State

import path_planner_util

import math

def local_check_path(state1, state2):
    it = local_planner.plan_path(state1, state2)

    path_planner_util.check_it_equal_to_state(it, state1)
    it.advance(it.travel_time)
    assert(it.finished())
    path_planner_util.check_it_equal_to_state(it, state2)
    it.reset()
    path_planner_util.check_it_equal_to_state(it, state1)

    path_planner_util.check_path(it)

    assert(it.finished())
    path_planner_util.check_it_equal_to_state(it, state2)

def test():
    yield (local_check_path,
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 1, 0, 0))
    yield (local_check_path,
           State(0, 0, 0, 1, 0, 1),
           State(1, 1, math.radians(90), 1, 0, 1))
    yield (local_check_path,
           State(0, 0, 0, 1, 0, 0),
           State(5, 1, 0, 1, 0, 0))
    yield (local_check_path,
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 0, 0, 0))
    yield (local_check_path,
           State(0, 0, 0, 1, 0, 0),
           State(5, 0, 0, 2, 0.7, 1))
