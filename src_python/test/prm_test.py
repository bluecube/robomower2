from nose.tools import *
from path_planning import prm, local_planner, State
import path_planner_util
import math

def check_path(states):
    times = [local_planner.plan_path(s1, s2).travel_time
             for s1, s2 in zip(states[:-1], states[1:])]

    it = prm._PathIterator(states, sum(times))
    path_planner_util.check_it_equal_to_state(it, states[0])

    for time, state in zip(times, states[1:]):
        it.advance(time)
        path_planner_util.check_it_equal_to_state(it, state)

    it.reset()

    path_planner_util.check_path(it)

def path_iterator_test():
    yield (check_path, [
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 1, 0, 0)])
    yield (check_path, [
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 1, 0, 0),
           State(2, 0, 0, 1, 0, 0)])
    yield (check_path, [
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 0.5, 0, 1),
           State(2, 0, 0, 1, 0, 0)])
    yield (check_path, [
           State(0, 0, 0, 1, 0, 0),
           State(1, 0, 0, 0.5, 0, 1),
           State(5, 2, math.radians(90), 1, 0, 0)])
