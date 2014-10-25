from . import local_planner
from . import path_iterator

import collections
import logging
import itertools

import kdtree

class Prm:
    """ General probabilistic roadmap """

    nearest_neighbors = 5

    Node = collections.namedtuple("Node", ["state", "connections"])
    Connection = collections.namedtuple("Connection", ["node", "travel_time", "cost"])

    def __init__(self, planning_parameters):
        self._parameters = planning_parameters
        self._nodes = kdtree.KdTree()

        self._logger = logging.getLogger(__name__)

        self._build_roadmap()

    def plan_path(self, state1, state2):
        raise NotImplementedError();

    def _build_roadmap(self):
        for i in range(500):
            print(i)
            self._add_state(self._parameters.random_state())

        self._logger.info("Finished building roadmap, %d nodes, %d connections",
                          len(self._nodes),
                          self._get_connection_count())

    def _add_state(self, state):
        cost = self._parameters.state_cost(state)

        if cost is None:
            return

        node = self.Node(state, [])
        self._nodes.insert((state.x, state.y), node)

        for other in itertools.islice(self._nodes.nearest_neighbors((state.x, state.y)),
                                      self.nearest_neighbors):
            self._try_connect(node, other)
            self._try_connect(other, node)

    def _try_connect(self, node1, node2):
        path = local_planner.plan_path(node1.state, node2.state)
        if path is None:
            return

        travel_time = path.travel_time
        cost = self._path_cost(path)

        if cost is None:
            return

        node1.connections.append(self.Connection(node2, travel_time, cost))


    def _path_cost(self, path_iterator, resolution = 0.1):
        """ Estimate integral of self._parameters.state_cost over the states on path_iterator. """

        cost = self._parameters.state_cost(path_iterator)
        if cost is None:
            # We shouldn't try to connect invalid states, but jerk limit might
            # get exceeded even in the first state of the path 
            return None
        while True:
            try:
                path_iterator.advance(resolution)
            except StopIteration:
                return cost

            state_cost = self._parameters.state_cost(path_iterator)
            if state_cost is None:
                return None
            else:
                cost += state_cost

    def _get_connection_count(self):
        return sum(len(node[1].connections) for node in self._nodes)

class _PathIterator(path_iterator.PathIterator):
    def __init__(self, states, travel_time):
        if len(states) < 2:
            raise ValueError("There must be at least two states.")
        self._states = states
        self.travel_time = travel_time

    def reset(self):
        self.time = 0
        self._i = 0
        self._load_sub()

    def _load_sub(self):
        self._sub = local_planner.plan_path(states[self._i], states[self._i + 1])

    def advance(self, dt):
        self.time += dt

        while dt >= self._sub.travel_time - self._sub.time:
            dt -= self._sub,travel_time - self._sub.time
            self._i += 1

            if self._i >= len(self._states) - 1:
                raise StopIteration()

            self._load_sub()

        assert(dt >= 0)
        assert(dt < self._sub.travel_time - self._sub.time)

        if dt == 0:
            return

        self._sub.advance(dt)

    def __getattr__(self, key):
        """ The rest of values gets taken from the sub iterator """
        return getattr(self._sub, key)
